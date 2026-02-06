# lambda/handlers/error_handlers.py

import logging
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_model import Response

from utils.jeedom_client import JeedomClient
from utils.response_builder import build_response
from schemas import QuestionStateError
import prompts

logger = logging.getLogger(__name__)


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Comprehensive exception handler with Jeedom logging."""

    def can_handle(self, handler_input, exception):
        """Handle all exceptions."""
        return True

    def handle(self, handler_input, exception) -> Response:
        """Handle exceptions with proper logging and user feedback."""
        logger.error(f"Exception caught: {type(exception).__name__}", exc_info=True)
        logger.error(f"Exception details: {str(exception)}")
        
        # Initialize Jeedom client
        try:
            jeedom = JeedomClient(handler_input)
        except Exception as e:
            logger.error(f"Failed to initialize Jeedom client in exception handler: {e}")
            jeedom = None
        
        # Get language strings
        data = handler_input.attributes_manager.request_attributes.get("_", {})
        
        # Determine appropriate error message
        speak_output = self._get_error_message(exception, jeedom, data)
        
        # Log to Jeedom
        if jeedom:
            try:
                error_log = f"Exception: {type(exception).__name__} - {str(exception)}"
                jeedom.post_log(error_log)
            except Exception as log_error:
                logger.error(f"Failed to log exception to Jeedom: {log_error}")
        
        # Build response
        return (
            handler_input.response_builder
            .speak(speak_output)
            .set_should_end_session(True)
            .response
        )

    def _get_error_message(self, exception, jeedom, data: dict) -> str:
        """
        Determine appropriate error message based on exception type and state.
        
        Args:
            exception: The caught exception
            jeedom: JeedomClient instance or None
            data: Language strings dictionary
            
        Returns:
            Error message to speak
        """
        # If Jeedom has state with text, use it
        if jeedom and jeedom.jee_state:
            if isinstance(jeedom.jee_state, QuestionStateError):
                return jeedom.jee_state.text
            elif hasattr(jeedom.jee_state, 'text') and jeedom.jee_state.text:
                return jeedom.jee_state.text
        
        # Check for specific exception types
        exception_type = type(exception).__name__
        
        # Network-related errors
        if exception_type in ('HTTPError', 'TimeoutError', 'MaxRetryError', 'URLError'):
            return data.get(prompts.ERROR_NETWORK, "Erreur de connexion au réseau")
        
        # Authentication errors
        if exception_type in ('AuthenticationError', 'PermissionError'):
            return data.get(prompts.ERROR_401, "Erreur d'authentification")
        
        # Parsing/data errors
        if exception_type in ('JSONDecodeError', 'ValueError', 'KeyError'):
            return data.get(prompts.ERROR_PARSE, "Erreur de traitement des données")
        
        # Slot/intent errors
        if 'slot' in str(exception).lower() or 'intent' in str(exception).lower():
            return data.get(prompts.ERROR_ACOUSTIC, "Je n'ai pas bien compris votre demande")
        
        # Generic error
        return data.get(prompts.ERROR_GENERAL, "Une erreur s'est produite")


class SpecificExceptionHandler(AbstractExceptionHandler):
    """Handler for specific known exceptions."""

    def can_handle(self, handler_input, exception):
        """Handle specific exception types."""
        return isinstance(exception, (ValueError, KeyError, AttributeError))

    def handle(self, handler_input, exception) -> Response:
        """Handle specific exceptions with targeted messages."""
        logger.warning(f"Specific exception: {type(exception).__name__} - {str(exception)}")
        
        data = handler_input.attributes_manager.request_attributes.get("_", {})
        
        if isinstance(exception, ValueError):
            speak_output = data.get(prompts.ERROR_INVALID_VALUE, "Valeur invalide")
        elif isinstance(exception, KeyError):
            speak_output = data.get(prompts.ERROR_MISSING_DATA, "Données manquantes")
        else:  # AttributeError
            speak_output = data.get(prompts.ERROR_CONFIG, "Erreur de configuration")
        
        return build_response(handler_input, speak_output, should_end_session=True)