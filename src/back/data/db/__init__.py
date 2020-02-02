from cassandra.auth import PlainTextAuthProvider
import ssl
import requests
try:
    from .config import USERNAME, PASSWORD, CONTACT_POINT, PORT
except:
    import os
    USERNAME, PASSWORD, CONTACT_POINT, PORT = os.getenv('DB_USERNAME'), os.getenv('DB_PASSWORD'), os.getenv('DB_CONTACT_POINT'), os.getenv('DB_PORT')
from cassandra.cqlengine import connection, management
from .models import User, Username
from uuid import uuid4
from time import time
import asyncio
from datetime import datetime
import cassandra
from aiocassandra import aiosession
import logging


logger = logging.getLogger(__name__)

# see https://docs.microsoft.com/en-us/azure/cosmos-db/create-cassandra-python
# if "certpath" in config:
#     ssl_opts["ca_certs"] = cfg.config["certpath"]

logger.info('connecting to database')
logger.info(requests.utils.DEFAULT_CA_BUNDLE_PATH)
session = cassandra.cluster.Cluster(
    contact_points=[CONTACT_POINT],
    port=int(PORT),
    auth_provider=cassandra.auth.PlainTextAuthProvider(
        username=USERNAME, password=PASSWORD
    ),
    ssl_options={
        # "ca_certs": requests.utils.DEFAULT_CA_BUNDLE_PATH,
        "ssl_version": ssl.PROTOCOL_TLSv1_2,
    },
    connect_timeout=10,
    control_connection_timeout=None
).connect()
logger.info('connected to database')
session.row_factory = cassandra.query.dict_factory

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
