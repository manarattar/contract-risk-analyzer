import PropTypes from 'prop-types';
import { useState, useCallback, useEffect } from "react";
import { uploadContract, getStatus, getAnalysis, compareContracts, getCompareStatus, getCompareResult } from "./api";
import UploadZone from "./components/UploadZone";
import CompareUploadZone from "./components/CompareUploadZone";
import CompareView from "./components/CompareView";
import RiskDashboard from "./components/RiskDashboard";
import ClauseTable from "./components/ClauseTable";
import ChatBox from "./components/ChatBox";
import ReportButton from "./components/ReportButton";
import Disclaimer from "./components/Disclaimer";
import Onboarding, { hasSeenTour } from "./components/Onboarding";
import Icon from "./components/Icon";

const STAGES = { idle: "idle", uploading: "uploading", analyzing: "analyzing", results: "results", error: "error" };

const LANDING_TOUR = "contracts.onboarded.v1";
const RESULTS_TOUR = "contracts.results-tour.v1";

const LANDING_STEPS = [
  {
    target: null,
    title: "A contract, marked up the way a reviewer would",
    body: (
      <>
        <p style={{ margin: 0 }}>Upload a contract and every clause comes back marked up, with the risky ones flagged and a rewrite suggested.</p>
        <ul style={{ margin: "10px 0 0", paddingLeft: 18 }}>
          <li>Jev, a decision model, puts each clause in one of six categories, from best practice to critical risk, and says how sure it is.</li>
          <li>The risk score is calculated from those probabilities, not a number an AI made up.</li>
          <li>An LLM explains each risk, suggests a rewrite, and points out missing clauses and clauses that contradict each other.</li>
        </ul>
      </>
    ),
  },
  {
    target: "upload",
    title: "Upload a contract",
    body: "PDF, Word or plain text, up to 10 MB. A typical contract takes 30 to 60 seconds to review.",
  },
  {
    target: "modes",
    title: "Or compare two versions",
    body: "Upload the draft you were sent and the revised one, and see clause by clause what got riskier and what got safer.",
  },
  {
    target: "sample",
    title: "Try it on the sample",
    body: "A freelance agreement written heavily in the client’s favour, so there is plenty to find. When the results are in, a second short tour shows how to read them.",
  },
];

const RESULTS_STEPS = [
  {
    target: "score",
    title: "The overall risk",
    body: "Drawn to scale: up to 35 is low, up to 70 medium, above that high. The recommendation and assessment sum up the whole contract.",
  },
  {
    target: "findings",
    title: "What to act on",
    body: "Real risks first, then clauses worth tightening, then what is already done well. Missing clauses are listed below.",
  },
  {
    target: "contradictions",
    title: "Clauses that work against each other",
    body: "Found by reading across the whole contract, for example a termination clause that another clause quietly cancels.",
  },
  {
    target: "clauses",
    title: "Every clause, marked up",
    body: "Riskiest first. Click a clause to read it as written, see how sure Jev was about its category, and get a suggested rewrite. “Check this one” means Jev was split, so a person should look.",
  },
  {
    target: "chat",
    title: "Ask about it",
    body: "Questions are answered from the contract’s own text, such as whether you can end it early or who owns your work.",
  },
  {
    target: "report",
    title: "Take it with you",
    body: "Download the full review as a PDF, to share or to bring to a lawyer.",
  },
];

