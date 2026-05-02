import { useState } from "react";

const RISK_SCORE_COLOR = (score) => {
  if (score <= 35) return "text-green-600";
  if (score <= 70) return "text-yellow-500";
  return "text-red-600";
};

const RISK_RING_COLOR = (score) => {
  if (score <= 35) return "#22c55e";
  if (score <= 70) return "#f59e0b";
  return "#ef4444";
};

const STATUS_STYLE = {
  improved: { label: "↓ Better", bg: "bg-green-50 text-green-700" },
  worsened: { label: "↑ Worse", bg: "bg-red-50 text-red-700" },
  unchanged: { label: "= Same", bg: "bg-gray-100 text-gray-500" },
  added: { label: "+ Added", bg: "bg-blue-50 text-blue-600" },
  removed: { label: "− Removed", bg: "bg-orange-50 text-orange-600" },
};

function ScoreRing({ score, riskLevel, label, colorClass }) {
  const ringColor = RISK_RING_COLOR(score);
  return (
    <div className="flex flex-col items-center gap-2">
      <p className={`text-xs font-bold uppercase tracking-widest ${colorClass}`}>{label}</p>
      <div
        className="w-24 h-24 rounded-full flex flex-col items-center justify-center border-4"
        style={{ borderColor: ringColor }}
      >
        <span className={`text-2xl font-bold ${RISK_SCORE_COLOR(score)}`}>{score}</span>
        <span className="text-xs text-gray-400">{riskLevel}</span>
      </div>
    </div>
  );
}

