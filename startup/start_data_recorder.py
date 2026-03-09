import requests

from startup.utils.config import resource_file_path_w_setuptools
from startup.utils.docker_service_starter import kill_container, start

containerName = "data_recorder"


def start_data_recorder():
    logFileName = "logs/data_recorder.log"
    dockerComposeDirectoryPath = resource_file_path_w_setuptools("DTsolution/DTservices/data_recorder")
    sleepTimeBetweenAttempts = 1
    maxAttempts = 10

    def test_connection_function():
        return True

    kill_container(containerName)
    start(logFileName,
             dockerComposeDirectoryPath,
             test_connection_function, sleepTimeBetweenAttempts, maxAttempts)


def stop_data_recorder():
    kill_container(containerName)


if __name__ == '__main__':
    start_data_recorder()
