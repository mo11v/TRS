FROM python:3.11-slim

# System deps
RUN apt-get update && apt-get install -y \
    gcc libffi-dev curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Make start script executable
RUN chmod +x start.sh

# Create temp dirs
RUN mkdir -p /tmp/jam_uploads /tmp/jam_reports

# Port
EXPOSE 10000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:10000/api/status || exit 1

CMD ["./start.sh"]
