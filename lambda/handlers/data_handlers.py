# lambda/handlers/data_handlers.py
import logging
import json
import isodate
from datetime import datetime
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.utils import is_intent_name, get_slot_value, get_slot
from ask_sdk_model import Response
from ask_sdk_model.slu.entityresolution import StatusCode

from lambda.utils.jeedom_client0 import JeedomClient
from utils.response_builder import ResponseBuilder
from utils.jeedom_logger import JeedomLogger
from const import (
    RESPONSE_NUMERIC,
    RESPONSE_STRING,
    RESPONSE_SELECT,
    RESPONSE_DURATION,
    RESPONSE_DATE_TIME,
)

logger = logging.getLogger(__name__)


class NumericIntentHandler(AbstractRequestHandler):
    """Handler for numeric input."""

    def can_handle(self, handler_input):
        return is_intent_name("Number")(handler_input)

    def handle(self, handler_input) -> Response:
        logger.info("Number Intent")
        
        try:
            number = get_slot_value(handler_input, "Numbers")
            logger.debug(f"Number: {number}")
            
            if not number or number == "?":
                return ResponseBuilder.build(
                    handler_input,
                    speech=ResponseBuilder.get_text(handler_input, "ERROR_NO_NUMBER"),
                    should_end_session=False
                )
            
            jeedom = JeedomClient(handler_input)
            jeedom.get_question()
            
            speak_output = jeedom.post_event(number, RESPONSE_NUMERIC)
            JeedomLogger.log_intent(handler_input, "Number", success=True)
            
            return ResponseBuilder.build(handler_input, speech=speak_output)
            
        except Exception as e:
            logger.error(f"Number Intent error: {e}", exc_info=True)
            JeedomLogger.log_error(handler_input, e, "NumericIntent")
            return ResponseBuilder.error_response(handler_input, "ERROR_GENERAL")


class StringIntentHandler(AbstractRequestHandler):
    """Handler for string/text input."""

    def can_handle(self, handler_input):
        return is_intent_name("String")(handler_input)

    def handle(self, handler_input) -> Response:
        logger.info("String Intent")
        
        try:
            string = get_slot_value(handler_input, "Strings")
            logger.debug(f"String: {string}")
            
            if not string:
                return ResponseBuilder.build(
                    handler_input,
                    speech=ResponseBuilder.get_text(handler_input, "ERROR_NO_STRING"),
                    should_end_session=False
                )
            
            jeedom = JeedomClient(handler_input)
            jeedom.get_question()
            
            speak_output = jeedom.post_event(string, RESPONSE_STRING)
            JeedomLogger.log_intent(handler_input, "String", success=True)
            
            return ResponseBuilder.build(handler_input, speech=speak_output)
            
        except Exception as e:
            logger.error(f"String Intent error: {e}", exc_info=True)
            JeedomLogger.log_error(handler_input, e, "StringIntent")
            return ResponseBuilder.error_response(handler_input, "ERROR_GENERAL")


class SelectIntentHandler(AbstractRequestHandler):
    """Handler for selection from list."""

    def can_handle(self, handler_input):
        return is_intent_name("Select")(handler_input)

    def handle(self, handler_input) -> Response:
        logger.info("Select Intent")
        
        try:
            selection = self._get_resolved_value(handler_input, "Selections")
            logger.debug(f"Selection: {selection}")
            
            if not selection:
                return ResponseBuilder.build(
                    handler_input,
                    speech=ResponseBuilder.get_text(handler_input, "ERROR_NO_SELECTION"),
                    should_end_session=False
                )
            
            jeedom = JeedomClient(handler_input)
            jeedom.get_question()
            
            speak_output = jeedom.post_event(selection, RESPONSE_SELECT)
            
            # Provide fallback response
            if not speak_output or speak_output == "OK":
                template = ResponseBuilder.get_text(handler_input, "SELECTED")
                speak_output = template.format(selection=selection)
            
            JeedomLogger.log_intent(handler_input, "Select", success=True)
            
            return ResponseBuilder.build(handler_input, speech=speak_output)
            
        except Exception as e:
            logger.error(f"Select Intent error: {e}", exc_info=True)
            JeedomLogger.log_error(handler_input, e, "SelectIntent")
            return ResponseBuilder.error_response(handler_input, "ERROR_GENERAL")

    @staticmethod
    def _get_resolved_value(handler_input, slot_name: str) -> str:
        """Get resolved value from slot entity resolution."""
        try:
            slot = get_slot(handler_input, slot_name)
            if not slot:
                return ""
            
            # Try entity resolution first
            if slot.resolutions and slot.resolutions.resolutions_per_authority:
                for resolution in slot.resolutions.resolutions_per_authority:
                    if resolution.status.code == StatusCode.ER_SUCCESS_MATCH:
                        if resolution.values:
                            value = resolution.values[0].value
                            if value and value.name:
                                return value.name
            
            # Fallback to slot value
            return get_slot_value(handler_input, slot_name) or ""
            
        except Exception as e:
            logger.error(f"Error resolving slot value: {e}")
            return get_slot_value(handler_input, slot_name) or ""


