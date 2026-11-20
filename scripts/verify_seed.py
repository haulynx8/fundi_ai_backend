from sqlalchemy import select, func

from app.core.database import SessionLocal
from app.models import Device, Fault

EXPECTED = {"phone": 20, "laptop": 20, "router": 20}


def verify() -> None:
    failed = False

    with SessionLocal() as db:
        print("\nFundi AI Database Verification\n")

        for slug, expected in EXPECTED.items():
            device = db.scalar(select(Device).where(Device.slug == slug))
            if device is None:
                actual = 0
                print(f"{slug.title()}: device missing")
                failed = True
                continue

            actual = db.scalar(
                select(func.count(Fault.id)).where(Fault.device_id == device.id)
            )
            status = "OK" if actual == expected else "MISMATCH"
            print(f"{slug.title()} faults: {actual}/{expected} [{status}]")
            if actual != expected:
                failed = True

        total = db.scalar(select(func.count(Fault.id)))
        device_total = db.scalar(select(func.count(Device.id)))

        print(f"\nDevices in database: {device_total}")
        print(f"Total faults in database: {total}")

        if device_total != 3 or total != 60:
            failed = True

        print(f"Status: {'FAILED' if failed else 'SUCCESS'}\n")

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    verify()
