from services.db_recorder_service import DBRecorderService
from utils.configuration import load_config
import os
import logging
from startup.utils.logging_config import config_logging

# Configure logging
log_dir = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "db_recorder_service.log")
config_logging(filename=log_file, level=logging.INFO)

logger = logging.getLogger("db_recorder_service")

def start_db_recorder_service(ok_queue=None):

    recorder = DBRecorderService()
    config = load_config("startup/startup.conf")
    recorder.setup(influxdb_config=config["influxdb"])

    if ok_queue is not None:
        ok_queue.put("OK")

    recorder.start_recording()

