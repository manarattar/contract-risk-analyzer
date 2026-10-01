import PropTypes from 'prop-types';
import { useEffect } from "react";
import { CATEGORY_ORDER, categoryStyle, hasText } from "../theme";

function JevDecision({ clause }) {
  const probs = clause.category_probabilities || {};
  return (
    <div className="rounded-[4px] border border-rule bg-desk px-4 py-3">
      <div className="flex items-baseline justify-between gap-3">
        <p className="text-[13px] font-semibold text-ink">Category decided by Jev</p>
        <p className="text-[12px] text-ink-3">
          <span className="num">{Math.round((clause.decision_confidence ?? 0) * 100)}%</span> confident
        </p>
      </div>
      <div className="mt-2 space-y-1">
        {CATEGORY_ORDER.filter(c => c in probs).map(c => {
          const chosen = c === clause.category;
          return (
            <div key={c} className="grid grid-cols-[128px_1fr_36px] items-center gap-2 text-[12px]">
              <span className={chosen ? "font-medium text-ink" : "text-ink-3"}>{c}</span>
              <div className="h-1 bg-rule">
                <div className={`h-full ${chosen ? categoryStyle(c).bar : "bg-ink-3"}`} style={{ width: `${probs[c] * 100}%` }} />
              </div>
              <span className="num text-right text-ink-2">{Math.round(probs[c] * 100)}%</span>
            </div>
          );
        })}
      </div>
      {clause.needs_review && (
        <p className="mt-2 text-[12px] font-medium text-warn">
          Low confidence: Jev is split between categories, so a person should check this clause.
        </p>
      )}
      <p className="mt-2 text-[12px] leading-snug text-ink-3">
        The risk score is the probability-weighted average of the category bands, not a number the AI picked.
        The explanation below is written by an LLM that was told this decision.
      </p>
    </div>
  );
}

function Section({ label, children }) {
  return (
    <section>
      <p className="label mb-1">{label}</p>
      <div className="text-[14.5px] leading-relaxed text-ink-2">{children}</div>
    </section>
  );
}

export default function ClauseDetail({ clause, onClose }) {
  useEffect(() => {
    const onKey = (e) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  if (!clause) return null;
  const cat = clause.category || "Moderate Risk";
  const s = categoryStyle(cat);

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-[var(--scrim)]" onClick={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="clause-title"
        className="flex h-full w-full max-w-xl flex-col overflow-y-auto border-l border-rule bg-sheet"
        onClick={e => e.stopPropagation()}
      >
        <div className="sticky top-0 z-10 flex items-start justify-between gap-4 border-b border-rule bg-sheet px-6 py-4">
          <div className="min-w-0">
            <p className="label">
              {clause._n ? <span className="num">§ {clause._n} · </span> : null}{clause.clause_type}
            </p>
            <h3 id="clause-title" className="mt-0.5 font-serif text-[20px] font-semibold leading-tight text-ink">{clause.clause_title}</h3>
          </div>
          <button onClick={onClose} aria-label="Close" className="shrink-0 rounded-[3px] border border-rule px-2.5 py-1 text-[13px] text-ink-2 hover:text-ink">
            Close
          </button>
        </div>

        <div className="flex flex-wrap items-center gap-x-6 gap-y-2 border-b border-rule px-6 py-3">
          <span className={`border-l-2 ${s.rule} pl-2 text-[14px] font-semibold ${s.text}`}>{cat}</span>
          <span className="text-[13px] text-ink-3">Risk score <span className="num font-semibold text-ink">{clause.risk_score}</span>/100</span>
          {clause.affected_party && (
            <span className="text-[13px] text-ink-3">Affects <span className="font-medium text-ink">{clause.affected_party}</span></span>
          )}
        </div>

        <div className="flex-1 space-y-6 px-6 py-5">
          {/* The clause as written, with the margin bar in the ink it was marked in */}
          <section>
            <p className="label mb-1.5">As written</p>
            <blockquote className={`border-l-2 ${s.rule} pl-4 font-serif text-[16px] leading-relaxed text-ink`}>
              {clause.original_text}
            </blockquote>
            {clause.enforceability_concern && (
              <p className="mt-2 pl-4 text-[13px] font-medium text-mark">
                May not hold up in court as written.
              </p>
            )}
          </section>

          {clause.decided_by === "jev" && <JevDecision clause={clause} />}

          {hasText(clause.what_works_well) && <Section label="What works">{clause.what_works_well}</Section>}
          {hasText(clause.risk_explanation) && <Section label="The problem">{clause.risk_explanation}</Section>}

          {hasText(clause.suggested_revision) && (
            <section>
              <p className="label mb-1.5">Suggested rewrite</p>
              {/* insertions are underlined in the revision ink, as in a tracked-changes draft */}
              <p className="border-l-2 border-rev pl-4 font-serif text-[16px] leading-relaxed text-rev underline decoration-rev/40 underline-offset-[4px]">
                {clause.suggested_revision}
              </p>
            </section>
          )}

          {hasText(clause.negotiation_advice) && <Section label="When negotiating">{clause.negotiation_advice}</Section>}
        </div>
      </div>
    </div>
  );
}

JevDecision.propTypes = { clause: PropTypes.object };

Section.propTypes = { label: PropTypes.string, children: PropTypes.node };

ClauseDetail.propTypes = { clause: PropTypes.object, onClose: PropTypes.func };
