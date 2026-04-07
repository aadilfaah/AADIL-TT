FROM python:3.9-slim

# Install Chrome and dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    google-chrome-stable \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Set display port to avoid crash
ENV DISPLAY=:99

WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt

# Start the app
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "main:app"]
