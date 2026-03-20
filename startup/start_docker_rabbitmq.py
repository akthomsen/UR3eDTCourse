import requests

from startup.utils.config import resource_file_path_w_setuptools
from startup.utils.docker_service_starter import kill_container, start
from startup.utils.logging_config import LOG_DIR_PATH

containerName = "rabbitmq-server"

# To fix file name and function name overlap
def start_rabbitmq():
    start_docker_rabbitmq()


def start_docker_rabbitmq():
    logFileName = LOG_DIR_PATH + "rabbitmq.log"
    dockerComposeDirectoryPath = resource_file_path_w_setuptools("communication/installation")
    sleepTimeBetweenAttempts = 1
    maxAttempts = 10

    def test_connection_function():
        try:
            r = requests.get("http://localhost:15672/api/overview", auth=('ur3e', 'ur3e'))
            if r.status_code == 200:
                print("RabbitMQ ready:\n " + r.text)
                return True
        except requests.exceptions.ConnectionError as x:
            # print("RabbitMQ not ready - Exception: " + x.__class__.__name__)
            pass
        return False

    kill_container(containerName)
    start(logFileName,
             dockerComposeDirectoryPath,
             test_connection_function, sleepTimeBetweenAttempts, maxAttempts)


def stop_docker_rabbitmq():
    kill_container(containerName)


if __name__ == '__main__':
    start_docker_rabbitmq()
