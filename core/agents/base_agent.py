"""
Base Agent Module

This module provides the foundation for all agents in the system.
It defines the BaseAgent class that encapsulates the core functionality
for orchestration, memory management, tool usage, and AI assistant integration.

The BaseAgent follows a modular design pattern, separating concerns into:
- Orchestration: Workflow management
- Memory: State tracking and persistence
- Models: AI model interactions
- Reasoning: Decision making and planning
- Tools: Specialized functionality
"""

import os
import sys
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Type
from abc import ABC, abstractmethod
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """
    Base class for all agents in the material ingestion pipeline.
    
    This standardized base agent provides a consistent structure for all agents
    in the ecosystem, following a modular architecture with:
    - Orchestration: Workflow management
    - Memory: State tracking and persistence
    - Models: AI model interactions
    - Reasoning: Decision making and planning
    - Tools: Specialized functionality
    
    Each agent should implement the required abstract methods to provide
    its specific functionality while maintaining this standard structure.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the agent with the specified configuration.
        
        Args:
            config (Dict[str, Any], optional): Configuration dictionary
        """
        # Initialize configuration with defaults
        self.config = config or {}
        
        # Set basic agent properties
        self.agent_id = str(uuid.uuid4())
        self.agent_name = self.__class__.__name__
        self.version = self.config.get("version", "1.0.0")
        self.created_at = datetime.now().isoformat()
        
        # Initialize components
        self._init_models()
        self._init_memory()
        self._init_orchestration()
        self._init_reasoning()
        self._init_tools()
        
        logger.info(f"Initialized {self.agent_name} v{self.version} with ID: {self.agent_id}")
    
    @abstractmethod
    def _init_models(self):
        """
        Initialize the model component for this agent.
        
        This method should be implemented by subclasses to define
        how AI models are initialized and configured.
        """
        pass
    
    @abstractmethod
    def _init_memory(self):
        """
        Initialize the memory component for this agent.
        
        This method should be implemented by subclasses to define
        how state tracking and persistence is handled.
        """
        pass
    
    @abstractmethod
    def _init_orchestration(self):
        """
        Initialize the orchestration component for this agent.
        
        This method should be implemented by subclasses to define
        how workflow management is handled.
        """
        pass
    
    @abstractmethod
    def _init_reasoning(self):
        """
        Initialize the reasoning component for this agent.
        
        This method should be implemented by subclasses to define
        how decision making and planning is implemented.
        """
        pass
    
    @abstractmethod
    def _init_tools(self):
        """
        Initialize tools for this agent.
        
        This method should be implemented by subclasses to define
        the specialized tools used by this agent.
        """
        pass
    
    @abstractmethod
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's main functionality.
        
        Args:
            input_data: Input data for the agent
            
        Returns:
            Output data from the agent
        """
        pass
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate the input data for the agent.
        
        Args:
            input_data: Input data to validate
            
        Returns:
            True if the input is valid, False otherwise
        """
        # Base implementation just checks if input_data is not None
        # Subclasses should implement more specific validation
        return input_data is not None
    
    def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """
        Validate the output data from the agent.
        
        Args:
            output_data: Output data to validate
            
        Returns:
            True if the output is valid, False otherwise
        """
        # Base implementation just checks if output_data is not None
        # Subclasses should implement more specific validation
        return output_data is not None
    
    def handle_error(self, error: Exception, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle errors that occur during agent execution.
        
        Args:
            error: The exception that occurred
            input_data: Input data that caused the error
            
        Returns:
            Error information and fallback response if available
        """
        logger.error(f"Error in {self.agent_name}: {error}")
        
        # Create a standardized error response
        error_response = {
            "status": "error",
            "error_type": str(type(error).__name__),
            "error_message": str(error),
            "agent": self.agent_name,
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat(),
            "input_summary": str(input_data)[:100] + "..." if len(str(input_data)) > 100 else str(input_data)
        }
        
        return error_response
    
    def run_with_error_handling(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the agent with standardized error handling.
        
        Args:
            input_data: Input data for the agent
            
        Returns:
            Output data from the agent or error information
        """
        # Record execution start time
        start_time = datetime.now()
        
        try:
            # Validate input
            if not self.validate_input(input_data):
                raise ValueError(f"Invalid input for {self.agent_name}")
            
            # Run the agent
            output = self.run(input_data)
            
            # Validate output
            if not self.validate_output(output):
                raise ValueError(f"Invalid output from {self.agent_name}")
            
            # Add execution metadata
            execution_time = (datetime.now() - start_time).total_seconds()
            output["execution_metadata"] = {
                "agent": self.agent_name,
                "agent_id": self.agent_id,
                "version": self.version,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            }
            
            return output
        
        except Exception as e:
            return self.handle_error(e, input_data) 