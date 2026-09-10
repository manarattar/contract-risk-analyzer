import { useEffect, useRef, useState } from 'react'
import PropTypes from 'prop-types'
import { request } from './review-api'

export default function OriginalPages({ token, documentId, pageCount, target, citation, onReturn }) {
  const [page, setPage] = useState(1)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [retry, setRetry] = useState(0)
  const [zoom, setZoom] = useState(100)
  const frame = useRef(null)
  const pendingFocus = useRef(false)

  useEffect(() => {
    if (target?.page) { setPage(target.page); pendingFocus.current = true }
  }, [target])

  useEffect(() => {
    const controller = new AbortController()
    setResult(null); setError('')
    const params = new URLSearchParams()
    if (target?.page === page) {
      params.set('block_id', target.id)
      if (citation) { params.set('start', citation.start); params.set('end', citation.end) }
    }
    request(token, `/documents/${documentId}/pages/${page}?${params}`, { signal: controller.signal })
      .then((data) => { if (!controller.signal.aborted) setResult(data) })
      .catch((e) => { if (e.name !== 'AbortError') setError(e.message) })
    return () => controller.abort()
  }, [token, documentId, page, target, citation, retry])

  function move(next) { pendingFocus.current = false; setPage(Math.max(1, Math.min(pageCount, next))) }
  return <section className="original-viewer" aria-label="Original PDF pages">
    <div className="pane-heading"><h2>Original PDF</h2><span>Page image · text alternative below</span></div>
    <div className="page-controls">
      <button disabled={page === 1} onClick={() => move(page-1)} aria-label="Previous PDF page">←</button>
      <label>Page<select aria-label="PDF page" value={page} onChange={(e) => move(Number(e.target.value))}>{Array.from({ length: pageCount }, (_, i) => <option key={i} value={i+1}>{i+1} of {pageCount}</option>)}</select></label>
      <button disabled={page === pageCount} onClick={() => move(page+1)} aria-label="Next PDF page">→</button>
      <label>Zoom<select value={zoom} onChange={(e) => setZoom(Number(e.target.value))}><option value={100}>Fit width</option><option value={150}>150%</option><option value={200}>200%</option><option value={300}>300%</option><option value={400}>400%</option></select></label>
    </div>
    {error ? <div role="alert" className="notice error"><p>{error}</p><button onClick={() => setRetry(retry+1)}>Retry page</button><button onClick={() => document.getElementById('source-heading')?.focus()}>Use extracted evidence</button></div> : !result ? <p role="status">Loading page {page}…</p> : <>
      <p role="status" className="hint">Page {result.page} of {result.page_count}. {result.match === 'quote' ? 'Supporting quote highlighted.' : result.match === 'block' ? 'Supporting block outlined; exact quote location could not be confirmed.' : 'No evidence selected on this page.'}</p>
      <div className="page-viewport" ref={frame} tabIndex={0} aria-label={`Original page ${page}. Use left and right arrow keys to change pages.`}
        onKeyDown={(e) => { if (e.target === e.currentTarget && ['ArrowLeft', 'ArrowRight'].includes(e.key)) { e.preventDefault(); move(page + (e.key === 'ArrowRight' ? 1 : -1)) } }}>
        <div className="page-image" style={{ width: `${zoom}%` }}>
          <img src={result.image} width={result.width} height={result.height} alt={`Original PDF page ${page}. Read the extracted page text below for an accessible text alternative.`}
            onLoad={() => { if (pendingFocus.current) { frame.current?.focus(); pendingFocus.current = false } }} />
          {result.rectangles.map((r, i) => <span key={i} aria-hidden="true" className={`page-highlight ${result.match}`} style={{ left: `${r[0]*100}%`, top: `${r[1]*100}%`, width: `${r[2]*100}%`, height: `${r[3]*100}%` }} />)}
        </div>
      </div>
      <details className="page-transcript"><summary>Extracted text for page {page}</summary>{result.blocks.length ? result.blocks.map((b) => <p key={b.id}>{b.text}</p>) : <p>No readable text was extracted from this page. A human must inspect the image; OCR is not available.</p>}</details>
    </>}
    <div className="actions"><button onClick={() => document.getElementById('source-heading')?.focus()}>Go to extracted evidence</button>{onReturn && <button onClick={onReturn}>Return to observation</button>}</div>
  </section>
}

OriginalPages.propTypes = {
  token: PropTypes.string.isRequired, documentId: PropTypes.string.isRequired,
  pageCount: PropTypes.number.isRequired, target: PropTypes.object,
  citation: PropTypes.object, onReturn: PropTypes.func,
}
