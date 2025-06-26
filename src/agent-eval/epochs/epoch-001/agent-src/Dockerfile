# Layer 1: Base environment setup
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Layer 2: System dependencies (cached when base image changes)
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Layer 3: Python dependencies (cached when requirements.txt doesn't change)
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Layer 4: Create directories and user (cached when filesystem structure doesn't change)
RUN mkdir -p /app/data/input \
    && mkdir -p /app/data/output \
    && mkdir -p /app/data/config \
    && mkdir -p /app/workspace

# Create logs directory as mount point (will be mounted from host)
RUN mkdir -p /app/logs

# Create non-root user for security
RUN useradd -m -u 1000 agent && chown -R agent:agent /app

# Layer 5: Application code (rebuilt when source code changes)
COPY agent.py .

# Switch to non-root user
USER agent

# Set working directory to workspace for agent execution
WORKDIR /app/workspace

# Default command - can be overridden when running the container
ENTRYPOINT ["python", "/app/agent.py"]
CMD []