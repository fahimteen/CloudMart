FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY applications/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend app code
COPY applications/backend/app ./app

EXPOSE 80
ENV PORT=80

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
