import os
import sys
import time
import math
import socket
import threading
import logging
import urllib.request


from datetime import datetime, timezone
from influxdb_client import InfluxDBClient

from src.communication.rabbitmq import Rabbitmq, ROUTING_KEY_STATE
from src.communication.factory import RabbitMQFactory
from src.communication.protocol import RobotArmStateKeys, encode_json
from src.services.db_service.db_service import DBService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("TestDBService")

INFLUXDB_URL    = os.environ.get("INFLUXDB_URL",    "http://localhost:8086")
INFLUXDB_TOKEN  = os.environ.get("INFLUXDB_TOKEN",  "NQuF6M2nTKehaIe-uUfOPbzOFpVGSj0sAjEoPvWhajeXh6ulk7r0Jq6_CkD33ydRGo2ayaNvDVAXqbmPJM9XdA==")
INFLUXDB_ORG    = os.environ.get("INFLUXDB_ORG",    "ur3e")
INFLUXDB_BUCKET = os.environ.get("INFLUXDB_BUCKET", "ur3e")

RABBITMQ_HOST = "localhost"
RABBITMQ_PORT = 5672


def preflight_checks():
    ok = True

    try:
        with socket.create_connection((RABBITMQ_HOST, RABBITMQ_PORT), timeout=3):
            logger.info("  ✓ RabbitMQ reachable at %s:%s", RABBITMQ_HOST, RABBITMQ_PORT)
    except OSError:
        logger.error(
            "  ✗ Cannot reach RabbitMQ at %s:%s\n"
            "    Fix: run the setup notebook, or manually:\n"
            "      docker stop rabbitmq && docker rm rabbitmq\n"
            "      docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 \\\n"
            "        -e RABBITMQ_DEFAULT_USER=ur3e \\\n"
            "        -e RABBITMQ_DEFAULT_PASS=ur3e \\\n"
            "        rabbitmq:3-management",
            RABBITMQ_HOST, RABBITMQ_PORT,
        )
        ok = False

    if ok:
        try:
            rmq = RabbitMQFactory().create_rabbitmq()
            with rmq:
                pass
            logger.info("  ✓ RabbitMQ authentication OK (user=ur3e)")
        except Exception as exc:
            logger.error(
                "  ✗ RabbitMQ authentication failed: %s\n"
                "    The broker is running but rejected the credentials.\n"
                "    Fix: recreate the container so it uses the ur3e/ur3e credentials:\n"
                "      docker stop rabbitmq && docker rm rabbitmq\n"
                "      docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 \\\n"
                "        -e RABBITMQ_DEFAULT_USER=ur3e \\\n"
                "        -e RABBITMQ_DEFAULT_PASS=ur3e \\\n"
                "        rabbitmq:3-management",
                exc,
            )
            ok = False

    try:
        with urllib.request.urlopen(f"{INFLUXDB_URL}/ping", timeout=3) as r:
            if r.status == 204:
                logger.info("  ✓ InfluxDB reachable at %s", INFLUXDB_URL)
    except Exception:
        logger.error(
            "  ✗ Cannot reach InfluxDB at %s\n"
            "    Fix: run the setup notebook, or manually:\n"
            "      docker stop influxdb && docker rm influxdb\n"
            "      docker run -d --name influxdb -p 8086:8086 \\\n"
            "        -e DOCKER_INFLUXDB_INIT_MODE=setup \\\n"
            "        -e DOCKER_INFLUXDB_INIT_USERNAME=ur3e \\\n"
            "        -e DOCKER_INFLUXDB_INIT_PASSWORD=ur3epassword \\\n"
            "        -e DOCKER_INFLUXDB_INIT_ORG=ur3e \\\n"
            "        -e DOCKER_INFLUXDB_INIT_BUCKET=ur3e \\\n"
            "        influxdb:2.0",
            INFLUXDB_URL,
        )
        ok = False

    if ok:
        if INFLUXDB_TOKEN == "your-influxdb-token-here":
            logger.error(
                "  ✗ INFLUXDB_TOKEN is still the placeholder value.\n"
                "    Fix: set it in your .env file or as an environment variable.\n"
                "    The token was printed at the end of the setup notebook."
            )
            ok = False
        else:
            try:
                client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
                client.buckets_api().find_buckets()
                client.close()
                logger.info("  ✓ InfluxDB token valid")
            except Exception as exc:
                logger.error(
                    "  ✗ InfluxDB token rejected: %s\n"
                    "    Fix: copy the correct token from the setup notebook output\n"
                    "    and update INFLUXDB_TOKEN in your .env file.",
                    exc,
                )
                ok = False

    if not ok:
        logger.error("\nPreflight failed — fix the issues above and re-run.")
        sys.exit(1)

    logger.info("  All preflight checks passed.\n")

def make_fake_state(tag: str = "test") -> dict:
    """Return a realistic robot arm state dict."""
    return {
        RobotArmStateKeys.TIMESTAMP:              time.time(),
        RobotArmStateKeys.ROBOT_MODE:             "Running",
        RobotArmStateKeys.Q_ACTUAL:               [0.1, -1.57,  1.57, -0.5, 0.3,  0.0],
        RobotArmStateKeys.QD_ACTUAL:              [0.05, 0.0,  -0.02,  0.01, 0.0, 0.0],
        RobotArmStateKeys.Q_TARGET:               [0.2, -1.57,  1.57, -0.5, 0.3,  0.0],
        RobotArmStateKeys.JOINT_MAX_SPEED:        [3.14, 3.14, 3.14, 3.14, 3.14, 3.14],
        RobotArmStateKeys.JOINT_MAX_ACCELERATION: [5.0,  5.0,  5.0,  5.0,  5.0,  5.0],
        RobotArmStateKeys.TCP_POSE:               [0.15, 0.23, 0.41, 0.0,  3.14, 0.0],
        "_test_tag": tag,
    }


