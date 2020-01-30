from cassandra.auth import PlainTextAuthProvider
import ssl
import requests
from .config import USERNAME, PASSWORD, CONTACT_POINT, PORT
from cassandra.cqlengine import connection, management
from .models import User, Username
from uuid import uuid4
from time import time
import asyncio
from datetime import datetime
import cassandra
from aiocassandra import aiosession

# see https://docs.microsoft.com/en-us/azure/cosmos-db/create-cassandra-python
# if "certpath" in config:
#     ssl_opts["ca_certs"] = cfg.config["certpath"]

session = cassandra.cluster.Cluster(
    contact_points=[CONTACT_POINT],
    port=PORT,
    auth_provider=cassandra.auth.PlainTextAuthProvider(
        username=USERNAME, password=PASSWORD
    ),
    ssl_options={
        "ca_certs": requests.utils.DEFAULT_CA_BUNDLE_PATH,
        "ssl_version": ssl.PROTOCOL_TLSv1_2,
    },
).connect()

try:
    session.set_keyspace("presidents")
except cassandra.InvalidRequest:  # if keyspace does not exist
    # TODO: these settings are currently ignored
    # https://docs.microsoft.com/en-us/azure/cosmos-db/cassandra-support#keyspace-and-table-options
    management.create_keyspace_network_topology(
        name="presidents", dc_replication_map={"datacenter": 1}
    )
    session.set_keyspace("presidents")

connection.set_session(session)
