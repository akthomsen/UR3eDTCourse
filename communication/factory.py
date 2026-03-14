import pika
import logging
import ssl as ssl_package
from .protocol import *
from .rabbitmq import *

class RabbitMQFactory:
    def __init__(self):
        pass

    def create_rabbitmq(self) -> Rabbitmq:
        rmq = Rabbitmq(
                ip="localhost",
                port=5672,
                username="ur3e",
                password="ur3e",
                vhost="/",
                exchange="UR3E_AMQP",
                type="topic"
            )

        return rmq
    