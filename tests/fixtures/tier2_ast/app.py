import boto3
from ingest.writer import put_object as write_object

s3 = boto3.client("s3")


class Handler:
    def process(self, batch):
        write_object(batch)
        self.validate(batch)

    def validate(self, batch):
        return len(batch) > 0


@app.route("/telemetry")
def handle_post():
    result = do_local_work()
    return result


def do_local_work():
    return 1
