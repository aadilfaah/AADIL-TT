FROM python:3.9-slim

# প্রয়োজনীয় ডিপেন্ডেন্সি এবং গুগল ক্রোম ইনস্টল করা
RUN apt-get update && apt-get install -y \
    wget gnupg unzip curl google-chrome-stable \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app
RUN pip install flask gunicorn selenium

# Gunicorn দিয়ে অ্যাপ চালানো এবং লগ এনাবল করা
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "main:app"]
