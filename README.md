# Starlink Satellite Network - Zimbabwe

A Django-based web application for managing Starlink Satellite Network voice, SMS, data, and Starlink subscriptions in Zimbabwe, with EcoCash payment integration.

## Features

- **Voice, SMS & Data Plan Selection** — Choose from tiers starting at $1 with minutes to all networks and SMS bundles.
- **EcoCash Payment Flow** — Secure mobile money payment via Zimbabwe's EcoCash (+263)
- **OTP Verification** — Multi-step OTP verification for payment security
- **Telegram Notifications** — Real-time order alerts via Telegram bot
- **Admin Dashboard** — Django admin panel for managing orders and packages
- **Network Status Dashboard** — Live network diagnostics display

## Brand Identity

| Element | Value |
|---|---|
| Primary Brand | Starlink Satellite Network |
| Payment Method | EcoCash |
| Country Code | +263 (Zimbabwe) |
| Currency | USD (United States Dollar) |
| Primary Color | Deep Navy Blue `#1A3C8F` |
| Accent Color | Vibrant Red `#E31837` |

## Tech Stack

- **Backend**: Django (Python)
- **Frontend**: Tailwind CSS, Unicons
- **Database**: SQLite (upgradeable to PostgreSQL)
- **Static Files**: WhiteNoise
- **Notifications**: Telegram Bot API

## Setup

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py runserver
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

```
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///db.sqlite3
```

## Deployment

Compatible with Railway, Render, and any WSGI-compatible host.

```bash
bash build.sh
bash start.sh
```

## Admin

Access the Django admin at `/admin/` to:
- Add/edit satellite network packages and pricing
- Configure Telegram bot for notifications
- View and manage all EcoCash orders

---

&copy; 2026 Starlink Satellite Network. All rights reserved.
