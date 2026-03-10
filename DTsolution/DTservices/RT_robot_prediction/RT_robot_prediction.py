from pathlib import Path
import time

from utils.utils import load_config
from communication import protocol
from communication.rabbitmq import Rabbitmq
from DTsolution.models.kinematic_model import KinematicModel
import threading

model_lock = threading.Lock()

def inject_ctrl_msg_to_model(model : KinematicModel, body : dict):
    with model_lock:
        if body["type"] == "load_program":
            model.fmi2SetCommandedJointAngles(body["joint_positions"][0])
        elif body["type"] == "play":
            model.fmi2StartMovement()
    

def run_simulation(model : KinematicModel, dt=0.10):
    with model_lock:
        i = 0
        while True:
            current_time = i * dt
            model.fmi2DoStep(current_time, dt)
            time.sleep(dt)
            i += 1

def main():
    config = load_config(Path("connect.yml"))

    with Rabbitmq(**config) as rabbit_mq:
        model = KinematicModel(movement_fidelity=1000)

        rabbit_mq.subscribe(protocol.ROUTING_KEY_CTRL, lambda *_, body_json :
                            inject_ctrl_msg_to_model(model, body_json))
        
        rmq_thread = threading.Thread(target=rabbit_mq.start_consuming, daemon=True)
        rmq_thread.start()

        run_simulation(model)

if __name__ == "__main__":
    main()