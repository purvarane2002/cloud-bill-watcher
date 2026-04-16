output "lambda_function_name" {
  description = "The name of the Lambda function"
  value       = aws_lambda_function.watcher.function_name
}

output "ecr_repository_url" {
  description = "ECR repository URL for Docker image"
  value       = aws_ecr_repository.app.repository_url
}

output "sns_topic_arn" {
  description = "SNS topic ARN for alerts"
  value       = aws_sns_topic.alerts.arn
}