/** A made-up clause showing what the markup looks like, so the first screen isn't just an upload box. */
function Specimen() {
  return (
    <aside className="rounded-[4px] border border-rule bg-sheet p-5 sm:p-6" aria-label="Example of the markup">
      <p className="label">Example markup</p>
      <div className="mt-3 space-y-5">
        <div className="grid grid-cols-[1fr_auto] gap-x-4">
          <p className="font-serif text-[15.5px] leading-relaxed text-ink">
            <span className="num mr-1.5 text-[12px] text-ink-3">§ 7</span>
            The Contractor shall indemnify the Client against <span className="redline">any and all losses, howsoever arising</span>, without limit.
          </p>
          <span className="h-fit border-l-2 border-mark pl-2 text-[12px] font-semibold leading-tight text-mark">
            High risk<br /><span className="num font-normal">84</span>
          </span>
          <p className="col-span-2 mt-2 border-l-2 border-rev pl-3 font-serif text-[14.5px] leading-relaxed text-rev">
            Suggested: <span className="underline decoration-rev/40 underline-offset-[3px]">capped at the fees paid under this agreement</span>
          </p>
        </div>
        <div className="grid grid-cols-[1fr_auto] gap-x-4 border-t border-rule pt-4">
          <p className="font-serif text-[15.5px] leading-relaxed text-ink">
            <span className="num mr-1.5 text-[12px] text-ink-3">§ 4</span>
            Invoices are payable within thirty (30) days of receipt.
          </p>
          <span className="h-fit border-l-2 border-ok pl-2 text-[12px] font-semibold leading-tight text-ok">
            Acceptable<br /><span className="num font-normal">18</span>
          </span>
        </div>
        <p className="border-t border-rule pt-4 text-[14px] text-ink-2">
          <span className="font-semibold text-rev" aria-hidden>+ </span>
          <span className="font-medium text-rev underline decoration-rev/50 underline-offset-[3px]">Limitation of liability</span>
          {" "}— missing. Essential in a services contract.
        </p>
      </div>
    </aside>
  );
}

function Working({ title, detail, steps }) {
  return (
    <div className="mx-auto mt-10 max-w-xl rounded-[4px] border border-rule bg-sheet p-6 sm:p-8">
      <p className="label">Reviewing</p>
      <p className="mt-1 font-serif text-[22px] font-semibold text-ink">{title}</p>
      <div className="mt-4 h-0.5 overflow-hidden bg-rule" role="progressbar" aria-label="Working">
        <div className="scan h-full w-2/5 bg-mark" />
      </div>
      <p className="mt-3 text-[14px] text-ink-3">{detail}</p>
      <ol className="mt-5 space-y-1.5 border-t border-rule pt-4 text-[14px] text-ink-2">
        {steps.map((s, i) => (
          <li key={s} className="grid grid-cols-[22px_1fr]">
            <span className="num text-[12px] text-ink-3">{i + 1}</span>{s}
          </li>
        ))}
      </ol>
    </div>
  );
}

function Failed({ message, onRetry }) {
  return (
    <div className="mx-auto mt-10 max-w-xl rounded-[4px] border border-rule bg-sheet p-6 sm:p-8">
      <p className="flex items-center gap-2 font-serif text-[20px] font-semibold text-mark">
        <Icon name="alert" size={20} /> That didn’t work
      </p>
      <p className="mt-2 text-[14px] leading-relaxed text-ink-2">{message}</p>
      <button onClick={onRetry} className="mt-4 rounded-[3px] bg-ink px-4 py-2 text-[14px] font-medium text-sheet hover:opacity-90">
        Try again
      </button>
    </div>
  );
}

