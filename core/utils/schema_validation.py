"""
Schema Validation Utilities

This module provides utilities for validating data against JSON schemas,
ensuring consistent data formats across the pipeline.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import jsonschema
from jsonschema import ValidationError

# Configure logging
logger = logging.getLogger(__name__)

def validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate data against a JSON schema.
    
    Args:
        data (Dict[str, Any]): The data to validate
        schema (Dict[str, Any]): The JSON schema to validate against
        
    Returns:
        List[str]: List of validation errors, empty if validation succeeds
    """
    validator = jsonschema.Draft7Validator(schema)
    errors = list(validator.iter_errors(data))
    
    if errors:
        error_messages = []
        for error in errors:
            path = ".".join(str(p) for p in error.path) if error.path else "root"
            error_messages.append(f"At {path}: {error.message}")
        
        logger.warning(f"Schema validation failed with {len(errors)} errors")
        for msg in error_messages:
            logger.warning(f"  - {msg}")
        
        return error_messages
    
    logger.debug("Schema validation succeeded")
    return []

def validate_and_log(data: Dict[str, Any], schema: Dict[str, Any], name: str) -> bool:
    """
    Validate data against a schema and log results.
    
    Args:
        data (Dict[str, Any]): The data to validate
        schema (Dict[str, Any]): The JSON schema to validate against
        name (str): Name of the validation for logging
        
    Returns:
        bool: True if validation succeeds, False otherwise
    """
    logger.info(f"Validating {name} against schema")
    
    try:
        errors = validate_against_schema(data, schema)
        if errors:
            logger.error(f"Validation failed for {name}:")
            for error in errors:
                logger.error(f"  - {error}")
            return False
        
        logger.info(f"Validation succeeded for {name}")
        return True
        
    except Exception as e:
        logger.error(f"Error during schema validation for {name}: {e}")
        return False

def create_standard_header(agent_name: str, 
                          version: str = "1.0.0", 
                          agent_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a standardized header for agent outputs.
    
    Args:
        agent_name (str): Name of the agent
        version (str): Version of the agent
        agent_id (Optional[str]): Unique ID for the agent instance
        
    Returns:
        Dict[str, Any]: Standardized header
    """
    return {
        "agent_name": agent_name,
        "agent_version": version,
        "agent_id": agent_id,
        "timestamp": datetime.now().isoformat(),
        "schema_version": "1.0.0"
    }

def load_schema_from_file(schema_file: str) -> Dict[str, Any]:
    """
    Load a JSON schema from a file.
    
    Args:
        schema_file (str): Path to the schema file
        
    Returns:
        Dict[str, Any]: The loaded schema
    """
    try:
        with open(schema_file, 'r') as f:
            schema = json.load(f)
        return schema
    except Exception as e:
        logger.error(f"Failed to load schema from {schema_file}: {e}")
        raise

# Common schema definitions that can be reused
AGENT_OUTPUT_SCHEMA_BASE = {
    "type": "object",
    "required": ["status", "agent_info", "output_type"],
    "properties": {
        "status": {
            "type": "string",
            "enum": ["success", "error", "partial_success"]
        },
        "agent_info": {
            "type": "object",
            "required": ["agent_name", "agent_version", "timestamp"],
            "properties": {
                "agent_name": {"type": "string"},
                "agent_version": {"type": "string"},
                "agent_id": {"type": "string"},
                "timestamp": {"type": "string", "format": "date-time"}
            }
        },
        "output_type": {"type": "string"},
        "error": {
            "type": "object",
            "properties": {
                "error_type": {"type": "string"},
                "error_message": {"type": "string"},
                "details": {"type": "object"}
            }
        }
    }
} 