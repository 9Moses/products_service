resource "docker_image" "api" {
  name = var.api_image
  build {
    context    = "../api"
    dockerfile = "Dockerfile"
  }
}

resource "docker_image" "main" {
  name = var.main_image
  build {
    context    = "../main"
    dockerfile = "Dockerfile"
  }
}

resource "docker_container" "rabbitmq" {
  name  = "rest-rabbitmq"
  image = var.rabbitmq_image
  ports {
    internal = 5672
    external = 5672
  }
  ports {
    internal = 15672
    external = 15672
  }
  env = [
    "RABBITMQ_DEFAULT_USER=guest",
    "RABBITMQ_DEFAULT_PASS=guest",
  ]
  restart = "always"
}

resource "docker_container" "api_db" {
  name    = "rest-api-db"
  image   = var.api_db_image
  command = ["--default-authentication-plugin=mysql_native_password"]
  env = [
    "MYSQL_DATABASE=admin",
    "MYSQL_ROOT_PASSWORD=root",
    "MYSQL_ALLOW_EMPTY_PASSWORD=no",
  ]
  volumes {
    volume_name    = docker_volume.api_dbdata.name
    container_path = "/var/lib/mysql"
  }
  ports {
    internal = 3306
    external = 33066
  }
  restart = "always"
   networks_advanced {
    name = docker_network.rest_local_net.name
  }
}

resource "docker_container" "main_db" {
  name    = "rest-main-db"
  image   = var.main_db_image
  command = ["--default-authentication-plugin=mysql_native_password"]
  env = [
    "MYSQL_DATABASE=main",
    "MYSQL_ROOT_PASSWORD=root",
    "MYSQL_ALLOW_EMPTY_PASSWORD=no",
  ]
  volumes {
    volume_name    = docker_volume.main_dbdata.name
    container_path = "/var/lib/mysql"
  }
  ports {
    internal = 3306
    external = 33067
  }
  restart = "always"
  networks_advanced {
    name = docker_network.rest_local_net.name
  }
}

resource "docker_container" "api" {
  name  = "rest-api"
  image = docker_image.api.image_id
  ports {
    internal = 8000
    external = 8000
  }
  env = [
    "RABBITMQ_URL=amqp://guest:guest@rest-rabbitmq:5672/",
  ]
  volumes {
    host_path      = abspath("${path.module}/../api")
    container_path = "/app"
  }
  command = ["python", "manage.py", "runserver", "0.0.0.0:8000"]
  restart = "on-failure"
  depends_on = [
    docker_container.api_db,
    docker_container.rabbitmq,
  ]
  networks_advanced {
    name    = docker_network.rest_local_net.name
    aliases = ["api-backend-1"]
  }
}

resource "docker_container" "api_consumer" {
  name  = "rest-api-consumer"
  image = docker_image.api.image_id
  env = [
    "RABBITMQ_URL=amqp://guest:guest@rest-rabbitmq:5672/",
  ]
  volumes {
    host_path      = abspath("${path.module}/../api")
    container_path = "/app"
  }
  command = ["python", "consumer.py"]
  restart = "on-failure"
  depends_on = [
    docker_container.api,
    docker_container.api_db,
    docker_container.rabbitmq,
  ]
  networks_advanced {
    name = docker_network.rest_local_net.name
  }
}

resource "docker_container" "main" {
  name  = "rest-main"
  image = docker_image.main.image_id
  ports {
    internal = 5000
    external = 8001
  }
  env = [
    "RABBITMQ_URL=amqp://guest:guest@rest-rabbitmq:5672/",
  ]
  volumes {
    host_path      = abspath("${path.module}/../main")
    container_path = "/app"
  }
  command = ["python", "main.py"]
  restart = "on-failure"
  depends_on = [
    docker_container.main_db,
    docker_container.rabbitmq,
  ]
  networks_advanced {
    name = docker_network.rest_local_net.name
  }
}

resource "docker_container" "main_consumer" {
  name  = "rest-main-consumer"
  image = docker_image.main.image_id
  env = [
    "RABBITMQ_URL=amqp://guest:guest@rest-rabbitmq:5672/",
  ]
  volumes {
    host_path      = abspath("${path.module}/../main")
    container_path = "/app"
  }
  command = ["python", "consumer.py"]
  restart = "on-failure"
  depends_on = [
    docker_container.main,
    docker_container.main_db,
    docker_container.rabbitmq,
  ]
  networks_advanced {
    name = docker_network.rest_local_net.name
  }
}

resource "docker_network" "rest_local_net" {
  name   = "rest_local_net"
  driver = "bridge"
}

resource "docker_volume" "api_dbdata" {
  name = "rest-api-dbdata"
}

resource "docker_volume" "main_dbdata" {
  name = "rest-main-dbdata"
}
