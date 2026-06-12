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
  # On Windows, Docker Desktop uses the named pipe by default.
  # Leave blank to use the environment or the provider default.
  host = var.docker_host
}
