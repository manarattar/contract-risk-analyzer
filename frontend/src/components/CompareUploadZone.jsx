import PropTypes from 'prop-types';
import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";

const ACCEPT = {
  "application/pdf": [".pdf"],
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
  "text/plain": [".txt"],
};

const TONE = {
  ink: { letter: "bg-ink text-sheet", label: "text-ink" },
  rev: { letter: "bg-rev text-sheet", label: "text-rev" },
};

function FileDropzone({ label, hint, file, onFile, letter, tone }) {
  const onDrop = useCallback((accepted) => {
    if (accepted[0]) onFile(accepted[0]);
  }, [onFile]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPT,
    maxFiles: 1,
  });
  const t = TONE[tone];

  return (
    <div
      {...getRootProps()}
      className={`flex-1 cursor-pointer rounded-[4px] border border-dashed p-5 transition-colors
        ${isDragActive ? "border-ink bg-desk" : file ? "border-rule" : "border-ink-3 hover:border-ink hover:bg-desk"}`}
    >
      <input {...getInputProps()} />
      <div className="flex items-start gap-3">
        <span className={`num flex h-7 w-7 shrink-0 items-center justify-center rounded-[3px] text-[14px] font-semibold ${t.letter}`}>
          {letter}
        </span>
        <div className="min-w-0">
          <p className={`text-[14px] font-semibold ${t.label}`}>{label}</p>
          {file ? (
            <p className="mt-0.5 break-all text-[13px] text-ink">
              {file.name} <span className="text-ok">· ready</span>
            </p>
          ) : (
            <p className="mt-0.5 text-[13px] text-ink-3">{hint}</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default function CompareUploadZone({ onCompare, loading }) {
  const [fileA, setFileA] = useState(null);
  const [fileB, setFileB] = useState(null);

  const canCompare = fileA && fileB && !loading;

  return (
    <div data-tour="upload" className="flex w-full flex-col gap-4">
      <div className="flex w-full flex-col items-stretch gap-3 sm:flex-row">
        <FileDropzone label="Version A" hint="The draft you started from. Drop or click." file={fileA} onFile={setFileA} letter="A" tone="ink" />
        <FileDropzone label="Version B" hint="The revised draft. Drop or click." file={fileB} onFile={setFileB} letter="B" tone="rev" />
      </div>

      <button
        onClick={() => canCompare && onCompare(fileA, fileB)}
        disabled={!canCompare}
        className="w-full rounded-[3px] bg-ink py-2.5 text-[14px] font-medium text-sheet hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-30"
      >
        {loading ? "Comparing…" : "Compare the two versions"}
      </button>

      {(!fileA || !fileB) && (
        <p className="text-center text-[12px] text-ink-3">Add both versions to compare them.</p>
      )}
    </div>
  );
}

FileDropzone.propTypes = {
  label: PropTypes.string, hint: PropTypes.string, file: PropTypes.object,
  onFile: PropTypes.func, letter: PropTypes.string, tone: PropTypes.string,
};

CompareUploadZone.propTypes = { onCompare: PropTypes.func, loading: PropTypes.bool };
