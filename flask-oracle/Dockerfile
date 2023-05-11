FROM ghcr.io/oracle/oraclelinux8-compat:8-slim

WORKDIR /code

RUN dnf -y module disable python36 && \
    dnf -y module enable python39 && \
    dnf -y install python39 python39-pip python39-setuptools python39-wheel && \
    rm -rf /var/cache/dnf

COPY requirements.txt requirements.txt
COPY . .
RUN pip3 install -r requirements.txt --no-cache-dir

EXPOSE 8080
CMD ["waitress-serve", "hitCounter:app"]