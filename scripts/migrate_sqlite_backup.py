from datetime import datetime
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from backend.database import Base, create_db_engine, run_startup_migrations
from backend.models import PredictionLog, User


SOURCE_SQLITE_PATH = Path("churn_app.db")


def parse_datetime(value):
    if value is None or isinstance(value, datetime):
        return value

    text_value = str(value).strip()
    if not text_value:
        return None

    return datetime.fromisoformat(text_value)


def fetch_source_rows(engine, query):
    with engine.connect() as connection:
        return connection.execute(text(query)).mappings().all()


def sync_postgres_sequences(engine):
    if engine.dialect.name != "postgresql":
        return

    sequence_updates = (
        ("users", "id"),
        ("predictions", "id"),
    )

    with engine.begin() as connection:
        for table_name, column_name in sequence_updates:
            connection.execute(
                text(
                    f"""
                    SELECT setval(
                        pg_get_serial_sequence('{table_name}', '{column_name}'),
                        COALESCE((SELECT MAX({column_name}) FROM {table_name}), 1),
                        true
                    )
                    """
                )
            )


def migrate_data():
    if not SOURCE_SQLITE_PATH.exists():
        raise FileNotFoundError(
            f"Source backup database was not found at {SOURCE_SQLITE_PATH.resolve()}"
        )

    source_engine = create_db_engine(f"sqlite:///{SOURCE_SQLITE_PATH.resolve().as_posix()}")
    from backend.database import DATABASE_URL

    target_engine = create_db_engine(DATABASE_URL)

    if str(source_engine.url) == str(target_engine.url):
        raise ValueError("Source and target databases point to the same location.")

    Base.metadata.create_all(bind=target_engine)
    run_startup_migrations(target_engine)

    source_users = fetch_source_rows(source_engine, "SELECT * FROM users ORDER BY id")
    source_predictions = fetch_source_rows(
        source_engine,
        "SELECT * FROM predictions ORDER BY id",
    )

    TargetSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=target_engine)
    target_session = TargetSessionLocal()

    try:
        for row in source_users:
            target_session.merge(
                User(
                    id=row["id"],
                    name=row["name"],
                    created_at=parse_datetime(row["created_at"]),
                )
            )

        for row in source_predictions:
            target_session.merge(
                PredictionLog(
                    id=row["id"],
                    user_id=row["user_id"],
                    churn_probability=row["churn_probability"],
                    risk_level=row["risk_level"],
                    input_payload=row["input_payload"],
                    created_at=parse_datetime(row["created_at"]),
                    actual_outcome=row.get("actual_outcome"),
                    outcome_recorded_at=parse_datetime(row.get("outcome_recorded_at")),
                )
            )

        target_session.commit()
    finally:
        target_session.close()

    sync_postgres_sequences(target_engine)

    print(
        "Migration complete:",
        f"{len(source_users)} users and {len(source_predictions)} predictions copied.",
    )
    print(f"Target database: {target_engine.url}")


if __name__ == "__main__":
    migrate_data()
