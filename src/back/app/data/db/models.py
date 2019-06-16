from cassandra.models import Model
from cassandra.cqlengine import columns

columns.DateTime.truncate_microseconds = False

class GameClicks(Model):
    __table_name__ = 'game_clicks'
    __keyspace__ = 'presidents'
    game_id = columns.Text(primary_key=True, partition_key=True, required=True)
    user_id = columns.Text(primary_key=True, partition_key=True, required=True)
    action = columns.Text(primary_key=True, required=True, clustering_order='ASC')
    timestamps = columns.List(value_type=columns.DateTime, required=True)


