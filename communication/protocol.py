import json

ENCODING = "ascii"

### ROUTING KEYS
ROUTING_KEY_STATE = "robotarm.pt.state"
MODEL_ROUTING_KEY_STATE = "robotarm.model.state"
ROUTING_KEY_CTRL = "robotarm.ctrl"

### MESSAGES
class CtrlMsgFields:
    """Types of control messages that can be sent to the robot arm."""

    LOAD_PROGRAM = "load_program"
    PLAY = "play"
    PAUSE = "pause"
    STOP = "stop"
    INJECT_FAULT = "inject_fault"


class CtrlMsgKeys:
    """Keys used in control messages sent to the robot arm."""

    TYPE = "type"
    JOINT_POSITIONS = "joint_positions"
    MAX_VELOCITY = "max_velocity"
    ACCELERATION = "acceleration"
    FAULT_TYPE = "fault_type"
    FAULT_VALUE = "fault_value"
    JOINTS = "joints"
    DURATION = "duration"


class FaultTypes:
    """Types of faults that can be injected into the robot arm."""

    STUCK_JOINT = "stuck_joint"
    WEAR = "wear"


class RobotArmStateKeys:
    """Keys used in state messages sent from the robot arm."""

    ROBOT_MODE = "robot_mode"
    Q_ACTUAL = "q_actual"
    QD_ACTUAL = "qd_actual"
    Q_TARGET = "q_target"
    TIMESTAMP = "timestamp"
    JOINT_MAX_SPEED = "joint_max_speed"
    JOINT_MAX_ACCELERATION = "joint_max_acceleration"
    TCP_POSE = "tcp_pose"


class RobotMode:
    """Possible modes of the robot arm (ROBOT_MODE)."""

    ROBOT_MODE_RUNNING = "Running"
    ROBOT_MODE_IDLE = "Idle"


def encode_json(object):
    return json.dumps(object).encode(ENCODING)


def decode_json(bytes):
    return json.loads(bytes.decode(ENCODING))
