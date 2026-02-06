# lambda/handlers/error_handlers.py
import logging
from typing import Optional
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_model import Response

from lambda.utils.jeedom_client0 import JeedomClient
from utils.response_builder import ResponseBuilder
from utils.jeedom_logger import JeedomLogger

logger = logging.getLogger(__name__)


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Comprehensive exception handler with Jeedom logging."""

    def can_handle(self, handler_input, exception):
        """Handle all exceptions."""
        return True

    def handle(self, handler_input, exception) -> Response:
        """Handle exceptions with proper logging and user feedback."""
        exception_type = type(exception).__name__
        exception_msg = str(exception)
        
        logger.error(f"Exception: {exception_type}", exc_info=True)
        logger.error(f"Details: {exception_msg}")
        
        # Log to Jeedom
        try:
            JeedomLogger.log_error(handler_input, exception, "Global Exception Handler")
        except Exception as log_error:
            logger.error(f"Failed to log to Jeedom: {log_error}")
        
        # Try to get Jeedom state for custom error message
        speak_output = self._get_error_message(handler_input, exception)
        
        return (
            handler_input.response_builder
            .speak(speak_output)
            .set_should_end_session(True)
            .response
        )

    def _get_error_message(self, handler_input, exception) -> str:
        """
        Get appropriate error message based on exception type.
        
        Args:
            handler_input: Handler input
            exception: The caught exception
            
        Returns:
            Error message to speak
        """
        exception_type = type(exception).__name__
        
        # Try to get custom error from Jeedom state
        try:
            jeedom = JeedomClient(handler_input)
            if jeedom.jee_state and hasattr(jeedom.jee_state, 'text'):
                if jeedom.jee_state.text:
                    return jeedom.jee_state.text
        except Exception as e:
            logger.debug(f"Could not get Jeedom state: {e}")
        
        # Map exception types to error message keys
        error_map = {
            # Network errors
            'HTTPError': 'ERROR_NETWORK',
            'TimeoutError': 'ERROR_TIMEOUT',
            'MaxRetryError': 'ERROR_NETWORK',
            'URLError': 'ERROR_NETWORK',
            'ConnectionError': 'ERROR_NETWORK',
            
            # Authentication errors
            'AuthenticationError': 'ERROR_401',
            'PermissionError': 'ERROR_403',
            'Unauthorized': 'ERROR_401',
            
            # Data errors
            'JSONDecodeError': 'ERROR_PARSE',
            'ValueError': 'ERROR_INVALID_VALUE',
            'KeyError': 'ERROR_MISSING_DATA',
            'TypeError': 'ERROR_INVALID_TYPE',
            
            # Intent/slot errors
            'SlotValueError': 'ERROR_ACOUSTIC',
            'IntentError': 'ERROR_ACOUSTIC',
        }
        
        error_key = error_map.get(exception_type, 'ERROR_GENERAL')
        
        return ResponseBuilder.get_text(handler_input, error_key)


class NetworkExceptionHandler(AbstractExceptionHandler):
    """Handler for network-related exceptions."""

    def can_handle(self, handler_input, exception):
        """Handle network exceptions."""
        exception_type = type(exception).__name__
        return exception_type in (
            'HTTPError',
            'TimeoutError',
            'MaxRetryError',
            'URLError',
            'ConnectionError',
            'ConnectTimeout',
            'ReadTimeout',
        )

    def handle(self, handler_input, exception) -> Response:
        """Handle network errors."""
        logger.error(f"Network error: {exception}", exc_info=True)
        
        JeedomLogger.log_error(handler_input, exception, "Network Error")
        
        speak_output = ResponseBuilder.get_text(handler_input, "ERROR_NETWORK")
        reprompt = ResponseBuilder.get_text(handler_input, "ERROR_NETWORK_REPROMPT")
        
        return ResponseBuilder.build(
            handler_input,
            speech=speak_output,
            reprompt=reprompt,
            should_end_session=True
        )


class ValidationExceptionHandler(AbstractExceptionHandler):
    """Handler for validation and data errors."""

    def can_handle(self, handler_input, exception):
        """Handle validation exceptions."""
        return isinstance(exception, (ValueError, KeyError, AttributeError, TypeError))

    def handle(self, handler_input, exception) -> Response:
        """Handle validation errors."""
        logger.warning(f"Validation error: {exception}", exc_info=True)
        
        JeedomLogger.log_error(handler_input, exception, "Validation Error")
        
        # Map exception type to message
        error_messages = {
            ValueError: "ERROR_INVALID_VALUE",
            KeyError: "ERROR_MISSING_DATA",
            AttributeError: "ERROR_CONFIG",
            TypeError: "ERROR_INVALID_TYPE",
        }
        
        error_key = error_messages.get(type(exception), "ERROR_GENERAL")
        speak_output = ResponseBuilder.get_text(handler_input, error_key)
        
        return ResponseBuilder.build(
            handler_input,
            speech=speak_output,
            should_end_session=False
        )


class JeedomExceptionHandler(AbstractExceptionHandler):
    """Handler for Jeedom-specific exceptions."""

    def can_handle(self, handler_input, exception):
        """Handle Jeedom exceptions."""
        exception_name = type(exception).__name__
        return 'jeedom' in exception_name.lower() or 'question' in exception_name.lower()

    def handle(self, handler_input, exception) -> Response:
        """Handle Jeedom errors."""
        logger.error(f"Jeedom error: {exception}", exc_info=True)
        
        JeedomLogger.log_error(handler_input, exception, "Jeedom Communication Error")
        
        speak_output = ResponseBuilder.get_text(handler_input, "ERROR_JEEDOM")
        
        return ResponseBuilder.build(
            handler_input,
            speech=speak_output,
            should_end_session=True
        )