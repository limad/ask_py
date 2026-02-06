# lambda/handlers/scenario_handlers.py

import logging
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.utils import is_intent_name, get_slot_value
from ask_sdk_model import Response

from utils.jeedom_client import JeedomClient
from utils.response_builder import build_response
from const import RESPONSE_SCENARIO
import prompts

logger = logging.getLogger(__name__)


class ActivateScenarioIntentHandler(AbstractRequestHandler):
    """Handler for activating scenarios/scenes."""

    def can_handle(self, handler_input):
        return is_intent_name("ActivateScenarioIntent")(handler_input)

    def handle(self, handler_input) -> Response:
        logger.info("ActivateScenario Intent triggered")
        
        scenario = get_slot_value(handler_input, "Scenario")
        
        logger.debug(f"Scenario: {scenario}")
        
        if not scenario:
            data = handler_input.attributes_manager.request_attributes.get("_", {})
            speak_output = data.get(prompts.ERROR_MISSING_SCENARIO, "Quel scénario voulez-vous activer ?")
            return build_response(handler_input, speak_output, should_end_session=False)
        
        jeedom = JeedomClient(handler_input)
        jeedom.get_question()
        
        speak_output = jeedom.post_event(
            response=scenario,
            response_type=RESPONSE_SCENARIO,
            scenario=scenario
        )
        
        if not speak_output or speak_output == "OK":
            data = handler_input.attributes_manager.request_attributes.get("_", {})
            template = data.get(prompts.SCENARIO_ACTIVATED, "Scénario {scenario} activé")
            speak_output = template.format(scenario=scenario)
        
        return build_response(handler_input, speak_output)