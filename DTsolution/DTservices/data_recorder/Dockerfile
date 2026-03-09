# Use Python base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

RUN  pip install pika influxdb-client

COPY ./communication/__init__.py /app/communication/
COPY ./communication/rabbitmq.py /app/communication/
COPY ./communication/protocol.py /app/communication/

COPY ./DTsolution/DTservices/data_recorder /app/
# RUN pip install poetry
# COPY ./pyproject.toml /app/
# RUN poetry install

# Command to run a script from the volume (this script will be provided by the volume)
CMD ["python", "-u", "/app/data_recorder.py"]
