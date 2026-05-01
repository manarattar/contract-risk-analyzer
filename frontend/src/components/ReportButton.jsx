import { getReportUrl } from "../api";

export default function ReportButton({ documentId }) {
  const url = getReportUrl(documentId);

  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      download
      className="inline-flex items-center gap-2 px-5 py-2.5 bg-slate-800 text-white rounded-xl text-sm font-medium hover:bg-slate-700 transition-colors"
    >
      <span>📥</span>
      Download PDF Report
    </a>
  );
}
