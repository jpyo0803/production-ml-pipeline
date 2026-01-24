FROM python:3.10-slim

WORKDIR /app

# 모듈 복사
COPY common /app/common
COPY ./feature_store .

ENV PYTHONPATH="/app"

# JAVA JRE 설치, PySpark 구동을 위해 필요
RUN mkdir -p /usr/share/man/man1 && \
    apt-get update && \
    apt-get install -y default-jre procps curl && \
    rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/default-java

RUN pip install -r requirements.txt

RUN mkdir -p /opt/jars && \
    curl -o /opt/jars/hadoop-aws-3.3.4.jar https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar && \
    curl -o /opt/jars/aws-java-sdk-bundle-1.12.262.jar https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar

CMD ["bash", "entrypoint.sh"]