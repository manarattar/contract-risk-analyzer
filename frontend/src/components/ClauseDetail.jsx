const CATEGORY_STYLES = {
  "Best Practice":        { badge: "bg-green-100 text-green-700 border-green-300",  bar: "bg-green-500" },
  "Acceptable Standard":  { badge: "bg-blue-100 text-blue-700 border-blue-300",     bar: "bg-blue-500" },
  "Minor Improvement":    { badge: "bg-yellow-100 text-yellow-700 border-yellow-300", bar: "bg-yellow-400" },
  "Moderate Risk":        { badge: "bg-orange-100 text-orange-700 border-orange-300", bar: "bg-orange-500" },
  "High Risk":            { badge: "bg-red-100 text-red-700 border-red-300",         bar: "bg-red-500" },
  "Critical Risk":        { badge: "bg-red-200 text-red-900 border-red-400",         bar: "bg-red-700" },
};

const PARTY_LABEL = {
  "Client":       "bg-sky-100 text-sky-700",
  "Provider":     "bg-violet-100 text-violet-700",
  "Both Parties": "bg-gray-100 text-gray-600",
};

function Section({ label, children }) {
  return (
    <div>
      <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">{label}</p>
      <p className="text-sm text-gray-700 leading-relaxed">{children}</p>
    </div>
  );
}

export default function ClauseDetail({ clause, onClose }) {
  if (!clause) return null;
  const cat = clause.category || "Moderate Risk";
  const s = CATEGORY_STYLES[cat] || CATEGORY_STYLES["Moderate Risk"];
  const partyStyle = PARTY_LABEL[clause.affected_party] || PARTY_LABEL["Both Parties"];

  const showRevision = clause.suggested_revision &&
    !["none required", "none"].includes(clause.suggested_revision.toLowerCase());
  const showIssue = clause.risk_explanation &&
    !["none", ""].includes(clause.risk_explanation.toLowerCase());
  const showWorks = clause.what_works_well &&
    !["none", "n/a", ""].includes(clause.what_works_well.toLowerCase());

  return (
    <div className="fixed inset-0 z-50 flex justify-end" onClick={onClose}>
      <div
        className="w-full max-w-lg bg-white shadow-2xl h-full overflow-y-auto flex flex-col"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-100 px-6 py-4 flex items-start justify-between gap-4">
          <div>
            <h3 className="font-semibold text-gray-900 text-base leading-tight">{clause.clause_title}</h3>
            <span className="text-xs text-gray-400">{clause.clause_type}</span>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <span className={`px-2 py-0.5 border rounded-full text-xs font-medium ${s.badge}`}>{cat}</span>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-700 text-xl leading-none">✕</button>
          </div>
        </div>

        {/* Score bar + affected party */}
        <div className="px-6 py-3 border-b border-gray-50 flex items-center gap-4">
          <div className="flex-1">
            <div className="flex justify-between text-xs text-gray-500 mb-1">
              <span>Risk Score</span>
              <span className="font-semibold">{clause.risk_score}/100</span>
            </div>
            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div className={`h-full rounded-full transition-all duration-700 ${s.bar}`}
                style={{ width: `${clause.risk_score}%` }} />
            </div>
          </div>
          {clause.affected_party && (
            <span className={`text-xs font-medium px-2 py-0.5 rounded-full shrink-0 ${partyStyle}`}>
              Affects: {clause.affected_party}
            </span>
          )}
        </div>

        {/* Enforceability warning */}
        {clause.enforceability_concern && (
          <div className="mx-6 mt-3 px-3 py-2 rounded-lg bg-purple-50 border border-purple-200 text-xs text-purple-700 font-medium">
            Enforceability concern — this clause may not hold up in court as written.
          </div>
        )}

        {/* Content */}
        <div className="px-6 py-5 space-y-5 flex-1">
          <Section label="Original Text">
            <span className="italic text-gray-500">{clause.original_text}</span>
          </Section>

          {showWorks && (
            <Section label="What Works Well">{clause.what_works_well}</Section>
          )}

          {showIssue && (
            <Section label="Issue">{clause.risk_explanation}</Section>
          )}

          {showRevision && (
            <Section label="Suggested Revision">{clause.suggested_revision}</Section>
          )}

          {clause.negotiation_advice && !["none required", "none"].includes(clause.negotiation_advice.toLowerCase()) && (
            <Section label="Negotiation Advice">{clause.negotiation_advice}</Section>
          )}
        </div>
      </div>
    </div>
  );
}
