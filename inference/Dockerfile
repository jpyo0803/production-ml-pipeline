FROM python:3.10-slim

WORKDIR /app

COPY inference /app

RUN pip install --no-cache-dir -r requirements.txt --ignore-installed

RUN chmod +x entrypoint.sh

CMD ["bash", "entrypoint.sh"]