# ── Helpers ──────────────────────────────────────────────────────────────────
def publish_message(state: dict):
    rmq: Rabbitmq = RabbitMQFactory().create_rabbitmq()
    with rmq:
        rmq.send_message(routing_key=ROUTING_KEY_STATE, message=state)
    logger.info("Published state message to RabbitMQ.")


def run_db_service_briefly(duration_s: float = 3.0):
    service = DBService()
    subscribed = threading.Event()

    original_subscribe = service._rmq.subscribe
    def subscribe_and_signal(*args, **kwargs):
        result = original_subscribe(*args, **kwargs)
        subscribed.set()
        return result
    service._rmq.subscribe = subscribe_and_signal

    def _run():
        try:
            service.run()
        except Exception as exc:
            logger.error("DBService thread error: %s", exc)

    t = threading.Thread(target=_run, daemon=True)
    t.start()

    subscribed.wait(timeout=5)
    logger.info("DBService subscribed and ready.")
    return service, t


def stop_db_service(service, thread, duration_s: float = 0.0):
    time.sleep(duration_s)
    try:
        service._rmq.channel.stop_consuming()
    except Exception:
        pass
    thread.join(timeout=5)


def query_influxdb(measurement: str, field: str, lookback: str = "30s"):
    client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
    query = f"""
from(bucket: "{INFLUXDB_BUCKET}")
  |> range(start: -{lookback})
  |> filter(fn: (r) => r._measurement == "{measurement}")
  |> filter(fn: (r) => r._field == "{field}")
"""
    tables = client.query_api().query(query)
    client.close()
    return [(r.get_time(), r.get_value()) for t in tables for r in t.records]


# ── Tests ────────────────────────────────────────────────────────────────────
PASS = []
FAIL = []

def check(name: str, condition: bool, detail: str = ""):
    if condition:
        PASS.append(name)
        logger.info("  ✓ PASS  %s", name)
    else:
        FAIL.append(name)
        logger.error("  ✗ FAIL  %s  %s", name, detail)


def test_normal_state():
    logger.info("\n── Test 1: Normal state message ────────────────────────")
    state = make_fake_state("normal")
    service, t = run_db_service_briefly()
    publish_message(state)
    stop_db_service(service, t, duration_s=2.0)

    rows = query_influxdb("robot_joint_state", "q_actual_0")
    check(
        "joint q_actual_0 written to InfluxDB",
        len(rows) > 0,
        f"got {len(rows)} rows",
    )
    if rows:
        stored_val = rows[-1][1]
        expected   = state[RobotArmStateKeys.Q_ACTUAL][0]
        check(
            "q_actual_0 value correct",
            math.isclose(stored_val, expected, rel_tol=1e-6),
            f"expected {expected}, got {stored_val}",
        )

    rows_tcp = query_influxdb("robot_tcp_pose", "x")
    check("tcp_pose.x written to InfluxDB", len(rows_tcp) > 0)
    if rows_tcp:
        check(
            "tcp_pose.x value correct",
            math.isclose(rows_tcp[-1][1], state[RobotArmStateKeys.TCP_POSE][0], rel_tol=1e-6),
        )

    rows_mode = query_influxdb("robot_mode", "mode")
    check("robot_mode written to InfluxDB", len(rows_mode) > 0)
    if rows_mode:
        check(
            "robot_mode value correct",
            rows_mode[-1][1] == "Running",
            f"got '{rows_mode[-1][1]}'",
        )


def test_malformed_message():
    logger.info("\n── Test 2: Malformed / empty message ───────────────────")
    bad_state = {"garbage_key": 42, "another_bad_key": [1, 2, 3]}
    try:
        service, t = run_db_service_briefly()
        publish_message(bad_state)
        stop_db_service(service, t, duration_s=2.0)
        check("DBService survives malformed message", True)
    except Exception as exc:
        check("DBService survives malformed message", False, str(exc))


def test_missing_timestamp():
    logger.info("\n── Test 3: State without timestamp (uses wall clock) ───")
    state = make_fake_state("no-ts")
    del state[RobotArmStateKeys.TIMESTAMP]
    try:
        service, t = run_db_service_briefly()
        publish_message(state)
        stop_db_service(service, t, duration_s=2.0)
        rows = query_influxdb("robot_joint_state", "q_actual_0")
        check("Message without timestamp handled correctly", len(rows) > 0)
    except Exception as exc:
        check("Message without timestamp handled correctly", False, str(exc))


if __name__ == "__main__":
    logger.info("Starting DB Service integration tests")
    logger.info("InfluxDB : %s  org=%s  bucket=%s", INFLUXDB_URL, INFLUXDB_ORG, INFLUXDB_BUCKET)

    logger.info("\n── Preflight checks ────────────────────────────────────")
    preflight_checks()

    test_normal_state()
    test_malformed_message()
    test_missing_timestamp()

    logger.info("\n%s", "=" * 55)
    logger.info("  Results:  %d passed,  %d failed", len(PASS), len(FAIL))
    logger.info("=" * 55)
    if FAIL:
        logger.error("  Failed tests: %s", ", ".join(FAIL))
        sys.exit(1)
    else:
        logger.info("  All tests passed!")
        sys.exit(0)