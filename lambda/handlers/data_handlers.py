# lambda/handlers/data_handlers.py

import logging
import json
import isodate
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.utils import is_intent_name, get_slot_value, get_slot
from ask_sdk_model import Response
from ask_sdk_model.slu.entityresolution import StatusCode

from utils.jeedom_client import JeedomClient
from utils.response_builder import build_response
from const import (
    RESPONSE_NUMERIC,
    RESPONSE_STRING,
    RESPONSE_SELECT,
    RESPONSE_DURATION,
    RESPONSE_DATE_TIME,
)
import prompts

logger = logging.getLogger(__name__)


class NumericIntentHandler(AbstractRequestHandler):
    """Handler for numeric responses."""

    def can_handle(self, handler_input):
        return is_intent_name("Number")(handler_input)

    def handle(self, handler_input) -> Response:
        logger.info("Number Intent triggered")
        
        number = get_slot_value(handler_input, "Numbers")
        logger.debug(f"Number: {number}")
        
        if not number or number == "?":
            data = handler_input.attributes_manager.request_attributes.get("_", {})
            speak_output = data.get(prompts.ERROR_NO_NUMBER, "Je n'ai pas compris le nombre")
            return build_response(handler_input, speak_output, should_end_session=False)
        
        jeedom = JeedomClient(handler_input)
        jeedom.get_question()
        
        speak_output = jeedom.post_event(number, RESPONSE_NUMERIC)
        return build_response(handler_input, speak_output)


class StringIntentHandler(AbstractRequestHandler):
    """Handler for string/text responses."""

    def can_handle(self, handler_input):
        return is_intent_name("String")(handler_input)

    def handle(self, handler_input) -> Response:
        logger.info("String Intent triggered")
        
        string = get_slot_value(handler_input, "Strings")
        logger.debug(f"String: {string}")
        
        if not string:
            data = handler_input.attributes_manager.request_attributes.get("_", {})
            speak_output = data.get(prompts.ERROR_NO_STRING, "Je n'ai pas entendu de texte")
            return build_response(handler_input, speak_output, should_end_session=False)
        
        jeedom = JeedomClient(handler_input)
        jeedom.get_question()
        
        speak_output = jeedom.post_event(string, RESPONSE_STRING)
        return build_response(handler_input, speak_output)


class SelectIntentHandler(AbstractRequestHandler):
    """Handler for selection from list."""

    def can_handle(self, handler_input):
        return is_intent_name("Select")(handler_input)

    def handle(self, handler_input) -> Response:
        logger.info("Select Intent triggered")
        
        # Get resolved value from slot
        selection = self._get_resolved_value(handler_input, "Selections")
        logger.debug(f"Selection: {selection}")
        
        if not selection:
            data = handler_input.attributes_manager.request_attributes.get("_", {})
            speak_output = data.get(prompts.ERROR_NO_SELECTION, "Je n'ai pas compris votre choix")
            return build_response(handler_input, speak_output, should_end_session=False)
        
        jeedom = JeedomClient(handler_input)
        jeedom.get_question()
        
        speak_output = jeedom.post_event(selection, RESPONSE_SELECT)
        
        if not speak_output or speak_output == "OK":
            data = handler_input.attributes_manager.request_attributes.get("_", {})
            template = data.get(prompts.SELECTED, "{selection} sélectionné")
            speak_output = template.format(selection=selection)
        
        return build_response(handler_input, speak_output)

    @staticmethod
    def _get_resolved_value(handler_input, slot_name: str) -> str:
        """Get resolved value from slot entity resolution."""
        slot = get_slot(handler_input, slot_name)
        if slot and slot.resolutions and slot.resolutions.resolutions_per_authority:
            for resolution in slot.resolutions.resolutions_per_authority:
                if resolution.status.code == StatusCode.ER_SUCCESS_MATCH:
                    for value in resolution.values:
                        if value.value and value.value.name:
                            return value.value.name
        return get_slot_value(handler_input, slot_name)


