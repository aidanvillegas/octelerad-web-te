import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

path = Path(__file__).resolve()
parents = list(path.parents)
for index in (1, 2, 3):
    if len(parents) > index and str(parents[index]) not in sys.path:
        sys.path.append(str(parents[index]))

try:
    from services.api.app.config import get_settings  # type: ignore
    from services.api.app.models import Base  # type: ignore
except ModuleNotFoundError:
    sys.path.append(str(path.parent.parent))
    from app.config import get_settings  # type: ignore
    from app.models import Base  # type: ignore

config = context.config
fileConfig(config.config_file_name)
settings = get_settings()
config.set_main_option("sqlalchemy.url", os.getenv("DB_URL", settings.db_url))
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
