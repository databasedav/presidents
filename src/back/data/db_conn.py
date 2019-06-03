# from confluent_kafka import Producer
from cassandra.cluster import Cluster
from cassandra import query
from cassandra.policies import DCAwareRoundRobinPolicy
from cassandra.cqlengine import connection
from cassandra.cqlengine import management
from cassandra.cqlengine import columns
from cassandra.cqlengine import models
import pandas as pd
import datetime
import numpy as np
import faust
import os


CASSANDRA_CONTACT_POINTS = ['127.0.0.1']
CASSANDRA_KEYSPACE = 'presidents'
CASSANDRA_CLUSTER_NAME = 'cluster1'

cluster = Cluster(CASSANDRA_CONTACT_POINTS)
session = cluster.connect()
connection.register_connection(CASSANDRA_CLUSTER_NAME, session=session, default=True)

os.environ['CQLENG_ALLOW_SCHEMA_MANAGEMENT'] = '1'

management.drop_keyspace(CASSANDRA_KEYSPACE)
management.create_keyspace_simple(name=CASSANDRA_KEYSPACE, replication_factor=3)

# management.drop_table('game_clicks')
management.sync_table(GameClicks)
