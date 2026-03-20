import numpy as np
import time
from datetime import datetime, timezone
import logging
import math
import threading
from models.robot_model import RobotModel
from communication.rabbitmq import Rabbitmq, ROUTING_KEY_MODEL_STATE, ROUTING_KEY_CTRL, ROUTING_KEY_RECORDER, RobotArmStateKeys, CtrlMsgFields, CtrlMsgKeys
from communication.factory import RabbitMQFactory
from startup.utils.config import load_config_w_setuptools; c=load_config_w_setuptools('startup.conf');
from startup.utils.logging_config import create_service_logger

class SimulationService:
    def __init__(self, start_time: float = 0.0):
        self.step_size = c.get("digital_twin.robot_model.step_size", 0.01)
        self.publish_period = c.get("digital_twin.robot_model.publish_period", 0.05)
        
        self.robot_model = RobotModel(step_size=self.step_size)
        self.consumer: Rabbitmq = RabbitMQFactory.create_rabbitmq()
        self.publisher: Rabbitmq = RabbitMQFactory.create_rabbitmq()
        self.time = start_time
        
        self._l = create_service_logger("simulation_service")
    
    def cleanup(self):
        self.consumer.close()
        self.publisher.close()

    def upload_state(self):
        self._l.debug("Uploading state to RabbitMQ.")
        # InfluxDB expects the timestamp to be either a datetime (tz-aware) or integer nanoseconds.
        # Use an RFC3339-aware timestamp so it can be parsed by the InfluxDB client.
        timestamp = datetime.fromtimestamp(self.time, timezone.utc).isoformat()

        fields = {
            RobotArmStateKeys.ROBOT_MODE: self.robot_model.state,
            RobotArmStateKeys.JOINT_MAX_SPEED: self.robot_model.max_velocity,
            RobotArmStateKeys.JOINT_MAX_ACCELERATION: self.robot_model.max_acceleration,
        }

        # Expand list-valued signals into individual numeric fields for InfluxDB
        # (InfluxDB field values must be scalar, not dict/list).
        fields.update(unroll_list(RobotArmStateKeys.Q_ACTUAL, self.robot_model.get_q_current().tolist()))
        fields.update(unroll_list(RobotArmStateKeys.QD_ACTUAL, self.robot_model.get_qd_current().tolist()))
        fields.update(unroll_list(RobotArmStateKeys.Q_TARGET, self.robot_model.get_q_end().tolist()))
        fields.update(unroll_list(RobotArmStateKeys.TCP_POSE, self.robot_model.get_tcp_pose_current().t.tolist()))

        rdata = {
            "measurement": "simulation_state",
            "time": timestamp,
            "tags": {
                "source": "simulator_service"
            },
            "fields": fields,
        }
        
        mdata = {
            RobotArmStateKeys.ROBOT_MODE: self.robot_model.state,
            RobotArmStateKeys.Q_ACTUAL: self.robot_model.get_q_current().tolist(),
            RobotArmStateKeys.QD_ACTUAL: self.robot_model.get_qd_current().tolist(),
            RobotArmStateKeys.Q_TARGET: self.robot_model.q_end.tolist(),
            RobotArmStateKeys.TIMESTAMP: timestamp,
            RobotArmStateKeys.JOINT_MAX_SPEED: self.robot_model.max_velocity,
            RobotArmStateKeys.JOINT_MAX_ACCELERATION: self.robot_model.max_acceleration,
            RobotArmStateKeys.TCP_POSE: self.robot_model.get_tcp_pose_current().t.tolist()
            }
        self.publisher.send_message("robotarm.recorder.arm_state", rdata)
        self.publisher.send_message(ROUTING_KEY_MODEL_STATE, mdata)
        
        
    def load_program(self, q_end: np.ndarray, max_velocity: float, acceleration: float) -> None:
        # Set the values in the robot model
        self.robot_model.load_program(q_end, max_velocity, acceleration)

    def read_control_message(self, ch, method, properties, message: dict):
        self._l.info(f"Received control message: {message}")
        msg_type = message.get(CtrlMsgKeys.TYPE)
        
        if msg_type == CtrlMsgFields.LOAD_PROGRAM:
            q_end = np.array(message.get(CtrlMsgKeys.JOINT_POSITIONS, [[0, 0, 0, 0, 0, 0]])[0]) # Default to 6 zeros if not provided
            max_velocity = math.radians(message.get(CtrlMsgKeys.MAX_VELOCITY, 0))
            acceleration = math.radians(message.get(CtrlMsgKeys.ACCELERATION, 0))
            self.load_program(q_end, max_velocity, acceleration)
        elif msg_type == CtrlMsgFields.PLAY:
            self.robot_model.play()
        elif msg_type == CtrlMsgFields.PAUSE:
            self.robot_model.pause()
        elif msg_type == CtrlMsgFields.STOP:
            self.robot_model.stop()
        else:
            self._l.warning(f"Unknown control message type: {msg_type}")

    def step_simulation(self):
        self.time += self.step_size
        self.robot_model.step(self.time)
    
    def setup(self):
        print(c.get("digital_twin.robot_model.initial_q"))
        self.robot_model.set_q_current(np.array(c.get("digital_twin.robot_model.initial_q", [0.0,0.0,0.0,0.0,0.0,0.0])))
        self.publisher.connect_to_server()
        self.consumer.connect_to_server()
        self.consumer.subscribe(routing_key=ROUTING_KEY_CTRL,
                                on_message_callback=self.read_control_message)
    
    def start_serving(self):
        stop_event = threading.Event()

        def _sim_loop():
            last_publish_time = time.time()
            while not stop_event.is_set():
                curr_time = time.time()
                if curr_time - self.time >= self.step_size:
                    self.step_simulation()

                if curr_time - last_publish_time >= self.publish_period:
                    self.upload_state()
                    last_publish_time = curr_time

                time.sleep(0.001)

        sim_thread = threading.Thread(target=_sim_loop, daemon=True)
        sim_thread.start()

        try:
            self.consumer.start_consuming()
        except KeyboardInterrupt:
            self._l.info("Simulation stopped by user.")
        finally:
            stop_event.set()
            self.cleanup()

def unroll_list(key_prefix, values):
    return {
        f"{key_prefix}_{i}": v
        for i, v in enumerate(values)
    }