function ClauseRow({ comp, isExpanded, onToggle }) {
  const ss = STATUS_STYLE[comp.status] || STATUS_STYLE.unchanged;

  return (
    <>
      <div
        onClick={onToggle}
        className={`grid grid-cols-[1fr_72px_60px_72px_92px] gap-2 items-center px-5 py-3 text-sm
          border-b border-gray-50 cursor-pointer hover:bg-gray-50 transition-colors
          ${isExpanded ? "bg-gray-50" : ""}`}
      >
        <span className="font-medium text-gray-800">{comp.clause_type}</span>
        <span className={`text-center font-mono font-semibold ${comp.clause_a ? RISK_SCORE_COLOR(comp.clause_a.risk_score) : "text-gray-300"}`}>
          {comp.clause_a ? comp.clause_a.risk_score : "—"}
        </span>
        <span className={`text-center font-mono text-sm font-semibold
          ${comp.risk_delta > 0 ? "text-red-500" : comp.risk_delta < 0 ? "text-green-500" : "text-gray-300"}`}>
          {comp.risk_delta !== 0 ? `${comp.risk_delta > 0 ? "+" : ""}${comp.risk_delta}` : "—"}
        </span>
        <span className={`text-center font-mono font-semibold ${comp.clause_b ? RISK_SCORE_COLOR(comp.clause_b.risk_score) : "text-gray-300"}`}>
          {comp.clause_b ? comp.clause_b.risk_score : "—"}
        </span>
        <span className="flex justify-end">
          <span className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${ss.bg}`}>{ss.label}</span>
        </span>
      </div>

      {isExpanded && (
        <div className="grid grid-cols-2 gap-0 border-b border-gray-100 bg-slate-50">
          {[
            { clause: comp.clause_a, label: "Contract A", colorClass: "text-blue-600" },
            { clause: comp.clause_b, label: "Contract B", colorClass: "text-purple-600" },
          ].map(({ clause, label, colorClass }) => (
            <div key={label} className="px-5 py-4 border-r last:border-r-0 border-gray-100">
              <p className={`text-xs font-bold mb-2 ${colorClass}`}>{label}</p>
              {clause ? (
                <div className="space-y-2 text-xs text-gray-600">
                  <p>
                    <span className="font-semibold text-gray-700">Risk: </span>
                    {clause.risk_explanation}
                  </p>
                  {clause.suggested_revision && (
                    <p>
                      <span className="font-semibold text-gray-700">Suggested: </span>
                      {clause.suggested_revision}
                    </p>
                  )}
                  <p>
                    <span className="font-semibold text-gray-700">Advice: </span>
                    {clause.negotiation_advice}
                  </p>
                </div>
              ) : (
                <p className="text-xs text-gray-400 italic">Not present in this contract</p>
              )}
            </div>
          ))}
        </div>
      )}
    </>
  );
}

export default function CompareView({ result }) {
  const [expandedRow, setExpandedRow] = useState(null);

  const {
    analysis_a, analysis_b,
    clause_comparisons, overall_delta, winner,
    key_differences, contract_a_name, contract_b_name,
  } = result;

  const winnerText =
    winner === "a" ? "Contract A is lower risk"
    : winner === "b" ? "Contract B is lower risk"
    : "Both contracts carry equal risk";

  const winnerColor =
    winner === "a" ? "text-blue-600"
    : winner === "b" ? "text-purple-600"
    : "text-gray-600";

  const deltaText =
    overall_delta > 0
      ? `Contract B is +${overall_delta} pts riskier`
      : overall_delta < 0
      ? `Contract B is ${Math.abs(overall_delta)} pts safer`
      : "Equal overall risk scores";

  return (
    <div className="space-y-6">
      {/* Score header */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
        <div className="grid grid-cols-3 gap-4 items-center">
          <div className="flex flex-col items-center gap-1">
            <ScoreRing
              score={analysis_a.overall_risk_score}
              riskLevel={analysis_a.overall_risk_level}
              label="Contract A"
              colorClass="text-blue-600"
            />
            <p className="text-xs text-gray-400 text-center max-w-36 truncate" title={contract_a_name}>
              {contract_a_name}
            </p>
          </div>

          <div className="flex flex-col items-center gap-3 text-center">
            <span className={`text-base font-bold ${winnerColor}`}>{winnerText}</span>
            <span className={`text-xs px-3 py-1 rounded-full font-medium
              ${overall_delta > 0 ? "bg-purple-50 text-purple-600"
                : overall_delta < 0 ? "bg-blue-50 text-blue-600"
                : "bg-gray-100 text-gray-500"}`}>
              {deltaText}
            </span>
          </div>

          <div className="flex flex-col items-center gap-1">
            <ScoreRing
              score={analysis_b.overall_risk_score}
              riskLevel={analysis_b.overall_risk_level}
              label="Contract B"
              colorClass="text-purple-600"
            />
            <p className="text-xs text-gray-400 text-center max-w-36 truncate" title={contract_b_name}>
              {contract_b_name}
            </p>
          </div>
        </div>
      </div>

      {/* Key differences */}
      {key_differences.length > 0 && (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
          <h3 className="font-semibold text-gray-800 mb-3 text-sm uppercase tracking-wide">Key Differences</h3>
          <ul className="space-y-1.5">
            {key_differences.map((diff, i) => (
              <li key={i} className="text-sm text-gray-600 flex gap-2">
                <span className="text-gray-300 mt-0.5">•</span>
                {diff}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Clause comparison table */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="grid grid-cols-[1fr_72px_60px_72px_92px] gap-2 px-5 py-3 border-b border-gray-100
          text-xs font-semibold text-gray-400 uppercase tracking-wide bg-gray-50">
          <span>Clause</span>
          <span className="text-center text-blue-500">A Score</span>
          <span className="text-center">Δ</span>
          <span className="text-center text-purple-500">B Score</span>
          <span className="text-right">Status</span>
        </div>

        {clause_comparisons.map((comp, i) => (
          <ClauseRow
            key={i}
            comp={comp}
            isExpanded={expandedRow === i}
            onToggle={() => setExpandedRow(expandedRow === i ? null : i)}
          />
        ))}
      </div>

      <p className="text-xs text-gray-400 text-center">
        Click any row to see clause details and negotiation advice
      </p>
    </div>
  );
}
