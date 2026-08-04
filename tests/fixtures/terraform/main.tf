resource "aws_s3_bucket" "raw_telemetry" {
  bucket = "raw-telemetry"
}

resource "aws_lambda_function" "normalize" {
  function_name = "normalize-lambda"
  s3_bucket     = aws_s3_bucket.raw_telemetry.id
  environment {
    variables = {
      TABLE = aws_dynamodb_table.events.name
    }
  }
}

resource "aws_dynamodb_table" "events" {
  name = "events"
}

resource "aws_iam_role" "unmapped_kind" {
  name = "some-role"
}
