from confluent_kafka import Producer
from cassandra.cluster import Cluster
from cassandra import query
from cassandra.policies import DCAwareRoundRobinPolicy
from cassandra.cqlengine import connection
from cassandra.cqlengine import management
from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model
import pandas as pd
import datetime
import numpy as np
import faust
import os


CASSANDRA_CONTACT_POINTS = ['172.17.0.2']
CASSANDRA_KEYSPACE = 'presidents'
CASSANDRA_CLUSTER_NAME = 'cluster1'

cluster = Cluster(CASSANDRA_CONTACT_POINTS)
session = cluster.connect()
connection.register_connection(CASSANDRA_CLUSTER_NAME, session=session, default=True)

os.environ['CQLENG_ALLOW_SCHEMA_MANAGEMENT'] = '1'

management.drop_keyspace(CASSANDRA_KEYSPACE)
management.create_keyspace_simple(name=CASSANDRA_KEYSPACE, replication_factor=3)

columns.DateTime.truncate_microseconds = False


class GameClicks(Model):
    __table_name__ = 'game_clicks'
    __keyspace__ = CASSANDRA_KEYSPACE
    game_id = columns.Text(primary_key=True, partition_key=True, required=True)
    username = columns.Text(primary_key=True, partition_key=True, required=True)
    action = columns.Text(primary_key=True, required=True, clustering_order='ASC')
    timestamps = columns.List(columns.DateTime, required=True)


management.drop_table
management.sync_table(GameClicks)
