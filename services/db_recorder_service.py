from influxdb_client.client.influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from communication.protocol import ROUTING_KEY_RECORDER
from communication.factory import RabbitMQFactory
from startup.utils.logging_config import create_service_logger
import threading

class DBRecorderService:
    def __init__(self):
        self.write_api = None
        self.influx_db_org = None
        self.influxdb_bucket = None
        self.rabbitmq = None
        self._l = create_service_logger("db_recorder_service")

    def record_message(self, ch, method, properties, body_json):
        self._l.debug("New record msg:")
        self._l.debug(body_json)
        try:
            if(self.write_api != None and self.influx_db_org != None and self.influxdb_bucket != None):
                self.write_api.write(self.influxdb_bucket, self.influx_db_org, body_json)
        except Exception as e:
            self._l.warning("Failed to write to InfluxDB")
            self._l.debug("",exc_info=e)
            return

    def setup(self, influxdb_config):
        self._l.info("InfluxDBRecorder setup with config ", influxdb_config)
        self.rabbitmq = RabbitMQFactory.create_rabbitmq()
        self.rabbitmq.connect_to_server()

        client = InfluxDBClient(**influxdb_config)
        write_api = client.write_api(write_options=SYNCHRONOUS)
        self.write_api = write_api
        self.influx_db_org = influxdb_config["org"]
        self.influxdb_bucket = influxdb_config["bucket"]

        self.rabbitmq.subscribe(routing_key=ROUTING_KEY_RECORDER,
                        on_message_callback=self.record_message)

    def start_recording(self):
        if self.rabbitmq == None:
            return
        try:
            def run():
                if self.rabbitmq == None:
                    return
                self.rabbitmq.start_consuming()

            self.thread = threading.Thread(target=run, daemon=False)
            self.thread.start()
        except KeyboardInterrupt:
            self.rabbitmq.close()