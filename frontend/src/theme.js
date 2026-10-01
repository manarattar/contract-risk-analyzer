// Shared markup styles. Class strings are written out in full so Tailwind finds them.

/** Clause categories, from best to worst, with the ink each is marked in. */
export const CATEGORY = {
  "Best Practice":       { text: "text-ok",   soft: "bg-ok-soft",   bar: "bg-ok",   rule: "border-ok",   risky: false },
  "Acceptable Standard": { text: "text-ok",   soft: "bg-ok-soft",   bar: "bg-ok",   rule: "border-ok",   risky: false },
  "Minor Improvement":   { text: "text-warn", soft: "bg-warn-soft", bar: "bg-warn", rule: "border-warn", risky: false },
  "Moderate Risk":       { text: "text-warn", soft: "bg-warn-soft", bar: "bg-warn", rule: "border-warn", risky: true },
  "High Risk":           { text: "text-mark", soft: "bg-mark-soft", bar: "bg-mark", rule: "border-mark", risky: true },
  "Critical Risk":       { text: "text-mark", soft: "bg-mark-soft", bar: "bg-mark", rule: "border-mark", risky: true },
};

export const CATEGORY_ORDER = [
  "Best Practice", "Acceptable Standard", "Minor Improvement",
  "Moderate Risk", "High Risk", "Critical Risk",
];

export const categoryStyle = (category) => CATEGORY[category] || CATEGORY["Moderate Risk"];

/** The backend's bands for the overall score: up to 35 low, up to 70 medium, above that high. */
export const BANDS = [
  { level: "Low",    from: 0,  to: 35,  soft: "bg-ok-soft",   text: "text-ok" },
  { level: "Medium", from: 35, to: 70,  soft: "bg-warn-soft", text: "text-warn" },
  { level: "High",   from: 70, to: 100, soft: "bg-mark-soft", text: "text-mark" },
];

export const scoreText = (score) =>
  score <= 35 ? "text-ok" : score <= 70 ? "text-warn" : "text-mark";

export const levelText = (level) =>
  ({ Low: "text-ok", Medium: "text-warn", High: "text-mark" })[level] || "text-ink";

/** A plain-text value counts as empty when the model wrote "none" or similar. */
export const hasText = (value) =>
  Boolean(value) && !["none", "none required", "n/a", ""].includes(String(value).trim().toLowerCase());
