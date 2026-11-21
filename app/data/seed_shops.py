"""
Seed script for initial repair shop listings in Fundi AI.
Idempotent: updates existing shops matching name and location, or inserts new records.
"""

from sqlalchemy import select
from app.core.database import SessionLocal
from app.models.shop import Shop

SAMPLE_SHOPS = [
    {
        "name": "Luthuli Tech Hub & Phone Care",
        "location": "Luthuli Avenue, Nairobi CBD",
        "phone": "+254712345001",
        "services": [
            "Phone screen replacement",
            "Charging port repair",
            "Battery replacement",
            "Water damage cleanup",
        ],
        "rating": 4.8,
        "price_range": "KSh 1,500 - 6,000",
    },
    {
        "name": "Moi Avenue Computer Diagnostics",
        "location": "Moi Avenue, Nairobi CBD",
        "phone": "+254722345002",
        "services": [
            "Laptop motherboard repair",
            "Display panel replacement",
            "SSD & RAM upgrades",
            "Fan & cooling cleaning",
        ],
        "rating": 4.7,
        "price_range": "KSh 2,500 - 12,000",
    },
    {
        "name": "Westlands QuickFix Gadget Clinic",
        "location": "Mpaka Road, Westlands, Nairobi",
        "phone": "+254733345003",
        "services": [
            "Phone & tablet servicing",
            "Laptop keyboard replacement",
            "Data recovery",
            "Power adapter repair",
        ],
        "rating": 4.9,
        "price_range": "KSh 2,000 - 15,000",
    },
    {
        "name": "Tom Mboya Network & Router Lab",
        "location": "Tom Mboya Street, Nairobi CBD",
        "phone": "+254744345004",
        "services": [
            "Router firmware flashing",
            "Wi-Fi antenna replacement",
            "WAN port repair",
            "Power supply diagnostics",
        ],
        "rating": 4.6,
        "price_range": "KSh 1,000 - 5,000",
    },
    {
        "name": "Kilimani Micro-Soldering Center",
        "location": "Argwings Kodhek Road, Kilimani, Nairobi",
        "phone": "+254755345005",
        "services": [
            "Advanced board-level diagnostics",
            "Power IC chip replacement",
            "Liquid corrosion ultrasonic bath",
            "MacBook logic board repair",
        ],
        "rating": 4.9,
        "price_range": "KSh 4,000 - 25,000",
    },
    {
        "name": "Ngara Electronics & Hardware Fundi",
        "location": "Ngara Road, Nairobi",
        "phone": "+254766345006",
        "services": [
            "Affordable phone repairs",
            "Screen replacement",
            "Speaker and mic repair",
            "Battery replacements",
        ],
        "rating": 4.5,
        "price_range": "KSh 800 - 4,500",
    },
]


def seed_shops():
    session = SessionLocal()
    inserted = 0
    updated = 0

    try:
        for data in SAMPLE_SHOPS:
            existing = session.scalar(
                select(Shop).where(Shop.name == data["name"])
            )

            if existing is None:
                shop = Shop(
                    name=data["name"],
                    location=data["location"],
                    phone=data["phone"],
                    services=data["services"],
                    rating=data["rating"],
                    price_range=data["price_range"],
                )
                session.add(shop)
                inserted += 1
            else:
                existing.location = data["location"]
                existing.phone = data["phone"]
                existing.services = data["services"]
                existing.rating = data["rating"]
                existing.price_range = data["price_range"]
                updated += 1

        session.commit()
        print(f"Shop seeding complete: {inserted} inserted, {updated} updated.")
    except Exception as exc:
        session.rollback()
        print(f"Error seeding shops: {exc}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_shops()
