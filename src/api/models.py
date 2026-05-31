import uuid
from typing import Dict, Optional, Literal, Annotated, Union
from pydantic import BaseModel, Field, BeforeValidator
from datetime import datetime, timezone

# Helper to convert UUID to string for Pydantic validation/serialization
def validate_uuid_str(v: Union[str, uuid.UUID]) -> str:
    if isinstance(v, uuid.UUID):
        return str(v)
    if isinstance(v, str):
        try:
            uuid.UUID(v) # Validate it's a valid UUID string
            return v
        except ValueError:
            raise ValueError("Invalid UUID string format")
    raise TypeError("UUID must be a string or uuid.UUID object")

UUIDStr = Annotated[str, BeforeValidator(validate_uuid_str)]

class PipelineRunRequest(BaseModel):
    material_id: str = Field(..., description="Unique identifier for the material to be ingested")
    config: Dict = Field(default_factory=dict, description="Optional configuration parameters for the pipeline run")

class PipelineRunResponse(BaseModel):
    pipeline_id: UUIDStr = Field(..., description="Unique ID assigned to the initiated pipeline run")
    status: Literal["initiated"] = Field("initiated", description="Current status of the pipeline run")
    message: str = Field("Pipeline run initiated successfully", description="Descriptive message")

class PipelineStatusResponse(BaseModel):
    pipeline_id: UUIDStr = Field(..., description="Unique ID of the pipeline run")
    status: Literal["pending", "running", "completed", "failed", "cancelled"] = Field(..., description="Current status (e.g., 'pending', 'running', 'completed', 'failed')")
    progress: float = Field(0.0, ge=0.0, le=100.0, description="Progress percentage of the pipeline run")
    report_url: Optional[str] = Field(None, description="URL to the detailed pipeline report, if available")
    error_details: Optional[str] = Field(None, description="Details if the pipeline failed")

class PipelineReportResponse(BaseModel):
    pipeline_id: UUIDStr = Field(..., description="Unique ID of the pipeline run")
    report_data: Dict = Field(..., description="Detailed report content")
    generated_at: datetime = Field(..., description="ISO 8601 date string")

class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Optional error code for programmatic handling")

class HealthCheckResponse(BaseModel):
    status: Literal["ok", "degraded", "unavailable"] = Field(..., description="Overall health status")
    message: str = Field(..., description="Descriptive health message")
    timestamp: datetime = Field(..., description="ISO 8601 date string of when the health check was performed")
    dependencies: Optional[Dict[str, str]] = Field(None, description="Status of key dependencies")
