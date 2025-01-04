# A Web Application Demo using containerised databases

A simple Python [Flask](https://palletsprojects.com/p/flask/) application using an [Oracle Database 23ai Free](https://www.oracle.com/database/free/) database as its backend for data storage. Rather than using the older `cx_oracle` database driver this application uses the new [Python OracleDB driver](https://oracle.github.io/python-oracledb/).

Both the "frontend" and "backend" run in containers. The application is deliberately kept simple, and implemented in a similar fashion as existing tutorials about software development using containers: all it does is count page views per visitor using cookies to identify individual sessions.

> **Warning:** This is not production-ready code, it merely serves as an example how to develop with Oracle database and Python(-oracledb). In particular no attention was spent on security to keep the example simple.

## Building

The Oracle Database 23ai Free Release database [container image](https://hub.docker.com/r/gvenzl/oracle-free) used in this application is provided by Gerald Venzl. No further modifications are required. You can always use the official image, available from [Oracle's container registry](https://container-registry.oracle.com/ords/ocr/ba/database/free) instead, but need to make sure the demo user is created.

Building the Application is also quite simple, just run `podman build -t pydemo:1.0 .` to build the application locally. Simply use the commands shown below.

## Testing

Podman has been used for creating and testing the application container image. Docker should work as well but might require adjustments to the code and secret management.

### Secrets, Networks, and Volumes

The following entities must be in place before the application can be tested:

- Secrets
  - `oracle-system-password`: a secret to store the Oracle database's `system` and `sys` passwords
  - `flask-user-password`: the password for the application user
- Volume
  - `oradata-vol` must be created to persistently store the database on disk
- Network
  - `oracle-net` is used to link the database container to the application container. Must have DNS enabled (`podman network inspect oracle-net | jq '.[0].dns_enabled'` must return `true`)

Gerald Venzl's database container image can be instructed to create an `APP_USER`. For simplicity this `APP_USER` account will be used by the Flask application. Update the `podman run` command below to change the username from `flaskdemo` to something of your liking. The user's password is be stored as the aforementioned `flask-user-password` secret.

Please refer to [this RedHat article](https://www.redhat.com/sysadmin/new-podman-secrets-command) for more details about Podman Secrets and how to create them. Before continuing, please ensure the entities listed above have been created.

### Database

Note that Oracle Database 23ai Free is started _rootless_ in the following code-snippet. Adjust the example as appropriate for your environment:

```shell
podman run --detach \
--name some-oracle \
--publish 1521:1521 \
--volume oradata-vol:/opt/oracle/oradata \
--secret oracle-system-password,type=env,target=ORACLE_PASSWORD \
--secret flask-user-password,type=env,target=APP_USER_PASSWORD \
--env APP_USER=flaskdemo \
--net oracle-net \
docker.io/gvenzl/oracle-free:23.6-slim
```

After a minute or so you have a working Oracle Database 23ai Free system running in the container. Use `podman logs -f some-oracle` to access the container logs, CTRL-C gets you out of there.

Use `podman ps` or `podman container ls` to check the database is up and running with port 1521 exposed.

### Application

Once the database is up and running you can test the Flask application next. The following command is for local testing/development only, the container image will use [Waitress](https://flask.palletsprojects.com/en/stable/deploying/waitress/) to serve the application. Note that you have to provide values for `PYTHON_USERNAME`, `PYTHON_PASSWORD` and `PYTHON_CONNECTSTRING` before you can start the application. If you are using `zsh` you can prevent the password from making it into the history by using `HIST_IGNORE_SPACE`, `bash` has `HISTCONTROL` etc. 

```sh
flask --app hit_counter run --debug
```

With that test successfully completed you can build the container image:

```bash
podman build -t pydemo:1.0 .
```

Now that the container has been built it can be started. Just like the database container it's started _rootless_

```bash
podman run --detach \
--name some-pythondemo \
--net oracle-net \
--env PYTHON_USERNAME=flaskdemo \
--secret flask-user-password,type=env,target=PYTHON_PASSWORD \
--env PYTHON_CONNECTSTRING="some-oracle/freepdb1" \
--publish 8080:8080 \
localhost/pydemo:1.0
```

Once the application start completed, point your browser to [http://localhost:8080](http://localhost:8080). [Waitress](https://flask.palletsprojects.com/en/stable/deploying/waitress/) serves the application from the container image.

Live demos benefit from the QR code that's generated by the app: after deployment to a cloud instance, simply provide the URL to the load balancer as a query parameter. Participants can point their mobile devices at the QR code and participate.

## Next Steps

As per the introduction the application has been kept simple to focus on the main topic: creating and running a web application in containers, connecting to an Oracle instance. Improvements to this code should include introduction of TLS security and automated build of the (application) container image.
