import { useState, useEffect, useMemo } from "react";
import { 
  AlertCircle, 
  CheckCircle2, 
  Clock, 
  FileText, 
  Filter, 
  LayoutDashboard, 
  Link2, 
  Loader2, 
  RefreshCw, 
  Upload,
  ChevronRight,
  ShieldAlert,
  Info
} from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import { ApiService } from "./api";
import { Alert, Mapping, Severity, AlertStatus } from "./types";

export default function App() {
  const [activeTab, setActiveTab] = useState<"dashboard" | "mappings">("dashboard");
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [mappings, setMappings] = useState<Mapping[]>([]);
  const [selectedAlertId, setSelectedAlertId] = useState<number | null>(null);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [loading, setLoading] = useState(false);
  const [isMockMode, setIsMockMode] = useState(false);
  
  // Filters
  const [severityFilter, setSeverityFilter] = useState<Severity | "all">("all");
  const [statusFilter, setStatusFilter] = useState<AlertStatus | "all">("all");

  const fetchData = async () => {
    setLoading(true);
    try {
      const [alertsData, mappingsData] = await Promise.all([
        ApiService.getAlerts(),
        ApiService.getMappings()
      ]);
      setAlerts(alertsData);
      setMappings(mappingsData);
      setIsMockMode(ApiService.getIsMockMode());
    } catch (error) {
      console.error("Fetch failed", error);
      setIsMockMode(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (selectedAlertId) {
      const fetchAlertDetail = async () => {
        try {
          const detail = await ApiService.getAlertById(selectedAlertId);
          setSelectedAlert(detail);
        } catch (error) {
          console.error("Failed to fetch alert detail", error);
        }
      };
      fetchAlertDetail();
    } else {
      setSelectedAlert(null);
    }
  }, [selectedAlertId]);

  const filteredAlerts = useMemo(() => {
    return alerts.filter(alert => {
      const matchesSeverity = severityFilter === "all" || alert.severity === severityFilter;
      const matchesStatus = statusFilter === "all" || alert.status === statusFilter;
      return matchesSeverity && matchesStatus;
    });
  }, [alerts, severityFilter, statusFilter]);

  const handleAcknowledge = () => {
    if (selectedAlert) {
      const updatedAlerts = alerts.map(a => 
        a.id === selectedAlert.id ? { ...a, status: "ack" as AlertStatus } : a
      );
      setAlerts(updatedAlerts);
      setSelectedAlert({ ...selectedAlert, status: "ack" });
    }
  };

  const handleRunPipeline = async () => {
    setLoading(true);
    try {
      await ApiService.runPipeline();
      await fetchData();
    } catch (error) {
      console.error("Pipeline failed", error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (type: "erp" | "field", file: File) => {
    setLoading(true);
    try {
      if (type === "erp") await ApiService.ingestErp(file);
      else await ApiService.ingestField(file);
      alert(`${type.toUpperCase()} file uploaded successfully`);
    } catch (error) {
      console.error("Upload failed", error);
    } finally {
      setLoading(false);
    }
  };

  const toggleMockMode = () => {
    const newState = !isMockMode;
    ApiService.setMockMode(newState);
    setIsMockMode(newState);
    fetchData();
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 h-16 flex items-center justify-between px-6 sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="bg-indigo-600 p-2 rounded-lg">
            <ShieldAlert className="text-white w-6 h-6" />
          </div>
          <h1 className="text-xl font-bold tracking-tight text-slate-800">Risk Alert Dashboard</h1>
        </div>
        
        <div className="flex items-center gap-4">
          <nav className="flex bg-slate-100 p-1 rounded-lg">
            <button 
              onClick={() => setActiveTab("dashboard")}
              className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${activeTab === "dashboard" ? "bg-white text-indigo-600 shadow-sm" : "text-slate-600 hover:text-slate-900"}`}
            >
              <div className="flex items-center gap-2">
                <LayoutDashboard className="w-4 h-4" />
                Dashboard
              </div>
            </button>
            <button 
              onClick={() => setActiveTab("mappings")}
              className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${activeTab === "mappings" ? "bg-white text-indigo-600 shadow-sm" : "text-slate-600 hover:text-slate-900"}`}
            >
              <div className="flex items-center gap-2">
                <Link2 className="w-4 h-4" />
                Mappings
              </div>
            </button>
          </nav>
          
          <button 
            onClick={toggleMockMode}
            className={`px-3 py-1.5 rounded-md text-xs font-semibold border transition-all ${isMockMode ? "bg-amber-50 text-amber-700 border-amber-200" : "bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100"}`}
          >
            {isMockMode ? "Mock Mode Active" : "Use Sample Data"}
          </button>
        </div>
      </header>

      {/* Mock Banner */}
      {isMockMode && (
        <div className="bg-amber-50 border-b border-amber-100 px-6 py-2 flex items-center gap-2 text-amber-800 text-sm font-medium">
          <Info className="w-4 h-4" />
          Mock mode: backend unavailable. Showing simulated data.
        </div>
      )}

      {/* Main Content */}
      <main className="flex-1 flex overflow-hidden">
        {activeTab === "dashboard" ? (
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* Action Bar */}
            <div className="bg-white border-b border-slate-200 p-4 flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <label className="flex items-center gap-2 px-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm font-medium text-slate-700 cursor-pointer hover:bg-slate-100 transition-colors">
                  <Upload className="w-4 h-4 text-slate-500" />
                  ERP CSV
                  <input type="file" className="hidden" accept=".csv" onChange={(e) => e.target.files?.[0] && handleFileUpload("erp", e.target.files[0])} />
                </label>
                <label className="flex items-center gap-2 px-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm font-medium text-slate-700 cursor-pointer hover:bg-slate-100 transition-colors">
                  <Upload className="w-4 h-4 text-slate-500" />
                  Field CSV
                  <input type="file" className="hidden" accept=".csv" onChange={(e) => e.target.files?.[0] && handleFileUpload("field", e.target.files[0])} />
                </label>
                <button 
                  onClick={handleRunPipeline}
                  disabled={loading}
                  className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold hover:bg-indigo-700 disabled:opacity-50 transition-colors"
                >
                  {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
                  Generate Crosswalk + Alerts
                </button>
              </div>

              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Filter className="w-4 h-4 text-slate-400" />
                  <select 
                    value={severityFilter}
                    onChange={(e) => setSeverityFilter(e.target.value as Severity | "all")}
                    className="bg-transparent text-sm font-medium border-none focus:ring-0 cursor-pointer"
                  >
                    <option value="all">All Severities</option>
                    <option value="high">High Severity</option>
                    <option value="med">Medium Severity</option>
                    <option value="low">Low Severity</option>
                  </select>
                </div>
                <div className="h-4 w-px bg-slate-200" />
                <select 
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value as AlertStatus | "all")}
                  className="bg-transparent text-sm font-medium border-none focus:ring-0 cursor-pointer"
                >
                  <option value="all">All Statuses</option>
                  <option value="open">Open</option>
                  <option value="ack">Acknowledged</option>
                  <option value="resolved">Resolved</option>
                </select>
              </div>
            </div>

            <div className="flex-1 flex overflow-hidden">
              {/* Alerts List */}
              <div className="w-96 border-r border-slate-200 overflow-y-auto bg-slate-50/50">
                {loading && alerts.length === 0 ? (
                  <div className="p-8 flex flex-col items-center justify-center text-slate-400 gap-2">
                    <Loader2 className="w-8 h-8 animate-spin" />
                    <p className="text-sm font-medium">Loading alerts...</p>
                  </div>
                ) : filteredAlerts.length === 0 ? (
                  <div className="p-8 text-center text-slate-400">
                    <AlertCircle className="w-12 h-12 mx-auto mb-2 opacity-20" />
                    <p className="text-sm font-medium">No alerts found</p>
                  </div>
                ) : (
                  filteredAlerts.map((alert) => (
                    <motion.div
                      layout
                      key={alert.id}
                      onClick={() => setSelectedAlertId(alert.id)}
                      className={`alert-card ${selectedAlertId === alert.id ? "active" : ""}`}
                    >
                      <div className="flex justify-between items-start mb-1">
                        <span className={`text-[10px] uppercase font-bold px-1.5 py-0.5 rounded border ${
                          alert.severity === "high" ? "severity-high" : 
                          alert.severity === "med" ? "severity-med" : "severity-low"
                        }`}>
                          {alert.severity}
                        </span>
                        <span className="text-[10px] text-slate-400 font-mono">
                          {new Date(alert.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <h3 className="text-sm font-semibold text-slate-800 line-clamp-1 mb-1">{alert.title}</h3>
                      <p className="text-xs text-slate-500 line-clamp-2 mb-2">{alert.summary}</p>
                      <div className="flex items-center justify-between">
                        <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                          alert.status === "open" ? "status-open" : 
                          alert.status === "ack" ? "status-ack" : "status-resolved"
                        }`}>
                          {alert.status.toUpperCase()}
                        </span>
                        <ChevronRight className={`w-4 h-4 text-slate-300 transition-transform ${selectedAlertId === alert.id ? "translate-x-1 text-indigo-400" : ""}`} />
                      </div>
                    </motion.div>
                  ))
                )}
              </div>

              {/* Details Panel */}
              <div className="flex-1 overflow-y-auto bg-white">
                <AnimatePresence mode="wait">
                  {selectedAlert ? (
                    <motion.div 
                      key={selectedAlert.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      className="p-8 max-w-4xl mx-auto"
                    >
                      <div className="flex justify-between items-start mb-6">
                        <div>
                          <div className="flex items-center gap-3 mb-2">
                            <span className={`text-xs uppercase font-bold px-2 py-1 rounded border ${
                              selectedAlert.severity === "high" ? "severity-high" : 
                              selectedAlert.severity === "med" ? "severity-med" : "severity-low"
                            }`}>
                              {selectedAlert.severity} Severity
                            </span>
                            <span className="text-xs text-slate-400 font-mono flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {new Date(selectedAlert.created_at).toLocaleString()}
                            </span>
                          </div>
                          <h2 className="text-2xl font-bold text-slate-900 mb-2">{selectedAlert.title}</h2>
                          <div className="flex items-center gap-4 text-sm">
                            <span className="text-slate-500">Type: <span className="text-slate-900 font-medium">{selectedAlert.alert_type}</span></span>
                            <span className="text-slate-500">Project: <span className="text-slate-900 font-medium">{selectedAlert.project_id}</span></span>
                          </div>
                        </div>
                        
                        <div className="flex flex-col items-end gap-2">
                          <span className={`text-sm font-bold px-3 py-1 rounded-full ${
                            selectedAlert.status === "open" ? "status-open" : 
                            selectedAlert.status === "ack" ? "status-ack" : "status-resolved"
                          }`}>
                            {selectedAlert.status.toUpperCase()}
                          </span>
                          {selectedAlert.status === "open" && (
                            <button 
                              onClick={handleAcknowledge}
                              className="flex items-center gap-2 px-4 py-2 bg-slate-900 text-white rounded-lg text-sm font-semibold hover:bg-slate-800 transition-colors"
                            >
                              <CheckCircle2 className="w-4 h-4" />
                              Acknowledge
                            </button>
                          )}
                        </div>
                      </div>

                      <div className="bg-slate-50 rounded-xl p-6 mb-8 border border-slate-100">
                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Summary</h4>
                        <p className="text-slate-700 leading-relaxed">{selectedAlert.summary}</p>
                      </div>

                      <div>
                        <h4 className="flex items-center gap-2 text-xs font-bold text-slate-400 uppercase tracking-wider mb-4">
                          <FileText className="w-4 h-4" />
                          Evidence & Context
                        </h4>
                        <div className="bg-slate-900 rounded-xl p-6 overflow-x-auto">
                          <pre className="text-emerald-400 font-mono text-sm">
                            {JSON.stringify(selectedAlert.evidence, null, 2)}
                          </pre>
                        </div>
                      </div>
                    </motion.div>
                  ) : (
                    <div className="h-full flex flex-col items-center justify-center text-slate-300 p-12 text-center">
                      <div className="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mb-4">
                        <LayoutDashboard className="w-10 h-10" />
                      </div>
                      <h3 className="text-lg font-semibold text-slate-400">Select an alert to view details</h3>
                      <p className="text-sm max-w-xs">Filter the list on the left or use the action bar to generate new alerts.</p>
                    </div>
                  )}
                </AnimatePresence>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col overflow-hidden bg-white">
            <div className="p-8 max-w-6xl mx-auto w-full">
              <div className="flex justify-between items-end mb-8">
                <div>
                  <h2 className="text-2xl font-bold text-slate-900 mb-2">Cost Code Mappings</h2>
                  <p className="text-slate-500">Crosswalk between ERP cost codes and Field task names.</p>
                </div>
                <div className="text-sm text-slate-400 font-medium">
                  Total Mappings: {mappings.length}
                </div>
              </div>

              <div className="border border-slate-200 rounded-xl overflow-hidden shadow-sm">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200">
                      <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Cost Code</th>
                      <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Task Name</th>
                      <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Confidence</th>
                      <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Method</th>
                      <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Status</th>
                      <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Last Updated</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {mappings.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="px-6 py-12 text-center text-slate-400">
                          No mappings found. Run the pipeline to generate suggestions.
                        </td>
                      </tr>
                    ) : (
                      mappings.map((mapping) => (
                        <tr key={mapping.id} className="hover:bg-slate-50/50 transition-colors">
                          <td className="px-6 py-4 text-sm font-mono text-indigo-600 font-medium">{mapping.cost_code}</td>
                          <td className="px-6 py-4 text-sm text-slate-700 font-medium">{mapping.task_name}</td>
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-2">
                              <div className="w-16 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                                <div 
                                  className={`h-full rounded-full ${mapping.confidence > 0.9 ? "bg-emerald-500" : mapping.confidence > 0.8 ? "bg-amber-500" : "bg-red-500"}`} 
                                  style={{ width: `${mapping.confidence * 100}%` }}
                                />
                              </div>
                              <span className="text-xs font-mono text-slate-500">{(mapping.confidence * 100).toFixed(0)}%</span>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase border ${
                              mapping.method === "human" ? "bg-slate-100 text-slate-600 border-slate-200" : 
                              mapping.method === "llm" ? "bg-indigo-50 text-indigo-700 border-indigo-100" : 
                              "bg-slate-50 text-slate-500 border-slate-100"
                            }`}>
                              {mapping.method}
                            </span>
                          </td>
                          <td className="px-6 py-4">
                            <span className={`text-xs font-semibold ${
                              mapping.status === "approved" ? "text-emerald-600" : 
                              mapping.status === "rejected" ? "text-red-600" : "text-amber-600"
                            }`}>
                              {mapping.status.charAt(0).toUpperCase() + mapping.status.slice(1)}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-xs text-slate-400 font-mono">
                            {new Date(mapping.updated_at).toLocaleDateString()}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
