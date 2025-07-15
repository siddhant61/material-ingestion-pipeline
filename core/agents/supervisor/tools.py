"""
Supervisor Agent Tools

This module provides tools for the SupervisorAgent, enabling it to
perform special operations and interact with external systems.
"""

import logging
from typing import Dict, List, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

class SupervisorTools:
    """
    Tools component for the SupervisorAgent.
    
    Provides utilities and tools for:
    - Validating outputs against schemas
    - Comparing versions of content
    - Generating reports
    - Exporting data
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the SupervisorTools component.
        
        Args:
            config (Dict[str, Any], optional): Configuration options
        """
        self.config = config or {}
        logger.info("SupervisorTools initialized")
    
    def validate_against_schema(self, content: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate content against a JSON schema.
        
        Args:
            content (Dict[str, Any]): Content to validate
            schema (Dict[str, Any]): JSON schema
            
        Returns:
            Dict[str, Any]: Validation results
        """
        # This is a placeholder for actual schema validation
        # In a real implementation, this would use a library like jsonschema
        
        validation_result = {
            "valid": True,
            "errors": []
        }
        
        # Check required fields
        if "required" in schema:
            for field in schema["required"]:
                if field not in content:
                    validation_result["valid"] = False
                    validation_result["errors"].append({
                        "type": "missing_required_field",
                        "field": field,
                        "message": f"Required field '{field}' is missing"
                    })
        
        # Check field types if properties are defined
        if "properties" in schema:
            for field, field_schema in schema["properties"].items():
                if field in content:
                    # Type validation
                    if "type" in field_schema:
                        expected_type = field_schema["type"]
                        if expected_type == "object" and not isinstance(content[field], dict):
                            validation_result["valid"] = False
                            validation_result["errors"].append({
                                "type": "type_mismatch",
                                "field": field,
                                "expected": "object",
                                "actual": type(content[field]).__name__,
                                "message": f"Field '{field}' should be an object"
                            })
                        elif expected_type == "array" and not isinstance(content[field], list):
                            validation_result["valid"] = False
                            validation_result["errors"].append({
                                "type": "type_mismatch",
                                "field": field,
                                "expected": "array",
                                "actual": type(content[field]).__name__,
                                "message": f"Field '{field}' should be an array"
                            })
                        elif expected_type == "string" and not isinstance(content[field], str):
                            validation_result["valid"] = False
                            validation_result["errors"].append({
                                "type": "type_mismatch",
                                "field": field,
                                "expected": "string",
                                "actual": type(content[field]).__name__,
                                "message": f"Field '{field}' should be a string"
                            })
                        elif expected_type == "number" and not isinstance(content[field], (int, float)):
                            validation_result["valid"] = False
                            validation_result["errors"].append({
                                "type": "type_mismatch",
                                "field": field,
                                "expected": "number",
                                "actual": type(content[field]).__name__,
                                "message": f"Field '{field}' should be a number"
                            })
                        elif expected_type == "boolean" and not isinstance(content[field], bool):
                            validation_result["valid"] = False
                            validation_result["errors"].append({
                                "type": "type_mismatch",
                                "field": field,
                                "expected": "boolean",
                                "actual": type(content[field]).__name__,
                                "message": f"Field '{field}' should be a boolean"
                            })
        
        return validation_result
    
    def compare_versions(self, original: Dict[str, Any], revised: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare two versions of content and identify differences.
        
        Args:
            original (Dict[str, Any]): Original content
            revised (Dict[str, Any]): Revised content
            
        Returns:
            Dict[str, Any]: Comparison results
        """
        comparison = {
            "added_fields": [],
            "removed_fields": [],
            "modified_fields": [],
            "unchanged_fields": []
        }
        
        # Get all keys from both versions
        original_keys = set(original.keys())
        revised_keys = set(revised.keys())
        
        # Identify added and removed fields
        comparison["added_fields"] = list(revised_keys - original_keys)
        comparison["removed_fields"] = list(original_keys - revised_keys)
        
        # Check common fields for changes
        for key in original_keys & revised_keys:
            if original[key] == revised[key]:
                comparison["unchanged_fields"].append(key)
            else:
                comparison["modified_fields"].append({
                    "field": key,
                    "original_type": type(original[key]).__name__,
                    "revised_type": type(revised[key]).__name__,
                    "type_changed": type(original[key]) != type(revised[key])
                })
        
        return comparison
    
    def generate_report(self, data: Dict[str, Any], report_type: str) -> Dict[str, Any]:
        """
        Generate a report from data.
        
        Args:
            data (Dict[str, Any]): Data to generate report from
            report_type (str): Type of report to generate
            
        Returns:
            Dict[str, Any]: Generated report
        """
        # This is a placeholder for actual report generation
        # In a real implementation, this would use templates or more sophisticated formatting
        
        if report_type == "supervision_summary":
            return self._generate_supervision_summary(data)
        elif report_type == "quality_metrics":
            return self._generate_quality_metrics(data)
        elif report_type == "consistency_metrics":
            return self._generate_consistency_metrics(data)
        else:
            return {
                "error": f"Unsupported report type: {report_type}",
                "supported_types": ["supervision_summary", "quality_metrics", "consistency_metrics"]
            }
    
    def _generate_supervision_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a supervision summary report.
        
        Args:
            data (Dict[str, Any]): Supervision data
            
        Returns:
            Dict[str, Any]: Summary report
        """
        # Extract necessary data
        agent_outputs = data.get("agent_outputs", {})
        refined_outputs = data.get("refined_outputs", {})
        
        # Generate summary
        summary = {
            "title": "Supervision Summary Report",
            "timestamp": data.get("timestamp", "Unknown"),
            "agents_supervised": len(agent_outputs),
            "agents_refined": sum(1 for output in refined_outputs.values() if output.get("refinement_status") == "refined"),
            "total_refinements": sum(len(output.get("refinements", [])) for output in refined_outputs.values()),
            "agent_summaries": {}
        }
        
        # Add per-agent summaries
        for agent_name, output in refined_outputs.items():
            summary["agent_summaries"][agent_name] = {
                "refinement_status": output.get("refinement_status", "unknown"),
                "refinements_count": len(output.get("refinements", [])),
                "quality_score": output.get("supervision_metadata", {}).get("quality_check", {}).get("quality_score", 0),
                "consistency_score": output.get("supervision_metadata", {}).get("consistency_check", {}).get("consistency_score", 0)
            }
        
        return summary
    
    def _generate_quality_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a quality metrics report.
        
        Args:
            data (Dict[str, Any]): Quality data
            
        Returns:
            Dict[str, Any]: Quality metrics report
        """
        # Extract necessary data
        refined_outputs = data.get("refined_outputs", {})
        
        # Generate quality metrics
        metrics = {
            "title": "Quality Metrics Report",
            "timestamp": data.get("timestamp", "Unknown"),
            "average_quality_score": 0,
            "quality_issues_by_type": {},
            "agent_metrics": {}
        }
        
        # Calculate average quality score and count issues by type
        quality_scores = []
        issues_by_type = {}
        
        for agent_name, output in refined_outputs.items():
            quality_check = output.get("supervision_metadata", {}).get("quality_check", {})
            quality_score = quality_check.get("quality_score", 0)
            quality_scores.append(quality_score)
            
            # Add agent-specific metrics
            metrics["agent_metrics"][agent_name] = {
                "quality_score": quality_score,
                "issues_count": len(quality_check.get("issues", []))
            }
            
            # Count issues by type
            for issue in quality_check.get("issues", []):
                issue_type = issue.get("type", "unknown")
                if issue_type not in issues_by_type:
                    issues_by_type[issue_type] = 0
                issues_by_type[issue_type] += 1
        
        # Calculate average quality score
        if quality_scores:
            metrics["average_quality_score"] = sum(quality_scores) / len(quality_scores)
        
        metrics["quality_issues_by_type"] = issues_by_type
        
        return metrics
    
    def _generate_consistency_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a consistency metrics report.
        
        Args:
            data (Dict[str, Any]): Consistency data
            
        Returns:
            Dict[str, Any]: Consistency metrics report
        """
        # Extract necessary data
        refined_outputs = data.get("refined_outputs", {})
        
        # Generate consistency metrics
        metrics = {
            "title": "Consistency Metrics Report",
            "timestamp": data.get("timestamp", "Unknown"),
            "average_consistency_score": 0,
            "consistency_issues_by_type": {},
            "agent_metrics": {}
        }
        
        # Calculate average consistency score and count issues by type
        consistency_scores = []
        issues_by_type = {}
        
        for agent_name, output in refined_outputs.items():
            consistency_check = output.get("supervision_metadata", {}).get("consistency_check", {})
            consistency_score = consistency_check.get("consistency_score", 0)
            consistency_scores.append(consistency_score)
            
            # Add agent-specific metrics
            metrics["agent_metrics"][agent_name] = {
                "consistency_score": consistency_score,
                "issues_count": len(consistency_check.get("issues", []))
            }
            
            # Count issues by type
            for issue in consistency_check.get("issues", []):
                issue_type = issue.get("type", "unknown")
                if issue_type not in issues_by_type:
                    issues_by_type[issue_type] = 0
                issues_by_type[issue_type] += 1
        
        # Calculate average consistency score
        if consistency_scores:
            metrics["average_consistency_score"] = sum(consistency_scores) / len(consistency_scores)
        
        metrics["consistency_issues_by_type"] = issues_by_type
        
        return metrics 