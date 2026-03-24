FROM python:3.11

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBUG FALSE

MAINTAINER https://pavelcode5426.github.io

WORKDIR /code


RUN pip install --upgrade pip
RUN  apt-get update && apt-get install -y --no-install-recommends supervisor && rm -rf /var/lib/apt/lists/*
RUN playwright install-deps
#https://databay.com/free-proxy-list/http
RUN HTTPS_PROXY=http://38.145.220.40:8446 playwright install

COPY requirements.txt .
COPY . .
COPY supervisor.conf /etc/supervisor/conf.d/supervisor.conf
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh


EXPOSE 8000
VOLUME ["/code/storage"]

CMD ["sh","/entrypoint.sh"]

