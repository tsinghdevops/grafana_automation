import logging
import json
import sys

LOG_FILE = "grafana_automation.log.json"
logger = logging.getLogger("grafana_automation")
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler(LOG_FILE)
file_formatter = logging.Formatter('%(message)s')
file_handler.setFormatter(file_formatter)

console_handler = logging.StreamHandler(sys.stdout)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

logger.handlers = [file_handler, console_handler]

def log_action(level: str, message: str, resource_type: str, resource_value: str):
    log_entry = {
        "log-level": level,
        "message": message,
        "resource_name": f"{resource_type}: {resource_value}"
    }
    if level == "info":
        logger.info(json.dumps(log_entry))
    elif level == "error":
        logger.error(json.dumps(log_entry))
