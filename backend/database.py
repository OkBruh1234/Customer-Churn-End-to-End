import os

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker


def normalize_database_url(database_url):
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)

    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    return database_url


def create_db_engine(database_url):
    normalized_url = normalize_database_url(database_url)

    engine_kwargs = {}
    if normalized_url.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
    else:
        # Serverless Postgres (Neon, Supabase) suspends compute after a few
        # minutes of inactivity and drops open connections. Without pre-ping the
        # pool hands out a connection the server has already closed and the
        # request fails with OperationalError; pre-ping tests it first and
        # transparently reconnects. This pairs with a spun-down free web
        # instance, where idle gaps are the normal case rather than the
        # exception.
        engine_kwargs["pool_pre_ping"] = True
        # Retire connections before the provider's idle-suspend window rather
        # than discovering server-side that they are gone.
        engine_kwargs["pool_recycle"] = 240
        # A 512 MB instance needs no large pool, and free Postgres tiers cap
        # concurrent connections.
        engine_kwargs["pool_size"] = 5
        engine_kwargs["max_overflow"] = 5

    return create_engine(normalized_url, **engine_kwargs)


DATABASE_URL = normalize_database_url(os.getenv("DATABASE_URL", "sqlite:///./churn_app.db"))

engine = create_db_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from backend import models

    Base.metadata.create_all(bind=engine)
    run_startup_migrations(engine)


def run_startup_migrations(target_engine=None):
    migration_engine = target_engine or engine
    inspector = inspect(migration_engine)
    if not inspector.has_table("predictions"):
        return

    existing_columns = {column["name"] for column in inspector.get_columns("predictions")}
    migration_statements = []

    if "actual_outcome" not in existing_columns:
        migration_statements.append(
            "ALTER TABLE predictions ADD COLUMN actual_outcome VARCHAR(20)"
        )

    if "outcome_recorded_at" not in existing_columns:
        migration_statements.append(
            "ALTER TABLE predictions ADD COLUMN outcome_recorded_at DATETIME"
        )

    if not migration_statements:
        return

    with migration_engine.begin() as connection:
        for statement in migration_statements:
            connection.execute(text(statement))
