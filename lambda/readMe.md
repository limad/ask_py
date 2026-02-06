Jeedom Skill for Alexa-Premium
Version 1.0.0 - Alexa-hosted skill for Jeedom home automation control.
📋 Quick Start
1. Configuration
Edit user_config.py with your Jeedom credentials:
python# Your Jeedom server URL (without trailing slash)
JEEDOM_URL = "https://your-jeedom-url.com"

# Your Jeedom API Key
APIKEY = "your-api-key-here"

# Debug Mode (set to True for detailed logging)
DEBUG = False

# SSL Verification (set to False only for testing)
VERIFY_SSL = True
⚠️ IMPORTANT: Only modify user_config.py - never edit config.py directly!
2. File Structure
lambda/
├── user_config.py          # ✏️ EDIT THIS - Your credentials
├── config.py               # ⛔ DO NOT EDIT - System config
├── const.py                # Constants
├── lambda_function.py      # Main handler
├── requirements.txt        # Dependencies
├── language_strings.json   # Translations
├── utils/
│   ├── __init__.py
│   ├── lwa_token.py       # LWA token manager
│   └── jeedom_logger.py   # Jeedom logger
└── handlers/
    ├── __init__.py
    ├── core_handlers.py
    ├── device_handlers.py
    ├── scenario_handlers.py
    ├── data_handlers.py
    └── error_handlers.py
🔧 Features
✅ Implemented

LWA Token Management: Automatic token refresh and caching
Jeedom Logging: All logs sent to your Jeedom server
DynamoDB Persistence: Token and state storage
Multi-locale Support: FR-FR, FR-CA supported
APL Support: Visual responses on Echo Show devices
Device Control: Control Jeedom devices via voice
Scenario Execution: Run Jeedom scenarios
Status Queries: Get device status

🔐 Security

SSL verification enabled
API key authentication
Secure token storage in DynamoDB

📊 Logging
All logs are automatically sent to your Jeedom server at:
{JEEDOM_URL}/plugins/alexaapiv2/core/php/askResponse.php?apikey={APIKEY}&command=log
Log levels:

info: Normal operations
warning: Non-critical issues
error: Critical errors
debug: Detailed debugging (when DEBUG=True)

🚀 Deployment

Create a new Alexa-hosted skill in the Alexa Developer Console
Choose Python runtime
Upload all files maintaining the directory structure
Edit user_config.py with your credentials
Deploy the skill

🛠️ Advanced Configuration
Edit user_config.py for these options:
pythonDEBUG = False              # Enable debug logging (CloudWatch)
VERIFY_SSL = True          # SSL certificate verification
System configuration in config.py (developers only - auto-configured):

Connection timeouts
Retry settings
Feature flags
API endpoints

📝 Usage Examples
Get LWA Token
pythonfrom utils.lwa_token import LWATokenManager

token = LWATokenManager.get_access_token(handler_input)
Log to Jeedom
pythonfrom utils.jeedom_logger import JeedomLogger

# Simple log
JeedomLogger.log_to_jeedom("Device turned on", level="info")

# Log intent
JeedomLogger.log_intent(handler_input, "ControlDeviceIntent", success=True)

# Log error
JeedomLogger.log_error(handler_input, exception, "Device control failed")
🐛 Troubleshooting
Logs not appearing in Jeedom

Verify JEEDOM_URL and APIKEY in user_config.py
Check Jeedom AlexaPremium plugin is installed and active
Verify network connectivity from AWS Lambda to your Jeedom server

Token issues

DynamoDB table JeedomSkillPersistence is created automatically
Check CloudWatch logs for token refresh errors
Ensure skill has proper permissions in Alexa console

Connection timeouts

Increase CONNECT_TIMEOUT and READ_TIMEOUT in config.py
Check if Jeedom server is accessible from internet
Verify SSL certificate is valid (or set VERIFY_SSL = False for testing)

📞 Support
For issues related to:

Jeedom plugin: Contact Jeedom AlexaPremium plugin support
Skill code: Check CloudWatch logs in AWS Console
Alexa integration: Verify skill configuration in Alexa Developer Console

📄 License
Copyright © 2024 - Jeedom Skill Premium