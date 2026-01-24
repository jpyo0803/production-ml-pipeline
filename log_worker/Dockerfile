FROM python:3.10-slim

# 작업 디렉토리 설정
WORKDIR /app

# 모듈 복사
COPY log_worker /app

# 의존성 설치
RUN pip install --no-cache-dir -r requirements.txt

# python -u 옵션은 로그를 버퍼링 없이 바로 출력하게 해줌 (Docker logs 확인용)
CMD ["python", "-u", "worker.py"]