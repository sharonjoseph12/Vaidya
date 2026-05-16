FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from backend and root (if needed)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all layers into the container
# We assume the context is the prism root
COPY backend/ /app/backend/
COPY layer2_reason/ /app/layer2_reason/
COPY layer3_twin/ /app/layer3_twin/
COPY layer4_rl/ /app/layer4_rl/
COPY contracts/ /app/contracts/
COPY data/ /app/data/

# Set python path
ENV PYTHONPATH=/app

WORKDIR /app/backend

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
