FROM python:3.14-slim

# Patch OS packages (e.g. zlib) that the base image hasn't picked up yet
RUN apt-get update \
 && apt-get upgrade -y --no-install-recommends \
 && rm -rf /var/lib/apt/lists/*

# Patch pip and setuptools: they ship with their own bundled libraries
RUN pip install --no-cache-dir --upgrade pip setuptools

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY templates/ templates/

RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin appuser
USER 10001

EXPOSE 5000

CMD ["python", "app.py"]