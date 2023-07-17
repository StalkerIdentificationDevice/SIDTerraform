output "lambda_function_arn" {
  value = aws_lambda_function.func.arn
}

output "lambda_iam_id" {
  value = aws_iam_role.iam_for_lambda.id
}