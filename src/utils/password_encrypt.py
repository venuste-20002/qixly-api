from passlib.context import CryptContext

encrypt_configuration = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return encrypt_configuration.hash(password)


def compare_password(input_password: str, stored_password) -> bool:
    return encrypt_configuration.verify(input_password, stored_password)
