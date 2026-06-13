variable "docker_host" {
  description = "Optional Docker host for the Docker provider"
  type        = string
  default     = null
}

variable "rabbitmq_image" {
  description = "RabbitMQ Docker image"
  type        = string
  default     = "rabbitmq:3.11-management"
}

variable "api_image" {
  description = "API service image tag"
  type        = string
  default     = "ghcr.io/9moses/rest-api:latest"
}

variable "main_image" {
  description = "Main service image tag"
  type        = string
  default     = "ghcr.io/9moses/rest-main:latest"
}

variable "api_db_image" {
  description = "MySQL image for API service"
  type        = string
  default     = "mysql:8.0"
}

variable "main_db_image" {
  description = "MySQL image for main service"
  type        = string
  default     = "mysql:8.0"
}
