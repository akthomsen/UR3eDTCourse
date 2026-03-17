from .protocol import *
from .rabbitmq import *

class RabbitMQFactory:
    
    @staticmethod
    def create_rabbitmq() -> Rabbitmq:
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
    