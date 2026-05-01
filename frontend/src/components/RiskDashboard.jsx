import ContradictionPanel from "./ContradictionPanel";

const RISK_COLORS = {
  Low:    { text: "text-green-700",  bg: "bg-green-100",  border: "border-green-300",  ring: "#16A34A" },
  Medium: { text: "text-yellow-700", bg: "bg-yellow-100", border: "border-yellow-300", ring: "#D97706" },
  High:   { text: "text-red-700",    bg: "bg-red-100",    border: "border-red-300",    ring: "#DC2626" },
};

const RELEVANCE_STYLES = {
  "Essential":              "bg-red-50 border-red-200 text-red-700",
  "Recommended":            "bg-yellow-50 border-yellow-200 text-yellow-700",
  "Optional / Not Required":"bg-green-50 border-green-200 text-green-700",
};

const QUALITY_COLORS = {
  Strong: "text-green-700", High: "text-green-700", Balanced: "text-green-700",
  "Ready with minor refinements": "text-green-700",
  Adequate: "text-yellow-700", Medium: "text-yellow-700", "Mostly Balanced": "text-yellow-700",
  "Needs revision": "text-yellow-700",
  Weak: "text-red-700", Low: "text-red-700", "One-sided": "text-red-700",
  Poor: "text-red-700", "Not ready": "text-red-700",
};

function ScoreGauge({ score, level }) {
  const c = RISK_COLORS[level] || RISK_COLORS.Medium;
  const radius = 52;
  const circ = 2 * Math.PI * radius;
  const offset = circ - (score / 100) * circ;
  return (
    <div className="flex flex-col items-center">
      <svg width="140" height="140" className="-rotate-90">
        <circle cx="70" cy="70" r={radius} fill="none" stroke="#E5E7EB" strokeWidth="12" />
        <circle cx="70" cy="70" r={radius} fill="none" stroke={c.ring} strokeWidth="12"
          strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 1s ease" }} />
      </svg>
      <div className="-mt-20 flex flex-col items-center">
        <span className="text-4xl font-bold text-gray-900">{score}</span>
        <span className="text-sm text-gray-500">/ 100</span>
      </div>
      <span className={`mt-6 px-4 py-1 rounded-full text-sm font-semibold ${c.text} ${c.bg} ${c.border} border`}>
        {level} Risk
      </span>
    </div>
  );
}

function QualityRow({ label, value }) {
  const color = QUALITY_COLORS[value] || "text-gray-700";
  return (
    <div className="flex items-center justify-between py-1.5 border-b border-gray-50 last:border-0">
      <span className="text-xs text-gray-500">{label}</span>
      <span className={`text-xs font-semibold ${color}`}>{value}</span>
    </div>
  );
}

export default function RiskDashboard({ analysis }) {
  const {
    overall_risk_score, overall_risk_level, document_summary,
    analysis_perspective, final_recommendation,
    main_risks, minor_improvements, best_practice_clauses,
    missing_clauses, contradictions, quality_summary,
  } = analysis;

  return (
    <div className="space-y-6">

      {/* Score + Summary + Recommendation */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
        <div className="flex flex-col md:flex-row gap-8 items-start">
          <div className="shrink-0 flex flex-col items-center">
            <ScoreGauge score={overall_risk_score} level={overall_risk_level} />
            {final_recommendation && (
              <div className="mt-3 text-center">
                <span className="text-xs font-medium text-gray-500">Recommendation</span>
                <p className="text-sm font-semibold text-gray-800 mt-0.5 max-w-[130px] text-center leading-tight">
                  {final_recommendation}
                </p>
              </div>
            )}
          </div>
          <div className="flex-1 space-y-3">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <h2 className="text-xl font-semibold text-gray-900">Assessment</h2>
                {analysis_perspective && (
                  <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">
                    {analysis_perspective}
                  </span>
                )}
              </div>
              <p className="text-gray-600 leading-relaxed">{document_summary}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Quality Summary */}
      {quality_summary && (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
          <h3 className="font-semibold text-gray-900 mb-3">Contract Quality Summary</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8">
            <div>
              <QualityRow label="Legal Structure" value={quality_summary.overall_legal_structure} />
              <QualityRow label="Commercial Balance" value={quality_summary.commercial_balance} />
              <QualityRow label="Drafting Clarity" value={quality_summary.drafting_clarity} />
            </div>
            <div>
              <QualityRow label="Enforceability Confidence" value={quality_summary.enforceability_confidence} />
              <QualityRow label="Negotiation Readiness" value={quality_summary.negotiation_readiness} />
            </div>
          </div>
        </div>
      )}

      {/* Findings grid */}
      <div className="grid md:grid-cols-3 gap-4">
        {/* True Risks */}
        {main_risks?.length > 0 && (
          <div className="bg-white rounded-2xl shadow-sm border border-red-100 p-5">
            <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-red-500 inline-block" /> True Risks
            </h3>
            <ul className="space-y-1.5">
              {main_risks.map((r, i) => (
                <li key={i} className="text-sm text-gray-700 flex gap-2">
                  <span className="text-red-400 shrink-0 mt-0.5">•</span>{r}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Minor Improvements */}
        {minor_improvements?.length > 0 && (
          <div className="bg-white rounded-2xl shadow-sm border border-yellow-100 p-5">
            <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-yellow-400 inline-block" /> Minor Improvements
            </h3>
            <ul className="space-y-1.5">
              {minor_improvements.map((m, i) => (
                <li key={i} className="text-sm text-gray-700 flex gap-2">
                  <span className="text-yellow-500 shrink-0 mt-0.5">•</span>{m}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Best Practice */}
        {best_practice_clauses?.length > 0 && (
          <div className="bg-white rounded-2xl shadow-sm border border-green-100 p-5">
            <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-green-500 inline-block" /> Best-Practice Clauses
            </h3>
            <ul className="space-y-1.5">
              {best_practice_clauses.map((b, i) => (
                <li key={i} className="text-sm text-gray-700 flex gap-2">
                  <span className="text-green-500 shrink-0 mt-0.5">✓</span>{b}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Missing Clauses */}
      {missing_clauses?.length > 0 && (
        <div className="bg-white rounded-2xl shadow-sm border border-orange-100 p-5">
          <h3 className="font-semibold text-gray-900 mb-3">Missing Clauses</h3>
          <div className="space-y-2">
            {missing_clauses.map((mc, i) => {
              const s = RELEVANCE_STYLES[mc.relevance] || RELEVANCE_STYLES["Recommended"];
              return (
                <div key={i} className={`flex flex-wrap items-start gap-3 p-2.5 rounded-lg border ${s}`}>
                  <span className="text-xs font-semibold shrink-0 mt-0.5 min-w-[90px]">{mc.relevance}</span>
                  <div className="flex-1 min-w-0">
                    <span className="text-xs font-medium">{mc.clause_type}</span>
                    {mc.reason && <span className="text-xs text-current opacity-75"> — {mc.reason}</span>}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Deep Logic: Contradictions */}
      <ContradictionPanel contradictions={contradictions} />
    </div>
  );
}
