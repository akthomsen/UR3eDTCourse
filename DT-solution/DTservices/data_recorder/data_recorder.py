from communication import protocol
from communication.rabbitmq import Rabbitmq
from datetime import datetime, timezone
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from random import random

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

def connect_to_influxdb(token : str = "g_q1cFD4Q3eSe-cvFdRqetoQEsoi2_Socof3rIvspMHQEGmCPcboL4kQVuuGoJmKchWqtEsoNRg4U6P6oL0Xlw=="):
    # Replace these with your InfluxDB token, organization, and bucket
    org = "ur3e"
    bucket = "ur3e"

    # Initialize the client
    client = InfluxDBClient(url="http://influxdb-server:8086", token=token, org=org)
    write_api = client.write_api(write_options=SYNCHRONOUS)   
    return write_api

def write_datapoint_to_influxdb(write_api, dp):
    # Replace these with your InfluxDB token, organization, and bucket
    org = "ur3e"
    bucket = "ur3e"

    # convert flatten lists in dp
    dp_flat = {
        "robot_mode": dp["robot_mode"],
        "joint_max_speed": dp["joint_max_speed"],
        "joint_max_acceleration": dp["joint_max_acceleration"],
        "timestamp": dp["timestamp"]
    }

    def flatten_array_and_add(dp: dict, dp_flat: dict, field: str):
        for i, val in enumerate(dp[field]):
            dp_flat[f"{field}_joint_{i}"] = val
    
    flatten_array_and_add(dp, dp_flat, "q_actual")
    flatten_array_and_add(dp, dp_flat, "qd_actual")
    flatten_array_and_add(dp, dp_flat, "q_target")
    flatten_array_and_add(dp, dp_flat, "tcp_pose")

    # Create a point with a measurement, tag, field, and a timestamp
    point = Point("sensor_data") \
        .tag("source", "data_recorder_service") \
        .time(datetime.now(timezone.utc)) 

    for key, value in dp_flat.items():
        point = point.field(key, value)

    # Write the point to the bucket
    try:
        write_api.write(bucket="ur3e", org="ur3e", record=point)
        print("Data point written successfully.")
    except Exception as e:
        print(f"FAILED to write to InfluxDB: {e}")

def subscribe_to_pt_state(rmq, write_api):
    def on_message_received(ch, method, properties, body):
        try:
            print("✓ State:")
            print(body)
            write_datapoint_to_influxdb(write_api, body) # Write the point to the db
        except Exception as e:
            print(f"✗ Failed to decode the message: {e}")

    rmq.subscribe(
        routing_key=protocol.ROUTING_KEY_STATE,
        on_message_callback=on_message_received,
    )

def write_ctrl_msg_to_influxdb(write_api, ctrl_msg):
    org = "ur3e"
    bucket = "ur3e"

    # Only save messages of type play and load_program
    if ctrl_msg["type"] not in ["load_program", "play"]:
        return

    point = Point("ctrl_msgs") \
        .tag("source", "data_recorder_service") \
        .tag("msg_type", ctrl_msg["type"]) \
        .field("msg_type", ctrl_msg["type"]) \
        .time(datetime.now(timezone.utc), WritePrecision.NS) 


    def flatten_array_and_add(dp: dict, dp_flat: dict, field: str):
        for i, val in enumerate(dp[field]):
            dp_flat[f"{field}_joint_{i}"] = val

    if ctrl_msg["type"] == "load_program":
        fields = {
            "max_velocity": ctrl_msg["max_velocity"],
            "acceleration": ctrl_msg["acceleration"]
        }

        ctrl_msg["joint_positions"] = ctrl_msg["joint_positions"][0] # For some reason it is nested

        flatten_array_and_add(ctrl_msg, fields, "joint_positions")

        for key, value in fields.items():
            point = point.field(key, value)

    # Write the point to the bucket
    try:
        write_api.write(bucket="ur3e", org="ur3e", record=point)
        print("Control message written successfully.")
    except Exception as e:
        print(f"FAILED to write to InfluxDB: {e}")


def subscribe_to_ctrl_signals(rmq, write_api):
    def on_message_received(ch, method, properties, body):
        try:
            print("✓ State:")
            print(body)
            write_ctrl_msg_to_influxdb(write_api, body) # Write the point to the db
        except Exception as e:
            print(f"✗ Failed to decode the message: {e}")

    rmq.subscribe(
        routing_key=protocol.ROUTING_KEY_CTRL,
        on_message_callback=on_message_received,
    )


if __name__ == "__main__":
    # Connect to db and rabbitmq
    rmq = connect_to_rabbitmq()
    write_api = connect_to_influxdb()

    # Listen for PT state
    subscribe_to_pt_state(rmq, write_api)
    subscribe_to_ctrl_signals(rmq, write_api)
    rmq.start_consuming()