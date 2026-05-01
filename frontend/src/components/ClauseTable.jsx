import { useState } from "react";
import ClauseDetail from "./ClauseDetail";

const CATEGORY_BADGE = {
  "Best Practice":        "bg-green-100 text-green-700 border border-green-200",
  "Acceptable Standard":  "bg-blue-100 text-blue-700 border border-blue-200",
  "Minor Improvement":    "bg-yellow-100 text-yellow-700 border border-yellow-200",
  "Moderate Risk":        "bg-orange-100 text-orange-700 border border-orange-200",
  "High Risk":            "bg-red-100 text-red-700 border border-red-200",
  "Critical Risk":        "bg-red-200 text-red-900 border border-red-300",
};

const SCORE_BAR = {
  "Best Practice":        "bg-green-500",
  "Acceptable Standard":  "bg-blue-400",
  "Minor Improvement":    "bg-yellow-400",
  "Moderate Risk":        "bg-orange-500",
  "High Risk":            "bg-red-500",
  "Critical Risk":        "bg-red-700",
};

const SORT_FIELDS = ["clause_title", "clause_type", "category", "risk_score"];

function ScoreBar({ score, category }) {
  const bar = SCORE_BAR[category] || "bg-gray-400";
  return (
    <div className="flex items-center gap-2 min-w-[80px]">
      <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${bar}`} style={{ width: `${score}%` }} />
      </div>
      <span className="text-xs text-gray-500 w-6 text-right">{score}</span>
    </div>
  );
}

export default function ClauseTable({ clauses }) {
  const [selected, setSelected] = useState(null);
  const [sort, setSort] = useState({ field: "risk_score", dir: "desc" });

  const sorted = [...clauses].sort((a, b) => {
    const av = a[sort.field], bv = b[sort.field];
    if (typeof av === "number") return sort.dir === "asc" ? av - bv : bv - av;
    return sort.dir === "asc"
      ? String(av).localeCompare(String(bv))
      : String(bv).localeCompare(String(av));
  });

  const toggleSort = (field) =>
    setSort(s => ({ field, dir: s.field === field && s.dir === "desc" ? "asc" : "desc" }));

  const SortIcon = ({ field }) =>
    sort.field === field ? (sort.dir === "asc" ? " ↑" : " ↓") : " ↕";

  return (
    <>
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-50">
          <h2 className="font-semibold text-gray-900">Clause-by-Clause Review</h2>
          <p className="text-xs text-gray-400 mt-0.5">Click a row to view full details</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 text-left">
                <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider w-8">#</th>
                {[
                  { label: "Clause",   field: "clause_title" },
                  { label: "Type",     field: "clause_type" },
                  { label: "Category", field: "category" },
                  { label: "Score",    field: "risk_score" },
                ].map(({ label, field }) => (
                  <th key={field}
                    className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-800 select-none"
                    onClick={() => toggleSort(field)}
                  >
                    {label}<SortIcon field={field} />
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {sorted.map((clause, i) => {
                const cat = clause.category || "Moderate Risk";
                const badge = CATEGORY_BADGE[cat] || CATEGORY_BADGE["Moderate Risk"];
                return (
                  <tr key={i} className="hover:bg-blue-50 cursor-pointer transition-colors"
                    onClick={() => setSelected(clause)}
                  >
                    <td className="px-4 py-3 text-gray-400 text-xs">{i + 1}</td>
                    <td className="px-4 py-3 max-w-[180px]">
                      <span className="font-medium text-gray-800 truncate block">{clause.clause_title}</span>
                      {clause.enforceability_concern && (
                        <span className="text-purple-600 text-xs">⚠ enforceability concern</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs">{clause.clause_type}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${badge}`}>{cat}</span>
                    </td>
                    <td className="px-4 py-3">
                      <ScoreBar score={clause.risk_score} category={cat} />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {selected && <ClauseDetail clause={selected} onClose={() => setSelected(null)} />}
    </>
  );
}
