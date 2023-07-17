output "bucket_arn" {
  value = aws_s3_bucket.bucket.arn
}

output "table_arn" {
  value = aws_dynamodb_table.user-tracking.arn
}