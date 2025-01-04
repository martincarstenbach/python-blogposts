"""
hit_counter.py

Martin Bach, 04 Jan 2025

Based on code by Christopher Jones, 10 Sep 2020
Original source: https://blogs.oracle.com/opal/post/how-to-use-python-flask-with-oracle-database

Demo: using Flask with Oracle Database Free 23ai

Before running, set these environment variables to connect to the database or provide them
to your container runtime as environment variables:

    PYTHON_USERNAME       - your DB username
    PYTHON_PASSWORD       - your DB password
    PYTHON_CONNECTSTRING  - the connection string to the database, e.g. "localhost/freepdb1"

This code serves as an example for establishing DevOps practices. It is deliberately written poorly
and should not be considered an example other than for the improvements that are going to be applied
to it over time
"""

import os
import uuid
import logging

from flask import Flask, render_template, make_response, request
import oracledb

##########################################################################
#
# start_pool(): create a connection pool
#

def start_pool():
    """Create a connection pool for the application."""

    logger = logging.getLogger(__name__)

    # Generally a fixed-size pool is recommended, i.e. pool_min=pool_max.
    # Here the pool contains 4 connections, which is fine for 4 conncurrent
    # users and absolutely adequate for this demo.

    pool_min = 4
    pool_max = 4
    pool_inc = 0

    python_username = os.environ.get("PYTHON_USERNAME")
    python_password = os.environ.get("PYTHON_PASSWORD")
    python_connectstring = os.environ.get("PYTHON_CONNECTSTRING")

    logger.info("Connecting to %s as %s", python_connectstring, python_username)

    return oracledb.create_pool(
        user=python_username,
        password=python_password,
        dsn=python_connectstring,
        min=pool_min,
        max=pool_max,
        increment=pool_inc
    )


##########################################################################
#
# create_schema(): drop and create the demo table
#

def create_schema():
    """This function initialises the database schema.

    Performing this task in that way is very bad practice, and must be avoided.
    Further iterations of this code will ensure industry best known methods are
    applied to this application.
    """

    logger = logging.getLogger(__name__)

    with pool.acquire() as connection:
        with connection.cursor() as cursor:

            try:
                cursor.execute(
                    """
                    CREATE TABLE if not exists hit_count (
                        session_id  varchar2(36),
                        hits        number,
                        ts          timestamp not null,
                        constraint pk_hit_count 
                        primary key(session_id, hits)
                    )
                    """
                )
            except oracledb.Error as e:
                # pylint: disable-next=unused-variable
                error_obj, *remaining_tuples = e.args
                logger.error("Error Message: %s", error_obj.message)

##########################################################################
#
# get_hit_count(): keep track of page hits, similar in a way it is done
# in many tutorials. The code in this example is multi-user capable.
#

def get_hit_count(session_id):
    """This function accesses the database table directly to display the number
    of page hits."""

    logger = logging.getLogger(__name__)
    logger.debug("Accessing hit count for session: %s", session_id)

    num_hits = 0

    with pool.acquire() as connection:
        with connection.cursor() as cursor:

            try:
                cursor.execute(
                    """
                    INSERT into hit_count (
                        session_id, hits, ts
                    )
                    SELECT :session_id, nvl((max(hits)+1), 1), systimestamp 
                    FROM hit_count 
                    WHERE session_id = :session_id
                    """,
                    session_id=session_id
                )

                connection.commit()

                max_hits_per_session = """
                    SELECT
                        max(hits)
                    FROM
                        hit_count
                    WHERE
                        session_id = :session_id
                    """

                for row in cursor.execute(max_hits_per_session, session_id=str(session_id)):
                    num_hits = row[0]

            except oracledb.Error as e:
                # pylint: disable-next=unused-variable
                error_obj, *remaining_tuples = e.args
                logger.error("Error Message: %s", error_obj.message)

        logger.debug("There were: %s hits recorded for session %s", num_hits, session_id)

    return num_hits


##########################################################################
#
# Main
#

app = Flask(__name__)

# Set logging level to DEBUG. This should be changed for production use
logging.basicConfig(level=logging.DEBUG)

# create the connection pool
pool = start_pool()

# Try to create the demo table
# You can safely consider this to be an anti-pattern, this call will later on
# be removed from this file
create_schema()

# Display the hit count

@app.route("/")
def index():
    """Return the HTML page with the embedded page hit count for this session"""

    logger = logging.getLogger(__name__)
    logger.debug("Accessing main application endpoint")

    # get the session ID from the cookie
    my_uuid = request.cookies.get("uuid")

    # it must be a new session if there is not session ID found
    # create one in that case and translate it to a string
    if my_uuid is None:
        my_uuid = str(uuid.uuid4())

    # get hit count by this session
    hits = get_hit_count(my_uuid)

    # and send a response to the browser
    response = make_response(render_template('index.html', hits=hits))
    response.set_cookie("uuid", my_uuid, samesite="Strict")
    return response

@app.route("/status")
def status():
    """Provide an endpoint for a health-check."""

    logger = logging.getLogger(__name__)
    logger.debug("Accessing healthcheck endpoint")

    return {
        "status": "healthy"
    }
