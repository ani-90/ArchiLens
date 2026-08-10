resource "aws_sqs_queue" "events_queue" {
  name = "events-queue"
}

resource "aws_lambda_function" "consumer" {
  function_name = "consumer-lambda"
  environment {
    variables = {
      QUEUE_URL = aws_sqs_queue.events_queue.id
      TABLE     = var.table_name
      REGION    = data.aws_region.current.name
      BUCKET    = module.storage.bucket_name
    }
  }
}

resource "aws_iam_role" "consumer_role" {
  name = "consumer-role"
}

resource "random_id" "suffix" {
  byte_length = 4
}

resource "aws_sns_topic" "alerts-topic" {
  name = "alerts-topic"
}

resource "aws_lambda_function" "publisher" {
  function_name = "publisher-lambda"
  environment {
    variables = {
      TOPIC_ARN = aws_sns_topic.alerts-topic.arn
    }
  }
}
