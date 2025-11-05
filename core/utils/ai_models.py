"""
AI Models Factory

This module provides a factory for creating AI model instances to be used by various components
in the educational content pipeline.
"""

import logging
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

class AIModelFactory:
    """
    Factory class for creating AI model instances.
    """
    
    @staticmethod
    def create_model(model_name: Optional[str] = None, config: Optional[Dict[str, Any]] = None) -> Any:
        """
        Create an AI model instance with the specified name and configuration.
        
        Args:
            model_name (str, optional): Name of the model to create. 
                                       If not provided, uses the default from settings.
                                       This parameter is now optional for convenience but
                                       existing code passing a model_name will continue to work.
            config (Dict[str, Any], optional): Additional configuration for the model.
                                              Overrides settings values if provided.
            
        Returns:
            Any: An initialized model instance
            
        Note:
            The model_name parameter is now optional (changed from required).
            This is backward compatible as existing callers can still pass it explicitly.
        """
        if config is None:
            config = {}
        
        # Use settings as defaults, allow config to override
        # Use explicit None checks to avoid masking falsy but valid values
        if model_name is None:
            model_name = config.get("model_name")
        if model_name is None:
            model_name = settings.ai_model_name
            
        temperature = config.get("temperature", settings.ai_model_temperature)
        fallback_model = config.get("fallback_model", settings.ai_fallback_model)
        
        try:
            logger.info(f"Creating model instance: {model_name}")
            
            # Create the OpenAI model
            model = ChatOpenAI(
                model=model_name,
                temperature=temperature
            )
            
            # Wrap the model instance to provide a consistent interface
            return AIModelWrapper(model)
            
        except Exception as e:
            logger.error(f"Error creating model {model_name}: {str(e)}")
            
            # Try to use a fallback model
            logger.info(f"Falling back to {fallback_model}")
            
            try:
                model = ChatOpenAI(
                    model=fallback_model,
                    temperature=temperature
                )
                return AIModelWrapper(model)
            except Exception as fallback_error:
                logger.error(f"Error creating fallback model: {str(fallback_error)}")
                raise RuntimeError(f"Failed to create model {model_name} and fallback failed: {str(e)}")

class AIModelWrapper:
    """
    Wrapper around AI models to provide a consistent interface.
    """
    
    def __init__(self, model):
        """
        Initialize the model wrapper.
        
        Args:
            model: The underlying model instance
        """
        self.model = model
        
    def generate(self, prompt: Dict[str, str]) -> str:
        """
        Generate text from a prompt.
        
        Args:
            prompt (Dict[str, str]): Prompt with system and user messages
            
        Returns:
            str: Generated text
        """
        from langchain_core.messages import SystemMessage, HumanMessage
        
        messages = []
        
        if "system" in prompt:
            messages.append(SystemMessage(content=prompt["system"]))
            
        if "user" in prompt:
            messages.append(HumanMessage(content=prompt["user"]))
            
        response = self.model.invoke(messages)
        return response.content 