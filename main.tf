terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "4.66.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

module "lambda_function" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = "process_images"
  description   = "Lambda Function to process images from mobile devices"
  handler       = "process_images.process"
  runtime       = "python3.8"

  source_path = "./lambda"

  tags = {
    Name = "process_images"
  }
}

resource "aws_s3_bucket" "photo_bucket" {
  bucket = "sid-user-public-photo-data"
}

resource "aws_s3_access_point" "photo_bucket" {
  bucket = aws_s3_bucket.photo_bucket.id
  name   = "sid-user-public-photo-data"
  policy = ""
}