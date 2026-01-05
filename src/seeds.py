from src.seeders.create_super_user import create_super_user
from src.seeders.permission_seeder import seed_permissions
from src.seeders.role_permission_seeder import seed_role_permission
from src.seeders.roles_seeder import roles_seeder
from src.seeders.sales_item_number_seeder import sales_items_number_seeder
from src.seeders.transaction_number_seeder import transaction_number_seeders
from src.seeders.trusted_seeder import generate_private_key


async def seeders_run():
    await roles_seeder()
    await create_super_user()
    await seed_permissions()
    await seed_role_permission()
    await generate_private_key()
    await transaction_number_seeders()
    await sales_items_number_seeder()
