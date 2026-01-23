FROM python:3.10-slim

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY . .

# python -u 옵션은 로그를 버퍼링 없이 바로 출력하게 해줌 (Docker logs 확인용)
CMD ["python", "-u", "worker.py"]