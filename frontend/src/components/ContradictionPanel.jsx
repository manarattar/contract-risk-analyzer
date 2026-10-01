import PropTypes from 'prop-types';
import Icon from "./Icon";

const SEVERITY = {
  Low:    { text: "text-ok",   rule: "border-ok" },
  Medium: { text: "text-warn", rule: "border-warn" },
  High:   { text: "text-mark", rule: "border-mark" },
};

const TYPE_ICON = {
  "Logical Conflict": "zap",
  "Self-Defeating": "recycle",
  "Ownership Conflict": "scale",
  "Nullification": "ban",
  "Scope Conflict": "shuffle",
};

export default function ContradictionPanel({ contradictions }) {
  if (!contradictions || contradictions.length === 0) return null;

  return (
    <section data-tour="contradictions" className="rounded-[4px] border border-rule bg-sheet p-5 sm:p-7">
      <h3 className="flex items-baseline gap-3 font-serif text-[19px] font-semibold text-ink">
        Clauses that work against each other
        <span className="num ml-auto font-sans text-[12px] font-normal text-ink-3">{contradictions.length} found</span>
      </h3>
      <p className="mt-0.5 text-[13px] text-ink-3">
        Read across the whole contract: one clause cancelling, overriding or contradicting another.
      </p>

      <ul className="mt-4 space-y-4">
        {contradictions.map((c, i) => {
          const s = SEVERITY[c.severity] || SEVERITY.Medium;
          return (
            <li key={i} className={`border-l-2 ${s.rule} pl-4`}>
              <p className="flex flex-wrap items-center gap-x-2 gap-y-1 text-[12px]">
                <Icon name={TYPE_ICON[c.contradiction_type] || "alert"} size={14} className={s.text} />
                <span className={`font-semibold uppercase tracking-[0.06em] ${s.text}`}>{c.severity}</span>
                <span className="text-ink-3">{c.contradiction_type}</span>
              </p>
              <p className="mt-1 font-serif text-[15px] font-semibold text-ink">
                {c.clause_a_title}
                {c.clause_b_title && <span className="font-normal text-ink-3"> ↔ </span>}
                {c.clause_b_title}
              </p>
              <p className="mt-1 text-[14px] leading-snug text-ink-2">{c.description}</p>
              {c.impact && <p className="mt-1 text-[13px] text-ink-3">Impact: {c.impact}</p>}
            </li>
          );
        })}
      </ul>
    </section>
  );
}

ContradictionPanel.propTypes = { contradictions: PropTypes.array };
