"""
This module starts the simulation service foud in ../services/simulation_service.py in a new process.
"""
import os
import threading
import time
from services.simulation_service import SimulationService
import logging
from startup.utils.logging_config import config_logging

# Configure logging
log_dir = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "simulation_service.log")
config_logging(filename=log_file, level=logging.INFO)

logger = logging.getLogger("simulation_service")

def start_sim_service(ok_queue=None):
    sim_service = SimulationService(time.time())
  
    sim_service.setup()
    if ok_queue is not None:
        ok_queue.put("OK")

    sim_service.start_serving()
    
