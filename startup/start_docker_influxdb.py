import requests

from startup.utils.config import resource_file_path_w_setuptools
from startup.utils.docker_service_starter import kill_container, start

containerName = "influxdb-server"


def start_docker_influxdb():
    logFileName = "logs/influxdb.log"
    dockerComposeDirectoryPath = resource_file_path_w_setuptools("communication/installation/influxdb")
    sleepTimeBetweenAttempts = 1
    maxAttempts = 10

    def test_connection_function():
        try:
            r = requests.get("http://localhost:8086/api/overview")
            if r.status_code == 200:
                print("Influxdb ready:\n " + r.text)
                return True
        except requests.exceptions.ConnectionError as x:
            # print("RabbitMQ not ready - Exception: " + x.__class__.__name__)
            pass
        return False

    kill_container(containerName)
    start(logFileName,
             dockerComposeDirectoryPath,
             test_connection_function, sleepTimeBetweenAttempts, maxAttempts)


def stop_docker_influxdb():
    kill_container(containerName)


if __name__ == '__main__':
    start_docker_influxdb()
