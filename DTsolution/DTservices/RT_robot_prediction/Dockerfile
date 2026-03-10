FROM python:3.11

WORKDIR /app

ENV POETRY_VIRTUALENVS_CREATE=false

RUN pip install poetry
COPY pyproject.toml .

COPY startup/ startup/
COPY communication/__init__.py communication/
COPY communication/rabbitmq.py communication/
COPY communication/protocol.py communication/
COPY communication/utils communication/
COPY communication/connect.yml .
RUN touch README.md

RUN poetry install

COPY DTsolution/models DTsolution/models
COPY DTsolution/utils DTsolution/utils
COPY DTsolution/DTservices/RT_robot_prediction .


CMD ["python", "-u", "RT_robot_prediction.py"]
