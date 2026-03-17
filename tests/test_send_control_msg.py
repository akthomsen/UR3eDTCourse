from communication.factory import RabbitMQFactory
from communication.protocol import ROUTING_KEY_CTRL, CtrlMsgKeys, CtrlMsgFields
import numpy as np

# Construct control message for loading a program
client = RabbitMQFactory.create_rabbitmq()
position = [0.0, -np.pi/2, np.pi/2, -np.pi/1, -np.pi/2, 0.0]
vel = 60 # deg/s
acc = 80 # deg/s²

msg = {
    CtrlMsgKeys.TYPE: CtrlMsgFields.LOAD_PROGRAM,
    CtrlMsgKeys.JOINT_POSITIONS: [position],
    CtrlMsgKeys.MAX_VELOCITY: vel,
    CtrlMsgKeys.ACCELERATION: acc,
}

# Create sender and that
print("Connecting client to rabbitmq")
client.connect_to_server()
print("Client sending message")
client.send_message(ROUTING_KEY_CTRL, msg)

msg = {
    CtrlMsgKeys.TYPE: CtrlMsgFields.PLAY,
    CtrlMsgKeys.JOINT_POSITIONS: [position],
    CtrlMsgKeys.MAX_VELOCITY: vel,
    CtrlMsgKeys.ACCELERATION: acc,
}
client.send_message(ROUTING_KEY_CTRL, msg)
print("script done")
