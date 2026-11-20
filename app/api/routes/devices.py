from fastapi import APIRouter

router = APIRouter(
    prefix="/devices",
    tags=["Devices"]
)

DEVICES = [
    {
        "id": 1,
        "name": "Phone",
        "description": "Smartphones and mobile devices"
    },
    {
        "id": 2,
        "name": "Laptop",
        "description": "Laptops and notebook computers"
    },
    {
        "id": 3,
        "name": "Router",
        "description": "Wi-Fi routers and networking devices"
    }
]

@router.get("/")
def get_devices():
    return {
        "success": True,
        "count": len(DEVICES),
        "devices": DEVICES
    }