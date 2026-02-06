# lambda/utils/response_builder.py

import logging
import json
from typing import Optional
from ask_sdk_model import Response
from ask_sdk_model.interfaces.alexa.presentation.apl import RenderDocumentDirective

logger = logging.getLogger(__name__)


def build_response(
    handler_input,
    speak_output: Optional[str],
    should_end_session: bool = True,
    reprompt: Optional[str] = None
) -> Response:
    """
    Build a response with consistent handling of empty speak_output.
    
    Args:
        handler_input: Alexa handler input
        speak_output: Text to speak (None or empty string for silent response)
        should_end_session: Whether to end the session
        reprompt: Optional reprompt text
        
    Returns:
        Response object
    """
    response_builder = handler_input.response_builder
    
    # Handle speak output
    if speak_output:
        response_builder.speak(speak_output)
        
        # Add reprompt if provided and session stays open
        if not should_end_session and reprompt:
            response_builder.ask(reprompt)
        elif not should_end_session:
            response_builder.ask(speak_output)
    
    # Set session end
    response_builder.set_should_end_session(should_end_session)
    
    return response_builder.response


def supports_apl(handler_input) -> bool:
    """
    Check if the device supports APL (Alexa Presentation Language).
    
    Args:
        handler_input: Alexa handler input
        
    Returns:
        True if APL is supported
    """
    try:
        supported_interfaces = (
            handler_input.request_envelope.context.system.device.supported_interfaces
        )
        return (
            hasattr(supported_interfaces, 'alexa_presentation_apl') and
            supported_interfaces.alexa_presentation_apl is not None
        )
    except (AttributeError, KeyError):
        return False


def load_apl_document(filename: str) -> Optional[dict]:
    """
    Load APL document from file.
    
    Args:
        filename: Name of APL document file in apl/ directory
        
    Returns:
        APL document dict or None
    """
    try:
        filepath = f"apl/{filename}"
        with open(filepath, 'r', encoding='utf-8') as f:
            document = json.load(f)
        logger.debug(f"Loaded APL document: {filename}")
        return document
    except FileNotFoundError:
        logger.warning(f"APL document not found: {filename}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse APL document {filename}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading APL document {filename}: {e}")
        return None


def add_apl_support(
    handler_input,
    response_builder,
    document_filename: str,
    datasources: dict
) -> None:
    """
    Add APL directive to response if supported.
    
    Args:
        handler_input: Alexa handler input
        response_builder: Response builder object
        document_filename: Name of APL document file
        datasources: Data sources for APL document
    """
    if not supports_apl(handler_input):
        logger.debug("APL not supported on this device")
        return
    
    document = load_apl_document(document_filename)
    if not document:
        logger.warning(f"Could not load APL document: {document_filename}")
        return
    
    try:
        response_builder.add_directive(
            RenderDocumentDirective(
                document=document,
                datasources=datasources
            )
        )
        logger.debug("APL directive added successfully")
    except Exception as e:
        logger.error(f"Failed to add APL directive: {e}")