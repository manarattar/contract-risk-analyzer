import PropTypes from 'prop-types';
import { useState } from "react";
import RiskRuler from "./RiskRuler";
import { scoreText, levelText } from "../theme";

/** How a clause changed from A to B, in redline terms. */
const STATUS = {
  improved:  { label: "Safer",   cls: "text-ok" },
  worsened:  { label: "Riskier", cls: "text-mark" },
  unchanged: { label: "Same",    cls: "text-ink-3" },
  added:     { label: "Added",   cls: "text-rev underline decoration-rev/50 underline-offset-2" },
  removed:   { label: "Removed", cls: "text-mark line-through" },
};

const GRID = "grid grid-cols-[minmax(140px,1fr)_56px_56px_56px_84px] gap-2";

function Side({ letter, tone, name, analysis }) {
  return (
    <div className="min-w-0">
      <p className={`text-[12px] font-semibold uppercase tracking-[0.08em] ${tone}`}>Version {letter}</p>
      <p className="truncate text-[13px] text-ink-3" title={name}>{name}</p>
      <p className="mt-1 flex items-baseline gap-2">
        <span className="num text-[32px] font-semibold leading-none text-ink">{analysis.overall_risk_score}</span>
        <span className={`text-[14px] font-semibold ${levelText(analysis.overall_risk_level)}`}>{analysis.overall_risk_level} risk</span>
      </p>
    </div>
  );
}

function ClauseRow({ comp, isExpanded, onToggle }) {
  const st = STATUS[comp.status] || STATUS.unchanged;

  return (
    <>
      <button
        onClick={onToggle}
        aria-expanded={isExpanded}
        className={`${GRID} w-full items-center border-b border-rule px-5 py-2.5 text-left text-[14px] hover:bg-desk sm:px-7 ${isExpanded ? "bg-desk" : ""}`}
      >
        <span className="font-serif text-[15px] text-ink">{comp.clause_type}</span>
        <span className={`num text-center font-semibold ${comp.clause_a ? scoreText(comp.clause_a.risk_score) : "text-ink-3"}`}>
          {comp.clause_a ? comp.clause_a.risk_score : "—"}
        </span>
        <span className={`num text-center text-[13px] ${comp.risk_delta > 0 ? "text-mark" : comp.risk_delta < 0 ? "text-ok" : "text-ink-3"}`}>
          {comp.risk_delta !== 0 ? `${comp.risk_delta > 0 ? "+" : ""}${comp.risk_delta}` : "—"}
        </span>
        <span className={`num text-center font-semibold ${comp.clause_b ? scoreText(comp.clause_b.risk_score) : "text-ink-3"}`}>
          {comp.clause_b ? comp.clause_b.risk_score : "—"}
        </span>
        <span className={`text-right text-[13px] font-medium ${st.cls}`}>{st.label}</span>
      </button>

      {isExpanded && (
        <div className="grid border-b border-rule bg-desk sm:grid-cols-2">
          {[
            { clause: comp.clause_a, label: "Version A", tone: "text-ink" },
            { clause: comp.clause_b, label: "Version B", tone: "text-rev" },
          ].map(({ clause, label, tone }) => (
            <div key={label} className="border-rule px-5 py-4 sm:px-7 sm:[&:first-child]:border-r">
              <p className={`text-[12px] font-semibold uppercase tracking-[0.08em] ${tone}`}>{label}</p>
              {clause ? (
                <div className="mt-2 space-y-2 text-[13.5px] leading-snug text-ink-2">
                  <p><span className="font-semibold text-ink">Risk: </span>{clause.risk_explanation}</p>
                  {clause.suggested_revision && (
                    <p><span className="font-semibold text-ink">Suggested: </span>{clause.suggested_revision}</p>
                  )}
                  <p><span className="font-semibold text-ink">Advice: </span>{clause.negotiation_advice}</p>
                </div>
              ) : (
                <p className="mt-2 text-[13px] italic text-ink-3">Not in this version.</p>
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
    winner === "a" ? "Version A is the safer one to sign"
    : winner === "b" ? "Version B is the safer one to sign"
    : "Both versions carry the same risk";

  const deltaText =
    overall_delta > 0
      ? `B scores ${overall_delta} points riskier than A`
      : overall_delta < 0
      ? `B scores ${Math.abs(overall_delta)} points safer than A`
      : "Same overall score";

  return (
    <div className="space-y-5">
      <section className="rounded-[4px] border border-rule bg-sheet p-5 sm:p-7">
        <h2 className="font-serif text-[22px] font-semibold text-ink">{winnerText}</h2>
        <p className="mt-0.5 text-[14px] text-ink-3">{deltaText}</p>

        <div className="mt-5 grid grid-cols-2 gap-6">
          <Side letter="A" tone="text-ink" name={contract_a_name} analysis={analysis_a} />
          <Side letter="B" tone="text-rev" name={contract_b_name} analysis={analysis_b} />
        </div>

        <RiskRuler
          markers={[
            { score: analysis_a.overall_risk_score, label: "A", tone: "bg-ink" },
            { score: analysis_b.overall_risk_score, label: "B", tone: "bg-rev" },
          ]}
        />
      </section>

      {key_differences.length > 0 && (
        <section className="rounded-[4px] border border-rule bg-sheet p-5 sm:p-7">
          <h3 className="font-serif text-[19px] font-semibold text-ink">What changed</h3>
          <ul className="mt-3 space-y-2">
            {key_differences.map((diff, i) => (
              <li key={i} className="grid grid-cols-[14px_1fr] gap-1.5 text-[14px] leading-snug text-ink-2">
                <span className="text-ink-3" aria-hidden>–</span>{diff}
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="overflow-hidden rounded-[4px] border border-rule bg-sheet">
        <div className="px-5 pt-5 pb-3 sm:px-7">
          <h3 className="font-serif text-[19px] font-semibold text-ink">Clause by clause</h3>
          <p className="mt-0.5 text-[13px] text-ink-3">Click a row to see both versions with negotiation advice.</p>
        </div>
        <div className="overflow-x-auto">
          <div className="min-w-[460px]">
            <div className={`${GRID} label border-y border-rule px-5 py-2.5 sm:px-7`}>
              <span>Clause</span>
              <span className="text-center">A</span>
              <span className="text-center">Change</span>
              <span className="text-center text-rev">B</span>
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
        </div>
      </section>
    </div>
  );
}

Side.propTypes = { letter: PropTypes.string, tone: PropTypes.string, name: PropTypes.string, analysis: PropTypes.object };

ClauseRow.propTypes = { comp: PropTypes.object, isExpanded: PropTypes.bool, onToggle: PropTypes.func };

CompareView.propTypes = { result: PropTypes.object };
