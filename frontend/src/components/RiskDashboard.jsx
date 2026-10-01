import PropTypes from 'prop-types';
import ContradictionPanel from "./ContradictionPanel";
import RiskRuler from "./RiskRuler";
import { levelText } from "../theme";

const RELEVANCE = {
  "Essential":               { text: "text-mark", label: "Essential" },
  "Recommended":             { text: "text-warn", label: "Recommended" },
  "Optional / Not Required": { text: "text-ink-3", label: "Optional" },
};

const QUALITY_TONE = {
  Strong: "text-ok", High: "text-ok", Balanced: "text-ok",
  "Ready with minor refinements": "text-ok",
  Adequate: "text-warn", Medium: "text-warn", "Mostly Balanced": "text-warn",
  "Needs revision": "text-warn",
  Weak: "text-mark", Low: "text-mark", "One-sided": "text-mark",
  Poor: "text-mark", "Not ready": "text-mark",
};

function QualityCell({ label, value }) {
  if (!value) return null;
  return (
    <div className="border-t border-rule pt-2">
      <dt className="text-[12px] text-ink-3">{label}</dt>
      <dd className={`mt-0.5 text-[14px] font-semibold ${QUALITY_TONE[value] || "text-ink"}`}>{value}</dd>
    </div>
  );
}

/** One column of findings, headed by a rule in its ink like a reviewer's colour-coded pen. */
function Findings({ title, items, rule, marker, markerClass }) {
  if (!items?.length) return null;
  return (
    <section className={`border-t-2 ${rule} pt-3`}>
      <h3 className="flex items-baseline justify-between text-[14px] font-semibold text-ink">
        {title}
        <span className="num text-[12px] font-normal text-ink-3">{items.length}</span>
      </h3>
      <ul className="mt-2 space-y-2">
        {items.map((text, i) => (
          <li key={i} className="grid grid-cols-[14px_1fr] gap-1.5 text-[14px] leading-snug text-ink-2">
            <span className={`font-semibold ${markerClass}`} aria-hidden>{marker}</span>
            <span>{text}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

export default function RiskDashboard({ analysis }) {
  const {
    overall_risk_score, overall_risk_level, document_summary,
    analysis_perspective, final_recommendation,
    main_risks, minor_improvements, best_practice_clauses,
    missing_clauses, contradictions, quality_summary,
  } = analysis;

  const markerTone = { Low: "bg-ok", Medium: "bg-warn", High: "bg-mark" }[overall_risk_level] || "bg-ink";

  return (
    <div className="space-y-5">

      {/* Overall score, recommendation and assessment */}
      <section data-tour="score" className="rounded-[4px] border border-rule bg-sheet p-5 sm:p-7">
        <div className="flex flex-wrap items-start justify-between gap-x-8 gap-y-3">
          <div>
            <p className="label">Overall risk</p>
            <p className="mt-1 flex items-baseline gap-3">
              <span className="num text-[44px] font-semibold leading-none text-ink">{overall_risk_score}</span>
              <span className="num text-[15px] text-ink-3">/ 100</span>
              <span className={`text-[17px] font-semibold ${levelText(overall_risk_level)}`}>{overall_risk_level} risk</span>
            </p>
          </div>
          {final_recommendation && (
            <div className="max-w-xs sm:text-right">
              <p className="label">Recommendation</p>
              <p className="mt-1 font-serif text-[18px] font-semibold leading-snug text-ink">{final_recommendation}</p>
            </div>
          )}
        </div>

        <RiskRuler markers={[{ score: overall_risk_score, tone: markerTone }]} />

        <div className="mt-6 border-t border-rule pt-5">
          <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
            <h2 className="font-serif text-[21px] font-semibold text-ink">Assessment</h2>
            {analysis_perspective && <span className="text-[13px] text-ink-3">Read from the side of: {analysis_perspective}</span>}
          </div>
          <p className="mt-2 max-w-[68ch] font-serif text-[16.5px] leading-relaxed text-ink-2">{document_summary}</p>
        </div>

        {quality_summary && (
          <dl className="mt-6 grid grid-cols-2 gap-x-6 gap-y-3 sm:grid-cols-3 lg:grid-cols-5">
            <QualityCell label="Legal structure" value={quality_summary.overall_legal_structure} />
            <QualityCell label="Commercial balance" value={quality_summary.commercial_balance} />
            <QualityCell label="Drafting clarity" value={quality_summary.drafting_clarity} />
            <QualityCell label="Enforceability" value={quality_summary.enforceability_confidence} />
            <QualityCell label="Ready to negotiate" value={quality_summary.negotiation_readiness} />
          </dl>
        )}
      </section>

      {/* Findings */}
      {(main_risks?.length > 0 || minor_improvements?.length > 0 || best_practice_clauses?.length > 0) && (
        <section data-tour="findings" className="grid gap-6 rounded-[4px] border border-rule bg-sheet p-5 sm:p-7 md:grid-cols-3">
          <Findings title="Real risks" items={main_risks} rule="border-mark" marker="×" markerClass="text-mark" />
          <Findings title="Worth tightening" items={minor_improvements} rule="border-warn" marker="~" markerClass="text-warn" />
          <Findings title="Done well" items={best_practice_clauses} rule="border-ok" marker="✓" markerClass="text-ok" />
        </section>
      )}

      {/* Missing clauses, marked as insertions the way a redline marks added text */}
      {missing_clauses?.length > 0 && (
        <section className="rounded-[4px] border border-rule bg-sheet p-5 sm:p-7">
          <h3 className="font-serif text-[19px] font-semibold text-ink">Missing clauses</h3>
          <p className="mt-0.5 text-[13px] text-ink-3">Clauses a contract like this usually has, which this one doesn’t.</p>
          <ul className="mt-3">
            {missing_clauses.map((mc, i) => {
              const r = RELEVANCE[mc.relevance] || RELEVANCE.Recommended;
              return (
                <li key={i} className="grid gap-x-4 gap-y-0.5 border-t border-rule py-2.5 sm:grid-cols-[110px_1fr]">
                  <span className={`text-[12px] font-semibold uppercase tracking-[0.06em] ${r.text}`}>{r.label}</span>
                  <p className="text-[14px] leading-snug text-ink-2">
                    <span className="font-semibold text-rev" aria-hidden>+ </span>
                    <span className="font-medium text-rev underline decoration-rev/50 underline-offset-[3px]">{mc.clause_type}</span>
                    {mc.reason && <span> — {mc.reason}</span>}
                  </p>
                </li>
              );
            })}
          </ul>
        </section>
      )}

      <ContradictionPanel contradictions={contradictions} />
    </div>
  );
}

QualityCell.propTypes = { label: PropTypes.string, value: PropTypes.string };

Findings.propTypes = {
  title: PropTypes.string, items: PropTypes.array, rule: PropTypes.string,
  marker: PropTypes.string, markerClass: PropTypes.string,
};

RiskDashboard.propTypes = { analysis: PropTypes.object };
