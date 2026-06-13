terraform {
  required_version = ">= 1.4.0"

  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = ">= 3.0.0"
    }
  }
}

provider "docker" {
  # When running inside a container (CI/CD), pass DOCKER_HOST via -e in the
  # docker run command (e.g. -e DOCKER_HOST=unix:///var/run/docker.sock).
  # When docker_host variable is null (default), the provider reads DOCKER_HOST
  # from the environment automatically — no hard-coded socket path needed.
  host = var.docker_host
}
