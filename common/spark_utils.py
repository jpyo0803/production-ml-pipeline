import os
from pyspark.sql import SparkSession

def get_spark_session(app_name):
    AWS_KEY = os.environ.get("AWS_ACCESS_KEY_ID", "minioadmin")
    AWS_SECRET = os.environ.get("AWS_SECRET_ACCESS_KEY", "minioadmin123")
    AWS_ENDPOINT = os.environ.get("AWS_ENDPOINT_URL", "http://minio:9000")

    # Dockerfile에서 다운로드 받은 JAR 파일들의 경로
    jar_paths = "/opt/jars/hadoop-aws-3.3.4.jar:/opt/jars/aws-java-sdk-bundle-1.12.262.jar"

    spark = SparkSession.builder \
        .appName(app_name) \
        .config("spark.driver.extraClassPath", jar_paths) \
        .config("spark.executor.extraClassPath", jar_paths) \
        .config("spark.hadoop.fs.s3a.endpoint", AWS_ENDPOINT) \
        .config("spark.hadoop.fs.s3a.access.key", AWS_KEY) \
        .config("spark.hadoop.fs.s3a.secret.key", AWS_SECRET) \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
        .config("spark.hadoop.fs.s3.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .getOrCreate()
    
    return spark