export default function App() {
  // Single-analysis state
  const [stage, setStage] = useState(STAGES.idle);
  const [documentId, setDocumentId] = useState(null);
  const [fileName, setFileName] = useState("");
  const [analysis, setAnalysis] = useState(null);
  const [statusMsg, setStatusMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  // Compare state
  const [mode, setMode] = useState("single"); // "single" | "compare"
  const [comparePhase, setComparePhase] = useState("idle"); // "idle" | "comparing" | "results" | "error"
  const [compareResult, setCompareResult] = useState(null);
  const [compareError, setCompareError] = useState("");

  // Guided tour: "landing" on the first visit, "results" the first time results appear
  const [tour, setTour] = useState(() => (hasSeenTour(LANDING_TOUR) ? null : "landing"));

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
    setFileName(file.name);
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

  const runSample = async () => {
    const res = await fetch("/sample_contract.pdf");
    const blob = await res.blob();
    const file = new File([blob], "sample_contract.pdf", { type: "application/pdf" });
    handleUpload(file);
  };

  const reset = () => {
    setStage(STAGES.idle);
    setDocumentId(null);
    setFileName("");
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

  // ── Tour ─────────────────────────────────────────────────────────────────

  useEffect(() => {
    if (stage === STAGES.results && !hasSeenTour(RESULTS_TOUR)) setTour("results");
  }, [stage]);

  const closeTour = (finished) => {
    const which = tour;
    setTour(null);
    if (which === "landing" && finished) runSample();
  };

  // ── Render ───────────────────────────────────────────────────────────────

  const showingSingleResults = stage === STAGES.results;
  const showingCompareResults = mode === "compare" && comparePhase === "results";
  const onLanding = stage === STAGES.idle && (mode === "single" || comparePhase === "idle");
  const canTour = onLanding || showingSingleResults;

  return (
    <div className="min-h-screen bg-desk text-ink">
      <header className="border-b border-rule bg-sheet">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6">
          <button onClick={() => { reset(); resetCompare(); }} className="flex items-baseline gap-2.5 text-left">
            <span className="font-serif text-[26px] font-semibold leading-none text-mark" aria-hidden>§</span>
            <span>
              <span className="block font-serif text-[18px] font-semibold leading-tight text-ink">Contract Risk Analyzer</span>
              <span className="block text-[12px] text-ink-3">Marked up clause by clause. Not legal advice.</span>
            </span>
          </button>
          <div className="flex items-center gap-4">
            {canTour && (
              <button
                onClick={() => { if (onLanding) setMode("single"); setTour(onLanding ? "landing" : "results"); }}
                className="text-[13px] text-ink-2 underline decoration-rule underline-offset-[3px] hover:text-ink hover:decoration-ink"
              >
                How it works
              </button>
            )}
            {showingSingleResults && (
              <button onClick={reset} className="rounded-[3px] border border-rule px-3 py-1.5 text-[13px] font-medium text-ink hover:border-ink">
                Review another
              </button>
            )}
            {showingCompareResults && (
              <button onClick={resetCompare} className="rounded-[3px] border border-rule px-3 py-1.5 text-[13px] font-medium text-ink hover:border-ink">
                Compare again
              </button>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6">

        {/* Idle: mode selector + upload */}
        {onLanding && (
          <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,1fr)]">
            <section className="rounded-[4px] border border-rule bg-sheet p-5 sm:p-8">
              <h2 className="max-w-[22ch] font-serif text-[30px] font-semibold leading-[1.15] text-ink sm:text-[34px]">
                {mode === "compare" ? "See what changed between two drafts." : "Find the clauses you shouldn’t sign as written."}
              </h2>
              <p className="mt-3 max-w-[58ch] text-[15px] leading-relaxed text-ink-2">
                {mode === "compare"
                  ? "Upload two versions of the same contract. Each is reviewed in full, then compared clause by clause: what got riskier, what got safer, what was added or removed."
                  : "Upload a contract. Each clause is categorised and scored, the risky ones get a plain explanation and a suggested rewrite, and missing or contradictory clauses are flagged."}
              </p>

              <div data-tour="modes" role="tablist" className="mt-6 flex gap-6 border-b border-rule">
                {[["single", "Review one contract"], ["compare", "Compare two versions"]].map(([key, label]) => (
                  <button
                    key={key}
                    role="tab"
                    aria-selected={mode === key}
                    onClick={() => setMode(key)}
                    className={`-mb-px border-b-2 pb-2 text-[14px] font-medium transition-colors ${
                      mode === key ? "border-mark text-ink" : "border-transparent text-ink-3 hover:text-ink"
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>

              <div className="mt-6">
                {mode === "single" ? (
                  <UploadZone onUpload={handleUpload} loading={false} />
                ) : (
                  <CompareUploadZone onCompare={handleCompare} loading={false} />
                )}
              </div>

              {mode === "single" && (
                <div className="mt-5 flex flex-wrap items-center gap-x-4 gap-y-2">
                  <button
                    data-tour="sample"
                    onClick={runSample}
                    className="rounded-[3px] bg-ink px-4 py-2 text-[14px] font-medium text-sheet hover:opacity-90"
                  >
                    Review the sample contract
                  </button>
                  <span className="text-[13px] text-ink-3">A one-sided freelance agreement, about a minute.</span>
                </div>
              )}

              <div className="mt-8 border-t border-rule pt-4">
                <Disclaimer />
              </div>
            </section>

            <div className="space-y-4">
              <Specimen />
              <p className="px-1 text-[13px] leading-relaxed text-ink-3">
                Useful for freelancers reading a client’s terms, startups checking a vendor agreement, or anyone about
                to sign an NDA.
              </p>
            </div>
          </div>
        )}

        {/* Single: uploading / analyzing */}
        {(stage === STAGES.uploading || stage === STAGES.analyzing) && (
          <Working
            title={fileName || "Your contract"}
            detail={`${statusMsg} ${stage === STAGES.analyzing ? "This usually takes 30 to 60 seconds." : ""}`}
            steps={[
              "Split the contract into clauses",
              "Jev puts each clause in a risk category",
              "An LLM explains the risks and drafts rewrites",
              "Check across clauses for contradictions and gaps",
            ]}
          />
        )}

        {/* Compare: comparing */}
        {mode === "compare" && comparePhase === "comparing" && (
          <Working
            title="Two versions"
            detail="Both are reviewed in parallel, then compared. This usually takes 60 to 90 seconds."
            steps={["Review version A in full", "Review version B in full", "Match the clauses and compare their risk"]}
          />
        )}

        {stage === STAGES.error && <Failed message={errorMsg} onRetry={reset} />}
        {mode === "compare" && comparePhase === "error" && <Failed message={compareError} onRetry={resetCompare} />}

        {/* Single: results */}
        {stage === STAGES.results && analysis && (
          <div className="space-y-5">
            <div className="flex flex-wrap items-end justify-between gap-4">
              <div className="min-w-0">
                <p className="label">Review of</p>
                <h2 className="truncate font-serif text-[26px] font-semibold text-ink">{fileName || "Your contract"}</h2>
              </div>
              <ReportButton documentId={documentId} />
            </div>
            <RiskDashboard analysis={analysis} />
            <ClauseTable clauses={analysis.clauses} />
            <ChatBox documentId={documentId} />
            <FeedbackBar context={{ document_id: documentId, type: "analysis" }} />
            <Disclaimer />
          </div>
        )}

        {/* Compare: results */}
        {mode === "compare" && comparePhase === "results" && compareResult && (
          <div className="space-y-5">
            <div>
              <p className="label">Comparison</p>
              <h2 className="font-serif text-[26px] font-semibold text-ink">Two versions, side by side</h2>
            </div>
            <CompareView result={compareResult} />
            <FeedbackBar context={{ type: "comparison" }} />
            <Disclaimer />
          </div>
        )}

      </main>

      {tour === "landing" && onLanding && (
        <Onboarding steps={LANDING_STEPS} storageKey={LANDING_TOUR} finishLabel="Review the sample" onClose={closeTour} />
      )}
      {tour === "results" && showingSingleResults && (
        <Onboarding steps={RESULTS_STEPS} storageKey={RESULTS_TOUR} finishLabel="Done" onClose={closeTour} />
      )}
    </div>
  );
}

function FeedbackBar({ context }) {
  const [rating, setRating] = useState(null);

  function submit(value) {
    setRating(value);
    try {
      const log = JSON.parse(localStorage.getItem("contract_feedback") || "[]");
      log.push({ ...context, rating: value, timestamp: new Date().toISOString() });
      localStorage.setItem("contract_feedback", JSON.stringify(log));
    } catch {
      /* storage blocked: the thanks still shows */
    }
  }

  return (
    <div className="flex items-center gap-3 border-t border-rule py-3">
      <span className="text-[13px] text-ink-3">Was this review accurate?</span>
      {rating === null ? (
        <>
          <button onClick={() => submit("up")} className="text-ink-3 hover:text-ok" title="Yes" aria-label="Accurate"><Icon name="thumbsUp" /></button>
          <button onClick={() => submit("down")} className="text-ink-3 hover:text-mark" title="No" aria-label="Not accurate"><Icon name="thumbsDown" /></button>
        </>
      ) : (
        <span className="text-[13px] font-medium text-ink-2">
          {rating === "up" ? "Thanks." : "Thanks, noted."}
        </span>
      )}
    </div>
  );
}

FeedbackBar.propTypes = { context: PropTypes.object };

Working.propTypes = { title: PropTypes.string, detail: PropTypes.string, steps: PropTypes.array };

Failed.propTypes = { message: PropTypes.string, onRetry: PropTypes.func };
