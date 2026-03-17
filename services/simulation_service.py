import numpy as np
import math
import logging
from models.robot_model import RobotModel
import communication.protocol as protocol
from communication.rabbitmq import Rabbitmq, MODEL_ROUTING_KEY_STATE, ROUTING_KEY_CTRL, RobotArmStateKeys, CtrlMsgFields, CtrlMsgKeys
from communication.factory import RabbitMQFactory

class SimulationService:
    def __init__(self, start_time: float = 0.0, step_size: float = 0.01):
        self.robot_model = RobotModel(start_time=start_time, step_size=step_size)
        self.rabbitmq: Rabbitmq = RabbitMQFactory.create_rabbitmq()
        self.time = start_time
        self.step_size = step_size

        self._l = logging.getLogger("SimulationService")
    
    def cleanup(self):
        self.rabbitmq.close()

    def upload_state(self):
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
        self.rabbitmq.send_message(routing_key=MODEL_ROUTING_KEY_STATE, message=data)
        
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
        self.rabbitmq.connect_to_server()
        self.rabbitmq.subscribe(routing_key=ROUTING_KEY_CTRL,
                                on_message_callback=self.read_control_message)

if __name__ == "__main__":
    import time
    from startup.utils.config import load_config_w_setuptools; c=load_config_w_setuptools('startup.conf');
    sim_service = SimulationService(time.time(), c.get("step_size", 0.01))
    #setup model
    publish_period = c.get("publish_period", 0.05)

    try:
        sim_service.setup()
        #put this on another thread
        sim_service.rabbitmq.start_consuming()
        while True:
            if time.time() - sim_service.time >= sim_service.step_size:
                sim_service.step_simulation()
                sim_service.upload_state()
            if time.time() - sim_service.time >= publish_period:
                sim_service.upload_state()
    except KeyboardInterrupt:
        sim_service._l.info("Simulation stopped by user.")
    finally:
        sim_service.cleanup()

#make a startup script