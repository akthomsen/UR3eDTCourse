"""
This module starts the executable in '../ur3e_mockup/' folder named 'ur3e_mockup'.
"""

import subprocess
import os
import platform
import logging
from startup.utils.logging_config import config_logging

# Configure logging
log_dir = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "ur3e_mockup.log")
config_logging(filename=log_file, level=logging.INFO)

logger = logging.getLogger("start_ur3e_mockup")


def _get_executable_path(system, machine):
    """
    Detects the OS type and returns the path to the appropriate ur3e_mockup executable.

    Returns:
        str: Path to the platform-specific executable

    Raises:
        OSError: If the OS is not supported or executable not found
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ur3e_mockup_dir = os.path.join(current_dir, "../ur3e_mockup")
    executable_path = None
    if system == "Darwin":
        # macOS (Intel and ARM/Apple Silicon)
        executable_name = "ur3e_mockup_macos_" + machine
        executable_path = os.path.join(ur3e_mockup_dir, executable_name)
    elif system == "Windows":
        # Windows
        executable_name = "ur3e_mockup_win.exe"
        executable_path = os.path.join(ur3e_mockup_dir, executable_name)
    elif system == "Linux":
        # Linux
        executable_name = "ur3e_mockup_linux_" + machine
        print(f"exec_name: {executable_name}")
        executable_path = os.path.join(ur3e_mockup_dir, executable_name)

    else:
        # Other systems
        raise OSError(
            f"Unsupported operating system: {system}. "
            f"Supported systems: Darwin (macOS), Windows, Linux"
        )

    if not os.path.exists(executable_path):
        raise FileNotFoundError(f"Executable not found for {system}: {executable_path}")

    return executable_path


def start_robot_arm_mockup(ok_queue=None):
    """
    Starts the ur3e_mockup executable and keeps it running.
    Handles graceful shutdown via Ctrl+C (SIGINT).
    """
    # Get the platform-specific executable path
    system = platform.system()
    machine = platform.machine()
    logger.info("Detected OS: %s, Machine: %s", system, machine)
    executable_path = _get_executable_path(system, machine)
    logger.info("Starting executable: %s", executable_path)

    # Start the subprocess
    process = subprocess.Popen([executable_path])

    if ok_queue:
        ok_queue.put("started")

    try:
        # Keep the process running until interrupted
        process.wait()
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        logger.info("Shutting down robot arm mockup...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
    finally:
        logger.info("Robot arm mockup stopped.")


if __name__ == "__main__":
    start_robot_arm_mockup()
