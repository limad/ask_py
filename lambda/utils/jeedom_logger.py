# lambda/utils/jeedom_logger.py
import logging
import requests
from datetime import datetime
from typing import Optional
from config import LOG_URL, VERIFY_SSL, CONNECT_TIMEOUT, READ_TIMEOUT

logger = logging.getLogger(__name__)


class JeedomLogger:
    """Send logs to Jeedom server."""
    
    @staticmethod
    def log_to_jeedom(
        message: str,
        level: str = "info",
        user_id: Optional[str] = None,
        context: Optional[dict] = None
    ) -> bool:
        """
        Send log message to Jeedom.
        
        Args:
            message: Log message
            level: Log level (info, warning, error, debug)
            user_id: Alexa user ID (optional)
            context: Additional context data (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            payload = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": level,
                "message": message,
            }
            
            if user_id:
                payload["user_id"] = user_id
            
            if context:
                payload["context"] = context
            
            response = requests.post(
                LOG_URL,
                json=payload,
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
                verify=VERIFY_SSL
            )
            
            if response.status_code == 200:
                logger.debug(f"Log sent to Jeedom: {message}")
                return True
            else:
                logger.warning(f"Jeedom log failed with status {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send log to Jeedom: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending log to Jeedom: {e}")
            return False
    
    @staticmethod
    def log_intent(handler_input, intent_name: str, success: bool = True):
        """Log intent execution to Jeedom."""
        try:
            user_id = handler_input.request_envelope.session.user.user_id
            session_id = handler_input.request_envelope.session.session_id
            
            message = f"Intent: {intent_name} - {'Success' if success else 'Failed'}"
            context = {
                "intent": intent_name,
                "session_id": session_id,
                "success": success
            }
            
            JeedomLogger.log_to_jeedom(
                message=message,
                level="info" if success else "warning",
                user_id=user_id,
                context=context
            )
        except Exception as e:
            logger.error(f"Failed to log intent: {e}")
    
    @staticmethod
    def log_error(handler_input, error: Exception, context_info: str = ""):
        """Log error to Jeedom."""
        try:
            user_id = getattr(handler_input.request_envelope.session.user, 'user_id', 'unknown')
            
            message = f"Error: {context_info} - {str(error)}"
            context = {
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context_info
            }
            
            JeedomLogger.log_to_jeedom(
                message=message,
                level="error",
                user_id=user_id,
                context=context
            )
        except Exception as e:
            logger.error(f"Failed to log error: {e}")