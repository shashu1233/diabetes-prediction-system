# Use official Python 3.12/3.13 slim image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Set work directory
WORKDIR /app

# Install system dependencies (optional, but good for building packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY backend/ml_model_train.py /app/backend/
COPY pima-indians-diabetes.csv /app/
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    jinja2 \
    pandas \
    numpy \
    scikit-learn \
    sqlalchemy \
    pyjwt \
    python-multipart \
    email-validator \
    httpx

# Copy project files
COPY backend /app/backend
COPY frontend /app/frontend

# Pre-train the model inside the container so it's packaged and ready
RUN python backend/ml_model_train.py

# Expose port
EXPOSE 8080

# Command to run the application
CMD ["sh", "-c", "python -m uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}"]
