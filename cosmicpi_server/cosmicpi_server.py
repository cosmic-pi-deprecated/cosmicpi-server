# -*- coding: utf-8 -*-

"""Implementation of a storage and queue processor."""

import pika
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

metadata = sa.MetaData()

events_table = sa.Table('events', metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('data', JSONB),
    sa.Column('created', sa.DateTime, server_default=sa.func.current_timestamp()),
)


class Storage(object):
    """Store events in the database."""

    def __init__(self, uri):
        """Initialize engine."""
        self.engine = sa.create_engine(uri)
        self.insert = events_table.insert()

    def __enter__(self):
        self.connection = self.engine.connect()
        metadata.create_all(self.engine)
        return self

    def __exit__(self, type, value, traceback):
        self.connection.close()

    def __call__(self, data):
        self.connection.execute(self.insert, data=data)
        self.connection.commit()


class EventsQueue(object):
    """Events queue."""

    def __init__(self, broker_url):
        """Connect to the broker."""
        connection = pika.BlockingConnection(pika.URLParameters(broker_url))
        self.channel = connection.channel()
        result = self.channel.queue_declare(exclusive=True)
        self.queue_name = result.method.queue
        self.channel.queue_bind(exchange='events', queue=self.queue_name)


    def __call__(self, callback):
        """Start consuming events."""
        def _callback(channel, method, properties, body):
            callback(body)

        self.channel.basic_consume(
            _callback, queue=self.queue_name, no_ack=True
        )
        self.channel.start_consuming()
