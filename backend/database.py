import os

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./churn_app.db")

engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)
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
    run_startup_migrations()


def run_startup_migrations():
    inspector = inspect(engine)
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

    with engine.begin() as connection:
        for statement in migration_statements:
            connection.execute(text(statement))
