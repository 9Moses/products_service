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

---

## Terraform + Ansible local IaC

A local infrastructure stack is provided using Terraform and Ansible, with support for direct or containerized execution.

### Local execution (direct)

**Terraform:**

```powershell
cd terraform
terraform init
terraform apply -auto-approve
```

**Ansible:**

```powershell
cd ansible
ansible-galaxy collection install community.docker
ansible-playbook playbook.yml
```

This builds the `api` and `main` service images and creates containers for:
- `rabbitmq`
- `rest-api-db`
- `rest-main-db`
- `rest-api`
- `rest-api-consumer`
- `rest-main`
- `rest-main-consumer`

The Ansible playbook now uses Docker named volumes for MySQL data (`rest_api_dbdata` and `rest_main_dbdata`) to preserve state and avoid host-path bind issues on Windows.

### Containerized execution (Docker)

Build and run IaC tools inside Docker containers for isolation and consistency.

**Build IaC Docker images:**

```bash
docker build -t terraform-iac:latest ./terraform
docker build -t ansible-iac:latest ./ansible
```

**Run Terraform inside container:**

```bash
docker run --rm \
  --volume $(pwd)/terraform:/workspace \
  --volume /var/run/docker.sock:/var/run/docker.sock \
  terraform-iac:latest init -input=false

docker run --rm \
  --volume $(pwd)/terraform:/workspace \
  --volume /var/run/docker.sock:/var/run/docker.sock \
  terraform-iac:latest apply -auto-approve
```

**Run Ansible inside container:**

```bash
docker run --rm \
  --volume $(pwd)/ansible:/workspace \
  --volume /var/run/docker.sock:/var/run/docker.sock \
  ansible-iac:latest -i localhost, -c local playbook.yml
```

### Jenkins Pipeline Integration

The Jenkins pipeline automatically executes IaC in Docker containers:

- Enable with build parameter: `RUN_IAC=true`
- Apply changes with: `APPLY_IAC=true`
- The pipeline builds `terraform-iac` and `ansible-iac` Docker images
- Terraform and Ansible run inside their respective containers with Docker socket access
- Cleanup automatically removes all IaC images

### Service URLs

- API: `http://localhost:8000`
- Main: `http://localhost:8001`
- RabbitMQ UI: `http://localhost:15672` (`guest` / `guest`)

### Notes

- The `terraform/Dockerfile` uses `hashicorp/terraform:latest` base image
- The `ansible/Dockerfile` uses `docker:latest` base image and includes Python, Ansible, and Docker SDK
- Both images mount the Docker socket to manage containers
- Install the `community.docker` Ansible collection before running directly if you are not using the containerized Ansible image:

```bash
ansible-galaxy collection install community.docker
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



"# products_service" 
Microservices Event-Driven Architecture (Flask + Django + RabbitMQ + MySQL)

This project is a microservices-based system built using Flask and Django, communicating via an event-driven architecture using RabbitMQ, with MySQL as the primary database.

It demonstrates service separation, asynchronous communication, and scalable