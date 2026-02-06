# lambda/utils/lwa_token.py
import logging
import time
from typing import Optional, Dict
from ask_sdk_model.services.api_configuration import ApiConfiguration
from ask_sdk_model.services import ServiceException

from const import LWA_TOKEN_KEY, LWA_TOKEN_EXPIRY_KEY

logger = logging.getLogger(__name__)


class LWATokenManager:
    """Manages Login with Amazon (LWA) access tokens."""
    
    # Token buffer: refresh 5 minutes before expiry
    TOKEN_BUFFER_SECONDS = 300
    
    @staticmethod
    def get_access_token(handler_input) -> Optional[str]:
        """
        Get valid LWA access token, refreshing if necessary.
        
        Args:
            handler_input: Alexa handler input
            
        Returns:
            Valid access token or None if unavailable
        """
        try:
            # Check if we have a cached token
            persistent_attrs = handler_input.attributes_manager.persistent_attributes
            cached_token = persistent_attrs.get(LWA_TOKEN_KEY)
            token_expiry = persistent_attrs.get(LWA_TOKEN_EXPIRY_KEY, 0)
            
            current_time = time.time()
            
            # Return cached token if still valid
            if cached_token and (token_expiry - current_time) > LWATokenManager.TOKEN_BUFFER_SECONDS:
                logger.debug("Using cached LWA token")
                return cached_token
            
            # Get fresh token from Alexa API
            logger.info("Fetching new LWA token")
            api_access_token = handler_input.request_envelope.context.system.api_access_token
            
            if not api_access_token:
                logger.error("No API access token available")
                return None
            
            # Cache the token (Alexa tokens typically valid for 1 hour)
            # We'll assume 3600 seconds and let the buffer handle early refresh
            expiry_time = current_time + 3600
            
            persistent_attrs[LWA_TOKEN_KEY] = api_access_token
            persistent_attrs[LWA_TOKEN_EXPIRY_KEY] = expiry_time
            handler_input.attributes_manager.save_persistent_attributes()
            
            logger.debug(f"LWA token cached, expires in {3600} seconds")
            return api_access_token
            
        except Exception as e:
            logger.error(f"Failed to get LWA token: {e}", exc_info=True)
            return None
    
    @staticmethod
    def invalidate_token(handler_input):
        """Invalidate cached token."""
        try:
            persistent_attrs = handler_input.attributes_manager.persistent_attributes
            persistent_attrs.pop(LWA_TOKEN_KEY, None)
            persistent_attrs.pop(LWA_TOKEN_EXPIRY_KEY, None)
            handler_input.attributes_manager.save_persistent_attributes()
            logger.info("LWA token invalidated")
        except Exception as e:
            logger.error(f"Failed to invalidate token: {e}")