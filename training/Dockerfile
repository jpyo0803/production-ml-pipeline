FROM python:3.10-slim

WORKDIR /app

# 모듈 복사
COPY common /common
COPY feature_store/feast_repo /feast_repo

COPY training /app

ENV PYTHONPATH="/"

# JAVA JRE 설치, PySpark 구동을 위해 필요
RUN mkdir -p /usr/share/man/man1 && \
    apt-get update && \
    apt-get install -y default-jre procps curl && \
    rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/default-java

# 현재는 CPU only 모드로 설치
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /opt/jars && \
    curl -o /opt/jars/hadoop-aws-3.3.4.jar https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar && \
    curl -o /opt/jars/aws-java-sdk-bundle-1.12.262.jar https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar

CMD ["python", "train.py"]