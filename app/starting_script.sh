#!/bin/bash

# Generate new self-signed certificate
echo "Generating self-signed certificate..."
openssl req -x509 -newkey rsa:4096 \
  -keyout key.pem \
  -out cert.pem \
  -days 365 \
  -nodes \
  -subj "/C=XX/ST=XX/L=XX/O=XX/OU=XX/CN=localhost"

echo "Certificate generated!"

# Run Flask app
echo "🚀 Starting Flask app..."
python3 app.py