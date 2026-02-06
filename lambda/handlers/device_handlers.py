# lambda/handlers/device_handlers.py
import logging
import json
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.utils import is_intent_name, get_slot_value
from ask_sdk_model import Response

from lambda.utils.jeedom_client0 import JeedomClient
from utils.response_builder import ResponseBuilder
from utils.jeedom_logger import JeedomLogger
from config import ENABLE_DEVICE_CONTROL
from const import RESPONSE_DEVICE_CONTROL, RESPONSE_STATUS_QUERY, RESPONSE_SET_VALUE

logger = logging.getLogger(__name__)


class ControlDeviceIntentHandler(AbstractRequestHandler):
    """Handler for device control (on/off, open/close, etc.)."""

    def can_handle(self, handler_input):
        return (is_intent_name("ControlDeviceIntent")(handler_input) and
                ENABLE_DEVICE_CONTROL)

    def handle(self, handler_input) -> Response:
        logger.info("ControlDevice Intent")
        
        try:
            # Extract slots
            device = get_slot_value(handler_input, "Device")
            action = get_slot_value(handler_input, "Action")
            room = get_slot_value(handler_input, "Room")
            
            logger.debug(f"Device: {device}, Action: {action}, Room: {room}")
            
            # Validate required slots
            if not device or not action:
                return ResponseBuilder.build(
                    handler_input,
                    speech=ResponseBuilder.get_text(handler_input, "ERROR_MISSING_SLOTS"),
                    should_end_session=False
                )
            
            # Send command to Jeedom
            jeedom = JeedomClient(handler_input)
            jeedom.get_question()
            
            # Build structured command data
            command_data = {
                "device": device,
                "action": action,
                "room": room or "default",
            }
            
            speak_output = jeedom.post_event(
                response=json.dumps(command_data),
                response_type=RESPONSE_DEVICE_CONTROL,
                device=device,
                action=action,
                room=room
            )
            
            # Provide fallback response if Jeedom doesn't return one
            if not speak_output or speak_output == "OK":
                template = ResponseBuilder.get_text(handler_input, "DEVICE_CONTROL_SUCCESS")
                speak_output = template.format(
                    action=action,
                    device=device,
                    room=f" dans {room}" if room else ""
                )
            
            JeedomLogger.log_to_jeedom(
                f"Device control: {action} {device} {room or ''}",
                level="info",
                context=command_data
            )
            
            return ResponseBuilder.build(handler_input, speech=speak_output)
            
        except Exception as e:
            logger.error(f"ControlDevice error: {e}", exc_info=True)
            JeedomLogger.log_error(handler_input, e, "ControlDeviceIntent")
            return ResponseBuilder.error_response(handler_input, "ERROR_DEVICE_CONTROL")


class GetStatusIntentHandler(AbstractRequestHandler):
    """Handler for status queries (temperature, state, etc.)."""

    def can_handle(self, handler_input):
        return is_intent_name("GetStatusIntent")(handler_input)

    def handle(self, handler_input) -> Response:
        logger.info("GetStatus Intent")
        
        try:
            device = get_slot_value(handler_input, "Device")
            room = get_slot_value(handler_input, "Room")
            
            logger.debug(f"Device: {device}, Room: {room}")
            
            # Need at least one identifier
            if not device and not room:
                return ResponseBuilder.build(
                    handler_input,
                    speech=ResponseBuilder.get_text(handler_input, "ERROR_NO_DEVICE"),
                    should_end_session=False
                )
            
            jeedom = JeedomClient(handler_input)
            jeedom.get_question()
            
            # Build query data
            query_data = {
                "device": device,
                "room": room,
            }
            
            speak_output = jeedom.post_event(
                response=json.dumps(query_data),
                response_type=RESPONSE_STATUS_QUERY,
                device=device,
                room=room
            )
            
            JeedomLogger.log_to_jeedom(
                f"Status query: {device or room}",
                level="info",
                context=query_data
            )
            
            return ResponseBuilder.build(handler_input, speech=speak_output)
            
        except Exception as e:
            logger.error(f"GetStatus error: {e}", exc_info=True)
            JeedomLogger.log_error(handler_input, e, "GetStatusIntent")
            return ResponseBuilder.error_response(handler_input, "ERROR_STATUS_QUERY")


class SetValueIntentHandler(AbstractRequestHandler):
    """Handler for setting values (temperature, brightness, volume, etc.)."""

    def can_handle(self, handler_input):
        return is_intent_name("SetValueIntent")(handler_input)

    def handle(self, handler_input) -> Response:
        logger.info("SetValue Intent")
        
        try:
            device = get_slot_value(handler_input, "Device")
            value = get_slot_value(handler_input, "Value")
            unit = get_slot_value(handler_input, "Unit")  # Optional: degrees, percent, etc.
            
            logger.debug(f"Device: {device}, Value: {value}, Unit: {unit}")
            
            # Validate required slots
            if not device or not value:
                return ResponseBuilder.build(
                    handler_input,
                    speech=ResponseBuilder.get_text(handler_input, "ERROR_MISSING_VALUE"),
                    should_end_session=False
                )
            
            # Parse numeric value
            try:
                numeric_value = float(value)
            except (ValueError, TypeError):
                return ResponseBuilder.build(
                    handler_input,
                    speech=ResponseBuilder.get_text(handler_input, "ERROR_INVALID_VALUE"),
                    should_end_session=False
                )
            
            jeedom = JeedomClient(handler_input)
            jeedom.get_question()
            
            # Build value command
            value_data = {
                "device": device,
                "value": numeric_value,
                "unit": unit or "default",
            }
            
            speak_output = jeedom.post_event(
                response=json.dumps(value_data),
                response_type=RESPONSE_SET_VALUE,
                device=device,
                value=numeric_value
            )
            
            # Provide fallback response
            if not speak_output or speak_output == "OK":
                template = ResponseBuilder.get_text(handler_input, "SET_VALUE_SUCCESS")
                speak_output = template.format(
                    device=device,
                    value=value,
                    unit=unit or ""
                )
            
            JeedomLogger.log_to_jeedom(
                f"Set value: {device} = {numeric_value} {unit or ''}",
                level="info",
                context=value_data
            )
            
            return ResponseBuilder.build(handler_input, speech=speak_output)
            
        except Exception as e:
            logger.error(f"SetValue error: {e}", exc_info=True)
            JeedomLogger.log_error(handler_input, e, "SetValueIntent")
            return ResponseBuilder.error_response(handler_input, "ERROR_SET_VALUE")