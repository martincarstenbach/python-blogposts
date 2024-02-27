FROM container-registry.oracle.com/os/oraclelinux:9-slim

WORKDIR /code

RUN microdnf install python3.11 python3.11-pip python3.11-setuptools python3.11-wheel && \
    rm -rf /var/cache/dnf && \
    useradd -ms /bin/bash waitress && chown -R waitress /code

USER waitress

COPY requirements.txt requirements.txt
COPY . .
RUN pip-3.11 install -r requirements.txt --no-cache-dir

EXPOSE 8080
CMD ["/home/waitress/.local/bin/waitress-serve", "hitCounter:app"]