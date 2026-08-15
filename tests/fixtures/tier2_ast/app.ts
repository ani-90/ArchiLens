import * as boto3 from "boto3";
import { putObject as writeObject } from "./ingest/writer";

const s3 = boto3.client("s3");

class Handler {
  @Route("/telemetry")
  process(batch: any) {
    writeObject(batch);
    this.validate(batch);
  }

  validate(batch: any) {
    return batch.length > 0;
  }
}

function handlePost() {
  const result = doLocalWork();
  return result;
}

function doLocalWork() {
  return 1;
}
