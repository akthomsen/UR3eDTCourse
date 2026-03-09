# Use Python base image
FROM python:3.11

# Set the working directory inside the container
WORKDIR /app
ENV POETRY_VIRTUALENVS_CREATE=false

# RUN  pip install pika influxdb-client roboticstoolbox-python
RUN pip install poetry
COPY ./pyproject.toml /app/
COPY ./README.md /app/
COPY ./startup/ /app/startup/
COPY ./communication/__init__.py /app/communication/
COPY ./communication/rabbitmq.py /app/communication/
COPY ./communication/protocol.py /app/communication/

RUN poetry install


COPY ./DTsolution/models /app/DTsolution/models
COPY ./DTsolution/DTservices/RT_robot_prediction /app/

# Command to run a script from the volume (this script will be provided by the volume)
CMD ["python", "-u", "/app/RT_robot_prediction.py"]
