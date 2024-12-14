# based on https://yum.oracle.com/oracle-linux-python.html#InstallOnOl9

FROM ghcr.io/oracle/oraclelinux:9 as python312

RUN dnf -y install python3.12 python3.12-libs python3.12-pip python3.12-setuptools python3.12-wheel && \
    rm -rf /var/cache/dnf

FROM python312 as runtime

WORKDIR /code

COPY requirements.txt requirements.txt
COPY . .
RUN pip3.12 install -r requirements.txt --no-cache-dir

EXPOSE 8080
CMD ["waitress-serve", "hit_counter:app"]