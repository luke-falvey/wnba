locals {
  lambda_filename = "lambda_function_payload.zip"
}

resource "aws_iam_role" "check_bookings_role" {
  name = "check_bookings_role"

  assume_role_policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
        "Action": "sts:AssumeRole",
        "Principal": {
            "Service": "lambda.amazonaws.com"
        },
        "Effect": "Allow",
        "Sid": ""
        }
    ]
}
EOF
}

resource "aws_lambda_function" "check_bookings" {
  filename      = local.lambda_filename
  function_name = "check_bookings"
  role          = aws_iam_role.check_bookings_role.arn
  handler       = "bookings.bookings_handler"
  timeout       = 5

  # The filebase64sha256() function is available in Terraform 0.11.12 and later
  # For Terraform 0.11.11 and earlier, use the base64sha256() function and the file() function:
  # source_code_hash = "${base64sha256(file("lambda_function_payload.zip"))}"
  source_code_hash = filebase64sha256(local.lambda_filename)

  runtime = "python3.12"

  environment {
    variables = {
      HELLO_CLUB_USERNAME = var.hello_club_username
      HELLO_CLUB_PASSWORD = var.hello_club_password
      SMTP_PASSWORD       = var.smpt_password
    }
  }
}

# This is to optionally manage the CloudWatch Log Group for the Lambda Function.
# If skipping this resource configuration, also add "logs:CreateLogGroup" to the IAM policy below.
resource "aws_cloudwatch_log_group" "check_bookings_log_group" {
  name              = "/aws/lambda/${aws_lambda_function.check_bookings.function_name}"
  retention_in_days = 7
}

# See also the following AWS managed policy: AWSLambdaBasicExecutionRole
resource "aws_iam_policy" "check_bookings" {
  name        = "check_bookings"
  path        = "/"
  description = "IAM policy for check_bookings lambda"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*",
      "Effect": "Allow"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.check_bookings_role.name
  policy_arn = aws_iam_policy.check_bookings.arn
}

resource "aws_cloudwatch_event_rule" "schedule" {
  name        = "daily-bookings-email"
  description = "Send an email containing time to book for the day"

  schedule_expression = "cron(0 3 * * ? *)"
}


resource "aws_cloudwatch_event_target" "sns" {
  rule      = aws_cloudwatch_event_rule.schedule.name
  target_id = "CheckBookings"
  arn       = aws_lambda_function.check_bookings.arn
}
