# lambda/config.py
# =====================================================
# SYSTEM CONFIGURATION - DO NOT MODIFY
# =====================================================

from user_config import JEEDOM_URL, APIKEY, DEBUG, VERIFY_SSL

# Skill Version
CODE_VERSION = "1.0.0"

# API Endpoints (auto-generated from user_config)
JEEDOM_URL_CLEAN = JEEDOM_URL.rstrip("/")
QUESTION_URL = f"{JEEDOM_URL_CLEAN}/plugins/alexaapiv2/core/php/askQuestion.php?apikey={APIKEY}"
RESPONSE_URL = f"{JEEDOM_URL_CLEAN}/plugins/alexaapiv2/core/php/askResponse.php?apikey={APIKEY}&command=reponseASK"
LOG_URL = f"{JEEDOM_URL_CLEAN}/plugins/alexaapiv2/core/php/askResponse.php?apikey={APIKEY}&command=log"

# Timeouts (seconds)
CONNECT_TIMEOUT = 10.0
READ_TIMEOUT = 10.0
MAX_RETRIES = 3
RETRY_DELAY = 1.0

# Feature Flags
ENABLE_APL = True
ENABLE_DEVICE_CONTROL = True
ENABLE_SCENARIOS = True

# DynamoDB Table for persistent storage
DYNAMODB_TABLE_NAME = "JeedomSkillPersistence"