class DurationIntentHandler(AbstractRequestHandler):
    """Handler for duration values (ISO 8601)."""

    def can_handle(self, handler_input):
        return is_intent_name("Duration")(handler_input)

    def handle(self, handler_input) -> Response:
        logger.info("Duration Intent")
        
        try:
            duration = get_slot_value(handler_input, "Durations")
            logger.debug(f"Duration: {duration}")
            
            if not duration:
                return ResponseBuilder.build(
                    handler_input,
                    speech=ResponseBuilder.get_text(handler_input, "ERROR_NO_DURATION"),
                    should_end_session=False
                )
            
            # Parse ISO 8601 duration
            try:
                duration_obj = isodate.parse_duration(duration)
                duration_seconds = int(duration_obj.total_seconds())
                logger.debug(f"Parsed duration: {duration_seconds} seconds")
            except Exception as parse_error:
                logger.error(f"Duration parse error: {parse_error}")
                return ResponseBuilder.build(
                    handler_input,
                    speech=ResponseBuilder.get_text(handler_input, "ERROR_INVALID_DURATION"),
                    should_end_session=False
                )
            
            jeedom = JeedomClient(handler_input)
            jeedom.get_question()
            
            speak_output = jeedom.post_event(str(duration_seconds), RESPONSE_DURATION)
            JeedomLogger.log_intent(handler_input, "Duration", success=True)
            
            return ResponseBuilder.build(handler_input, speech=speak_output)
            
        except Exception as e:
            logger.error(f"Duration Intent error: {e}", exc_info=True)
            JeedomLogger.log_error(handler_input, e, "DurationIntent")
            return ResponseBuilder.error_response(handler_input, "ERROR_GENERAL")


class DateTimeIntentHandler(AbstractRequestHandler):
    """Handler for date and time values."""

    def can_handle(self, handler_input):
        return is_intent_name("Date")(handler_input)

    def handle(self, handler_input) -> Response:
        logger.info("DateTime Intent")
        
        try:
            date = get_slot_value(handler_input, "Dates")
            time = get_slot_value(handler_input, "Times")
            
            logger.debug(f"Date: {date}, Time: {time}")
            
            if not date and not time:
                return ResponseBuilder.build(
                    handler_input,
                    speech=ResponseBuilder.get_text(handler_input, "ERROR_NO_DATETIME"),
                    should_end_session=False
                )
            
            # Parse date and time into structured format
            datetime_data = {
                **self._parse_date(date),
                **self._parse_time(time),
                "raw_date": date,
                "raw_time": time,
            }
            
            logger.debug(f"Parsed datetime: {datetime_data}")
            
            jeedom = JeedomClient(handler_input)
            jeedom.get_question()
            
            speak_output = jeedom.post_event(
                json.dumps(datetime_data),
                RESPONSE_DATE_TIME
            )
            
            JeedomLogger.log_intent(handler_input, "Date", success=True)
            
            return ResponseBuilder.build(handler_input, speech=speak_output)
            
        except Exception as e:
            logger.error(f"DateTime Intent error: {e}", exc_info=True)
            JeedomLogger.log_error(handler_input, e, "DateTimeIntent")
            return ResponseBuilder.error_response(handler_input, "ERROR_GENERAL")

    @staticmethod
    def _parse_date(date_str: str) -> dict:
        """
        Parse date string to components.
        Supports: YYYY-MM-DD, YYYY-MM, YYYY
        """
        result = {"day": None, "month": None, "year": None}
        
        if not date_str:
            return result
        
        try:
            parts = date_str.split("-")
            if len(parts) >= 1:
                result["year"] = int(parts[0])
            if len(parts) >= 2:
                result["month"] = int(parts[1])
            if len(parts) >= 3:
                result["day"] = int(parts[2])
        except (ValueError, IndexError) as e:
            logger.warning(f"Date parse error: {e}")
        
        return result

    @staticmethod
    def _parse_time(time_str: str) -> dict:
        """
        Parse time string to components.
        Supports: HH:MM:SS, HH:MM, special formats (10H, 30M, 15S)
        """
        result = {"hour": None, "minute": None, "second": None}
        
        if not time_str:
            return result
        
        try:
            time_lower = time_str.lower()
            
            # Handle special single-unit formats
            if time_lower.endswith("s"):
                result["second"] = int(time_lower[:-1])
            elif time_lower.endswith("m"):
                result["minute"] = int(time_lower[:-1])
            elif time_lower.endswith("h"):
                result["hour"] = int(time_lower[:-1])
            else:
                # Standard format HH:MM:SS
                parts = time_str.split(":")
                if len(parts) >= 1:
                    result["hour"] = int(parts[0])
                if len(parts) >= 2:
                    result["minute"] = int(parts[1])
                if len(parts) >= 3:
                    result["second"] = int(parts[2])
        except (ValueError, IndexError) as e:
            logger.warning(f"Time parse error: {e}")
        
        return result