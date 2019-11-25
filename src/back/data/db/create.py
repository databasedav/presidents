from cassandra.auth import PlainTextAuthProvider
from ssl import PROTOCOL_TLSv1_2
from requests.utils import DEFAULT_CA_BUNDLE_PATH
import config as cfg
from cassandra.cqlengine import connection, management
from models import GameClicks
from uuid import uuid4
from time import time
import asyncio
from datetime import datetime
from cassandra.cluster import Cluster
from aiocassandra import aiosession


ssl_opts = {
    "ca_certs": DEFAULT_CA_BUNDLE_PATH,
    "ssl_version": PROTOCOL_TLSv1_2,
}

# TODO: see azure cassandra python quickstart guide
if "certpath" in cfg.config:
    ssl_opts["ca_certs"] = cfg.config["certpath"]

auth_provider = PlainTextAuthProvider(
    username=cfg.config["username"], password=cfg.config["password"]
)

session = Cluster(
    contact_points=[cfg.config["contactPoint"]],
    port=cfg.config["port"],
    auth_provider=auth_provider,
    ssl_options=ssl_opts,
).connect(keyspace="presidents")

connection.register_connection(
    name="cluster1", session=aiosession(session), default=True
)

management.create_keyspace_network_topology(
    name="presidents", dc_replication_map={"datacenter": 1}
)
management.sync_table(GameClicks)

# g = "6e4cec52-e932-422b-8a33-d852eb98cdee"
# u = "fe2f62b9-1340-4db5-a51e-fd24f1b44aaa"


# async def test():
#     await GameClicks.objects(game_id=g, user_id=u, action="1").async_update(
#         timestamps__append=[datetime.utcnow()]
#     )


# asyncio.run(test())
