""" This modul is for sending control msg to the robot with the target and constrains, 
then subscribes to the state topic to log the data and save it to a file when the scenario is done. 
"""

import numpy as np
from communication import protocol
from communication.rabbitmq import Rabbitmq
from data_logger.log_data import Logger



def send_control_message(rmq, msg):
    """Send a control message to the UR3e Mockup via RabbitMQ."""
    try:
        rmq.send_message(
            routing_key=protocol.ROUTING_KEY_CTRL,
            message=msg
        )
        print(f"✓ Control message: {msg} sent successfully")
    except Exception as e:
        print(f"✗ Failed to send control message: {e}")


def on_message_received(ch, method, properties, body, logger: Logger):
    try:
        logger.handle_received_step(body)
        logger.is_scenario_finished()
        print(f"✓ Status: {logger.scenario_status}")
        if logger.scenario_status == "finished":
            ch.stop_consuming()
    except Exception as e:
        print(f"✗ Failed to handle the message: {e}")



def main():

    # Initialize RabbitMQ connection (adjust parameters as needed)
    try:
        rmq = Rabbitmq(
            ip="localhost",
            port=5672,
            username="incubator",
            password="incubator", # noqa
            vhost="/",
            exchange="UR3E_AMQP",
            type="topic",
        )
        rmq.connect_to_server()
        print("✓ Connected to RabbitMQ successfully")


    except Exception as e:
        print(f"✗ Failed to connect to RabbitMQ: {e}")


    scenario_name = "example_scenario"
    logger = Logger(scenario_name)


    # Construct control message for loading a program
    #target = [0.06, 0.05, 0.04, 0.03, 0.02, 0.01]
    target = [np.pi/2, np.pi/2, -np.pi/2, np.pi/2, -np.pi/2, np.pi/2]

    vel = 60 # deg/s
    acc = 80 # deg/s^2


    msg = {
    protocol.CtrlMsgKeys.TYPE: protocol.CtrlMsgFields.LOAD_PROGRAM,
    protocol.CtrlMsgKeys.JOINT_POSITIONS: [target],
    protocol.CtrlMsgKeys.MAX_VELOCITY: vel,
    protocol.CtrlMsgKeys.ACCELERATION: acc,
}

    send_control_message(rmq, msg)

    play_msg = {
        protocol.CtrlMsgKeys.TYPE: protocol.CtrlMsgFields.PLAY,
    }
    send_control_message(rmq, play_msg)

    rmq.subscribe(
        routing_key=protocol.ROUTING_KEY_STATE,
        on_message_callback=lambda ch, method, properties, body: on_message_received(ch, method, properties, body, logger),
    )
    rmq.start_consuming()


    logger.save_data_to_file("from_0_to_90.csv", "./data")
    rmq.close()


if __name__ == "__main__":
    main()










