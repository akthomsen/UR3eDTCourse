from communication import protocol
from communication.rabbitmq import Rabbitmq

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

def subscribe_to_pt_state(rmq):
    def on_message_received(ch, method, properties, body):
        try:
            print("✓ State:")
            print(body)
        except Exception as e:
            print(f"✗ Failed to decode the message: {e}")

    rmq.subscribe(
        routing_key=protocol.ROUTING_KEY_STATE,
        on_message_callback=on_message_received,
    )


if __name__ == "__main__":
    rmq = connect_to_rabbitmq()
    subscribe_to_pt_state(rmq)
    rmq.start_consuming()
