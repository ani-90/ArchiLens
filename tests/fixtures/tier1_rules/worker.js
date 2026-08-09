// new SQSClient() setup used to live here, ripped out
const { S3Client } = require("@aws-sdk/client-s3");
const s3 = new S3Client({ region: "us-east-1" });

const { DynamoDBClient } = require("@aws-sdk/client-dynamodb");
const ddb = new DynamoDBClient({});

/* multi-line comment
   new Redis() should not match inside here
*/
const pg = require("pg");
const Redis = require("ioredis");
const cache = new Redis();
