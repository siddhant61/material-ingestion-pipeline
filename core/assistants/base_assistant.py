"""
Base Assistant Module

This module provides the foundation for all AI-powered assistants in the system.
It defines the BaseAssistant class that encapsulates the core functionality for
interacting with AI models, managing context, and implementing chain-of-thought reasoning.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Union, Callable
from abc import ABC, abstractmethod
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough

# Configure logging
logger = logging.getLogger(__name__)

class BaseAssistant(ABC):
    """
    Base class for all AI-powered assistants in the material ingestion pipeline.
    
    This class provides standardized interfaces for:
    - Interacting with AI models (primarily GPT-4o-mini)
    - Implementing chain-of-thought reasoning
    - Managing context and knowledge
    - Handling errors and fallbacks
    - Parsing and validating outputs
    """
    
    def __init__(self, 
                 model_name: str = "gpt-4o-mini", 
                 temperature: float = 0.2,
                 config: Dict[str, Any] = None):
        """
        Initialize the base assistant with the specified model and configuration.
        
        Args:
            model_name (str): The name of the LLM to use, defaults to gpt-4o-mini
            temperature (float): The temperature setting for the model
            config (Dict[str, Any]): Additional configuration parameters
        """
        self.model_name = model_name
        self.temperature = temperature
        self.config = config or {}
        self.assistant_name = self.__class__.__name__
        
        # Initialize the model
        self._init_model()
        
        # Initialize prompt templates
        self._init_prompts()
        
        logger.info(f"Initialized {self.assistant_name} with model {self.model_name}")
    
    def _init_model(self):
        """Initialize the AI model for this assistant."""
        try:
            self.model = ChatOpenAI(
                model=self.model_name,
                temperature=self.temperature
            )
            logger.info(f"Successfully initialized model {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize model {self.model_name}: {e}")
            # Fallback to a simpler model if available
            fallback_model = self.config.get("fallback_model", "gpt-3.5-turbo")
            logger.info(f"Falling back to {fallback_model}")
            self.model = ChatOpenAI(
                model=fallback_model,
                temperature=self.temperature
            )
            self.model_name = fallback_model
    
    @abstractmethod
    def _init_prompts(self):
        """
        Initialize prompt templates for this assistant.
        
        This method should be implemented by subclasses to define
        specific prompts used by the assistant.
        """
        pass
    
    def build_chain_of_thought_chain(self, 
                                    prompt_template: ChatPromptTemplate,
                                    output_parser: Any = None):
        """
        Build a chain-of-thought reasoning chain using LangChain.
        
        Args:
            prompt_template: The prompt template to use
            output_parser: Optional parser for the output
            
        Returns:
            A runnable chain that can be invoked with inputs
        """
        # If no parser is specified, use string parser
        if output_parser is None:
            output_parser = StrOutputParser()
        
        # Build the chain
        chain = (
            RunnablePassthrough()
            | RunnableLambda(self._preprocess_input)
            | prompt_template
            | self.model
            | output_parser
        )
        
        return chain
    
    def _preprocess_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preprocess the input data before sending to the model.
        
        This method ensures the input data is properly structured for the prompt templates.
        If the input contains a single 'input' key, it unpacks it to match expected variables.
        
        Args:
            input_data: The input data to preprocess
            
        Returns:
            The preprocessed input data
        """
        # If input_data contains only a single 'input' key with a dict value,
        # unpack it to match expected prompt variables
        if len(input_data) == 1 and 'input' in input_data and isinstance(input_data['input'], dict):
            return input_data['input']
        return input_data
    
    def _handle_model_error(self, e: Exception, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle errors that occur during model inference.
        
        Args:
            e: The exception that occurred
            input_data: The input data that caused the error
            
        Returns:
            A fallback response or error information
        """
        logger.error(f"Error in {self.assistant_name}: {e}")
        
        # Create a standardized error response
        error_response = {
            "status": "error",
            "error_type": str(type(e).__name__),
            "error_message": str(e),
            "assistant": self.assistant_name,
            "model": self.model_name,
            "input_summary": str(input_data)[:100] + "..." if len(str(input_data)) > 100 else str(input_data)
        }
        
        return error_response
    
    def run_with_error_handling(self, chain: Any, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a chain with standardized error handling.
        
        Args:
            chain: The chain to run
            input_data: The input data for the chain
            
        Returns:
            The chain output or error information
        """
        try:
            return {"status": "success", "result": chain.invoke(input_data)}
        except Exception as e:
            return self._handle_model_error(e, input_data) 