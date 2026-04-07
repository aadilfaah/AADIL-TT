FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    wget curl gnupg unzip ca-certificates \
    --no-install-recommends

RUN curl -fSsL https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor | tee /usr/share/keyrings/google-chrome.gpg > /dev/null \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y google-chrome-stable --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app
RUN pip install flask gunicorn selenium

# লগের জন্য বিশেষ কনফিগারেশন
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "main:app"]
