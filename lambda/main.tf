data "archive_file" "process_images" {
  type        = "zip"
  source_file = "lambda/process_images.py"
  output_path = "lambda.zip"
}

resource "aws_lambda_function" "func" {
  filename         = "lambda.zip"
  function_name    = "process_images"
  role             = aws_iam_role.iam_for_lambda.arn
  handler          = "process_images.lambda_handler"
  runtime          = "python3.10"
  source_code_hash = data.archive_file.process_images.output_base64sha256
}

data "aws_iam_policy_document" "assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "iam_for_lambda" {
  name               = "iam_for_lambda"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}