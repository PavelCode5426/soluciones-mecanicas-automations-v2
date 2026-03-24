FROM python:3.11

ARG PLAYWRIGHT_PROXY

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBUG FALSE

MAINTAINER https://pavelcode5426.github.io

WORKDIR /code


RUN pip install --upgrade pip
RUN  apt-get update && apt-get install -y --no-install-recommends supervisor && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install-deps
#https://databay.com/free-proxy-list/http
RUN if [ -n "$PLAYWRIGHT_PROXY" ]; then \
      HTTPS_PROXY=$PLAYWRIGHT_PROXY playwright install; \
    else \
      playwright install; \
    fi


COPY . .
COPY supervisor.conf /etc/supervisor/conf.d/supervisor.conf
COPY entrypoint.sh /entrypoint.sh


EXPOSE 8000
VOLUME ["/code/storage"]

CMD ["sh","/entrypoint.sh"]

