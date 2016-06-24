FROM python:3.5

WORKDIR /dd_crawler

RUN apt-get update && \
    apt-get install -y dnsmasq redis-tools

COPY ./requirements.txt .

RUN pip install -U pip setuptools wheel && \
    pip install -r requirements.txt

COPY ./docker/dnsmasq.conf /etc/
COPY ./docker/resolv.dnsmasq /etc/

COPY . .

RUN pip install -e .

ENTRYPOINT /bin/bash /dd_crawler/docker/crawl.sh
