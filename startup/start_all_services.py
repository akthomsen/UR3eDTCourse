from startup.utils.start_as_daemon import start_as_daemon
from startup.start_docker_rabbitmq import start_docker_rabbitmq

from startup.start_ur3e_mockup import start_robot_arm_mockup

if __name__ == "__main__":
    start_docker_rabbitmq()
    start_as_daemon(start_robot_arm_mockup)
