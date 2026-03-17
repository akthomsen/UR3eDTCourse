import numpy as np
import time
import logging
import math
import threading
from models.robot_model import RobotModel
import communication.protocol as protocol
from communication.rabbitmq import Rabbitmq, MODEL_ROUTING_KEY_STATE, ROUTING_KEY_CTRL, RobotArmStateKeys, CtrlMsgFields, CtrlMsgKeys
from communication.factory import RabbitMQFactory
from startup.utils.logging_config import config_logging

class SimulationService:
    def __init__(self, start_time: float = 0.0, step_size: float = 0.01):
        self.robot_model = RobotModel(start_time=start_time, step_size=step_size)
        self.consumer: Rabbitmq = RabbitMQFactory.create_rabbitmq()
        self.publisher: Rabbitmq = RabbitMQFactory.create_rabbitmq()
        self.time = start_time
        self.step_size = step_size

        self._l = logging.getLogger("SimulationService")
    
    def cleanup(self):
        self.consumer.close()
        self.publisher.close()

    def upload_state(self):
        self._l.info("Uploading state to RabbitMQ.")
        data = {
            RobotArmStateKeys.ROBOT_MODE: self.robot_model.state,
            RobotArmStateKeys.Q_ACTUAL: self.robot_model.get_q_current().tolist(),
            RobotArmStateKeys.QD_ACTUAL: self.robot_model.get_qd_current().tolist(),
            RobotArmStateKeys.Q_TARGET: self.robot_model.q_end.tolist(),
            RobotArmStateKeys.TIMESTAMP: self.time,
            RobotArmStateKeys.JOINT_MAX_SPEED: self.robot_model.max_velocity,
            RobotArmStateKeys.JOINT_MAX_ACCELERATION: self.robot_model.max_acceleration,
            RobotArmStateKeys.TCP_POSE: self.robot_model.get_current_tcp_pose().tolist()
        }
        self.publisher.send_message(routing_key=MODEL_ROUTING_KEY_STATE, message=data)
        
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
        self.publisher.connect_to_server()
        self.consumer.connect_to_server()
        self.consumer.subscribe(routing_key=ROUTING_KEY_CTRL,
                                on_message_callback=self.read_control_message)

if __name__ == "__main__":
    from startup.utils.config import load_config_w_setuptools; c=load_config_w_setuptools('startup.conf');
    import os
    # Configure logging
    log_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "simulation_service.log")
    config_logging(filename=log_file, level=logging.INFO)

    logger = logging.getLogger("simulation_service")
    sim_service = SimulationService(time.time(), c.get("digital_twin.robot_model.step_size", 0.01))
    #setup model
    publish_period = c.get("digital_twin.robot_model.publish_period", 0.05)

    sim_service.setup()

    stop_event = threading.Event()

    def sim_loop():
        last_publish_time = time.time()
        while not stop_event.is_set():
            if time.time() - sim_service.time >= sim_service.step_size:
                sim_service.step_simulation()

            if time.time() - last_publish_time >= publish_period:
                sim_service.upload_state()
                last_publish_time = time.time()

            time.sleep(0.001)

    sim_thread = threading.Thread(target=sim_loop, daemon=True)
    sim_thread.start()

    try:
        sim_service.consumer.start_consuming()
    except KeyboardInterrupt:
        sim_service._l.info("Simulation stopped by user.")
    finally:
        stop_event.set()
        sim_service.cleanup()

#make a startup script