FROM python:3.10-slim

WORKDIR /app

COPY . .

# 현재는 CPU only 모드로 설치
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

CMD ["python", "train.py"]