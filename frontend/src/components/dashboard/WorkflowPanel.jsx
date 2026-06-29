import { useEffect, useRef, useState } from "react";
import toast from "react-hot-toast";
import { apiService } from "../../services/api";

const LAST_CSV_NAME_KEY = "cmds_last_csv_name";

function isCsvFile(file) {
  if (!file) return false;
  const name = String(file.name || "").toLowerCase();
  const type = String(file.type || "").toLowerCase();
  if (name.endsWith(".csv")) return true;
  return type === "text/csv" || type === "application/csv" || type === "text/plain";
}

async function readFileAsText(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(new Error("Could not read CSV file"));
    reader.readAsText(file);
  });
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export default function WorkflowPanel({ onCompleted }) {
  const fileInputRef = useRef(null);
  const [csvFile, setCsvFile] = useState(null);
  const [lastCsvName, setLastCsvName] = useState(() => localStorage.getItem(LAST_CSV_NAME_KEY) || "");
  const [busy, setBusy] = useState(false);
  const [monitoring, setMonitoring] = useState(false);
  const [resultsSize, setResultsSize] = useState(0);

  useEffect(() => {
    let mounted = true;
    apiService
      .getMonitoringStatus()
      .then((status) => {
        if (!mounted) return;
        setMonitoring(Boolean(status?.monitoring));
        setResultsSize(Number(status?.results_size || 0));
      })
      .catch(() => {});
    return () => {
      mounted = false;
    };
  }, []);

  const clearSelectedCsv = () => {
    setCsvFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const loadCsvText = async () => {
    if (!csvFile) {
      throw new Error("Select a CSV file first");
    }
    if (!isCsvFile(csvFile)) {
      clearSelectedCsv();
      throw new Error("Only CSV files are supported. Please upload a .csv file.");
    }

    const csvText = await readFileAsText(csvFile);
    const trimmed = csvText.trim();
    if (trimmed.startsWith("{") || trimmed.startsWith("[")) {
      clearSelectedCsv();
      throw new Error("The selected file looks like JSON. Please upload a CSV dataset.");
    }
    return csvText;
  };

  const withBusy = async (action) => {
    setBusy(true);
    try {
      await action();
      onCompleted?.();
    } catch (error) {
      toast.error(error?.message || "Operation failed. Please try again.");
    } finally {
      setBusy(false);
    }
  };

  const onFileChange = (event) => {
    const selected = event.target.files?.[0] || null;
    if (!selected) {
      clearSelectedCsv();
      return;
    }
    if (!isCsvFile(selected)) {
      clearSelectedCsv();
      toast.error("Unsupported file type. Upload a .csv file only.");
      return;
    }
    setCsvFile(selected);
    setLastCsvName(selected.name || "");
    localStorage.setItem(LAST_CSV_NAME_KEY, selected.name || "");
  };

  const onTrain = async () => {
    await withBusy(async () => {
      const csvText = await loadCsvText();
      const response = await apiService.trainModel(csvText);
      const metrics = response?.metrics || {};
      toast.success(`Model trained: F1 ${(metrics.f1 ?? 0).toFixed(2)}`);
    });
  };

  const onPredictOrMonitor = async () => {
    await withBusy(async () => {
      if (csvFile) {
        const csvText = await loadCsvText();
        const response = await apiService.predictFromCsv(csvText);
        setLastCsvName(csvFile.name || "");
        localStorage.setItem(LAST_CSV_NAME_KEY, csvFile.name || "");
        const status = await apiService.getMonitoringStatus();
        setMonitoring(Boolean(status?.monitoring));
        setResultsSize(Number(status?.results_size || 0));
        toast.success(`Predicted ${response?.count || 0} transactions`);
        return;
      }

      const response = await apiService.startMonitoring();
      setMonitoring(Boolean(response?.monitoring));
      const status = await apiService.getMonitoringStatus();
      setResultsSize(Number(status?.results_size || 0));
      toast.success(response?.monitoring ? "Monitoring started" : "Monitoring status checked");
    });
  };

  const onGenerateReport = async () => {
    await withBusy(async () => {
      const response = await apiService.generateReport("json");
      const body = response?.data || response || {};
      const blob = new Blob([JSON.stringify(body, null, 2)], { type: "application/json" });
      downloadBlob(blob, "money_mule_report.json");
      toast.success("Report generated");
    });
  };

  const onExportCsv = async () => {
    await withBusy(async () => {
      const response = await apiService.generateReport("csv");
      const blob = response?.data instanceof Blob ? response.data : new Blob([response?.data || ""], { type: "text/csv" });
      downloadBlob(blob, "money_mule_report.csv");
      toast.success("CSV exported");
    });
  };

  const onReset = async () => {
    await withBusy(async () => {
      await apiService.resetData();
      clearSelectedCsv();
      setMonitoring(false);
      setResultsSize(0);
      setLastCsvName("");
      localStorage.removeItem(LAST_CSV_NAME_KEY);
      toast.success("Runtime state reset");
    });
  };

  const csvBadgeLabel = csvFile?.name || lastCsvName || (resultsSize > 0 ? "loaded in runtime" : "none");

  return (
    <section className="card overflow-hidden p-4">
      <div className="flex flex-col gap-4 rounded-2xl border border-slate-700/50 bg-slate-950/35 p-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-[0.16em] text-muted">Model Workflow</p>
          <h2 className="text-lg font-semibold">Train, predict, report, and reset</h2>
          <p className="text-sm text-slate-400">
            Load a CSV dataset or use the live stream. Buttons are wired to the backend and return real results.
          </p>
        </div>
        <div className="flex flex-wrap gap-2 text-xs text-muted">
          <span className="rounded-full border border-slate-700 px-3 py-1">Monitoring: {monitoring ? "On" : "Off"}</span>
          <span className="rounded-full border border-slate-700 px-3 py-1">CSV: {csvBadgeLabel}</span>
        </div>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-[1fr_auto]">
        <label className="text-sm text-muted">
          Transaction CSV
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,text/csv"
            className="input mt-1"
            onChange={onFileChange}
          />
        </label>
        <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-5">
          <button type="button" className="btn" disabled={busy} onClick={onTrain}>
            Train Model
          </button>
          <button type="button" className="btn-secondary" disabled={busy} onClick={onPredictOrMonitor}>
            Predict / Start Monitoring
          </button>
          <button type="button" className="btn-secondary" disabled={busy} onClick={onGenerateReport}>
            Generate Report
          </button>
          <button type="button" className="btn-secondary" disabled={busy} onClick={onExportCsv}>
            Export CSV
          </button>
          <button type="button" className="btn-secondary" disabled={busy} onClick={onReset}>
            Delete / Reset Data
          </button>
        </div>
      </div>
    </section>
  );
}
