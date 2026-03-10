from pathlib import Path
from datetime import datetime, timezone
from functools import partial
from typing import Callable, Any

from communication import protocol
from communication.rabbitmq import Rabbitmq
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS, WriteApi
from utils.utils import load_config

WriterFn = Callable[[Point], Any]
CallbackFn = Callable[[WriterFn, dict], None]


def flatten_array_and_add(dp: dict, dp_flat: dict, field: str):
    for i, val in enumerate(dp[field]):
        dp_flat[f"{field}_joint_{i}"] = val


def create_point(measurement: str, tags: dict | None = None) -> Point:
    point = Point(measurement).time(datetime.now(timezone.utc))
    if tags:
        for k, v in tags.items():
            point = point.tag(k, v)
    return point


def add_fields(point: Point, fields: dict) -> Point:
    for key, value in fields.items():
        point = point.field(key, value)
    return point


def safe_write(writer: WriterFn, point: Point, success_msg: str):
    try:
        writer(record=point)
        print(success_msg)
    except Exception as e:
        print(f"FAILED to write to InfluxDB: {e}")


def write_datapoint_to_influxdb(writer: WriterFn, dp: dict):
    dp_flat = {
        "robot_mode": dp["robot_mode"],
        "joint_max_speed": dp["joint_max_speed"],
        "joint_max_acceleration": dp["joint_max_acceleration"],
        "timestamp": dp["timestamp"]
    }

    for field in ["q_actual", "qd_actual", "q_target", "tcp_pose"]:
        flatten_array_and_add(dp, dp_flat, field)

    point = create_point("sensor_data", tags={"source": "data_recorder_service"})
    point = add_fields(point, dp_flat)

    safe_write(writer, point, "Data point written successfully.")


def write_ctrl_msg_to_influxdb(writer: WriterFn, ctrl_msg: dict):
    if ctrl_msg["type"] not in ["load_program", "play"]:
        return

    point = create_point("ctrl_msgs", tags={
        "source": "data_recorder_service",
        "msg_type": ctrl_msg["type"]
    }).field("msg_type", ctrl_msg["type"])

    if ctrl_msg["type"] == "load_program":
        fields = {
            "max_velocity": ctrl_msg["max_velocity"],
            "acceleration": ctrl_msg["acceleration"]
        }
        ctrl_msg["joint_positions"] = ctrl_msg["joint_positions"][0]
        flatten_array_and_add(ctrl_msg, fields, "joint_positions")
        point = add_fields(point, fields)

    safe_write(writer, point, "Control message written successfully.")

def main():
    connect_config = load_config(Path("connect.yml"))
    influx_config = load_config(Path("influx.yml"))

    with Rabbitmq(**connect_config) as rabbit_mq, InfluxDBClient(**influx_config) as client:
        write_api: WriteApi = client.write_api(write_options=SYNCHRONOUS)
        writer = partial(write_api.write, bucket=influx_config["bucket"], org=influx_config["org"])

        subscriptions = {
            protocol.ROUTING_KEY_STATE: write_datapoint_to_influxdb,
            protocol.ROUTING_KEY_CTRL: write_ctrl_msg_to_influxdb,
        }

        for routing_key, func in subscriptions.items():
            rabbit_mq.subscribe(routing_key, lambda *_, body_json, f=func: f(writer, body_json))

        rabbit_mq.start_consuming()


if __name__ == "__main__":
    main()