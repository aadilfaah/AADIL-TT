FROM python:3.9-slim

# প্রয়োজনীয় টুলস ইনস্টল
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    unzip \
    --no-install-recommends

# গুগল ক্রোম ইনস্টল করার সঠিক পদ্ধতি
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app
RUN pip install flask gunicorn selenium

# Gunicorn রান করা
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--timeout", "120", "main:app"]
