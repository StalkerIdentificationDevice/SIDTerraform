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

module "api_gateway" {
  source = "terraform-aws-modules/apigateway-v2/aws"

  name          = "process_images_gateway"
  description   = "HTTP API Gateway to access lambda function"
  protocol_type = "HTTP"

  cors_configuration = {
    allow_headers = ["content-type", "x-amz-date", "authorization", "x-api-key", "x-amz-security-token", "x-amz-user-agent"]
    allow_methods = ["*"]
    allow_origins = ["*"]
  }

  # Routes and integrations
  integrations = {
    "POST /" = {
      lambda_arn             = module.lambda_function.lambda_function_invoke_arn
      payload_format_version = "2.0"
      timeout_milliseconds   = 12000
    }
  }

  tags = {
    Name = "process_images_gateway"
  }
}