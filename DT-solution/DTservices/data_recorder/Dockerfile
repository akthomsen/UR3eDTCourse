# Use Python base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app
COPY ./DT-solution/DTservices/data_recorder /app/
RUN  pip install pika
# RUN pip install poetry
# COPY ./pyproject.toml /app/
# RUN poetry install
COPY ./communication/ /app/communication/

# Command to run a script from the volume (this script will be provided by the volume)
CMD ["python", "/app/data_recorder.py"]
