# Shuhna – Merchant-to-Delivery-Rep Logistics Platform

A backend platform connecting **merchants** with **delivery representatives**, enabling merchants to submit delivery orders and representatives to discover, accept, and fulfill nearby requests with **real-time tracking** and **push notifications**.

---

# Overview

Shohna is a two-sided marketplace API built with **Django REST Framework**.

Merchants create delivery orders, nearby representatives discover and accept them, and both parties track the order through its full lifecycle—from **pending** to **delivered**—with live location tracking and push notifications.

---

# Features

### Authentication & User Management
- Separate merchant and representative accounts
- JWT Authentication (SimpleJWT)
- Email verification via OTP
- Password reset
- Role-based permissions

### Geolocation-Powered Order Matching
- Built with **PostGIS** & **GeoDjango**
- Representatives discover nearby pending orders within a configurable radius

### Automatic Delivery Fee Calculation
- Delivery fee calculated from the real geographic distance between merchant and destination

### Order Lifecycle
- Enforced order state transitions:

```
pending
    ↓
accepted
    ↓
picked_up
    ↓
on_the_way
    ↓
delivered
```

- Role-specific cancellation rules
- Complete order status history

### Concurrency-Safe Order Acceptance
- Uses `select_for_update()` row-level locking
- Prevents multiple representatives from accepting the same order

### Real-Time Tracking
- Django Channels
- WebSockets
- Redis
- Live representative location updates

### Push Notifications
- Firebase Cloud Messaging (FCM)
- Decoupled using Django Signals

### 📄 API Documentation
- Swagger UI
- OpenAPI
- Powered by **drf-spectacular**

### Rate Limiting
- Endpoint throttling for:
  - Password reset
  - Email verification
  - Sensitive authentication endpoints

---

# Tech Stack

| Layer | Technology |
|--------|------------|
| Framework | Django, Django REST Framework |
| Database | PostgreSQL + PostGIS |
| Real-Time | Django Channels, WebSockets, Redis |
| Authentication | JWT (SimpleJWT) + Token Blacklisting |
| Notifications | Firebase Cloud Messaging |
| API Docs | drf-spectacular (Swagger/OpenAPI) |

---

# Project Structure

```text
shuhna/
├── users/         # Custom user model, authentication, merchant & rep profiles
├── orders/           # Order lifecycle, geolocation matching, status history
├── tracking/         # WebSocket consumers & live location updates
└── notifications/    # Push notifications & notification feed
```

---

# Core Flow

1. Merchant registers and sets their shop location.
2. Merchant creates a delivery order.
3. Delivery fee and distance are calculated automatically.
4. Nearby representatives receive the order.
5. A representative accepts the order (race-condition safe).
6. Representative updates order status during delivery.
7. Merchant tracks the representative in real time.
8. Push notifications are sent throughout the delivery lifecycle.

---

# Getting Started

## Prerequisites

- Python 3.11+
- PostgreSQL with PostGIS
- Redis
- GDAL / GEOS

---

## Installation

Clone the repository:

```bash
git clone https://github.com/Nayra-04/Shuhna.git
cd shuhna
```

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Linux / macOS

```bash
source .venv/bin/activate
```

Windows

```bash
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file:

```env
DATABASE_URL=postgis://user:password@localhost:5432/shohna

EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
```

Add your Firebase service account file:

```
firebase-service-account.json
```

Place it in the project root.

---

## Run the Project

```bash
python manage.py migrate

python manage.py createsuperuser

python manage.py runserver
```

---

# API Documentation

Swagger documentation is available at:

```
/api/docs/
```

---

# API Highlights

| Method | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/auth/register/merchant/` | Merchant registration |
| POST | `/api/auth/register/rep/` | Representative registration |
| POST | `/api/auth/login/` | Login (JWT) |
| POST | `/api/orders/create/` | Create a delivery order |
| GET | `/api/orders/nearby/` | Nearby pending orders |
| POST | `/api/orders/{id}/accept/` | Accept an order |
| PATCH | `/api/orders/{id}/status/` | Update order status |
| GET | `/api/tracking/{order_id}/last-location/` | Get last representative location |
| WS | `/ws/tracking/{order_id}/` | Live location tracking |
| GET | `/api/notifications/` | List notifications |

---
