import { useState, useCallback } from "react";
import { uploadContract, getStatus, getAnalysis, compareContracts, getCompareStatus, getCompareResult } from "./api";
import UploadZone from "./components/UploadZone";
import CompareUploadZone from "./components/CompareUploadZone";
import CompareView from "./components/CompareView";
import RiskDashboard from "./components/RiskDashboard";
import ClauseTable from "./components/ClauseTable";
import ChatBox from "./components/ChatBox";
import ReportButton from "./components/ReportButton";
import Disclaimer from "./components/Disclaimer";

const STAGES = { idle: "idle", uploading: "uploading", analyzing: "analyzing", results: "results", error: "error" };

export default function App() {
  // Single-analysis state
  const [stage, setStage] = useState(STAGES.idle);
  const [documentId, setDocumentId] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [statusMsg, setStatusMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  // Compare state
  const [mode, setMode] = useState("single"); // "single" | "compare"
  const [comparePhase, setComparePhase] = useState("idle"); // "idle" | "comparing" | "results" | "error"
  const [compareResult, setCompareResult] = useState(null);
  const [compareError, setCompareError] = useState("");

  // ── Single analysis ──────────────────────────────────────────────────────

  const pollStatus = useCallback(async (docId) => {
    try {
      const res = await getStatus(docId);
      const { status, error_message } = res.data;
      if (status === "complete") {
        const aRes = await getAnalysis(docId);
        setAnalysis(aRes.data);
        setStage(STAGES.results);
      } else if (status === "failed") {
        setErrorMsg(error_message || "Analysis failed. Please try again.");
        setStage(STAGES.error);
      } else {
        setStatusMsg("Analyzing clauses...");
        setTimeout(() => pollStatus(docId), 2000);
      }
    } catch {
      setErrorMsg("Lost connection to server. Please refresh and try again.");
      setStage(STAGES.error);
    }
  }, []);

  const handleUpload = async (file) => {
    setStage(STAGES.uploading);
    setErrorMsg("");
    setStatusMsg(`Uploading ${file.name}...`);
    try {
      const res = await uploadContract(file, (pct) => setStatusMsg(`Uploading... ${pct}%`));
      const docId = res.data.document_id;
      setDocumentId(docId);
      setStage(STAGES.analyzing);
      setStatusMsg("Processing document...");
      pollStatus(docId);
    } catch (e) {
      const msg = e.response?.data?.detail || "Upload failed. Please try again.";
      setErrorMsg(msg);
      setStage(STAGES.error);
    }
  };

  const reset = () => {
    setStage(STAGES.idle);
    setDocumentId(null);
    setAnalysis(null);
    setStatusMsg("");
    setErrorMsg("");
  };

  // ── Compare ──────────────────────────────────────────────────────────────

  const pollCompare = useCallback(async (comparisonId) => {
    try {
      const res = await getCompareStatus(comparisonId);
      const { status, error_message } = res.data;
      if (status === "complete") {
        const rRes = await getCompareResult(comparisonId);
        setCompareResult(rRes.data);
        setComparePhase("results");
      } else if (status === "failed") {
        setCompareError(error_message || "Comparison failed. Please try again.");
        setComparePhase("error");
      } else {
        setTimeout(() => pollCompare(comparisonId), 2000);
      }
    } catch {
      setCompareError("Lost connection to server.");
      setComparePhase("error");
    }
  }, []);

  const handleCompare = async (fileA, fileB) => {
    setComparePhase("comparing");
    setCompareError("");
    try {
      const res = await compareContracts(fileA, fileB);
      pollCompare(res.data.comparison_id);
    } catch (e) {
      setCompareError(e.response?.data?.detail || "Comparison failed. Please try again.");
      setComparePhase("error");
    }
  };

  const resetCompare = () => {
    setComparePhase("idle");
    setCompareResult(null);
    setCompareError("");
  };

  // ── Render ───────────────────────────────────────────────────────────────

  const showingSingleResults = stage === STAGES.results;
  const showingCompareResults = mode === "compare" && comparePhase === "results";

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-100 shadow-sm">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">⚖️</span>
            <div>
              <h1 className="text-lg font-bold text-gray-900">Contract Risk Analyzer</h1>
              <p className="text-xs text-gray-400">AI-powered risk detection — not legal advice</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {showingSingleResults && (
              <button onClick={reset} className="text-sm text-blue-600 hover:underline">
                Analyze another →
              </button>
            )}
            {showingCompareResults && (
              <button onClick={resetCompare} className="text-sm text-blue-600 hover:underline">
                Compare again →
              </button>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">

        {/* Idle: mode selector + upload */}
        {stage === STAGES.idle && (mode === "single" || (mode === "compare" && comparePhase === "idle")) && (
          <div className="flex flex-col items-center gap-8 mt-12">
            <div className="text-center">
              <h2 className="text-3xl font-bold text-gray-900 mb-2">
                {mode === "compare" ? "Compare Two Contracts" : "Analyze Your Contract"}
              </h2>
              <p className="text-gray-500 max-w-lg">
                {mode === "compare"
                  ? "Upload two contracts to see a side-by-side risk comparison — ideal for negotiating revisions."
                  : "Upload a PDF, DOCX, or TXT contract. Our AI identifies risk clauses, scores each one, and generates a full report in seconds."}
              </p>
            </div>

            {/* Mode tabs */}
            <div className="flex gap-1 bg-gray-100 p-1 rounded-xl">
              <button
                onClick={() => setMode("single")}
                className={`px-5 py-2 rounded-lg text-sm font-medium transition-colors
                  ${mode === "single" ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"}`}
              >
                Single Analysis
              </button>
              <button
                onClick={() => setMode("compare")}
                className={`px-5 py-2 rounded-lg text-sm font-medium transition-colors
                  ${mode === "compare" ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"}`}
              >
                Compare Contracts
              </button>
            </div>

            {mode === "single" ? (
              <UploadZone onUpload={handleUpload} loading={false} />
            ) : (
              <CompareUploadZone onCompare={handleCompare} loading={false} />
            )}

            <div className="w-full max-w-2xl">
              <Disclaimer />
            </div>
          </div>
        )}

        {/* Single: uploading / analyzing spinner */}
        {(stage === STAGES.uploading || stage === STAGES.analyzing) && (
          <div className="flex flex-col items-center justify-center mt-24 gap-6">
            <div className="w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
            <div className="text-center">
              <p className="text-lg font-medium text-gray-800">{statusMsg}</p>
              <p className="text-sm text-gray-400 mt-1">
                {stage === STAGES.analyzing ? "This may take 30–60 seconds depending on document length." : ""}
              </p>
            </div>
          </div>
        )}

        {/* Compare: comparing spinner */}
        {mode === "compare" && comparePhase === "comparing" && (
          <div className="flex flex-col items-center justify-center mt-24 gap-6">
            <div className="w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
            <div className="text-center">
              <p className="text-lg font-medium text-gray-800">Analyzing both contracts...</p>
              <p className="text-sm text-gray-400 mt-1">Running both analyses in parallel. This may take 60–90 seconds.</p>
            </div>
          </div>
        )}

        {/* Single: error */}
        {stage === STAGES.error && (
          <div className="flex flex-col items-center mt-24 gap-4">
            <div className="text-5xl">⚠️</div>
            <p className="text-red-600 font-medium text-center max-w-md">{errorMsg}</p>
            <button onClick={reset} className="px-5 py-2 bg-blue-600 text-white rounded-xl text-sm hover:bg-blue-700">
              Try Again
            </button>
          </div>
        )}

        {/* Compare: error */}
        {mode === "compare" && comparePhase === "error" && (
          <div className="flex flex-col items-center mt-24 gap-4">
            <div className="text-5xl">⚠️</div>
            <p className="text-red-600 font-medium text-center max-w-md">{compareError}</p>
            <button onClick={resetCompare} className="px-5 py-2 bg-blue-600 text-white rounded-xl text-sm hover:bg-blue-700">
              Try Again
            </button>
          </div>
        )}

        {/* Single: results */}
        {stage === STAGES.results && analysis && (
          <div className="space-y-6">
            <Disclaimer />
            <div className="flex items-center justify-between flex-wrap gap-4">
              <h2 className="text-2xl font-bold text-gray-900">Analysis Results</h2>
              <ReportButton documentId={documentId} />
            </div>
            <RiskDashboard analysis={analysis} />
            <ClauseTable clauses={analysis.clauses} />
            <ChatBox documentId={documentId} />
            <Disclaimer />
          </div>
        )}

        {/* Compare: results */}
        {mode === "compare" && comparePhase === "results" && compareResult && (
          <div className="space-y-6">
            <Disclaimer />
            <div className="flex items-center justify-between flex-wrap gap-4">
              <h2 className="text-2xl font-bold text-gray-900">Contract Comparison</h2>
            </div>
            <CompareView result={compareResult} />
            <Disclaimer />
          </div>
        )}

      </main>
    </div>
  );
}
