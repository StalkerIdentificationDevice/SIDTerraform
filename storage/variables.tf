variable "lambda_function_arn" {
  type = string
}

variable "bucket_prefix" {
  type = string
}

variable "db_table_info" {
  type = map(string)
}