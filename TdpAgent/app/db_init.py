from app.db import ENGINE, Base
from app import models  # noqa: F401

def init_db() -> None:
    Base.metadata.create_all(bind=ENGINE)

if __name__ == "__main__":
    init_db()
    print("DB initialized.")
