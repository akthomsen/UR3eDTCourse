from startup.utils.start_as_daemon import start_as_daemon
from startup.start_docker_rabbitmq import start_docker_rabbitmq
from startup.start_sim_service import start_sim_service
from startup.start_ur3e_mockup import start_robot_arm_mockup
from startup.start_db_recorder_service import start_db_recorder_service
from startup.start_docker_influxdb import start_docker_influxdb
from startup.utils.logging_config import setup_root_logging

if __name__ == "__main__":
    setup_root_logging("all_service_logs")
    start_docker_rabbitmq()
    start_docker_influxdb()
    start_as_daemon(start_robot_arm_mockup)
    start_as_daemon(start_db_recorder_service)
    start_as_daemon(start_sim_service)
