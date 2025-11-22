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
# We will create these models in the next steps, but we must import them here.
from app.models import *

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the target metadata for 'autogenerate' support.
# Our Base class from app/db/base_class.py holds this metadata.
target_metadata = Base.metadata

# Get the database URL from our application settings
# We use the synchronous DATABASE_URL for the offline runner,
# as it doesn't execute async code.
# We must replace the 'asyncpg' driver with 'psycopg' for this.
db_url = str(settings.DATABASE_URL).replace("postgresql+asyncpg", "postgresql+psycopg")
config.set_main_option("sqlalchemy.url", db_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
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
    """
    Helper function to run the migrations.
    """
    context.configure(
        connection=connection, 
        target_metadata=target_metadata
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    This is an async version.
    """
    
    # Create an async engine using our app's settings
    connectable = create_async_engine(
        str(settings.DATABASE_URL),  # Use the async URL from settings
        pool_pre_ping=True,
    )

    async with connectable.connect() as connection:
        # Run the migrations within an async context
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    # Run the async 'online' migration function
    asyncio.run(run_migrations_online())

