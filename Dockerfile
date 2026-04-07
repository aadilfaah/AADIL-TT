FROM python:3.9-slim

# ১. সিস্টেম আপডেট এবং প্রয়োজনীয় টুলস ইনস্টল
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    unzip \
    ca-certificates \
    --no-install-recommends

# ২. গুগল ক্রোম ইনস্টল করার সঠিক ও লেটেস্ট পদ্ধতি
RUN curl -fSsL https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor | tee /usr/share/keyrings/google-chrome.gpg > /dev/null \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    --no-install-recommends

# ৩. ক্লিনআপ (ইমেজ হালকা করার জন্য)
RUN rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

# ৪. লাইব্রেরি ইনস্টল
RUN pip install --no-cache-dir flask gunicorn selenium

# ৫. পোর্ট এবং স্টার্ট কমান্ড
EXPOSE 10000
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--timeout", "120", "main:app"]
