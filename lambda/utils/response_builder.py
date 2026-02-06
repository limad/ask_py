# lambda/utils/response_builder.py
import logging
import json
from typing import Optional, Dict, Any
from ask_sdk_model import Response
from ask_sdk_model.ui import SimpleCard
from ask_sdk_model.interfaces.alexa.presentation.apl import RenderDocumentDirective

logger = logging.getLogger(__name__)


class ResponseBuilder:
    """Utility class for building Alexa responses with consistent patterns."""
    
    @staticmethod
    def get_text(handler_input, key: str, default: str = "") -> str:
        """
        Get localized text from language strings.
        
        Args:
            handler_input: Alexa handler input
            key: Language string key
            default: Default text if key not found
            
        Returns:
            Localized text string
        """
        try:
            data = handler_input.attributes_manager.request_attributes.get("_", {})
            return data.get(key, default)
        except Exception as e:
            logger.error(f"Error getting text for key '{key}': {e}")
            return default
    
    @staticmethod
    def build(
        handler_input,
        speech: str,
        reprompt: Optional[str] = None,
        card_title: Optional[str] = None,
        card_text: Optional[str] = None,
        should_end_session: bool = True,
        apl_document: Optional[str] = None,
        apl_data: Optional[Dict[str, Any]] = None
    ) -> Response:
        """
        Build a complete Alexa response.
        
        Args:
            handler_input: Alexa handler input
            speech: Text to speak
            reprompt: Reprompt text (keeps session open)
            card_title: Card title
            card_text: Card text
            should_end_session: Whether to end session
            apl_document: APL document filename
            apl_data: Data for APL document
            
        Returns:
            Alexa Response object
        """
        response_builder = handler_input.response_builder
        
        # Add speech
        response_builder.speak(speech)
        
        # Add reprompt if provided
        if reprompt:
            response_builder.ask(reprompt)
            should_end_session = False
        
        # Add card if provided
        if card_title and card_text:
            response_builder.set_card(SimpleCard(title=card_title, content=card_text))
        
        # Add APL if supported and requested
        if apl_document and ResponseBuilder.supports_apl(handler_input):
            try:
                apl_directive = ResponseBuilder._build_apl_directive(
                    apl_document, 
                    apl_data or {}
                )
                if apl_directive:
                    response_builder.add_directive(apl_directive)
            except Exception as e:
                logger.warning(f"Failed to add APL: {e}")
        
        # Set session state
        response_builder.set_should_end_session(should_end_session)
        
        return response_builder.response
    
    @staticmethod
    def error_response(
        handler_input,
        error_key: str = "ERROR_GENERAL",
        custom_message: Optional[str] = None
    ) -> Response:
        """
        Build an error response.
        
        Args:
            handler_input: Alexa handler input
            error_key: Error message key
            custom_message: Custom error message (overrides key)
            
        Returns:
            Alexa Response object
        """
        if custom_message:
            speak_output = custom_message
        else:
            speak_output = ResponseBuilder.get_text(
                handler_input,
                error_key,
                "Une erreur s'est produite"
            )
        
        return ResponseBuilder.build(
            handler_input,
            speech=speak_output,
            should_end_session=True
        )
    
    @staticmethod
    def supports_apl(handler_input) -> bool:
        """
        Check if device supports APL.
        
        Args:
            handler_input: Alexa handler input
            
        Returns:
            True if APL is supported
        """
        try:
            supported_interfaces = (
                handler_input.request_envelope.context.system.device
                .supported_interfaces
            )
            return hasattr(supported_interfaces, 'alexa_presentation_apl')
        except Exception as e:
            logger.debug(f"APL support check failed: {e}")
            return False
    
    @staticmethod
    def _build_apl_directive(
        document_name: str,
        data: Dict[str, Any]
    ) -> Optional[RenderDocumentDirective]:
        """
        Build APL directive from document file.
        
        Args:
            document_name: APL document filename
            data: Data for APL document
            
        Returns:
            RenderDocumentDirective or None
        """
        try:
            with open(f"apl_documents/{document_name}", encoding="utf-8") as f:
                apl_document = json.load(f)
            
            datasources = {
                "data": {
                    "type": "object",
                    "properties": data
                }
            }
            
            return RenderDocumentDirective(
                document=apl_document,
                datasources=datasources
            )
            
        except FileNotFoundError:
            logger.error(f"APL document not found: {document_name}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Invalid APL document JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Error building APL directive: {e}")
            return None