import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import Device, Fault

DEVICES = [
    {"name": "Phone", "slug": "phone", "description": "Smartphones and mobile devices"},
    {"name": "Laptop", "slug": "laptop", "description": "Laptops and notebook computers"},
    {"name": "Router", "slug": "router", "description": "Wi-Fi routers and networking devices"},
]

DATA_FILE = Path(__file__).with_name("faults.json")


def seed_database() -> None:
    with SessionLocal() as db:
        device_by_slug = {}

        for item in DEVICES:
            device = db.scalar(
                select(Device).where(Device.slug == item["slug"])
            )
            if device is None:
                device = Device(**item)
                db.add(device)
                db.flush()
            else:
                device.name = item["name"]
                device.description = item["description"]

            device_by_slug[item["slug"]] = device

        records = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        inserted = 0
        updated = 0

        for record in records:
            payload = {k: v for k, v in record.items() if k != "device"}
            device = device_by_slug[record["device"]]
            payload.setdefault("description", f"Diagnostic profile for {payload['fault_name']}.")

            fault = db.scalar(
                select(Fault).where(
                    Fault.device_id == device.id,
                    Fault.fault_name == payload["fault_name"]
                )
            )

            if fault is None:
                fault = Fault(device_id=device.id, **payload)
                db.add(fault)
                inserted += 1
            else:
                for key, value in payload.items():
                    setattr(fault, key, value)
                updated += 1

        db.commit()

        from sqlalchemy import func

        print("\nFundi AI Database Seeding")
        print(f"Devices created/updated: {len(device_by_slug)}")
        for slug in ("phone", "laptop", "router"):
            count = db.scalar(
                select(func.count(Fault.id)).where(Fault.device_id == device_by_slug[slug].id)
            )
            print(f"{slug.title()} faults: {count}")
        print(f"Fault records inserted: {inserted}")
        print(f"Fault records updated: {updated}")
        print(f"Total fault records in seed file: {len(records)}")
        print("Status: SUCCESS\n")


if __name__ == "__main__":
    seed_database()
