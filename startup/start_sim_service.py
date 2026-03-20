"""
This module starts the simulation service foud in ../services/simulation_service.py in a new process.
"""
import os
import time
from services.simulation_service import SimulationService
from startup.utils.logging_config import create_service_logger

def start_sim_service(ok_queue=None):
    sim_service = SimulationService(time.time())
  
    sim_service.setup()
    if ok_queue is not None:
        ok_queue.put("OK")

    sim_service.start_serving()
    
