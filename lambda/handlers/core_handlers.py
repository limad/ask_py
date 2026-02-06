# lambda/handlers/core_handlers.py
import logging
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_model import Response
from ask_sdk_model.ui import SimpleCard

from lambda.utils.jeedom_client0 import JeedomClient
from utils.response_builder import ResponseBuilder
from utils.jeedom_logger import JeedomLogger
from config import ENABLE_APL
from const import RESPONSE_YES, RESPONSE_NO, RESPONSE_NONE

logger = logging.getLogger(__name__)


class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""

    def can_handle(self, handler_input):
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input) -> Response:
        logger.info("Launch Request")
        
        try:
            jeedom = JeedomClient(handler_input)
            
            # Get initial question from Jeedom
            if not jeedom.get_question():
                logger.error("Failed to get question from Jeedom")
                JeedomLogger.log_error(handler_input, Exception("Launch failed"), "get_question")
                return ResponseBuilder.error_response(
                    handler_input,
                    "ERROR_CONFIG",
                    "Impossible de se connecter à Jeedom"
                )
            
            speak_output = jeedom.jee_state.text
            event_id = jeedom.jee_state.event_id
            
            # Log successful launch
            JeedomLogger.log_intent(handler_input, "LaunchRequest", success=True)
            
            # Build response with APL support
            return ResponseBuilder.build(
                handler_input,
                speech=speak_output,
                reprompt=speak_output if event_id else None,
                card_title="Jeedom",
                card_text=speak_output,
                should_end_session=not bool(event_id),
                apl_document="launch_document.json" if ENABLE_APL else None,
                apl_data={"text": speak_output, "hasEvent": bool(event_id)}
            )
            
        except Exception as e:
            logger.error(f"Launch error: {e}", exc_info=True)
            JeedomLogger.log_error(handler_input, e, "LaunchRequest")
            return ResponseBuilder.error_response(handler_input, "ERROR_GENERAL")


class YesIntentHandler(AbstractRequestHandler):
    """Handler for AMAZON.YesIntent."""

    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.YesIntent")(handler_input)

    def handle(self, handler_input) -> Response:
        logger.info("Yes Intent")
        
        try:
            jeedom = JeedomClient(handler_input)
            jeedom.get_question()
            
            speak_output = jeedom.post_event(RESPONSE_YES, RESPONSE_YES)
            JeedomLogger.log_intent(handler_input, "AMAZON.YesIntent", success=True)
            
            return ResponseBuilder.build(handler_input, speech=speak_output)
            
        except Exception as e:
            logger.error(f"Yes Intent error: {e}", exc_info=True)
            JeedomLogger.log_error(handler_input, e, "YesIntent")
            return ResponseBuilder.error_response(handler_input, "ERROR_GENERAL")


class NoIntentHandler(AbstractRequestHandler):
    """Handler for AMAZON.NoIntent."""

    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.NoIntent")(handler_input)

    def handle(self, handler_input) -> Response:
        logger.info("No Intent")
        
        try:
            jeedom = JeedomClient(handler_input)
            jeedom.get_question()
            
            speak_output = jeedom.post_event(RESPONSE_NO, RESPONSE_NO)
            JeedomLogger.log_intent(handler_input, "AMAZON.NoIntent", success=True)
            
            return ResponseBuilder.build(handler_input, speech=speak_output)
            
        except Exception as e:
            logger.error(f"No Intent error: {e}", exc_info=True)
            JeedomLogger.log_error(handler_input, e, "NoIntent")
            return ResponseBuilder.error_response(handler_input, "ERROR_GENERAL")


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for AMAZON.HelpIntent."""

    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input) -> Response:
        logger.info("Help Intent")
        
        try:
            speak_output = ResponseBuilder.get_text(handler_input, "HELP_MESSAGE")
            reprompt = ResponseBuilder.get_text(handler_input, "HELP_REPROMPT")
            
            JeedomLogger.log_intent(handler_input, "AMAZON.HelpIntent", success=True)
            
            return ResponseBuilder.build(
                handler_input,
                speech=speak_output,
                reprompt=reprompt,
                card_title="Aide Jeedom",
                card_text=speak_output,
                should_end_session=False
            )
            
        except Exception as e:
            logger.error(f"Help Intent error: {e}", exc_info=True)
            return ResponseBuilder.error_response(handler_input, "ERROR_GENERAL")


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Handler for AMAZON.CancelIntent and AMAZON.StopIntent."""

    def can_handle(self, handler_input):
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input) -> Response:
        logger.info("Cancel/Stop Intent")
        
        try:
            speak_output = ResponseBuilder.get_text(handler_input, "STOP_MESSAGE")
            
            JeedomLogger.log_intent(handler_input, "AMAZON.StopIntent", success=True)
            
            return ResponseBuilder.build(
                handler_input,
                speech=speak_output,
                should_end_session=True
            )
            
        except Exception as e:
            logger.error(f"Stop Intent error: {e}", exc_info=True)
            return ResponseBuilder.error_response(handler_input, "ERROR_GENERAL")


class FallbackHandler(AbstractRequestHandler):
    """Handler for AMAZON.FallbackIntent."""

    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input) -> Response:
        logger.info("Fallback Intent")
        
        try:
            jeedom = JeedomClient(handler_input)
            jeedom.get_question()
            jeedom.post_event(RESPONSE_NONE, RESPONSE_NONE)
            
            speak_output = ResponseBuilder.get_text(handler_input, "FALLBACK_MESSAGE")
            reprompt = ResponseBuilder.get_text(handler_input, "FALLBACK_REPROMPT")
            
            JeedomLogger.log_intent(handler_input, "AMAZON.FallbackIntent", success=False)
            
            return ResponseBuilder.build(
                handler_input,
                speech=speak_output,
                reprompt=reprompt,
                should_end_session=False
            )
            
        except Exception as e:
            logger.error(f"Fallback error: {e}", exc_info=True)
            return ResponseBuilder.error_response(handler_input, "ERROR_GENERAL")


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for SessionEndedRequest."""

    def can_handle(self, handler_input):
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input) -> Response:
        reason = handler_input.request_envelope.request.reason
        logger.info(f"Session ended: {reason}")
        
        try:
            from ask_sdk_model import SessionEndedReason
            
            # Only post RESPONSE_NONE for certain end reasons
            if reason in (SessionEndedReason.EXCEEDED_MAX_REPROMPTS, 
                         SessionEndedReason.USER_INITIATED):
                jeedom = JeedomClient(handler_input)
                jeedom.get_question()
                jeedom.post_event(RESPONSE_NONE, RESPONSE_NONE)
            
            JeedomLogger.log_to_jeedom(
                f"Session ended: {reason}",
                level="info",
                user_id=handler_input.request_envelope.session.user.user_id
            )
            
        except Exception as e:
            logger.error(f"Session end error: {e}", exc_info=True)
        
        return handler_input.response_builder.response