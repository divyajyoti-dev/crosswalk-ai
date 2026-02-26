import { Alert, Mapping, IngestResponse, RunResponse } from "./types";
import { MOCK_ALERTS, MOCK_MAPPINGS } from "./mockData";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export class ApiService {
  private static isMockMode = false;

  static setMockMode(enabled: boolean) {
    this.isMockMode = enabled;
  }

  static getIsMockMode() {
    return this.isMockMode;
  }

  private static async request<T>(path: string, options?: RequestInit): Promise<T> {
    if (this.isMockMode) {
      throw new Error("Mock mode active");
    }

    try {
      const response = await fetch(`${API_BASE_URL}${path}`, options);
      if (!response.ok) {
        throw new Error(`API Error: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.warn(`API request to ${path} failed, falling back to mock:`, error);
      this.isMockMode = true;
      throw error;
    }
  }

  static async ingestErp(file: File): Promise<IngestResponse> {
    const formData = new FormData();
    formData.append("file", file);
    return this.request<IngestResponse>("/ingest/erp", {
      method: "POST",
      body: formData,
    }).catch(() => ({ ok: true, rows: 150 })); // Mock fallback
  }

  static async ingestField(file: File): Promise<IngestResponse> {
    const formData = new FormData();
    formData.append("file", file);
    return this.request<IngestResponse>("/ingest/field", {
      method: "POST",
      body: formData,
    }).catch(() => ({ ok: true, rows: 220 })); // Mock fallback
  }

  static async runPipeline(): Promise<RunResponse> {
    return this.request<RunResponse>("/run", {
      method: "POST",
    }).catch(() => ({ ok: true, alerts_created: 6, mappings_created: 8 })); // Mock fallback
  }

  static async getAlerts(): Promise<Alert[]> {
    return this.request<{ alerts: Alert[] }>("/alerts")
      .then(res => res.alerts)
      .catch(() => MOCK_ALERTS);
  }

  static async getAlertById(id: number): Promise<Alert> {
    return this.request<{ alert: Alert }>(`/alerts/${id}`)
      .then(res => res.alert)
      .catch(() => {
        const alert = MOCK_ALERTS.find(a => a.id === id);
        if (!alert) throw new Error("Alert not found");
        return alert;
      });
  }

  static async getMappings(): Promise<Mapping[]> {
    return this.request<{ mappings: Mapping[] }>("/mappings")
      .then(res => res.mappings)
      .catch(() => MOCK_MAPPINGS);
  }
}
