from communication import protocol
from communication.rabbitmq import Rabbitmq
from datetime import datetime, timezone
from random import random
from DTsolution.models.kinematic_model import KinematicModel

def connect_to_rabbitmq():
    try:
        rmq = Rabbitmq(
            ip="rabbitmq-server",
            port=5672,
            username="ur3e",
            password="ur3e",
            vhost="/",
            exchange="UR3E_AMQP",
            type="topic",
        )
        rmq.connect_to_server()
        print("✓ Connected to RabbitMQ successfully")
        return rmq
    except Exception as e:
        print(f"✗ Failed to connect to RabbitMQ: {e}")
        print("\nMake sure RabbitMQ is running. You can start it with:")
        print("  python -m startup.start_docker_rabbitmq")
        raise e # Throw error if server was not connected to


def subscribe_to_ctrl_signals(rmq):
    def on_message_received(ch, method, properties, body):
        try:
            print("✓ State:")
            print(body)
            # TODO: Do something
        except Exception as e:
            print(f"✗ Failed to decode the message: {e}")

    rmq.subscribe(
        routing_key=protocol.ROUTING_KEY_CTRL,
        on_message_callback=on_message_received,
    )


if __name__ == "__main__":
    # Connect to db and rabbitmq
    rmq = connect_to_rabbitmq()

    # Listen for PT state
    subscribe_to_ctrl_signals(rmq)
    rmq.start_consuming()