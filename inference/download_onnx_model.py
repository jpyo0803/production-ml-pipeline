import boto3
import os

MODEL_DIR = "/models/home_credit_default/1"
os.makedirs(MODEL_DIR, exist_ok=True)

s3 = boto3.client(
    "s3",
    endpoint_url=os.environ["MLFLOW_S3_ENDPOINT_URL"],
    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
)

s3.download_file(
    Bucket="models",
    Key="home_credit_default/1/model.onnx",
    Filename=f"{MODEL_DIR}/model.onnx",
)
