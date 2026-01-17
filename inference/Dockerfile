FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --ignore-installed

COPY . .

RUN chmod +x entrypoint.sh

CMD ["bash", "entrypoint.sh"]
