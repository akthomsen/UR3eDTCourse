from communication import protocol
from communication.rabbitmq import Rabbitmq
from datetime import datetime, timezone
from random import random
from DTsolution.models.kinematic_model import KinematicModel

# Needed for parallism
import threading

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


def inject_ctrl_msg_to_model(model : KinematicModel, body):
    if body["type"] == "load_program":
        model.fmi2SetCommandedJointAngles(body["joint_positions"][0])
    elif body["type"] == "play":
        model.fmi2StartMovement()
    

def subscribe_to_ctrl_signals(rmq, model : KinematicModel):
    def on_message_received(ch, method, properties, body):
        try:
            print("✓ State:")
            print(body)
            inject_ctrl_msg_to_model(model, body)
        except Exception as e:
            print(f"✗ Failed to decode the message: {e}")

    rmq.subscribe(
        routing_key=protocol.ROUTING_KEY_CTRL,
        on_message_callback=on_message_received,
    )

def run_simulation(model, dt=0.10):
    i = 0
    while True:
        current_time = i * dt
        model.fmi2DoStep(current_time, dt)
        angles = model.current_joint_angles
        time.sleep(dt)
        i += 1
    

if __name__ == "__main__":
    # Connect to db and rabbitmq
    rmq = connect_to_rabbitmq()

    # Instantiate kinematric model
    model = KinematicModel(movement_fidelity=1000)

    # Listen for PT state
    subscribe_to_ctrl_signals(rmq, model)

    # Start new thread for consuming ctrl messages
    rmq_thread = threading.Thread(target=rmq.start_consuming, daemon=True)
    rmq_thread.start()

    run_simulation(model)