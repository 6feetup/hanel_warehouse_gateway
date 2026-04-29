FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV AUTO_COMPLETE_SECONDS=10
ENV MOCK_DATA_DIR=/app/data
EXPOSE 8080
CMD ["python", "app.py"]
