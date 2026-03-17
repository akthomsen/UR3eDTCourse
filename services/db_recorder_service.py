import json
from influxdb_client.client.influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from communication.rabbitmq import Rabbitmq
from communication.protocol import ROUTING_KEY_RECORDER
from communication.factory import RabbitMQFactory
from influxdb_client.client.write.point import Point
import threading

class DBRecorderService:
    def __init__(self):
        self.write_api = None
        self.influx_db_org = None
        self.influxdb_bucket = None
        self.rabbitmq = None

    def read_record_request(self, ch, method, properties, body_json):
        msg = json.loads(body_json)
                # --- STATE MESSAGE ---
        if "q_actual" in msg:
            self.write_state(msg)

        # --- UNKNOWN ---
        else:
            print("Unknown message format:", msg)

    def write_state(self, msg):
        robot_mode = msg["robot_mode"]
        q_actual = msg["q_actual"]
        qd_actual = msg["qd_actual"]
        q_target = msg["q_target"]
        timestamp = msg["timestamp"]
        joint_max_speed = msg["joint_max_speed"]
        joint_max_acceleration = msg["joint_max_acceleration"]
        tcp_pose = msg["tcp_pose"]

        point = Point("robotarm_state") \
            .field("robot_mode", robot_mode) \
            .field("q_actual_0", q_actual[0]) \
            .field("q_actual_1", q_actual[1]) \
            .field("q_actual_2", q_actual[2]) \
            .field("q_actual_3", q_actual[3]) \
            .field("q_actual_4", q_actual[4]) \
            .field("q_actual_5", q_actual[5]) \
            .field("qd_actual_0", qd_actual[0]) \
            .field("qd_actual_1", qd_actual[1]) \
            .field("qd_actual_2", qd_actual[2]) \
            .field("qd_actual_3", qd_actual[3]) \
            .field("qd_actual_4", qd_actual[4]) \
            .field("qd_actual_5", qd_actual[5]) \
            .field("q_target_0", q_target[0]) \
            .field("q_target_0", q_target[0]) \
            .field("q_target_1", q_target[1]) \
            .field("q_target_2", q_target[2]) \
            .field("q_target_3", q_target[3]) \
            .field("q_target_4", q_target[4]) \
            .field("q_target_5", q_target[5]) \
            .field("timestamp", timestamp) \
            .field("joint_max_speed", joint_max_speed) \
            .field("joint_max_acceleration", joint_max_acceleration) \
            .field("tcp_pose_x", tcp_pose[0]) \
            .field("tcp_pose_y", tcp_pose[1]) \
            .field("tcp_pose_z", tcp_pose[2])
                        
       
        self.write_api.write(self.influxdb_bucket, self.influx_db_org, point)

    def write_control(self, msg):
        raise NotImplementedError

    def setup(self, influxdb_config):
        self.rabbitmq = RabbitMQFactory.create_rabbitmq()
        self.rabbitmq.connect_to_server()

        client = InfluxDBClient(**influxdb_config)
        write_api = client.write_api(write_options=SYNCHRONOUS)
        self.write_api = write_api
        self.influx_db_org = influxdb_config["org"]
        self.influxdb_bucket = influxdb_config["bucket"]

        self.rabbitmq.subscribe(routing_key=ROUTING_KEY_RECORDER,
                        on_message_callback=self.read_record_request)

    def start_recording(self):
        try:
            def run():
                self.rabbitmq.start_consuming()

            self.thread = threading.Thread(target=run, daemon=True)
            self.thread.start()
        except KeyboardInterrupt:
            self.rabbitmq.close()