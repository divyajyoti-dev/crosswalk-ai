export type Severity = "high" | "med" | "low";
export type AlertStatus = "open" | "ack" | "resolved";
export type MappingStatus = "suggested" | "approved" | "rejected";
export type MappingMethod = "fuzzy" | "llm" | "human";

export interface Alert {
  id: number;
  project_id: string;
  alert_type: string;
  severity: Severity;
  title: string;
  summary: string;
  evidence: any;
  status: AlertStatus;
  created_at: string;
}

export interface Mapping {
  id: number;
  project_id: string;
  cost_code: string;
  task_name: string;
  confidence: number;
  method: MappingMethod;
  status: MappingStatus;
  updated_at: string;
}

export interface IngestResponse {
  ok: boolean;
  rows: number;
}

export interface RunResponse {
  ok: boolean;
  alerts_created: number;
  mappings_created: number;
}
