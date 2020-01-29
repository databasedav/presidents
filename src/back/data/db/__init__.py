from cassandra.auth import PlainTextAuthProvider
import ssl
import requests
from .config import USERNAME, PASSWORD, CONTACT_POINT, PORT
from cassandra.cqlengine import connection, management
from .models import User
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
    auth_provider=cassandra.auth.PlainTextAuthProvider(username=USERNAME, password=PASSWORD),
    ssl_options={"ca_certs": requests.utils.DEFAULT_CA_BUNDLE_PATH, "ssl_version": ssl.PROTOCOL_TLSv1_2},
).connect()

try:
    session.set_keyspace('presidents')
except cassandra.InvalidRequest:  # if keyspace does not exist
    # TODO: these settings are currently ignored
    # https://docs.microsoft.com/en-us/azure/cosmos-db/cassandra-support#keyspace-and-table-options
    management.create_keyspace_network_topology(
        name="presidents", dc_replication_map={"datacenter": 1}
    )
    session.set_keyspace('presidents')

connection.set_session(session)

management.sync_table(User)

if __name__ == '__main__':
    aiosession(session)
    

# g = "6e4cec52-e932-422b-8a33-d852eb98cdee"
# u = "fe2f62b9-1340-4db5-a51e-fd24f1b44aaa"


# async def test():
#     await GameClicks.objects(game_id=g, user_id=u, action="1").async_update(
#         timestamps__append=[datetime.utcnow()]
#     )


# asyncio.run(test())
