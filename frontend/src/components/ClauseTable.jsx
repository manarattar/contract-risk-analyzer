import PropTypes from 'prop-types';
import { useState } from "react";
import ClauseDetail from "./ClauseDetail";
import { categoryStyle } from "../theme";

const COLUMNS = [
  { label: "Clause",   field: "clause_title" },
  { label: "Type",     field: "clause_type" },
  { label: "Marked as", field: "category" },
  { label: "Score",    field: "risk_score" },
];

function ScoreBar({ score, category }) {
  const s = categoryStyle(category);
  return (
    <div className="flex min-w-[88px] items-center gap-2">
      <div className="h-1 flex-1 bg-rule">
        <div className={`h-full ${s.bar}`} style={{ width: `${score}%` }} />
      </div>
      <span className="num w-7 text-right text-[12px] text-ink-2">{score}</span>
    </div>
  );
}

export default function ClauseTable({ clauses }) {
  const [selected, setSelected] = useState(null);
  const [sort, setSort] = useState({ field: "risk_score", dir: "desc" });

  // Clause numbers follow the order in the contract, whatever the sort.
  const numbered = clauses.map((c, i) => ({ ...c, _n: i + 1 }));
  const sorted = [...numbered].sort((a, b) => {
    const av = a[sort.field], bv = b[sort.field];
    if (typeof av === "number") return sort.dir === "asc" ? av - bv : bv - av;
    return sort.dir === "asc"
      ? String(av).localeCompare(String(bv))
      : String(bv).localeCompare(String(av));
  });

  const toggleSort = (field) =>
    setSort(s => ({ field, dir: s.field === field && s.dir === "desc" ? "asc" : "desc" }));

  const arrow = (field) => (sort.field === field ? (sort.dir === "asc" ? "↑" : "↓") : "");

  return (
    <>
      <section data-tour="clauses" className="overflow-hidden rounded-[4px] border border-rule bg-sheet">
        <div className="px-5 pt-5 pb-3 sm:px-7 sm:pt-7">
          <h2 className="font-serif text-[21px] font-semibold text-ink">Clause by clause</h2>
          <p className="mt-0.5 text-[13px] text-ink-3">
            Every clause, marked up. Click one to read it with the reasoning and a suggested rewrite.
          </p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[620px] text-[14px]">
            <thead>
              <tr className="border-y border-rule text-left">
                <th className="label w-12 py-2.5 pl-5 sm:pl-7">§</th>
                {COLUMNS.map(({ label, field }) => (
                  <th key={field} className="py-2.5 pr-4">
                    <button onClick={() => toggleSort(field)} className="label hover:text-ink">
                      {label} <span className="num">{arrow(field)}</span>
                    </button>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sorted.map((clause) => {
                const cat = clause.category || "Moderate Risk";
                const s = categoryStyle(cat);
                return (
                  <tr
                    key={clause._n}
                    onClick={() => setSelected(clause)}
                    className="cursor-pointer border-b border-rule last:border-b-0 hover:bg-desk"
                  >
                    <td className="num py-3 pl-5 align-top text-[12px] text-ink-3 sm:pl-7">{clause._n}</td>
                    <td className="max-w-[240px] py-3 pr-4 align-top">
                      <span className={`block truncate font-serif text-[15px] text-ink ${s.risky && cat !== "Moderate Risk" ? "redline" : ""}`}>
                        {clause.clause_title}
                      </span>
                      {clause.enforceability_concern && (
                        <span className="text-[12px] text-mark">May not be enforceable as written</span>
                      )}
                    </td>
                    <td className="py-3 pr-4 align-top text-[13px] text-ink-3">{clause.clause_type}</td>
                    <td className="py-3 pr-4 align-top">
                      <span className={`inline-block border-l-2 ${s.rule} pl-2 text-[13px] font-medium ${s.text}`}>{cat}</span>
                      {clause.needs_review && (
                        <span className="mt-0.5 block text-[12px] text-warn" title="Jev is split between categories">
                          Check this one: low confidence
                        </span>
                      )}
                    </td>
                    <td className="py-3 pr-5 align-top sm:pr-7">
                      <ScoreBar score={clause.risk_score} category={cat} />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      {selected && <ClauseDetail clause={selected} onClose={() => setSelected(null)} />}
    </>
  );
}

ScoreBar.propTypes = { score: PropTypes.number, category: PropTypes.string };

ClauseTable.propTypes = { clauses: PropTypes.array };
