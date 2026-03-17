from services.db_recorder_service import DBRecorderService
from utils.configuration import load_config

def start_db_service(ok_queue=None):

    recorder = DBRecorderService()
    config = load_config("startup/startup.conf")
    recorder.setup(influxdb_config=config["influxdb"])

    if ok_queue is not None:
        ok_queue.put("OK")

    recorder.start_recording()

