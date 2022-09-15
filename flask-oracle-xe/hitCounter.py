"""
app.py

Martin Bach, 12 Sep 2022

Based on code by Christopher Jones, 10 Sep 2020
Original source: https://blogs.oracle.com/opal/post/how-to-use-python-flask-with-oracle-database

Demo: using Flask with Oracle Database XE 21c

Before running, set these environment variables to connect to the database:

    PYTHON_USERNAME       - your DB username
    PYTHON_PASSWORD       - your DB password
    PYTHON_CONNECTSTRING  - the connection string to the DB, e.g. "example.com/XEPDB1"

"""

import oracledb
import os
import uuid
import socket

from waitress import serve
from flask import Flask, render_template, make_response, request

##########################################################################
#
# start_pool(): create a connection pool
#


def start_pool():

    # Generally a fixed-size pool is recommended, i.e. pool_min=pool_max.
    # Here the pool contains 4 connections, which is fine for 4 conncurrent
    # users and absolutely adequate for this demo.

    pool_min = 4
    pool_max = 4
    pool_inc = 0

    print("Connecting to", os.environ.get("PYTHON_CONNECTSTRING"))

    pool = oracledb.create_pool(
        user=os.environ.get("PYTHON_USERNAME"),
        password=os.environ.get("PYTHON_PASSWORD"),
        dsn=os.environ.get("PYTHON_CONNECTSTRING"),
        min=pool_min,
        max=pool_max,
        increment=pool_inc
    )

    return pool

##########################################################################
#
# create_schema(): drop and create the demo table
#


def create_schema():
    with pool.acquire() as connection:
        with connection.cursor() as cursor:

            try:
                cursor.execute(
                    """
                    CREATE table hit_count (
                        session_id  varchar2(36),
                        hits        number,
                        ts          timestamp not null,
                        constraint pk_hit_count 
                        primary key(session_id, hits)
                    )
                    """
                )
            except oracledb.Error as err:
                error_obj, = err.args
                print(f"Error creating hit_count table: {error_obj.message}")

##########################################################################
#
# get_hit_count(): keep track of page hits, similar in a way it is done
# in many tutorials. The code in this example is multi-user capable.
#


def get_hit_count(sessionID):

    print(f"DEBUG: hostname: {socket.gethostname()} session ID: {sessionID}")

    with pool.acquire() as connection:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                INSERT into hit_count (
                    session_id, hits, ts
                )
                SELECT :session_id, nvl((max(hits)+1), 1), systimestamp 
                  FROM hit_count 
                 WHERE session_id = :session_id
                """,
                session_id=sessionID
            )

            connection.commit()

            maxHitsBySession = "SELECT max(hits) from hit_count WHERE session_id = :session_id"

            numHits = 0
            for row in cursor.execute(maxHitsBySession, session_id=str(sessionID)):
                numHits = row[0]

    return numHits


##########################################################################
#
# Main
#

app = Flask(__name__)

pool = start_pool()

# Try to create the demo table
create_schema()

# Display the hit count


@app.route('/')
def index():
    # get the session ID from the cookie
    myUUID = request.cookies.get("uuid")

    # it must be a new session if there is not session ID found
    # create one in that case and translate it to a string
    if myUUID is None:
        myUUID = str(uuid.uuid4())

    # get hit count by this session
    hits = get_hit_count(myUUID)

    # and send a response to the browser
    response = make_response(render_template('index.html', hits=hits))
    response.set_cookie("uuid", myUUID)
    return response
