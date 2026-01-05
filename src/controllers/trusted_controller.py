import base64
import json
from typing import Any

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from sqlmodel import Session, SQLModel

from src.config import settings
from src.helpers.access_token import create_access_token
from src.models.authentication_model import Blacklist, Users
from src.models.trusted_model import Trusted
from src.utils.custom_errors import AuthorisationError
from src.utils.fetcher import Fetcher

error_message = "Trusted Service not found"


def serialize_public_key(public_key):
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")


def serialize_private_key(private_key):
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")


def generate_rsa_key_pair():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return private_key


def load_private_key_from_pem(pem) -> Any:
    return serialization.load_pem_private_key(pem.encode("utf-8"), password=None)


def generate_public_key(db: Session):
    is_private_key_exist = Fetcher(
        database=db,
        table=(Trusted,),
        where=(Trusted.name == settings.SUPER_PRIVATE_KEY,),
    ).get_value()
    private_ = load_private_key_from_pem(is_private_key_exist.private_key)
    return private_.public_key()


def load_public_key_from_pem(pem) -> Any:
    return serialization.load_pem_public_key(pem.encode("utf-8"))


def load_from_pem_to_raw(pem) -> Any:
    lines = pem.strip().splitlines()
    public_key_lines = [line for line in lines if not line.startswith("----")]
    return "".join(public_key_lines)


def get_public_key(name: str, db: Session):
    get_service = Fetcher(
        database=db,
        table=(Trusted,),
        where=(Trusted.name == name,),
        error=error_message,
    ).get_one()
    get_serialized_data = load_from_pem_to_raw(get_service.public_key)
    return get_serialized_data


def generate_keys(name: str, db: Session):
    public_key = generate_public_key(db)
    public_key = serialize_public_key(public_key)

    Fetcher(
        database=db,
        table=(Trusted,),
        where=(Trusted.name == name,),
        error="Trusted Service already exists",
    ).get_exist()

    save_keys = Trusted(
        name=name,
        public_key=public_key,
    )

    db.add(save_keys)
    db.commit()
    db.refresh(save_keys)

    return save_keys


class TrustedEncryptData(SQLModel):
    request_id: str
    username: str
    phone: str


def encrypt_data(data: TrustedEncryptData, name: str, db: Session):
    get_service = Fetcher(
        database=db,
        table=(Trusted,),
        where=(Trusted.name == name,),
        error=error_message,
    ).get_one()

    load_public_key_pem = load_public_key_from_pem(get_service.public_key)
    public_key: rsa.RSAPublicKey = load_public_key_pem

    message = json.dumps(data.__dict__).encode()
    ciphertext = public_key.encrypt(
        message,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    return base64.b64encode(ciphertext)


class TokenDataDecode(SQLModel):
    request_id: str
    username: str
    phone: str


def decrypt_data(data: str, db: Session):
    get_service = Fetcher(
        database=db,
        table=(Trusted,),
        where=(Trusted.name == settings.SUPER_PRIVATE_KEY,),
        error=error_message,
    ).get_one()
    private_key: rsa.RSAPrivateKey = load_private_key_from_pem(
        get_service.private_key,
    )
    try:
        decrypted_data = private_key.decrypt(
            base64.b64decode(data),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        info = json.loads(decrypted_data.decode())
        decoded_token_data = TokenDataDecode(**info)
        check_request_id(
            decoded_token_data.request_id,
            db,
        )
        return authorise_user(
            name=decoded_token_data.username, phone=decoded_token_data.phone, db=db
        )
    except Exception as e:
        raise AuthorisationError(f"Unauthorised Access:{e}")


def check_request_id(request_id: str, db: Session) -> bool:
    Fetcher(
        database=db,
        table=(Blacklist,),
        where=(Blacklist.token == request_id,),
        error="Request ID already used",
    ).get_exist()
    add_request_to_black_list = Blacklist(token=request_id)
    db.add(add_request_to_black_list)
    db.commit()
    return True


class TokenData(SQLModel):
    id: str
    name: str
    phone: str


def authorise_user(name: str, phone: str, db: Session):
    get_user = Fetcher(
        database=db,
        table=(Users,),
        where=(
            Users.name == name,
            Users.phone == phone,
        ),
    ).get_value()

    if not get_user:
        get_user = Users(
            name=name,
            phone=phone,
            verified=True,
        )

        db.add(get_user)
        db.commit()
        db.refresh(get_user)

    return create_access_token(
        data=TokenData(
            id=str(get_user.id),
            **get_user.model_dump(exclude={"id"}),
        ).model_dump()
    )
