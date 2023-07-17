terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "4.66.0"
    }
  }
}

provider "aws" {
  region     = "us-east-1"
  access_key = var.access_key
  secret_key = var.secret_key
}

module "storage" {
  source = "./storage"

  lambda_function_arn = module.lambda.lambda_function_arn
  db_table_info = {
    name          = "user-tracking",
    partition_key = "User"
  }
  bucket_prefix = "sid-user-public-photo-data"
}

module "lambda" {
  source = "./lambda"
}

module "messaging" {
  source = "./messaging"

  sns_app_name = "S.I.D"
}

module "connect_services" {
  source = "./connect_services"

  lambda_function_arn = module.lambda.lambda_function_arn
  lambda_iam_id       = module.lambda.lambda_iam_id

  table_arn  = module.storage.table_arn
  bucket_arn = module.storage.bucket_arn
}