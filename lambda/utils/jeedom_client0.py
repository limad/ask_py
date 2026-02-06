# lambda/utils/jeedom_client.py

import logging
import json
import time
from typing import Optional, Union, Dict, Any
from urllib3 import PoolManager, HTTPResponse, Timeout
from urllib3.exceptions import HTTPError, MaxRetryError, TimeoutError

from ask_sdk_core.utils import get_account_linking_access_token
from schemas import QuestionState, QuestionStateError
from config import (
    JEEDOM_URL,
    TOKEN,
    VERIFY_SSL,
    MAX_RETRIES,
    RETRY_DELAY,
    CONNECT_TIMEOUT,
    READ_TIMEOUT,
    QUESTION_URL,
    RESPONSE_URL,
    LOG_URL,
    CODE_VERS,
    CAN_POST_LOGS,
)
import prompts

logger = logging.getLogger(__name__)


class JeedomClient:
    """Enhanced Jeedom API Client with retry logic and better error handling."""

    def __init__(self, handler_input=None):
        """
        Initialize Jeedom client.
        
        Args:
            handler_input: Alexa handler input object
        """
        self.handler_input = handler_input
        self.jee_state: Optional[Union[QuestionState, QuestionStateError]] = None
        self.token = self._fetch_token() if TOKEN == "" else TOKEN
        
        # Initialize HTTP pool
        self.http = PoolManager(
            cert_reqs="CERT_REQUIRED" if VERIFY_SSL else "CERT_NONE",
            timeout=Timeout(connect=CONNECT_TIMEOUT, read=READ_TIMEOUT),
            retries=False  # We handle retries manually
        )
        
        # Get language strings
        if handler_input:
            self.language_strings = handler_input.attributes_manager.request_attributes.get("_", {})
        else:
            self.language_strings = {}

    def _fetch_token(self) -> Optional[str]:
        """Fetch OAuth token from Alexa account linking."""
        if not self.handler_input:
            logger.warning("No handler_input provided, cannot fetch token")
            return None
            
        try:
            token = get_account_linking_access_token(self.handler_input)
            logger.debug("Successfully fetched OAuth token")
            return token
        except Exception as e:
            logger.error(f"Failed to fetch token: {e}")
            return None

    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for requests."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
            
        return headers

    def _build_url(self, *paths: str) -> str:
        """Build full URL from path components."""
        url = f"{JEEDOM_URL}/" + "/".join(p.lstrip("/") for p in paths)
        logger.debug(f"Built URL: {url}")
        return url

    def _handle_http_error(self, response: HTTPResponse) -> Optional[str]:
        """
        Handle HTTP errors and return error message if any.
        
        Returns:
            Error message string or None if no error
        """
        if response.status == 401:
            error_msg = self.language_strings.get(prompts.ERROR_401, "Authentication error")
            logger.error(f"401 Unauthorized - {error_msg}")
            self.post_log(f"ERROR 401: {error_msg}")
            return f"Error 401: {error_msg}"
            
        if response.status == 404:
            error_msg = self.language_strings.get(prompts.ERROR_404, "Resource not found")
            logger.error(f"404 Not Found - {error_msg}")
            self.post_log(f"ERROR 404: {error_msg}")
            return f"Error 404: {error_msg}"
            
        if response.status >= 400:
            error_msg = self.language_strings.get(prompts.ERROR_400, "Request error")
            logger.error(f"{response.status} Error - {error_msg}")
            self.post_log(f"ERROR {response.status}: {error_msg}")
            return f"Error {response.status}: {error_msg}"
            
        return None

    def _request_with_retry(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        body: Optional[Dict[str, Any]] = None
    ) -> Optional[HTTPResponse]:
        """
        Make HTTP request with automatic retry on failure.
        
        Args:
            method: HTTP method (GET, POST)
            url: Full URL
            headers: Request headers
            body: Request body (for POST)
            
        Returns:
            HTTPResponse or None on failure
        """
        for attempt in range(MAX_RETRIES):
            try:
                if method == "GET":
                    response = self.http.request("GET", url, headers=headers)
                else:  # POST
                    response = self.http.request(
                        "POST",
                        url,
                        headers=headers,
                        body=json.dumps(body).encode("utf-8") if body else None
                    )
                
                logger.debug(f"Response status: {response.status}")
                logger.debug(f"Response data: {response.data[:500]}")  # First 500 chars
                
                # Check for HTTP errors
                error_msg = self._handle_http_error(response)
                if error_msg:
                    self.jee_state = QuestionStateError(text=error_msg)
                    return None
                    
                return response
                
            except (HTTPError, MaxRetryError, TimeoutError) as e:
                logger.warning(f"Request attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
                
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))  # Exponential backoff
                else:
                    error_msg = f"Request failed after {MAX_RETRIES} attempts: {str(e)}"
                    logger.error(error_msg)
                    self.post_log(f"ERROR: {error_msg}")
                    self.jee_state = QuestionStateError(
                        text=self.language_strings.get(prompts.ERROR_NETWORK, "Network error")
                    )
                    return None
                    
            except Exception as e:
                logger.error(f"Unexpected error in request: {e}", exc_info=True)
                self.jee_state = QuestionStateError(
                    text=self.language_strings.get(prompts.ERROR_GENERAL, "An error occurred")
                )
                return None

    def get_question(self) -> bool:
        """
        Fetch current question/state from Jeedom.
        
        Returns:
            True if successful, False otherwise
        """
        url = self._build_url(QUESTION_URL)
        headers = self._get_headers()
        
        response = self._request_with_retry("GET", url, headers)
        if not response:
            return False
            
        try:
            # Decode response
            response_data = json.loads(response.data.decode("utf-8"))
            state_data = response_data.get("state")
            
            if not state_data:
                logger.error("No state data in response")
                self.jee_state = QuestionStateError(
                    text=self.language_strings.get(prompts.ERROR_CONFIG, "Configuration error")
                )
                return False
                
            # Parse state
            state = json.loads(state_data) if isinstance(state_data, str) else state_data
            
            self.jee_state = QuestionState(
                event_id=state.get("event"),
                suppress_confirmation=self._string_to_bool(state.get("suppress_confirmation")),
                text=state.get("text"),
                deviceSerialNumber=state.get("deviceSerialNumber"),
                textBrut=state.get("textBrut"),
            )
            
            logger.info(f"Question retrieved: event_id={self.jee_state.event_id}")
            return True
            
        except (json.JSONDecodeError, KeyError, AttributeError) as e:
            logger.error(f"Failed to parse question response: {e}", exc_info=True)
            self.jee_state = QuestionStateError(
                text=self.language_strings.get(prompts.ERROR_PARSE, "Failed to parse response")
            )
            return False

    def post_event(
        self,
        response: str,
        response_type: str,
        **kwargs
    ) -> Optional[str]:
        """
        Post event response to Jeedom.
        
        Args:
            response: Response value
            response_type: Type of response (YES, NO, NUMERIC, etc.)
            **kwargs: Additional parameters
            
        Returns:
            Text to speak to user or None
        """
        if not self.jee_state or isinstance(self.jee_state, QuestionStateError):
            logger.error("Cannot post event: no valid state")
            return self.language_strings.get(prompts.ERROR_CONFIG, "Error")
            
        # Build request body
        body = {
            "event_id": self.jee_state.event_id,
            "event_response": response,
            "event_response_type": response_type,
            "deviceSerialNumber": self.jee_state.deviceSerialNumber,
            "textBrut": self.jee_state.textBrut,
            "code_version": CODE_VERS,
        }
        body.update(kwargs)
        
        # Add person ID if available
        if self.handler_input and self.handler_input.request_envelope.context.system.person:
            person_id = self.handler_input.request_envelope.context.system.person.person_id
            body["event_person_id"] = person_id
            
        # Send request
        url = self._build_url(RESPONSE_URL)
        headers = self._get_headers()
        
        response = self._request_with_retry("POST", url, headers, body)
        if not response:
            return self.jee_state.text  # Fallback to question text
            
        # Determine response
        if not self.jee_state.suppress_confirmation:
            self.clear_state()
            return self.language_strings.get(prompts.OKAY, "OK")
            
        self.clear_state()
        return ""  # Silent confirmation

    def post_log(self, log_message: str, **kwargs) -> bool:
        """
        Post log message to Jeedom.
        
        Args:
            log_message: Log message to send
            **kwargs: Additional parameters
            
        Returns:
            True if successful
        """
        if not CAN_POST_LOGS:
            logger.debug("Log posting disabled")
            return False
            
        try:
            body = {
                "log": log_message,
                "code_version": CODE_VERS,
            }
            body.update(kwargs)
            
            url = self._build_url(LOG_URL)
            headers = self._get_headers()
            
            # Don't retry log posts to avoid loops
            response = self.http.request(
                "POST",
                url,
                headers=headers,
                body=json.dumps(body).encode("utf-8")
            )
            
            logger.debug(f"Log posted: {log_message[:100]}")
            return response.status < 400
            
        except Exception as e:
            logger.warning(f"Failed to post log: {e}")
            return False

    def clear_state(self):
        """Clear the current state."""
        logger.debug("Clearing Jeedom state")
        self.jee_state = None

    @staticmethod
    def _string_to_bool(value: Optional[str], default: bool = False) -> bool:
        """Convert string to boolean."""
        if isinstance(value, bool):
            return value
        if not isinstance(value, str):
            return default
            
        return value.lower() in ("true", "1", "yes", "oui")