class DurationIntentHandler(AbstractRequestHandler):
    """Handler for duration values."""

    def can_handle(self, handler_input):
        return is_intent_name("Duration")(handler_input)

    def handle(self, handler_input) -> Response:
        logger.info("Duration Intent triggered")
        
        duration = get_slot_value(handler_input, "Durations")
        logger.debug(f"Duration: {duration}")
        
        if not duration:
            data = handler_input.attributes_manager.request_attributes.get("_", {})
            speak_output = data.get(prompts.ERROR_NO_DURATION, "Je n'ai pas compris la durée")
            return build_response(handler_input, speak_output, should_end_session=False)
        
        try:
            # Parse ISO 8601 duration to seconds
            duration_seconds = isodate.parse_duration(duration).total_seconds()
        except Exception as e:
            logger.error(f"Failed to parse duration: {e}")
            data = handler_input.attributes_manager.request_attributes.get("_", {})
            speak_output = data.get(prompts.ERROR_INVALID_DURATION, "Durée invalide")
            return build_response(handler_input, speak_output, should_end_session=False)
        
        jeedom = JeedomClient(handler_input)
        jeedom.get_question()
        
        speak_output = jeedom.post_event(str(duration_seconds), RESPONSE_DURATION)
        return build_response(handler_input, speak_output)


class DateTimeIntentHandler(AbstractRequestHandler):
    """Handler for date and time values."""

    def can_handle(self, handler_input):
        return is_intent_name("Date")(handler_input)

    def handle(self, handler_input) -> Response:
        logger.info("DateTime Intent triggered")
        
        date = get_slot_value(handler_input, "Dates")
        time = get_slot_value(handler_input, "Times")
        
        logger.debug(f"Date: {date}, Time: {time}")
        
        if not date and not time:
            data = handler_input.attributes_manager.request_attributes.get("_", {})
            speak_output = data.get(prompts.ERROR_NO_DATETIME, "Je n'ai pas compris la date ou l'heure")
            return build_response(handler_input, speak_output, should_end_session=False)
        
        # Parse date and time
        date_data = self._parse_date(date)
        time_data = self._parse_time(time)
        
        datetime_data = {**date_data, **time_data}
        
        jeedom = JeedomClient(handler_input)
        jeedom.get_question()
        
        speak_output = jeedom.post_event(
            json.dumps(datetime_data),
            RESPONSE_DATE_TIME
        )
        
        return build_response(handler_input, speak_output)

    @staticmethod
    def _parse_date(date: str) -> dict:
        """Parse date string to components."""
        date_data = {
            "day": None,
            "month": None,
            "year": None,
        }
        
        if not date:
            return date_data
        
        parts = date.split("-")
        date_data["year"] = parts[0] if len(parts) >= 1 else None
        date_data["month"] = parts[1] if len(parts) >= 2 else None
        date_data["day"] = parts[2] if len(parts) >= 3 else None
        
        return date_data

    @staticmethod
    def _parse_time(time: str) -> dict:
        """Parse time string to components."""
        time_data = {
            "hour": None,
            "minute": None,
            "seconds": None,
        }
        
        if not time:
            return time_data
        
        # Handle special formats (e.g., "10H", "30M", "15S")
        time_lower = time.lower()
        if "s" in time_lower:
            time_data["seconds"] = time_lower.replace("s", "")
            return time_data
        if "m" in time_lower:
            time_data["minute"] = time_lower.replace("m", "")
            return time_data
        if "h" in time_lower:
            time_data["hour"] = time_lower.replace("h", "")
            return time_data
        
        # Parse standard format (HH:MM:SS)
        parts = time.split(":")
        time_data["hour"] = parts[0] if len(parts) >= 1 else None
        time_data["minute"] = parts[1] if len(parts) >= 2 else None
        time_data["seconds"] = parts[2] if len(parts) >= 3 else None
        
        return time_data