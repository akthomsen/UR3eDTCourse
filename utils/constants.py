from enum import Enum
import numpy as np

pi = np.pi
step_size = 0.05 # 0.05 seconds (default)

class State(Enum):
    IDLE = "Idle"
    RUNNING = "Running"
