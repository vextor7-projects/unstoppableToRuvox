import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

# Import the Base from our app's db module
from app.db.base_class import Base

# Import the settings to get the database URL
from app.core.config import settings

# Import all models so that autogenerate can detect changes
from app.models import *

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the target metadata for 'autogenerate' support.
target_metadata = Base.metadata

# Get the database URL from our application settings
# We use the synchronous DATABASE_URL for the offline runner.
db_url = str(settings.DATABASE_URL).replace("postgresql+asyncpg", "postgresql+psycopg")
config.set_main_option("sqlalchemy.url", db_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Helper function to run the migrations."""
    context.configure(
        connection=connection, 
        target_metadata=target_metadata
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    
    # CRITICAL FIX: Add connect_args={"statement_cache_size": 0} here as well
    connectable = create_async_engine(
        str(settings.DATABASE_URL),
        pool_pre_ping=True,
        connect_args={"statement_cache_size": 0}
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())