"""
This module starts the simulation service foud in ../services/simulation_service.py in a new process.
"""
import time
from services.simulation_service import SimulationService

def start_sim_service(ok_queue=None):
    sim_service = SimulationService(time.time())
  
    sim_service.setup()
    if ok_queue is not None:
        ok_queue.put("OK")

    sim_service.start_serving()
    
