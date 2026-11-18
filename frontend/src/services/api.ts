
const API_BASE = '/api/v1'

// --------------------------------------------------
// 1. Pipeline execution data types
// --------------------------------------------------

export interface PipelineRun {
  run_id: number
  started_at: string
  finished_at: string | null
  status: string
  duration_seconds: number | null
  error_message: string | null
}

export interface PipelineRunsResponse {
  total_returned: number
  runs: PipelineRun[]
}

// --------------------------------------------------
// 2. Individual pipeline stage data types
// --------------------------------------------------

export interface PipelineStage {
  stage_id: number
  stage_name: string
  started_at: string
  finished_at: string | null
  status: string
  duration_seconds: number | null
  error_message: string | null
}

export interface PipelineRunDetails {
  run: PipelineRun
  stages: PipelineStage[]
}

// --------------------------------------------------
// 3. Fetch pipeline execution history
// --------------------------------------------------

export async function fetchPipelineRuns(): Promise<PipelineRunsResponse> {
  const response = await fetch(`${API_BASE}/pipeline/runs`)

  if (!response.ok) {
    throw new Error(
      `Failed to fetch pipeline runs: HTTP ${response.status}`
    )
  }

  return response.json() as Promise<PipelineRunsResponse>
}

// --------------------------------------------------
// 4. Fetch details for an individual pipeline run
// --------------------------------------------------

export async function fetchPipelineRunDetails(
  runId: number
): Promise<PipelineRunDetails> {
  if (!Number.isInteger(runId) || runId <= 0) {
    throw new Error('Invalid pipeline run ID')
  }

  const response = await fetch(
    `${API_BASE}/pipeline/runs/${runId}`
  )

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error(`Pipeline run #${runId} was not found`)
    }

    throw new Error(
      `Failed to fetch pipeline run #${runId}: HTTP ${response.status}`
    )
  }

  return response.json() as Promise<PipelineRunDetails>
}

export interface DataQualityMetric {
  dataset_name: string
  source_count: number
  accepted_count: number
  rejected_count: number
  rejection_rate_pct: number
}

export interface PipelineQualityResponse {
  run_id: number
  total_datasets: number
  quality_metrics: DataQualityMetric[]
}

export async function fetchPipelineQuality(
  runId: number
): Promise<PipelineQualityResponse> {
  const response = await fetch(
    `${API_BASE}/pipeline/runs/${runId}/quality`
  )

  if (!response.ok) {
    throw new Error(
      `Failed to fetch quality metrics for run ${runId}: ${response.status}`
    )
  }

  return response.json()
}
