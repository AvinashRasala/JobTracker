"""
Run once after migrations: python -m scripts.seed_platforms
Populates the platforms table with all supported job portals.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal
from app.models.platform import Platform, DEFAULT_PLATFORMS


def run():
    db = SessionLocal()
    try:
        for entry in DEFAULT_PLATFORMS:
            exists = db.query(Platform).filter(Platform.slug == entry["slug"]).first()
            if not exists:
                db.add(Platform(**entry))
        db.commit()
        print(f"Seeded {len(DEFAULT_PLATFORMS)} platforms (skipping any that already exist).")
    finally:
        db.close()


if __name__ == "__main__":
    run()
