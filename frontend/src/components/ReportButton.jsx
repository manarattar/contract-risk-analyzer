import PropTypes from 'prop-types';
import { getReportUrl } from "../api";
import Icon from "./Icon";

export default function ReportButton({ documentId }) {
  const url = getReportUrl(documentId);

  return (
    <a
      data-tour="report"
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      download
      className="inline-flex items-center gap-2 rounded-[3px] border border-ink px-4 py-2 text-[14px] font-medium text-ink hover:bg-ink hover:text-sheet"
    >
      <Icon name="download" size={16} />
      PDF report
    </a>
  );
}

ReportButton.propTypes = { documentId: PropTypes.string };
