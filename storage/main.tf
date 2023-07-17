resource "aws_dynamodb_table" "user-tracking" {
  name         = var.db_table_info["name"]
  hash_key     = var.db_table_info["partition_key"]
  billing_mode = "PAY_PER_REQUEST"
  attribute {
    name = var.db_table_info["partition_key"]
    type = "S"
  }
  point_in_time_recovery { enabled = false }
  server_side_encryption { enabled = true }
}

resource "aws_s3_bucket" "bucket" {
  bucket_prefix = var.bucket_prefix
}

resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.bucket.id

  lambda_function {
    lambda_function_arn = var.lambda_function_arn
    events              = ["s3:ObjectCreated:*"]
  }
}