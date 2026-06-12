output "api_container_id" {
  description = "Docker container ID for the API service"
  value       = docker_container.api.id
}

output "main_container_id" {
  description = "Docker container ID for the Main service"
  value       = docker_container.main.id
}

output "rabbitmq_management_url" {
  description = "RabbitMQ management URL"
  value       = "http://localhost:15672"
}
