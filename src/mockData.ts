import { Alert, Mapping } from "./types";

export const MOCK_ALERTS: Alert[] = [
  {
    id: 1,
    project_id: "PRJ-2024-001",
    alert_type: "unmapped_spend",
    severity: "high",
    title: "Unmapped ERP Spend Detected",
    summary: "A transaction of $12,500 in ERP does not correspond to any field log entry for the specified period.",
    evidence: {
      erp_transaction_id: "TXN-99283",
      amount: 12500,
      vendor: "Concrete Solutions Inc.",
      date: "2024-02-15",
      description: "Foundation pour - Phase 2"
    },
    status: "open",
    created_at: "2024-02-20T10:00:00Z"
  },
  {
    id: 2,
    project_id: "PRJ-2024-001",
    alert_type: "labor_spike",
    severity: "med",
    title: "Labor Hours Spike",
    summary: "Field logs show a 40% increase in labor hours for 'Electrical Rough-in' compared to the previous week.",
    evidence: {
      task: "Electrical Rough-in",
      previous_week_hours: 120,
      current_week_hours: 168,
      variance: 0.4,
      affected_crews: ["Crew A", "Crew C"]
    },
    status: "open",
    created_at: "2024-02-21T14:30:00Z"
  },
  {
    id: 3,
    project_id: "PRJ-2024-001",
    alert_type: "keyword_risk",
    severity: "high",
    title: "Risk Keyword Detected in Field Notes",
    summary: "Field notes contain the word 'delay' and 'hazardous' which may indicate potential liability or schedule impact.",
    evidence: {
      log_id: "LOG-4421",
      author: "John Smith (Superintendent)",
      snippet: "...unexpected hazardous material found during excavation, causing a significant delay in trenching...",
      keywords_found: ["hazardous", "delay"]
    },
    status: "ack",
    created_at: "2024-02-22T09:15:00Z"
  },
  {
    id: 4,
    project_id: "PRJ-2024-001",
    alert_type: "unmapped_spend",
    severity: "low",
    title: "Minor Spend Discrepancy",
    summary: "Small difference ($45.00) between ERP invoice and Field log material receipt.",
    evidence: {
      erp_amount: 450.00,
      field_amount: 405.00,
      item: "Safety Signage",
      vendor: "SiteSafe Co."
    },
    status: "resolved",
    created_at: "2024-02-23T11:00:00Z"
  },
  {
    id: 5,
    project_id: "PRJ-2024-001",
    alert_type: "labor_spike",
    severity: "high",
    title: "Critical Overtime Alert",
    summary: "Overtime hours exceeded project budget limits for the third consecutive day.",
    evidence: {
      total_ot_hours: 45,
      budget_limit: 20,
      cost_impact: "$3,200",
      location: "Sector 7G"
    },
    status: "open",
    created_at: "2024-02-24T16:45:00Z"
  },
  {
    id: 6,
    project_id: "PRJ-2024-001",
    alert_type: "keyword_risk",
    severity: "med",
    title: "Safety Incident Mentioned",
    summary: "Field log mentions a 'near miss' during crane operations.",
    evidence: {
      log_id: "LOG-4500",
      timestamp: "2024-02-25T08:00:00Z",
      description: "Crane cable tension issue - no injuries reported but work paused for inspection."
    },
    status: "open",
    created_at: "2024-02-25T10:20:00Z"
  }
];

export const MOCK_MAPPINGS: Mapping[] = [
  {
    id: 1,
    project_id: "PRJ-2024-001",
    cost_code: "03-3000",
    task_name: "Cast-in-Place Concrete",
    confidence: 0.98,
    method: "human",
    status: "approved",
    updated_at: "2024-02-10T08:00:00Z"
  },
  {
    id: 2,
    project_id: "PRJ-2024-001",
    cost_code: "05-1200",
    task_name: "Structural Steel Framing",
    confidence: 0.92,
    method: "llm",
    status: "approved",
    updated_at: "2024-02-12T14:20:00Z"
  },
  {
    id: 3,
    project_id: "PRJ-2024-001",
    cost_code: "09-2900",
    task_name: "Gypsum Board",
    confidence: 0.85,
    method: "fuzzy",
    status: "suggested",
    updated_at: "2024-02-15T11:30:00Z"
  },
  {
    id: 4,
    project_id: "PRJ-2024-001",
    cost_code: "26-0500",
    task_name: "Common Work Results for Electrical",
    confidence: 0.78,
    method: "llm",
    status: "suggested",
    updated_at: "2024-02-18T16:00:00Z"
  },
  {
    id: 5,
    project_id: "PRJ-2024-001",
    cost_code: "31-2000",
    task_name: "Earth Moving",
    confidence: 0.95,
    method: "human",
    status: "approved",
    updated_at: "2024-02-19T09:00:00Z"
  },
  {
    id: 6,
    project_id: "PRJ-2024-001",
    cost_code: "01-1000",
    task_name: "General Requirements",
    confidence: 0.65,
    method: "fuzzy",
    status: "rejected",
    updated_at: "2024-02-20T13:45:00Z"
  },
  {
    id: 7,
    project_id: "PRJ-2024-001",
    cost_code: "07-2100",
    task_name: "Thermal Insulation",
    confidence: 0.88,
    method: "llm",
    status: "suggested",
    updated_at: "2024-02-21T10:10:00Z"
  },
  {
    id: 8,
    project_id: "PRJ-2024-001",
    cost_code: "08-1100",
    task_name: "Metal Doors and Frames",
    confidence: 0.91,
    method: "llm",
    status: "approved",
    updated_at: "2024-02-22T15:30:00Z"
  }
];
