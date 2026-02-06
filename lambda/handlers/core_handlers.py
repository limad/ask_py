# lambda/handlers/core_handlers.py

import logging
import json
from typing import Optional
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_model import Response
from ask_sdk_model.interfaces.alexa.presentation.apl import (
    RenderDocumentDirective,
    ExecuteCommandsDirective,
)

from utils.jeedom_client import JeedomClient
from utils.response_builder import build_response, supports_apl, load_apl_document
from config import ENABLE_APL
from const import RESPONSE_YES, RESPONSE_NO, RESPONSE_NONE
import prompts

logger = logging.getLogger(__name__)


class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch with APL support."""

    def can_handle(self, handler_input):
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input) -> Response:
        logger.info("Launch Request triggered")
        
        jeedom = JeedomClient(handler_input)
        
        # Get question from Jeedom
        if not jeedom.get_question():
            logger.error("Failed to get question from Jeedom")
            speak_output = jeedom.language_strings.get(
                prompts.ERROR_CONFIG,
                "Unable to connect to Jeedom"
            )
            return build_response(handler_input, speak_output)
        
        speak_output = jeedom.jee_state.text
        event_id = jeedom.jee_state.event_id
        
        # Build response
        response_builder = handler_input.response_builder.speak(speak_output)
        
        # Keep session open if there's an active event
        if event_id:
            response_builder.ask(speak_output)
        
        # Add APL if supported
        if ENABLE_APL and supports_apl(handler_input):
            try:
                apl_document = load_apl_document("launch_document.json")
                if apl_document:
                    datasources = {
                        "jeedomData": {
                            "type": "object",
                            "properties": {
                                "text": speak_output,
                                "hasEvent": bool(event_id),
                                "logo": "https://your-domain.com/images/jeedom-logo.png",
                            }
                        }
                    }
                    
                    response_builder.add_directive(
                        RenderDocumentDirective(
                            document=apl_document,
                            datasources=datasources
                        )
                    )
                    logger.debug("APL document added to response")
            except Exception as e:
                logger.warning(f"Failed to add APL: {e}")
        
        return response_builder.response


class YesIntentHandler(AbstractRequestHandler):
    """Handler for Yes Intent."""

    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.YesIntent")(handler_input)

    def handle(self, handler_input) -> Response:
        logger.info("Yes Intent triggered")
        
        jeedom = JeedomClient(handler_input)
        jeedom.get_question()
        
        speak_output = jeedom.post_event(RESPONSE_YES, RESPONSE_YES)
        return build_response(handler_input, speak_output)


class NoIntentHandler(AbstractRequestHandler):
    """Handler for No Intent."""

    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.NoIntent")(handler_input)

    def handle(self, handler_input) -> Response:
        logger.info("No Intent triggered")
        
        jeedom = JeedomClient(handler_input)
        jeedom.get_question()
        
        speak_output = jeedom.post_event(RESPONSE_NO, RESPONSE_NO)
        return build_response(handler_input, speak_output)


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""

    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input) -> Response:
        logger.info("Help Intent triggered")
        
        data = handler_input.attributes_manager.request_attributes.get("_", {})
        speak_output = data.get(prompts.HELP_MESSAGE, "How can I help you?")
        
        return build_response(handler_input, speak_output, should_end_session=False)


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Handler for Cancel and Stop Intent."""

    def can_handle(self, handler_input):
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input) -> Response:
        logger.info("Cancel/Stop Intent triggered")
        
        data = handler_input.attributes_manager.request_attributes.get("_", {})
        speak_output = data.get(prompts.STOP_MESSAGE, "Goodbye")
        
        return build_response(handler_input, speak_output, should_end_session=True)


class FallbackHandler(AbstractRequestHandler):
    """Handler for Fallback Intent."""

    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input) -> Response:
        logger.info("Fallback triggered")
        
        jeedom = JeedomClient(handler_input)
        jeedom.get_question()
        jeedom.post_event(RESPONSE_NONE, RESPONSE_NONE)
        
        data = handler_input.attributes_manager.request_attributes.get("_", {})
        speak_output = data.get(prompts.FALLBACK_MESSAGE, "I didn't understand")
        
        return build_response(handler_input, speak_output, should_end_session=True)


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""

    def can_handle(self, handler_input):
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input) -> Response:
        logger.info("Session Ended")
        
        jeedom = JeedomClient(handler_input)
        jeedom.get_question()
        
        from ask_sdk_model import SessionEndedReason
        reason = handler_input.request_envelope.request.reason
        
        if reason in (SessionEndedReason.EXCEEDED_MAX_REPROMPTS, SessionEndedReason.USER_INITIATED):
            jeedom.post_event(RESPONSE_NONE, RESPONSE_NONE)
        
        return handler_input.response_builder.response