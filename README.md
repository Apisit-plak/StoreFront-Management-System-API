# StoreFront Management System — Backend API

Django REST Framework backend for a marketplace where **Sellers** manage product listings and **Buyers** browse, purchase, and checkout via a shopping cart. PostgreSQL runs in Docker; the frontend is a separate project.

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Django 5 + Django REST Framework |
| Auth | JWT (`djangorestframework-simplejwt`) |
| Database | PostgreSQL 16 |
| Containerization | Docker Compose |
| Image handling | Pillow |

## Architecture

```
┌─────────────────┐         HTTPS/JSON          ┌──────────────────────────┐
│  Frontend App   │ ◄──────────────────────────► │  Django REST API         │
│  (separate repo)│         JWT Bearer Token       │  (this project)          │
└─────────────────┘                              └────────────┬─────────────┘
                                                                │
                                                     ┌──────────▼──────────┐
                                                     │  PostgreSQL (Docker) │
                                                     └─────────────────────┘
```

### Design Choices

- **App-based separation**: `accounts` (auth/roles), `products` (listings/inventory), `orders` (cart/checkout) — each owns its models, serializers, views, and permissions.
- **Service layer**: Inventory mutations (`purchase_product`, `checkout_cart`) live in `services.py` with `@transaction.atomic` and `select_for_update()` to prevent race conditions.
- **Role-based access**: Custom DRF permissions (`IsSeller`, `IsBuyer`, `ProductPermission`) enforce feature boundaries at the API layer.
- **Price snapshots**: `OrderItem.unit_price` stores the price at checkout time so historical orders remain accurate if sellers change prices later.
- **Consistent API responses**: Errors are wrapped as `{ "success": false, "errors": {...} }`; successes include `success: true`.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (recommended)
- Alternatively: Python 3.12+, PostgreSQL 16

## Quick Start (Docker)

```bash
# 1. Clone and enter the project
cd BackEnd

# 2. Create environment file
cp .env.example .env

# 3. Start PostgreSQL + API
docker compose up --build -d

# 4. Create a superuser (optional, for Django Admin)
docker compose exec web python manage.py createsuperuser
```

API available at: **http://localhost:8000**

### Run Tests (Docker)

```bash
docker compose --profile test run --rm test
```

### Stop Services

```bash
docker compose down          # keep data
docker compose down -v       # remove volumes (reset DB)
```

## Local Development (without Docker for the API)

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env

# Start only the database container
docker compose up db -d

# Update .env: POSTGRES_HOST=localhost
python manage.py migrate
python manage.py runserver
python manage.py test
```

## Environment Variables

Copy `.env.example` to `.env` and adjust as needed:

| Variable | Description | Default |
|---|---|---|
| `DEBUG` | Enable debug mode | `True` |
| `SECRET_KEY` | Django secret key | *(must change in production)* |
| `ALLOWED_HOSTS` | Comma-separated hosts | `localhost,127.0.0.1` |
| `POSTGRES_DB` | Database name | `storefront` |
| `POSTGRES_USER` | Database user | `storefront_user` |
| `POSTGRES_PASSWORD` | Database password | `storefront_pass` |
| `POSTGRES_HOST` | DB host (`db` in Docker, `localhost` locally) | `db` |
| `POSTGRES_PORT` | DB port | `5432` |
| `CORS_ALLOWED_ORIGINS` | Frontend origins | `http://localhost:3000` |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | Access token TTL | `60` |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | Refresh token TTL | `7` |

## API Endpoints

### Authentication

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `POST` | `/api/auth/register/` | Public | Register as Seller or Buyer |
| `POST` | `/api/auth/login/` | Public | Obtain JWT access + refresh tokens |
| `POST` | `/api/auth/token/refresh/` | Public | Refresh access token |
| `GET` | `/api/auth/me/` | Authenticated | Current user profile |

### Products

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/api/products/` | Authenticated | List products (filters: `search`, `min_price`, `max_price`, `in_stock`, `seller`, `ordering`) |
| `POST` | `/api/products/` | Seller | Create product listing (multipart for image) |
| `GET` | `/api/products/{id}/` | Authenticated | Product detail with stock status |
| `PUT/PATCH` | `/api/products/{id}/` | Seller (owner) | Update own listing |
| `DELETE` | `/api/products/{id}/` | Seller (owner) | Delete own listing |
| `POST` | `/api/products/{id}/purchase/` | Buyer | Mock single-item purchase (decrements stock) |

**Seller filter**: `GET /api/products/?mine=true` returns only the authenticated seller's products.

### Cart & Orders

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/api/cart/` | Buyer | View shopping cart |
| `GET/POST` | `/api/cart/items/` | Buyer | List / add cart items |
| `GET/PATCH/DELETE` | `/api/cart/items/{id}/` | Buyer | Manage cart line item |
| `POST` | `/api/cart/checkout/` | Buyer | Checkout — creates order, reduces inventory, clears cart |
| `GET` | `/api/orders/` | Buyer | Order history |
| `GET` | `/api/orders/{id}/` | Buyer | Order detail |

## Example Requests

### Register a Seller

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "seller1",
    "email": "seller@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "role": "SELLER"
  }'
```

### Login

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "seller1", "password": "SecurePass123!"}'
```

### Create Product (Seller)

```bash
curl -X POST http://localhost:8000/api/products/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -F "title=Wireless Keyboard" \
  -F "description=Mechanical keyboard" \
  -F "unit_price=49.99" \
  -F "quantity=25" \
  -F "image=@/path/to/image.jpg"
```

### Browse with Filters (Buyer)

```bash
curl "http://localhost:8000/api/products/?search=keyboard&min_price=10&max_price=100&in_stock=true" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### Checkout (Buyer)

```bash
# Add to cart
curl -X POST http://localhost:8000/api/cart/items/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "quantity": 2}'

# Checkout
curl -X POST http://localhost:8000/api/cart/checkout/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

## Database Schema

See [docs/ER_DIAGRAM.md](docs/ER_DIAGRAM.md) for the full Entity-Relationship diagram with tables, keys, and relationships.

## Testing

Tests cover critical paths:

- User registration, login, JWT, and profile
- Seller product CRUD and ownership enforcement
- Buyer product browsing, filtering, and mock purchase
- Cart operations, checkout, inventory deduction, and order history
- Permission denials (buyer cannot create products, seller cannot access cart)

```bash
# Docker
docker compose --profile test run --rm test

# Local
python manage.py test --verbosity=2
```

## Project Structure

```
BackEnd/
├── accounts/          # User model, JWT auth, role permissions
├── products/          # Product listings, filters, inventory purchase
├── orders/            # Cart, checkout, order history
├── storefront/        # Django project settings, URLs, exception handler
├── tests/             # Shared test factories
├── docs/              # ER diagram
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Security Notes

- All API endpoints require JWT authentication except register/login/refresh
- Passwords validated with Django's built-in validators
- Role-based permissions enforced per endpoint
- CORS restricted to configured frontend origins
- Inventory updates use database row locking to prevent overselling
- Set `DEBUG=False` and a strong `SECRET_KEY` in production

## Frontend Integration

This API is designed for a separate frontend folder/project. Configure the frontend to:

1. Store JWT access/refresh tokens after login
2. Send `Authorization: Bearer <token>` on every request
3. Point API calls to `http://localhost:8000/api/`
4. Handle paginated list responses (`count`, `next`, `previous`, `results`)
