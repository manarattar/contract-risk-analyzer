import PropTypes from 'prop-types';
import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import Icon from "./Icon";

const ACCEPTED = { "application/pdf": [".pdf"], "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"], "text/plain": [".txt"] };

export default function UploadZone({ onUpload, loading }) {
  const [error, setError] = useState("");

  const onDrop = useCallback((accepted, rejected) => {
    setError("");
    if (rejected.length > 0) {
      setError("Only PDF, DOCX, and TXT files under 10 MB are accepted.");
      return;
    }
    if (accepted.length > 0) onUpload(accepted[0]);
  }, [onUpload]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED,
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024,
    disabled: loading,
  });

  return (
    <div data-tour="upload" className="w-full">
      <div
        {...getRootProps()}
        className={`cursor-pointer rounded-[4px] border border-dashed px-6 py-10 text-center transition-colors
          ${isDragActive ? "border-ink bg-desk" : "border-ink-3 hover:border-ink hover:bg-desk"}
          ${loading ? "cursor-not-allowed opacity-50" : ""}`}
      >
        <input {...getInputProps()} />
        <Icon name="file" size={36} className="mx-auto mb-3 text-ink-3" />
        {isDragActive ? (
          <p className="text-[16px] font-medium text-ink">Drop the contract here</p>
        ) : (
          <>
            <p className="text-[16px] font-medium text-ink">Drop a contract here, or click to choose one</p>
            <p className="num mt-1.5 text-[12px] text-ink-3">PDF · DOCX · TXT — up to 10 MB</p>
          </>
        )}
      </div>
      {error && <p className="mt-2 text-center text-[13px] text-mark">{error}</p>}
    </div>
  );
}

UploadZone.propTypes = { onUpload: PropTypes.func, loading: PropTypes.bool };
