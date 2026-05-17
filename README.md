# eSociety - Project Documentation

A Django-based society management system with role-based portals for Admin, Resident, and Security Guard users.

## Overview

This project manages daily apartment/society operations, including:

- User onboarding and OTP-based authentication
- Resident management and approval workflows
- Visitor pass and gate entry workflows
- Complaint management
- Facility booking and payment tracking
- Monthly maintenance dues generation and collection
- Community notices and polls
- Role-specific notifications and settings

## Tech Stack

- Python
- Django (custom user model)
- PostgreSQL
- Razorpay (online payment integration)
- ReportLab (PDF receipt generation)
- Pillow (image support)
- HTML/CSS/JS templates and static assets

## Repository Structure

```text
2026_intership_esociety/
  README.md
  esociety/
    manage.py
    esociety/          # Django project config
      settings.py
      urls.py
    core/              # Authentication and account lifecycle
    society/           # Society business modules
    templates/         # Role-based UI templates
    static/            # CSS/JS/images
    media/             # Uploaded files (for example visitor photos)
```

## Applications

### 1) `core` app

Handles identity and account lifecycle:

- Signup/login/logout
- Session-based OTP verification and resend
- Forgot-password OTP flow and reset
- Admin approval/rejection for pending users
- Admin creation of staff/security accounts
- Demo booking from public landing page

Main files:

- `esociety/core/models.py`
- `esociety/core/views.py`
- `esociety/core/forms.py`
- `esociety/core/urls.py`

### 2) `society` app

Handles day-to-day society operations:

- Admin dashboard, residents, complaints, maintenance, finance, community, settings
- Resident dashboard, visitor pass, complaints, payments, notifications, profile settings
- Security dashboard, visitor logging/entry status, notifications, guard settings
- Payment-related workflows (Razorpay + manual UPI flow)
- CSV/PDF exports for finance and dues

Main files:

- `esociety/society/models.py`
- `esociety/society/views.py`
- `esociety/society/forms.py`
- `esociety/society/urls.py`

## Roles and Access

The custom user model (`core.User`) supports these roles:

- `Admin`
- `Resident`
- `Securityguard`

Account status values:

- `pending`
- `inactive`
- `active`
- `blocked`
- `deleted`

Role-based decorators are used to protect views and route users to role-specific dashboards.

## Core Data Models

From `society/models.py`:

- `Visitor`
- `Complaint`
- `Facility`
- `FacilityBooking`
- `Payment`
- `MaintenanceConfig`
- `MaintenanceDue`
- `Notice`
- `Notification`
- `EmergencyAlert`
- `Poll`
- `PollVote`

From `core/models.py`:

- `User` (custom auth user)
- `DemoBooking`

## URL Routing

Project-level routes (`esociety/esociety/urls.py`):

- `/admin/` Django admin
- `/core/` core app URLs
- `/society/` society app URLs
- `/` home page
- `/book-demo/` demo booking

Examples from app routes:

- Auth: `/core/signup/`, `/core/login/`, `/core/verify-otp/`
- Resident: `/society/resident/`, `/society/resident/payments/`
- Security: `/society/security/`, `/society/guard/log-visitor/`
- Admin: `/society/admin/`, `/society/admin/finance/`, `/society/admin/maintenance/`

## Local Setup

## Prerequisites

- Python 3.10+
- PostgreSQL (running locally)
- pip

## 1. Clone and enter project

```bash
git clone <your-repo-url>
cd 2026_intership_esociety/esociety
```

## 2. Create and activate virtual environment

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

## 3. Install dependencies

```bash
pip install django psycopg2-binary razorpay reportlab pillow
```

If you add a requirements file later:

```bash
pip freeze > requirements.txt
```

## 4. Configure database

`esociety/esociety/settings.py` is configured for PostgreSQL:

- Database: `esociety`
- Host: `localhost`
- Port: `5432`

Create the database in PostgreSQL before migrations.

## 5. Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

## 6. Create superuser

```bash
python manage.py createsuperuser
```

## 7. Run the server

```bash
python manage.py runserver
```

Open: `http://127.0.0.1:8000/`

## Static and Media

- `STATIC_URL = /static/`
- `STATICFILES_DIRS` points to `esociety/static/`
- `MEDIA_URL = /media/`
- `MEDIA_ROOT = esociety/media/`

Uploaded visitor images are stored under `media/visitor_photos/`.

## Email and OTP

The project sends OTP/welcome/approval emails via SMTP settings in `settings.py`.

For security and portability, move credentials and secrets to environment variables in production.

## Render Deployment

This project can be deployed on Render as a Python web service with PostgreSQL.

### Files already prepared

- `requirements.txt`
- `render.yaml`
- production-friendly settings in `esociety/esociety/settings.py`

### Required environment variables on Render

- `SECRET_KEY`
- `DEBUG=False`
- `ALLOWED_HOSTS` set to your Render domain, for example `your-service.onrender.com`
- `DATABASE_URL` from the Render PostgreSQL database
- `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` if you use SMTP
- `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` if payments are enabled

### Manual setup steps

1. Create a new PostgreSQL database on Render.
2. Create a new Web Service and connect this GitHub repository.
3. Set the build command to `pip install -r requirements.txt && python esociety/manage.py collectstatic --noinput && python esociety/manage.py migrate`.
4. Set the start command to `gunicorn esociety.wsgi:application --chdir esociety`.
5. Add the environment variables above.
6. Deploy.

### Important note

Uploaded media such as visitor photos are stored locally in `media/`. If you need uploads to survive redeploys or disk replacement on Render, move media storage to a persistent disk or an external storage service such as S3 or Cloudinary.

## Payments

Razorpay endpoints are available under resident payment routes, including order creation and signature verification.

Maintenance and facility booking payments are tracked through `Payment` with status transitions (`pending` -> `completed`).

## Useful Commands

```bash
python manage.py runserver
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py shell
```

## Security Notes

Current settings are development-oriented (`DEBUG=True`) and include hardcoded sensitive values.
Before deploying:

- Set `DEBUG=False`
- Configure `ALLOWED_HOSTS`
- Move DB, email, and payment keys to environment variables
- Use production-grade static/media serving and HTTPS

## Future Improvements

- Add `requirements.txt` and `.env.example`
- Add automated tests for critical workflows (OTP, visitor flow, payment verification)
- Add CI checks for linting/tests/migrations
- Add deployment documentation (Gunicorn/Uvicorn + reverse proxy)

## License

Add your preferred license (MIT/Apache-2.0/etc.) in a `LICENSE` file.
