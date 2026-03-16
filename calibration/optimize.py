import numpy as np
from scipy.optimize import least_squares
from scipy.interpolate import interp1d
from models.model import MotionModel

def compute_residuals(params, model, scenario, sim_dt=0.002, use_delay=False):
    pass
