# Flask Oracle XE 21c Demo

A simple Python [Flask](https://flask.palletsprojects.com/en/2.2.x/) application using an Oracle XE 21c database as its backend for data storage. Both the "frontend" and "backend" run in containers. The application is deliberately kept simple, and implemented similar to existing tutorials about software development using containers. The application count page visits per visitor using cookies to identify individual sessions.

> This is not production-ready code, it merely serves as an example how to develop with Oracle database

# Building

The Oracle XE 21c database [container image](https://github.com/gvenzl/oci-oracle-xe) is provided by Gerald Venzl. No further modifications are required.

Building the Application is also quite simple, just run `podman build -t pydemo:1.0 .` to build the application locally.

# Testing

Podman has been used for creating and testing the container images. Docker should work as well but might require adjustments to the code. 

## Secrets, Networks, and Volumes

The following entities must be in place before the application can be tested:

- Secrets
    * `oracle-system-password`: a secret to store the Oracle XE 21c database's `system`and `sys` passwords
    * `flask-user-password`: the password for the application user
- Volume
    * `oradata-vol` must be created to persistently store the database on disk
- Network
    * `oracle-net` is used to link the database container to the application container

The XE database container image can be instructed to create an `APP_USER`. For simplicity this `APP_USER` account will be used by the Flask application. Update the `podman run` command below to change the username from `flaskdemo` to something of your liking. The user's password is be stored as the aforementioned `flask-user-password` secret.

Please refer to [this article](https://www.redhat.com/sysadmin/new-podman-secrets-command) for more details about Podman Secrets and how to create them. 

## Database 

Note that the Oracle XE 21c container in the following code-snippet is started _rootless_. Adjust the example as appropriate for your environment

```
podman run --detach \
--secret oracle-system-password --env ORACLE_PASSWORD_FILE=/run/secrets/oracle-system-password \
--env APP_USER=flaskdemo \
--secret flask-user-password,type=env,target=APP_USER_PASSWORD \
--volume oradata-vol:/opt/oracle/oradata \
--name oraclexe \
--net oracle-net \
--publish 1521:1521 \
docker.io/gvenzl/oracle-xe:21-slim
```

After a minute or so you have a working Oracle XE 21c database. Use `podman logs -f oraclexe` to access the container logs, CTRL-C gets you out of there.

Use `podman ps` or `podman container ls` to check the database is up and running with port 1521 exposed.

## Application

With the database up and running you can start the Flask application next. If not yet built, create the container image

```bash
cd pydemo
podman build -t pydemo:1.0 .
```

Now that the container has been built it can be started:

```bash
podman run --detach \
--name pydemo \
--net oracle-net \
--env PYTHON_USERNAME=flaskdemo \
--secret flask-user-password,type=env,target=PYTHON_PASSWORD \
--env PYTHON_CONNECTSTRING="oraclexe/xepdb1" \
--publish 8080:8080 \
localhost/pydemo:1.0
```

Once the application start completed, point your browser to [http://localhost:8080](http://localhost:8080). [Waitress](https://flask.palletsprojects.com/en/2.2.x/deploying/waitress/) serves the application from the container image.
