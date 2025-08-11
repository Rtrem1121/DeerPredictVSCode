# Multi-stage Docker build for deer prediction app
FROM python:3.10-slim as base

# Install system dependencies (basic for now, can add GDAL later)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    mkdir -p /home/appuser && \
    chown -R appuser:appuser /home/appuser

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies (LiDAR support will be added in future version)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# --- Backend Stage ---
FROM base as backend

# Copy backend code
COPY ./backend /app/backend

# Copy data
COPY ./data /app/data

# Copy LiDAR processing modules
COPY ./lidar /app/lidar

# Set permissions and create logs directory
RUN mkdir -p /app/logs && \
    chown -R appuser:appuser /app /home/appuser

# Switch to non-root user
USER appuser

# Change working directory to backend
WORKDIR /app/backend

EXPOSE 8000

# Health check for FastAPI
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

# --- Frontend Stage ---
FROM base as frontend

# Copy frontend code
COPY ./frontend /app/frontend

# Set permissions and create logs directory
RUN mkdir -p /app/logs && \
    chown -R appuser:appuser /app /home/appuser

# Set environment variable for Streamlit
ENV HOME=/home/appuser
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_FILE_WATCHER_TYPE=none

# Switch to non-root user
USER appuser

EXPOSE 8501

# Health check for Streamlit
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "frontend/app.py", "--server.port", "8501", "--server.address", "0.0.0.0", "--server.headless", "true"]
