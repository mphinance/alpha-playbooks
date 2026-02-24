import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {
        "VULTR_ALIAS": "vultr",
        "VULTR_WEB_ROOT": "/home/mphinance/public_html/alpha",
        "VENUS_STORAGE": "backups"
    }

config = load_config()
VULTR_ALIAS = config.get("VULTR_ALIAS", "vultr")
VULTR_WEB_ROOT = config.get("VULTR_WEB_ROOT", "/home/mphinance/public_html/alpha")
VENUS_STORAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), config.get("VENUS_STORAGE", "backups"))
