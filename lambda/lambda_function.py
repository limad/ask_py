# lambda/lambda_function.py - Jeedom Skill Premium
import logging
import json
from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestInterceptor, AbstractResponseInterceptor
from ask_sdk_dynamodb.adapter import DynamoDbAdapter

from config import CODE_VERSION, DEBUG
from utils.jeedom_logger import JeedomLogger

# Import handlers
from handlers.core_handlers import (
    LaunchRequestHandler,
    YesIntentHandler,
    NoIntentHandler,
    CancelOrStopIntentHandler,
    HelpIntentHandler,
    FallbackHandler,
    SessionEndedRequestHandler,
)
from handlers.device_handlers import (
    ControlDeviceIntentHandler,
    GetStatusIntentHandler,
    SetValueIntentHandler,
)
from handlers.scenario_handlers import (
    ActivateScenarioIntentHandler,
)
from handlers.data_handlers import (
    NumericIntentHandler,
    StringIntentHandler,
    SelectIntentHandler,
    DurationIntentHandler,
    DateTimeIntentHandler,
)
from handlers.error_handlers import (
    CatchAllExceptionHandler,
)

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)


class LocalizationInterceptor(AbstractRequestInterceptor):
    """Load locale-specific strings."""

    def process(self, handler_input):
        locale = handler_input.request_envelope.request.locale
        logger.info(f"Processing request for locale: {locale}")

        try:
            with open("language_strings.json", encoding="utf-8") as f:
                language_data = json.load(f)
            
            # Get base locale (e.g., "fr" from "fr-FR")
            base_locale = locale.split('-')[0]
            strings = language_data.get(base_locale, language_data.get("en", {}))
            
            # Override with specific locale if exists
            if locale in language_data:
                strings.update(language_data[locale])
            
            handler_input.attributes_manager.request_attributes["_"] = strings
            
        except FileNotFoundError:
            logger.warning("language_strings.json not found, using empty strings")
            handler_input.attributes_manager.request_attributes["_"] = {}
        except Exception as e:
            logger.error(f"Failed to load language strings: {e}")
            handler_input.attributes_manager.request_attributes["_"] = {}


class RequestLoggerInterceptor(AbstractRequestInterceptor):
    """Log incoming requests for debugging."""

    def process(self, handler_input):
        logger.debug("=" * 80)
        logger.debug(f"REQUEST: {handler_input.request_envelope.request.request_type}")
        
        if hasattr(handler_input.request_envelope.request, 'intent'):
            logger.debug(f"INTENT: {handler_input.request_envelope.request.intent.name}")
        
        if DEBUG:
            logger.debug(json.dumps(handler_input.request_envelope.to_dict(), indent=2))
        
        logger.debug("=" * 80)


class ResponseLoggerInterceptor(AbstractResponseInterceptor):
    """Log outgoing responses and send to Jeedom."""

    def process(self, handler_input, response):
        logger.debug("=" * 80)
        logger.debug("RESPONSE:")
        logger.debug(json.dumps(response, indent=2, default=str))
        logger.debug("=" * 80)
        
        # Log to Jeedom
        try:
            if hasattr(handler_input.request_envelope.request, 'intent'):
                intent_name = handler_input.request_envelope.request.intent.name
                JeedomLogger.log_intent(handler_input, intent_name, success=True)
        except Exception as e:
            logger.error(f"Failed to log response to Jeedom: {e}")


class VersionLoggerInterceptor(AbstractRequestInterceptor):
    """Log skill version on launch."""

    def process(self, handler_input):
        if handler_input.request_envelope.request.request_type == "LaunchRequest":
            logger.info(f"Jeedom Skill Premium v{CODE_VERSION} started")
            JeedomLogger.log_to_jeedom(
                message=f"Skill launched - Version {CODE_VERSION}",
                level="info",
                user_id=handler_input.request_envelope.session.user.user_id
            )


# Initialize DynamoDB adapter for persistent attributes (LWA token storage)
from config import DYNAMODB_TABLE_NAME

ddb_adapter = DynamoDbAdapter(
    table_name=DYNAMODB_TABLE_NAME,
    create_table=True,
    partition_key_name="id",
    attribute_name="attributes"
)

# Build skill with DynamoDB persistence
sb = CustomSkillBuilder(persistence_adapter=ddb_adapter)

# Register request handlers (ORDER MATTERS - most specific first!)
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(HelpIntentHandler())

# Device control handlers
sb.add_request_handler(ControlDeviceIntentHandler())
sb.add_request_handler(GetStatusIntentHandler())
sb.add_request_handler(SetValueIntentHandler())

# Scenario handlers
sb.add_request_handler(ActivateScenarioIntentHandler())

# Data input handlers (specific before generic)
sb.add_request_handler(YesIntentHandler())
sb.add_request_handler(NoIntentHandler())
sb.add_request_handler(NumericIntentHandler())
sb.add_request_handler(StringIntentHandler())
sb.add_request_handler(SelectIntentHandler())
sb.add_request_handler(DurationIntentHandler())
sb.add_request_handler(DateTimeIntentHandler())

# System handlers (catch-all patterns last)
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackHandler())
sb.add_request_handler(SessionEndedRequestHandler())

# Exception handlers
sb.add_exception_handler(CatchAllExceptionHandler())

# Request interceptors (run before handlers)
sb.add_global_request_interceptor(VersionLoggerInterceptor())
sb.add_global_request_interceptor(LocalizationInterceptor())

if DEBUG:
    sb.add_global_request_interceptor(RequestLoggerInterceptor())

# Response interceptors (run after handlers)
sb.add_global_response_interceptor(ResponseLoggerInterceptor())

# Lambda handler entry point
lambda_handler = sb.lambda_handler()