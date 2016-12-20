# -*- coding: utf-8 -*-

"""Command line interface for CosmicPi Server."""

import os
import sys
import time

import click
import pika


@click.command()
@click.option('--broker-url', envvar='BROKER_URL')
@click.option('--sqlalchemy-uri', envvar='SQLALCHEMY_URI')
def main(broker_url, sqlalchemy_uri):
    """Console script for cosmicpi_server"""
    connection = pika.BlockingConnection(pika.URLParameters(broker_url))
    channel = connection.channel()
    result = channel.queue_declare(exclusive=True)
    queue_name = result.method.queue
    channel.queue_bind(exchange='events', queue=queue_name)

    def callback(channel, method, properties, body):
        click.echo(body)

    channel.basic_consume(callback, queue=queue_name, no_ack=True)
    channel.start_consuming()


if __name__ == "__main__":
    main()
