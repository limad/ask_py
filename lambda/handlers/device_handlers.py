# lambda/handlers/device_handlers.py

import logging
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.utils import is_intent_name, get_slot_value
from ask_sdk_model import Response

from utils.jeedom_client import JeedomClient
from utils.response_builder import build_response
from const import RESPONSE_DEVICE_CONTROL, RESPONSE_STATUS_QUERY, RESPONSE_SET_VALUE
import prompts

logger = logging.getLogger(__name__)


class ControlDeviceIntentHandler(AbstractRequestHandler):
    """Handler for device control (turn on/off, open/close, etc.)."""

    def can_handle(self, handler_input):
        return is_intent_name("ControlDeviceIntent")(handler_input)

    def handle(self, handler_input) -> Response:
        logger.info("ControlDevice Intent triggered")
        
        # Extract slots
        device = get_slot_value(handler_input, "Device")
        action = get_slot_value(handler_input, "Action")
        room = get_slot_value(handler_input, "Room")
        
        logger.debug(f"Device: {device}, Action: {action}, Room: {room}")
        
        # Validate slots
        if not device or not action:
            data = handler_input.attributes_manager.request_attributes.get("_", {})
            speak_output = data.get(prompts.ERROR_MISSING_SLOTS, "Je n'ai pas compris l'appareil ou l'action")
            return build_response(handler_input, speak_output, should_end_session=False)
        
        # Send to Jeedom
        jeedom = JeedomClient(handler_input)
        jeedom.get_question()
        
        # Build control command
        command_data = {
            "device": device,
            "action": action,
            "room": room,
        }
        
        speak_output = jeedom.post_event(
            response=str(command_data),
            response_type=RESPONSE_DEVICE_CONTROL,
            device=device,
            action=action,
            room=room
        )
        
        # If no custom response, build one
        if not speak_output or speak_output == "OK":
            data = handler_input.attributes_manager.request_attributes.get("_", {})
            template = data.get(prompts.DEVICE_CONTROL_SUCCESS, "{action} {device} effectué")
            speak_output = template.format(action=action, device=device, room=room or "")
        
        return build_response(handler_input, speak_output)


class GetStatusIntentHandler(AbstractRequestHandler):
    """Handler for status queries (temperature, state, etc.)."""

    def can_handle(self, handler_input):
        return is_intent_name("GetStatusIntent")(handler_input)

    def handle(self, handler_input) -> Response:
        logger.info("GetStatus Intent triggered")
        
        device = get_slot_value(handler_input, "Device")
        room = get_slot_value(handler_input, "Room")
        
        logger.debug(f"Device: {device}, Room: {room}")
        
        if not device and not room:
            data = handler_input.attributes_manager.request_attributes.get("_", {})
            speak_output = data.get(prompts.ERROR_MISSING_SLOTS, "De quel appareil voulez-vous connaître l'état ?")
            return build_response(handler_input, speak_output, should_end_session=False)
        
        jeedom = JeedomClient(handler_input)
        jeedom.get_question()
        
        speak_output = jeedom.post_event(
            response=device or room,
            response_type=RESPONSE_STATUS_QUERY,
            device=device,
            room=room
        )
        
        return build_response(handler_input, speak_output)


class SetValueIntentHandler(AbstractRequestHandler):
    """Handler for setting values (temperature, brightness, etc.)."""

    def can_handle(self, handler_input):
        return is_intent_name("SetValueIntent")(handler_input)

    def handle(self, handler_input) -> Response:
        logger.info("SetValue Intent triggered")
        
        device = get_slot_value(handler_input, "Device")
        value = get_slot_value(handler_input, "Value")
        
        logger.debug(f"Device: {device}, Value: {value}")
        
        if not device or not value:
            data = handler_input.attributes_manager.request_attributes.get("_", {})
            speak_output = data.get(prompts.ERROR_MISSING_SLOTS, "Appareil ou valeur manquant")
            return build_response(handler_input, speak_output, should_end_session=False)
        
        try:
            numeric_value = float(value)
        except (ValueError, TypeError):
            data = handler_input.attributes_manager.request_attributes.get("_", {})
            speak_output = data.get(prompts.ERROR_INVALID_VALUE, "Valeur invalide")
            return build_response(handler_input, speak_output, should_end_session=False)
        
        jeedom = JeedomClient(handler_input)
        jeedom.get_question()
        
        speak_output = jeedom.post_event(
            response=str(numeric_value),
            response_type=RESPONSE_SET_VALUE,
            device=device,
            value=numeric_value
        )
        
        if not speak_output or speak_output == "OK":
            data = handler_input.attributes_manager.request_attributes.get("_", {})
            template = data.get(prompts.SET_VALUE_SUCCESS, "{device} réglé à {value}")
            speak_output = template.format(device=device, value=value)
        
        return build_response(handler_input, speak_output)