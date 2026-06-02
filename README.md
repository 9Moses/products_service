# REST Microservice Project

This repository contains two microservices that communicate via RabbitMQ:

- `api/` — Django REST API (users/admin/products)
- `main/` — Flask app (frontend-like service) and background consumer/producer

**This README** explains how to run the project locally (venv) and with Docker.

**Prerequisites**
- Python 3.11+ (3.13 used in Dockerfiles)
- Docker + Docker Compose (if using Docker)
- MySQL locally (or use the containers provided)

**Environment variables**
Put secrets and connection URLs in an `.env` file at each service root (`api/.env`, `main/.env`). Required variables:

- `RABBITMQ_URL` — full AMQPS/AMQP URL for RabbitMQ/CloudAMQP

Example `api/.env` (already added in this repo):

```
RABBITMQ_URL=amqps://<USER>:<PASS>@<HOST>/<VHOST>
```

Local development (Windows)

1. Start the Django API

```powershell
cd api
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
# ensure api/.env exists and contains RABBITMQ_URL
python manage.py migrate
# manually create API users if needed
# either use Django admin / createsuperuser or connect to the Docker MySQL container:
#   docker compose exec db mysql -u root -proot admin
python manage.py runserver 0.0.0.0:8000
```

2. Start the Flask `main` service

```powershell
cd main
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
# ensure main/.env exists and contains RABBITMQ_URL
set FLASK_APP=main.py
flask db upgrade
python main.py
```

3. Start consumers (optional, for background processing)

```powershell
# Django consumer (listens to product events)
python api/consumer.py

# Flask/main consumer (example local consumer)
python main/consumer.py
```

Manual user creation

If the API has no user-registration endpoint available, add users manually after database migration:

- Use Django admin or `python manage.py createsuperuser`
- Or connect to the Docker MySQL container and insert records directly:

```bash
cd api
docker compose exec db mysql -u root -proot admin
```

Docker (recommended for parity)

This repository has `docker-compose.yml` files under `api/` and `main/` for each service. Run them from each folder, or create a combined compose if you prefer.

Build and run the Django API container:

```bash
cd api
docker compose build
docker compose up -d
```

Apply Django migrations inside the API container if needed:

```bash
cd api
docker compose exec backend python manage.py migrate
```

Build and run the Flask `main` container:

```bash
cd main
docker compose build
docker compose up -d
```

Apply Flask migrations inside the `main` container if needed:

```bash
cd main
docker compose exec backend flask db upgrade
```

Note: containers rely on `.env` files to be present inside the build context. To pass environment variables into the container at runtime, add an `env_file` entry under the service in the compose file, for example:

```yaml
services:
  backend:
    build: .
    env_file:
      - .env
    command: python main.py
```

Troubleshooting

- PRECONDITION_FAILED (existing queue declared with other arguments):
  - This occurs when the same queue name is redeclared with different properties (e.g., `durable=True` vs `durable=False`).
  - Solution: ensure producers and consumers declare the queue with identical arguments, or create a new queue name and update both sides. You may need to delete the existing queue from RabbitMQ.

- Django settings not configured when importing models in standalone scripts:
  - Ensure `DJANGO_SETTINGS_MODULE=api.settings` is set and `django.setup()` has been called before importing Django models.

Useful commands

- Inspect running containers:

```bash
docker compose ps
```

- View logs for a service (from the service folder):

```bash
docker compose logs -f
```

Security

- Do not commit `.env` files with real secrets to version control. This repo currently contains `.env` files for local development; rotate credentials if they were leaked.
- For production, use Docker secrets, environment injection in your CI/CD system, or a secrets manager.

If you want, I can:

- Add `env_file` entries to `docker-compose.yml` files so containers pick up `.env` automatically.
- Create a combined `docker-compose.yml` at the repo root to orchestrate both `api` and `main` services together.

"# products_service" 
Microservices Event-Driven Architecture (Flask + Django + RabbitMQ + MySQL)

This project is a microservices-based system built using Flask and Django, communicating via an event-driven architecture using RabbitMQ, with MySQL as the primary database.

It demonstrates service separation, asynchronous communication, and scalable