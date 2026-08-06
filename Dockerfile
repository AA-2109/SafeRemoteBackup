# Base image for 32-bit ARM (Raspberry Pi)
FROM python:3.11-slim

# Install pre-compiled C libraries and python-pillow binaries
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pillow \
    python3-dev \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy application files
COPY app/ /app/
COPY requirements.txt /app/requirements.txt

# Install dependencies using pre-compiled wheels
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

# Ensure the upload folder is writable
RUN mkdir -p /app/static/uploads && chmod -R 755 /app/static/uploads

# Expose the Flask app port
EXPOSE 5000

# Command to run the Flask app
CMD ["bash", "starting_script.sh"]
