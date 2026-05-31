/**
 * @interface PipelineRunRequest
 * @description Defines the structure for initiating a new material ingestion pipeline run.
 */
export interface PipelineRunRequest {
  material_id: string;
  config?: { [key: string]: any }; // Optional configuration parameters for the pipeline run
}

/**
 * @interface PipelineRunResponse
 * @description Defines the structure for the response after initiating a pipeline run.
 */
export interface PipelineRunResponse {
  pipeline_id: string; // Using string for UUID representation
  status: "initiated";
  message: string;
}

/**
 * @interface PipelineStatusResponse
 * @description Defines the structure for retrieving the status of an ongoing or completed pipeline run.
 */
export interface PipelineStatusResponse {
  pipeline_id: string; // Using string for UUID representation
  status: "pending" | "running" | "completed" | "failed" | "cancelled"; // Current status
  progress: number; // Progress percentage (0.0 to 100.0)
  report_url?: string; // URL to the detailed pipeline report, if available
  error_details?: string; // Details if the pipeline failed
}

/**
 * @interface PipelineReportResponse
 * @description Defines the structure for a detailed pipeline report.
 * This is a placeholder and would be expanded with actual report data.
 */
export interface PipelineReportResponse {
  pipeline_id: string;
  report_data: { [key: string]: any }; // Placeholder for detailed report content
  generated_at: string; // ISO 8601 date string
}

/**
 * @interface ErrorResponse
 * @description Standard error response structure for API errors.
 */
export interface ErrorResponse {
  detail: string;
  code?: string; // Optional error code for programmatic handling
}

/**
 * @interface HealthCheckResponse
 * @description Response for the API health check endpoint.
 */
export interface HealthCheckResponse {
  status: "ok" | "degraded" | "unavailable";
  message: string;
  timestamp: string; // ISO 8601 date string
  dependencies?: { [key: string]: "ok" | "degraded" | "unavailable" | string }; // Status of internal dependencies
}