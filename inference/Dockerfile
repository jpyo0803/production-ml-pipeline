FROM nvcr.io/nvidia/tritonserver:24.01-py3

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x entrypoint.sh

EXPOSE 8000 8001 8002

CMD ["bash", "entrypoint.sh"]
