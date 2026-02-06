# lambda/config.py

import os

# Version
CODE_VERSION = "1.0.0"
CODE_VERS = 1.0

# Jeedom Configuration
JEEDOM_URL = os.environ.get("JEEDOM_URL", "").rstrip("/")
APIKEY = os.environ.get("JEEDOM_API_KEY", "123")
TOKEN = os.environ.get("JEEDOM_TOKEN", "")  # Optional long-lived token

# API Endpoints
QUESTION_URL = f"plugins/alexaapiv2/core/php/askQuestion.php?apikey={APIKEY}"
RESPONSE_URL = f"plugins/alexaapiv2/core/php/askResponse.php?apikey={APIKEY}&command=reponseASK"
LOG_URL = f"plugins/alexaapiv2/core/php/askResponse.php?apikey={APIKEY}&command=log"

# SSL Verification
VERIFY_SSL = os.environ.get("VERIFY_SSL", "true").lower() == "true"

# Debug Mode
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"

# Retry Configuration
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "3"))
RETRY_DELAY = float(os.environ.get("RETRY_DELAY", "1.0"))

# Timeout Configuration
CONNECT_TIMEOUT = float(os.environ.get("CONNECT_TIMEOUT", "10.0"))
READ_TIMEOUT = float(os.environ.get("READ_TIMEOUT", "10.0"))

# APL Support
ENABLE_APL = os.environ.get("ENABLE_APL", "true").lower() == "true"

# Feature Flags
CAN_POST_LOGS = os.environ.get("CAN_POST_LOGS", "true").lower() == "true"
ENABLE_DEVICE_CONTROL = os.environ.get("ENABLE_DEVICE_CONTROL", "true").lower() == "true"
ENABLE_SCENARIOS = os.environ.get("ENABLE_SCENARIOS", "true").lower() == "true"