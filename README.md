# Fundi AI — Backend API & Diagnostic Engine

Fundi AI is an intelligent hardware diagnostic and repair-support platform tailored for the Kenyan market. It diagnoses hardware faults across phones, laptops, and networking routers using bilingual English, Kiswahili, and Sheng symptom analysis, recommends troubleshooting steps, and connects users to local repair shops (*fundis*) for professional repair bookings.

---

## Tech Stack

- **Framework:** FastAPI (Python 3.13)
- **Database:** MySQL 8.4
- **ORM:** SQLAlchemy 2.0 (declarative mapped columns)
- **Migrations:** Alembic
- **Validation & Serialization:** Pydantic v2
- **Testing:** Pytest (52 automated unit & integration tests)
- **Package Management:** `uv`

---

## Getting Started

### 1. Prerequisites
- **Python 3.13+**
- **MySQL 8.4+** running locally or via Docker

### 2. Environment Configuration
Create a `.env` file in the root `backend/` directory:

```ini
APP_NAME=Fundi AI
APP_VERSION=0.1.0
DEBUG=True

FRONTEND_URL=http://localhost:5173

# MySQL connection string (PyMySQL driver)
DATABASE_URL=mysql+pymysql://<user>:<password>@127.0.0.1:3306/fundi_ai
```

### 3. Installation
Using standard virtual environment:

```bash
# Install dependencies
uv add -r requirements.txt
# or:
uv pip install -e .

# Activate virtual environment
source .venv/bin/activate

```

### 4. Database Setup & Migrations
Ensure the `fundi_ai` database exists in MySQL, then run migrations:

```bash
alembic upgrade head
```

### 5. Seed Knowledge Base & Repair Shops
Run the idempotent seed scripts:

```bash
# Seed 60 hardware fault profiles (phone, laptop, router)
python -m app.data.seed

# Seed initial Kenyan repair shops (CBD, Westlands, Kilimani, etc.)
python -m app.data.seed_shops
```

### 6. Run the Development Server
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- API Base URL: `http://127.0.0.1:8000`
- Interactive Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc Documentation: `http://127.0.0.1:8000/redoc`

---

## API Endpoints

### Diagnostic Pipeline
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/diagnose/` | Submit device symptoms (English/Swahili) to receive ranked faults, fix steps, safety warnings, and suggested shops. |

#### Example Request:
```json
POST /api/diagnose/
Content-Type: application/json

{
  "device": "laptop",
  "language": "sw",
  "symptom": "Laptop yangu inawaka lakini screen ni nyeusi"
}
```

### Repair Shops Directory
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/shops/` | List all available repair shops (supports `?location=Westlands` and `?service=router`). |
| `GET` | `/api/shops/{id}` | Retrieve details for a specific repair shop. |
| `POST` | `/api/shops/` | Register a new repair shop. |

### Repair Bookings
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/bookings/` | Submit a repair booking request. |
| `GET` | `/api/bookings/` | List bookings (supports `?shop_id=` and `?status=`). |
| `GET` | `/api/bookings/{id}` | Get booking details by ID. |
| `PATCH` | `/api/bookings/{id}/status` | Update booking status (`confirmed`, `completed`, `cancelled`). |

---

## Running Automated Tests

Run the full automated test suite with pytest:

```bash
pytest -v
```

All 52 tests verify:
- Normalization, tokenization, Swahili prefix stripping, and Sheng code-switching.
- Defect-targeted negation detection and clause splitting.
- Diagnostic matching accuracy across phones, laptops, and routers.
- Safety details, score capping (95%), and rejection of generic queries.
- Shop listing, location filtering, and repair booking lifecycle.

---

## License
Proprietary — Developed for Fundi AI.
