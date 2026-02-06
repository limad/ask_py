# lambda/lambda_function.py - Jeedom Skill Premium
# VERSION 1.0.0

import logging
import json
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestInterceptor

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

from config import DEBUG

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)


class LocalizationInterceptor(AbstractRequestInterceptor):
    """Add locale-specific data to request attributes."""

    def process(self, handler_input):
        """Load locale specific data."""
        locale = handler_input.request_envelope.request.locale
        logger.info(f"Locale: {locale}")

        try:
            with open("language_strings.json", encoding="utf-8") as f:
                language_data = json.load(f)
            
            # Default to base language (e.g., "fr" from "fr-FR")
            base_locale = locale[:2]
            data = language_data.get(base_locale, language_data.get("en", {}))
            
            # Override with specific locale if exists
            if locale in language_data:
                data.update(language_data[locale])
            
            handler_input.attributes_manager.request_attributes["_"] = data
            
        except Exception as e:
            logger.error(f"Failed to load language strings: {e}")
            # Fallback to English
            handler_input.attributes_manager.request_attributes["_"] = {}


class RequestLoggerInterceptor(AbstractRequestInterceptor):
    """Log all incoming requests."""

    def process(self, handler_input):
        """Log request details."""
        logger.debug("=" * 80)
        logger.debug("REQUEST ENVELOPE")
        logger.debug(json.dumps(handler_input.request_envelope.to_dict(), indent=2))
        logger.debug("=" * 80)


# Build skill
sb = SkillBuilder()

# Register request handlers (ORDER MATTERS!)
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(HelpIntentHandler())

# Device control handlers
sb.add_request_handler(ControlDeviceIntentHandler())
sb.add_request_handler(GetStatusIntentHandler())
sb.add_request_handler(SetValueIntentHandler())

# Scenario handlers
sb.add_request_handler(ActivateScenarioIntentHandler())

# Data input handlers
sb.add_request_handler(YesIntentHandler())
sb.add_request_handler(NoIntentHandler())
sb.add_request_handler(NumericIntentHandler())
sb.add_request_handler(StringIntentHandler())
sb.add_request_handler(SelectIntentHandler())
sb.add_request_handler(DurationIntentHandler())
sb.add_request_handler(DateTimeIntentHandler())

# System handlers
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackHandler())
sb.add_request_handler(SessionEndedRequestHandler())

# Exception handlers
sb.add_exception_handler(CatchAllExceptionHandler())

# Interceptors
sb.add_global_request_interceptor(LocalizationInterceptor())
if DEBUG:
    sb.add_global_request_interceptor(RequestLoggerInterceptor())

# Lambda handler
lambda_handler = sb.lambda_handler()