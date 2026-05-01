const SEVERITY_COLORS = {
  Low: { text: "text-green-700", bg: "bg-green-50", border: "border-green-200", badge: "bg-green-100 text-green-700" },
  Medium: { text: "text-yellow-700", bg: "bg-yellow-50", border: "border-yellow-300", badge: "bg-yellow-100 text-yellow-700" },
  High: { text: "text-red-700", bg: "bg-red-50", border: "border-red-300", badge: "bg-red-100 text-red-700" },
};

const TYPE_ICON = {
  "Logical Conflict": "⚡",
  "Self-Defeating": "♻️",
  "Ownership Conflict": "⚖️",
  "Nullification": "🚫",
  "Scope Conflict": "🔀",
};

export default function ContradictionPanel({ contradictions }) {
  if (!contradictions || contradictions.length === 0) return null;

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-purple-200 p-5">
      <h3 className="font-semibold text-gray-900 mb-1 flex items-center gap-2">
        <span>🔍</span> Deep Logic Issues
        <span className="ml-auto text-xs font-medium px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full">
          {contradictions.length} found
        </span>
      </h3>
      <p className="text-xs text-gray-400 mb-4">
        Cross-clause contradictions and self-defeating provisions identified by deep logical analysis.
      </p>

      <div className="space-y-3">
        {contradictions.map((c, i) => {
          const sc = SEVERITY_COLORS[c.severity] || SEVERITY_COLORS.Medium;
          const icon = TYPE_ICON[c.contradiction_type] || "⚠️";
          return (
            <div key={i} className={`rounded-xl border p-4 ${sc.bg} ${sc.border}`}>
              <div className="flex flex-wrap items-center gap-2 mb-2">
                <span className="text-base">{icon}</span>
                <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${sc.badge}`}>
                  {c.severity} · {c.contradiction_type}
                </span>
                <span className="text-xs font-medium text-gray-700 truncate">
                  {c.clause_a_title}
                  {c.clause_b_title && (
                    <span className="text-gray-400"> ↔ {c.clause_b_title}</span>
                  )}
                </span>
              </div>
              <p className="text-sm text-gray-800 mb-1">{c.description}</p>
              <p className="text-xs text-gray-500 italic">Impact: {c.impact}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
