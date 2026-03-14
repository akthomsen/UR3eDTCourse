from services.simulation_service import UR3eService
import numpy as np
import roboticstoolbox as rtb
import time
from startup.start_docker_rabbitmq import start_rabbitmq
import communication.factory as factory
from communication.protocol import ROUTING_KEY_STATE
import threading

# Description: Tests that we can get state messages from the controller and that they can be sent and received over rabbitmq.

pi = np.pi
# Maybe use later
# ur3e_service.set_fault(15, "stuck_joint") # Example fault injection after 15 steps

start_rabbitmq() # Start the rabbitmq server (remember to turn on docker first)

fac = factory.RabbitMQFactory()
print("Creating cli")
client = fac.create_rabbitmq()
print("Creating sub")
subscriber = fac.create_rabbitmq()

# define a callback function to handle received messages
def on_message_received(ch, method, properties, body):
    try:
        print("✓ State:")
        print(body)
    except Exception as e:
        print(f"✗ Failed to decode the message: {e}")


def run_subscriber():
    print("Subscriber connect to server")
    subscriber.connect_to_server()
    print("subscriber subscribe")
    subscriber.subscribe(ROUTING_KEY_STATE, on_message_callback=on_message_received)
    print("Subscriber start consuming")
    subscriber.start_consuming()

threading.Thread(
    target=run_subscriber,
    daemon=True
).start()

ur3e_service = UR3eService()

q_end = [0.0, -pi/2, pi/2, -pi/2, -pi/2, 0.0] # From exercise class
max_velocity = 60 # deg/s
acceleration = 80 # deg/s²

ur3e_service.load_program(q_end, max_velocity, acceleration)
ur3e_service.play()
 