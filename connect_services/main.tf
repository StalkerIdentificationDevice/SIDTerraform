resource "aws_iam_role_policy" "dynamodb-lambda-policy" {
  name = "dynamodb_lambda_policy"
  role = var.lambda_iam_id
  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Effect" : "Allow",
        "Action" : ["dynamodb:*"],
        "Resource" : "${var.table_arn}"
      }
    ]
  })
}

resource "aws_iam_role_policy" "rekognition-lambda-policy" {
  name = "rekognition_lambda_policy"
  role = var.lambda_iam_id
  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Effect" : "Allow",
        "Action" : ["rekognition:*"],
        "Resource" : "*"
      }
    ]
  })
}

resource "aws_iam_role_policy" "s3-lambda-policy" {
  name = "s3_lambda_policy"
  role = var.lambda_iam_id
  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Effect" : "Allow",
        "Action" : ["s3:*"],
        "Resource" : "${var.bucket_arn}/*"
      }
    ]
  })
}

resource "aws_lambda_permission" "allow_bucket" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_arn
  principal     = "s3.amazonaws.com"
  source_arn    = var.bucket_arn
}
