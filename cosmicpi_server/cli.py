# -*- coding: utf-8 -*-

"""Command line interface for CosmicPi Server."""

from __future__ import absolute_import

import click

from .cosmicpi_server import EventsQueue, Storage


@click.command()
@click.option('--broker-url', envvar='BROKER_URL')
@click.option('--database-uri', envvar='DATABASE_URI')
def main(broker_url, database_uri):
    """Console script for cosmicpi_server"""
    processor = EventsQueue(broker_url)

    with Storage(database_uri) as storage:
        processor(storage)
