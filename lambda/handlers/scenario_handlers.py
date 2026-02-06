# lambda/handlers/scenario_handlers.py
import logging
import json
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.utils import is_intent_name, get_slot_value
from ask_sdk_model import Response

from lambda.utils.jeedom_client0 import JeedomClient
from utils.response_builder import ResponseBuilder
from utils.jeedom_logger import JeedomLogger
from config import ENABLE_SCENARIOS
from const import RESPONSE_SCENARIO

logger = logging.getLogger(__name__)


class ActivateScenarioIntentHandler(AbstractRequestHandler):
    """Handler for activating scenarios/scenes."""

    def can_handle(self, handler_input):
        return (is_intent_name("ActivateScenarioIntent")(handler_input) and
                ENABLE_SCENARIOS)

    def handle(self, handler_input) -> Response:
        logger.info("ActivateScenario Intent")
        
        try:
            scenario = get_slot_value(handler_input, "Scenario")
            action = get_slot_value(handler_input, "Action")  # Optional: start, stop, enable
            
            logger.debug(f"Scenario: {scenario}, Action: {action}")
            
            # Validate scenario name
            if not scenario:
                return ResponseBuilder.build(
                    handler_input,
                    speech=ResponseBuilder.get_text(handler_input, "ERROR_MISSING_SCENARIO"),
                    should_end_session=False
                )
            
            jeedom = JeedomClient(handler_input)
            jeedom.get_question()
            
            # Build scenario command
            scenario_data = {
                "scenario": scenario,
                "action": action or "activate",
            }
            
            speak_output = jeedom.post_event(
                response=json.dumps(scenario_data),
                response_type=RESPONSE_SCENARIO,
                scenario=scenario
            )
            
            # Provide fallback response if Jeedom doesn't return one
            if not speak_output or speak_output == "OK":
                template = ResponseBuilder.get_text(handler_input, "SCENARIO_ACTIVATED")
                speak_output = template.format(scenario=scenario)
            
            JeedomLogger.log_to_jeedom(
                f"Scenario activated: {scenario}",
                level="info",
                context=scenario_data
            )
            
            return ResponseBuilder.build(handler_input, speech=speak_output)
            
        except Exception as e:
            logger.error(f"ActivateScenario error: {e}", exc_info=True)
            JeedomLogger.log_error(handler_input, e, "ActivateScenarioIntent")
            return ResponseBuilder.error_response(handler_input, "ERROR_SCENARIO")


class ListScenariosIntentHandler(AbstractRequestHandler):
    """Handler for listing available scenarios."""

    def can_handle(self, handler_input):
        return (is_intent_name("ListScenariosIntent")(handler_input) and
                ENABLE_SCENARIOS)

    def handle(self, handler_input) -> Response:
        logger.info("ListScenarios Intent")
        
        try:
            jeedom = JeedomClient(handler_input)
            jeedom.get_question()
            
            # Request scenario list from Jeedom
            speak_output = jeedom.post_event(
                response="list_scenarios",
                response_type=RESPONSE_SCENARIO
            )
            
            JeedomLogger.log_intent(handler_input, "ListScenariosIntent", success=True)
            
            return ResponseBuilder.build(handler_input, speech=speak_output)
            
        except Exception as e:
            logger.error(f"ListScenarios error: {e}", exc_info=True)
            JeedomLogger.log_error(handler_input, e, "ListScenariosIntent")
            return ResponseBuilder.error_response(handler_input, "ERROR_SCENARIO_LIST")


class StopScenarioIntentHandler(AbstractRequestHandler):
    """Handler for stopping running scenarios."""

    def can_handle(self, handler_input):
        return (is_intent_name("StopScenarioIntent")(handler_input) and
                ENABLE_SCENARIOS)

    def handle(self, handler_input) -> Response:
        logger.info("StopScenario Intent")
        
        try:
            scenario = get_slot_value(handler_input, "Scenario")
            
            logger.debug(f"Stop scenario: {scenario}")
            
            if not scenario:
                return ResponseBuilder.build(
                    handler_input,
                    speech=ResponseBuilder.get_text(handler_input, "ERROR_MISSING_SCENARIO"),
                    should_end_session=False
                )
            
            jeedom = JeedomClient(handler_input)
            jeedom.get_question()
            
            scenario_data = {
                "scenario": scenario,
                "action": "stop",
            }
            
            speak_output = jeedom.post_event(
                response=json.dumps(scenario_data),
                response_type=RESPONSE_SCENARIO,
                scenario=scenario
            )
            
            if not speak_output or speak_output == "OK":
                template = ResponseBuilder.get_text(handler_input, "SCENARIO_STOPPED")
                speak_output = template.format(scenario=scenario)
            
            JeedomLogger.log_to_jeedom(
                f"Scenario stopped: {scenario}",
                level="info",
                context=scenario_data
            )
            
            return ResponseBuilder.build(handler_input, speech=speak_output)
            
        except Exception as e:
            logger.error(f"StopScenario error: {e}", exc_info=True)
            JeedomLogger.log_error(handler_input, e, "StopScenarioIntent")
            return ResponseBuilder.error_response(handler_input, "ERROR_SCENARIO_STOP")