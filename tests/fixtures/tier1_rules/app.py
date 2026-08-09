import boto3
import psycopg2
import redis

# boto3.client("sqs") -- old queue code, no longer used
s3 = boto3.client("s3")
bucket = s3.Bucket("raw-telemetry")

table = boto3.resource("dynamodb")

queue = boto3.client("sqs")

conn = psycopg2.connect("dbname=app user=admin")

cache = redis.Redis(host="localhost")
