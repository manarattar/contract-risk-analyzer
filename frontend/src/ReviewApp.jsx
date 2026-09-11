import { useCallback, useEffect, useRef, useState } from 'react'
import { abortRequests, request } from './review-api'
import OriginalPages from './OriginalPages'
import PrivateSignIn from './PrivateSignIn'
import WorkspaceAccess from './WorkspaceAccess'
import './review.css'

const initialContext = { contract_type: 'Services agreement', party: '', role: 'Unknown', governing_law: 'Unknown', forum: 'Unknown', objectives: [], confirmed: false }
const pageFromHash = () => window.location.hash.slice(1) || 'library'
const go = (path) => { window.location.hash = path }
const formatDate = (value) => new Date(value).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })

export default function ReviewApp() {
  const [page, setPage] = useState(pageFromHash)
  const [token, setToken] = useState('')
  const [credential, setCredential] = useState('')
  const [session, setSession] = useState(null)
  const [publicDemo, setPublicDemo] = useState(false)
  const [accountsAvailable, setAccountsAvailable] = useState(false)
  const [publicSignup, setPublicSignup] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)
  const [items, setItems] = useState([])
  const [offset, setOffset] = useState(0)
  const [nextOffset, setNextOffset] = useState(null)
  const [search, setSearch] = useState('')
  const [doc, setDoc] = useState(null)
  const [blocks, setBlocks] = useState([])
  const [sourceOffset, setSourceOffset] = useState(0)
  const [sourceNext, setSourceNext] = useState(null)
  const [evidenceTarget, setEvidenceTarget] = useState('')
  const [selectedId, setSelectedId] = useState('')
  const [note, setNote] = useState('')
  const [draft, setDraft] = useState('')
  const [decisionStatus, setDecisionStatus] = useState('accepted')
  const [decisionVersion, setDecisionVersion] = useState(0)
  const [saveState, setSaveState] = useState('')
  const [file, setFile] = useState(null)
  const [context, setContext] = useState(initialContext)
  const [privacyAck, setPrivacyAck] = useState(false)
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState(null)
  const [compareA, setCompareA] = useState('')
  const [compareB, setCompareB] = useState('')
  const [comparison, setComparison] = useState(null)
  const [includeDismissed, setIncludeDismissed] = useState(false)
  const [receipt, setReceipt] = useState(null)
  const [completeAck, setCompleteAck] = useState(false)
  const [annotationBlock, setAnnotationBlock] = useState('')
  const [annotationTitle, setAnnotationTitle] = useState('')
  const [annotationNote, setAnnotationNote] = useState('')
  const titleRef = useRef(null)
  const dialogRef = useRef(null)
  const deleteButtonRef = useRef(null)
  const operationKey = useRef(crypto.randomUUID())
  const [view, documentId] = page.split('/')
  const findings = doc?.result?.findings || []
  const selected = findings.find((f) => f.id === selectedId)
  const canWrite = session?.principal.role !== 'viewer'

  useEffect(() => {
    const controller = new AbortController()
    request('', '/public-config', { signal: controller.signal }).then((r) => { setPublicDemo(r.public_demo); setAccountsAvailable(r.accounts); setPublicSignup(r.public_signup) }).catch(() => {})
    return () => controller.abort()
  }, [])

  async function startDemo() {
    await act(async () => {
      const access = await request('', '/demo-session', { method: 'POST' })
      const identity = await request(access.token, '/session')
      setToken(access.token); setSession(identity)
      const example = await request(access.token, '/sample?pdf=true', { method: 'POST', key: crypto.randomUUID() })
      go(`review/${example.id}`)
    })
  }

  useEffect(() => {
    const handler = () => setPage(pageFromHash())
    window.addEventListener('hashchange', handler)
    return () => window.removeEventListener('hashchange', handler)
  }, [])

  useEffect(() => {
    setError(''); setMessage('')
    titleRef.current?.focus()
  }, [page])

  const loadLibrary = useCallback(async (signal) => {
    const result = await request(token, `/documents?offset=${offset}`, { signal })
    setItems(result.items); setNextOffset(result.next_offset)
  }, [token, offset])

  useEffect(() => {
    if (!token || !['library', 'compare'].includes(view)) return
    const controller = new AbortController()
    loadLibrary(controller.signal).catch((e) => { if (e.name !== 'AbortError') setError(e.message) })
    return () => controller.abort()
  }, [token, view, loadLibrary])

  const loadDocument = useCallback(async (signal) => {
    const result = await request(token, `/documents/${documentId}`, { signal })
    setDoc(result)
    return result
  }, [token, documentId])

  useEffect(() => {
    if (!token || !documentId || !['review', 'data'].includes(view)) return
    const controller = new AbortController()
    let timer, delay = 1500
    setDoc(null); setBlocks([]); setSelectedId(''); setEvidenceTarget(''); setAnswer(null); setCompleteAck(false); setAnnotationBlock('')
    async function poll() {
      try {
        const result = await loadDocument(controller.signal)
        if (controller.signal.aborted) return
        setError('')
        if (['queued', 'processing'].includes(result.status)) {
          delay = Math.min(delay * 1.5, 15000)
          timer = setTimeout(poll, document.hidden ? 30000 : delay)
        }
      } catch (e) {
        if (e.name !== 'AbortError') {
          setError(e.message + ' Your saved job may still be running.')
          timer = setTimeout(poll, 15000)
        }
      }
    }
    poll()
    return () => { controller.abort(); clearTimeout(timer) }
  }, [token, documentId, view, loadDocument])

  const loadSource = useCallback(async (newOffset = 0, blockId = '', signal) => {
    const result = await request(token, `/documents/${documentId}/source?offset=${newOffset}${blockId ? `&block_id=${encodeURIComponent(blockId)}` : ''}`, { signal })
    setBlocks(result.blocks); setSourceOffset(result.offset); setSourceNext(result.next_offset)
    if (blockId) setEvidenceTarget(blockId)
  }, [token, documentId])

  useEffect(() => {
    if (!doc?.source || blocks.length || view !== 'review') return
    const controller = new AbortController()
    loadSource(0, '', controller.signal).catch((e) => { if (e.name !== 'AbortError') setError(e.message) })
    return () => controller.abort()
  }, [doc?.source, blocks.length, loadSource, view])

  useEffect(() => {
    if (evidenceTarget && blocks.some((b) => b.id === evidenceTarget)) {
      document.getElementById(`source-${evidenceTarget}`)?.focus()
    }
  }, [blocks, evidenceTarget])

  async function act(fn) {
    setBusy(true); setError(''); setMessage('')
    try { await fn() } catch (e) { if (e.name !== 'AbortError') setError(e.message) }
    finally { setBusy(false) }
  }

  async function signIn(event) {
    event.preventDefault()
    await act(async () => {
      const value = credential.trim()
      const result = await request(value, '/session')
      setToken(value); setSession(result); setCredential('')
    })
  }

  async function signOut() {
    const previousToken = token
    abortRequests()
    setToken(''); setSession(null); setDoc(null); setItems([]); setBlocks([]); setAnswer(null)
    setComparison(null); setNote(''); setDraft(''); setFile(null); setReceipt(null); go('library')
    try { await request(previousToken, '/accounts/logout', { method: 'POST' }) } catch { /* Local credentials are already cleared. */ }
  }

  async function sample() {
    await act(async () => {
      const result = await request(token, '/sample', { method: 'POST', key: operationKey.current })
      operationKey.current = crypto.randomUUID(); go(`review/${result.id}`)
    })
  }

  async function upload(event) {
    event.preventDefault()
    await act(async () => {
      if (!file) throw new Error('Choose a file before starting.')
      if (file.size > 10 * 1024 * 1024) throw new Error('Choose a file no larger than 10 MiB.')
      const form = new FormData()
      form.append('file', file); form.append('context', JSON.stringify(context)); form.append('privacy_acknowledged', String(privacyAck))
      const result = await request(token, '/documents', { method: 'POST', body: form, key: operationKey.current })
      operationKey.current = crypto.randomUUID(); setFile(null); go(`review/${result.id}`)
    })
  }

  function chooseFinding(finding) {
    const saved = doc.decisions.find((d) => d.finding_id === finding.id)
    setSelectedId(finding.id); setNote(saved?.note || ''); setDraft(saved?.revision_text || '')
    setDecisionStatus(saved?.status === 'unreviewed' ? 'accepted' : saved?.status || 'accepted')
    setDecisionVersion(saved?.version || 0); setSaveState('')
    requestAnimationFrame(() => document.getElementById('finding-heading')?.focus())
  }

  async function saveDecision(event) {
    event.preventDefault()
    setSaveState('Saving…')
    await act(async () => {
      const saved = await request(token, `/documents/${documentId}/findings/${encodeURIComponent(selectedId)}`, {
        method: 'PATCH', body: { status: decisionStatus, note, revision_text: draft, version: decisionVersion },
      })
      setDecisionVersion(saved.version); setSaveState('Saved. Original AI text remains unchanged.')
      await loadDocument()
    })
    setSaveState((state) => state === 'Saving…' ? 'Not saved. Your draft is preserved; review the error above.' : state)
  }

  async function jobAction(action) {
    await act(async () => {
      await request(token, `/documents/${documentId}/${action}`, { method: 'POST' })
      // Remount status polling for a retried job without losing document identity.
      go(`library`)
      setMessage(action === 'retry' ? 'Retry queued. Open the saved review to follow progress.' : 'Cancellation recorded. Saved checkpoints remain available until deletion.')
    })
  }

  async function ask(event) {
    event.preventDefault()
    await act(async () => setAnswer(await request(token, `/documents/${documentId}/questions`, { method: 'POST', body: { question } })))
  }

  async function exportReview() {
    await act(async () => {
      const blob = await request(token, `/documents/${documentId}/export?include_dismissed=${includeDismissed}`, { download: true })
      const url = URL.createObjectURL(blob), anchor = document.createElement('a')
      anchor.href = url; anchor.download = 'review-record.html'; anchor.click()
      setTimeout(() => URL.revokeObjectURL(url), 1000)
      setMessage('Review record downloaded. Downloaded copies are outside app deletion control.')
    })
  }

  async function deleteReview() {
    await act(async () => {
      await request(token, `/documents/${documentId}`, { method: 'DELETE' })
      dialogRef.current.close()
      const result = await request(token, `/deletions/${documentId}`)
      setReceipt(result); setDoc(null); go('receipt')
    })
  }

  const field = (key, value) => { setContext((old) => ({ ...old, [key]: value })); operationKey.current = crypto.randomUUID() }

  if (!session) return <main className="sign-in">
    <div className="wordmark"><span className="brand-mark" aria-hidden="true">R</span> Review desk</div>
    <h1>Every observation<br />starts with evidence.</h1>
    <p className="lead">A workspace for reading contracts, checking sources and recording human decisions.</p>
    {publicDemo && <section className="panel"><h2>Explore a synthetic review</h2><p>Try source navigation and review decisions with a fictional agreement. Your demo is isolated, expires after 30 minutes, and cannot accept uploads. No AI provider is called.</p><button className="primary" disabled={busy} onClick={startDemo}>{busy ? 'Opening…' : 'Try the public demo'}</button></section>}
    {accountsAvailable && <PrivateSignIn publicSignup={publicSignup} onAuthenticated={async value => { const identity = await request(value, '/session'); setToken(value); setSession(identity); go('library') }} />}
    <details open={!accountsAvailable}><summary>Operator access</summary>
    <form onSubmit={signIn} className="login-form">
      <h2>Open your workspace</h2>
      <label>Workspace access token<input type="password" autoComplete="off" value={credential} onChange={(e) => setCredential(e.target.value)} required minLength={32} /></label>
      <p className="hint">Use your operator-issued token. It stays in memory and is cleared when you sign out or reload.</p>
      {error && <p role="alert" className="notice error">{error}</p>}
      <button className="primary" disabled={busy}>{busy ? 'Opening…' : 'Open workspace'}</button>
    </form></details>
    <p className="legal">Issue spotting for human review. Not legal advice or approval to sign.</p>
  </main>

  return <div className="app-shell">
    <a className="skip-link" href="#main-content">Skip to workspace</a>
    <header className="topbar">
      <a className="wordmark" href="#library"><span className="brand-mark" aria-hidden="true">R</span> Review desk</a>
      <nav aria-label="Main navigation">
        <a href="#library" aria-current={view === 'library' ? 'page' : undefined}>Documents</a>
        <a href="#upload" aria-current={view === 'upload' ? 'page' : undefined}>New review</a>
        <a href="#compare" aria-current={view === 'compare' ? 'page' : undefined}>Compare</a>
        {accountsAvailable && session.principal.role === 'owner' && <a href="#access" aria-current={view === 'access' ? 'page' : undefined}>Workspace access</a>}
      </nav>
      <div className="account"><span>{session.principal.display_name || session.principal.id}</span><button onClick={signOut}>Sign out</button></div>
    </header>
    <div className="mode-bar"><span className="status-dot" />{session.mode === 'demo' ? 'Synthetic demo — no live AI analysis' : session.mode === 'manual' ? 'Manual review — no live AI analysis' : session.mode === 'trial' ? 'Experimental AI trial — interpretations are unverified' : session.mode === 'disabled' ? 'Review service disabled' : 'AI observations require human verification'}<span>Not legal advice</span></div>
    <main id="main-content" className="main-content" tabIndex={-1}>
      {error && <div role="alert" className="notice error">{error}</div>}
      {message && <p role="status" className="notice">{message}</p>}

      {view === 'access' && accountsAvailable && session.principal.role === 'owner' && <WorkspaceAccess token={token} />}
      {view === 'library' && <>
        <div className="page-heading"><div><p className="overline">Your workspace</p><h1 ref={titleRef} tabIndex={-1}>Contract reviews</h1><p>Pick up where you left off. Check the source before deciding.</p></div><a className="button primary" href="#upload">New review <span aria-hidden="true">↗</span></a></div>
        <div className="toolbar"><label>Find a review<input type="search" placeholder="Search this page by filename" value={search} onChange={(e) => setSearch(e.target.value)} /></label><button disabled={busy} onClick={() => act(() => loadLibrary())}>Refresh library</button></div>
        {!items.length ? <section className="empty-state"><span className="document-glyph" aria-hidden="true">≡</span><h2>Your first review starts here</h2><p>Explore a clearly labelled synthetic agreement, or upload a supported file when your workspace permits it.</p><button className="primary" disabled={busy || !canWrite || session.mode === 'disabled'} onClick={sample}>{busy ? 'Preparing sample…' : 'Explore synthetic example'}</button></section> : <div className="document-list">
          <div className="list-heading"><span>Document</span><span>Review state</span><span>Retention</span></div>
          {items.filter((item) => item.filename.toLowerCase().includes(search.toLowerCase())).map((item) => <article className="document-row" key={item.id}>
            <div><a href={`#review/${item.id}`}>{item.filename}</a><p>{item.mode === 'demo' ? 'Synthetic example' : `${item.mode} review`} · Added {formatDate(item.created)}</p></div>
            <div><span className={`badge ${item.status === 'failed' ? 'warning' : ''}`}>{item.review_complete ? 'Human review recorded' : item.status}</span></div>
            <div><span>Until {formatDate(item.retention_until)}</span><a className="subtle-link" href={`#data/${item.id}`}>Export & data</a></div>
          </article>)}
          {search && !items.some((i) => i.filename.toLowerCase().includes(search.toLowerCase())) && <p className="empty-state">No matches on this page. <button onClick={() => setSearch('')}>Clear search</button></p>}
        </div>}
        <div className="actions"><button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset-20))}>Previous page</button><button disabled={nextOffset === null} onClick={() => setOffset(nextOffset)}>Next page</button>{items.length > 0 && <button disabled={busy || !canWrite} onClick={sample}>Open synthetic example</button>}</div>
      </>}

      {view === 'upload' && <>
        <div className="page-heading"><div><p className="overline">New review</p><h1 ref={titleRef} tabIndex={-1}>Set the review context</h1><p>Choose your document and tell the reviewer what matters.</p></div></div>
        {!session.upload_enabled && <div className="notice warning"><strong>File uploads are not enabled.</strong><p>Parser isolation and data-handling gates must be approved first. You can explore the synthetic sample without sending a document.</p><button onClick={sample} disabled={busy || !canWrite || session.mode === 'disabled'}>Use synthetic example</button></div>}
        <form onSubmit={upload} className="two-columns">
          <section className="panel"><h2>1. Document & privacy</h2><label className="file-field">Contract file<input type="file" accept=".txt,.pdf,.docx" disabled={!session.upload_enabled} required onChange={(e) => { setFile(e.target.files[0] || null); operationKey.current = crypto.randomUUID() }} /></label><p className="hint">PDF, DOCX or UTF-8 TXT · Maximum 10 MiB, 50 PDF pages. Scans need manual review; OCR is not available. Selecting a file does not upload it.</p><div className="policy"><h3>Where your document goes</h3><p>{session.privacy}</p><dl><dt>AI provider</dt><dd>{session.provider}</dd><dt>Provider retention</dt><dd>{session.provider_retention}</dd><dt>Active retention</dt><dd>{session.retention_days} days</dd><dt>Backups</dt><dd>{session.backup_retention}</dd></dl></div><label className="checkbox"><input type="checkbox" checked={privacyAck} onChange={(e) => setPrivacyAck(e.target.checked)} required /><span>I understand the configured handling and have permission to submit this document.</span></label></section>
          <section className="panel"><h2>2. Review context</h2><label>Contract type<select value={context.contract_type} onChange={(e) => field('contract_type', e.target.value)}><option>Services agreement</option><option>Unknown</option></select></label><label>Exact party you represent<input required maxLength={200} value={context.party} onChange={(e) => field('party', e.target.value)} placeholder="Named entity or Unknown" /></label><label>Party role<select value={context.role} onChange={(e) => field('role', e.target.value)}>{['Unknown', 'Customer', 'Provider', 'Other'].map((v) => <option key={v}>{v}</option>)}</select></label><div className="two-columns compact"><label>Governing law<input required maxLength={200} value={context.governing_law} onChange={(e) => field('governing_law', e.target.value)} /></label><label>Dispute forum<input required maxLength={200} value={context.forum} onChange={(e) => field('forum', e.target.value)} /></label></div><fieldset><legend>Review objectives</legend>{['Liability', 'Payment', 'Termination', 'Intellectual property', 'Data handling'].map((v) => <label key={v} className="checkbox"><input type="checkbox" checked={context.objectives.includes(v)} onChange={(e) => field('objectives', e.target.checked ? [...context.objectives, v] : context.objectives.filter((x) => x !== v))} /><span>{v}</span></label>)}</fieldset><label className="checkbox"><input type="checkbox" checked={context.confirmed} onChange={(e) => field('confirmed', e.target.checked)} /><span>I have confirmed these values; unknown values remain unresolved.</span></label><button className="primary" disabled={busy || !session.upload_enabled || !canWrite}>{busy ? 'Transferring file — please wait…' : 'Start processing'}</button></section>
        </form>
      </>}

      {['review', 'data'].includes(view) && !doc && <p role="status" className="empty-state">Loading saved review…</p>}
      {view === 'review' && doc && <>
        <div className="page-heading"><div><a className="back-link" href="#library">← Documents</a><h1 ref={titleRef} tabIndex={-1}>{doc.filename}</h1><p>{doc.context.party} · {doc.context.role} perspective · Governing law: {doc.context.governing_law}</p></div><a className="button" href={`#data/${doc.id}`}>Export & data</a></div>
        {doc.mode === 'demo' && <p className="notice"><strong>Synthetic example.</strong> These observations belong only to this sample. No AI provider was used.</p>}
        <section className="processing-bar" aria-label="Processing status"><div role="status"><strong>{doc.status === 'ready' ? 'Ready for human review' : doc.status === 'partial' ? 'Incomplete extraction — verify coverage' : doc.status}</strong><span>{doc.job.stage.replaceAll('_', ' ')} · Attempt {doc.job.attempts} of 3</span></div><div className="actions">{['queued', 'processing'].includes(doc.status) && <button disabled={busy || !canWrite} onClick={() => jobAction('cancel')}>Cancel processing</button>}{['failed', 'cancelled'].includes(doc.status) && <button disabled={busy || !canWrite || doc.job.attempts >= 3} onClick={() => jobAction('retry')}>Retry saved job</button>}<button disabled={busy} onClick={() => act(() => loadDocument())}>Refresh status</button></div></section>
        {doc.error_code && <div className="notice error"><strong>Processing could not finish.</strong><p>Reason: {doc.error_code.replaceAll('_', ' ')}. No completed risk assessment is available. Retry a temporary failure, or replace an unreadable file.</p><a href="#upload">Choose another file</a></div>}
        {doc.source && <>
          <div className="coverage-line">{doc.source.block_count} extracted text blocks · {doc.source.page_count ? `${doc.source.page_count} PDF pages` : 'Logical text locations'} · Completeness requires your confirmation</div>
          <details className="limitations"><summary>Coverage and limitations</summary>{doc.source.warnings.map((w) => <p key={w}>{w}</p>)}{doc.result?.limitations.map((w) => <p key={w}>{w}</p>)}<p>PDF page images preserve the original visual layout when rendering is enabled. Extracted text may omit or reorder material. DOCX and TXT use a text-only view; verify their layout against your original file.</p></details>
          <div className="review-grid">
            <section className="source-pane" aria-labelledby="source-heading">{doc.source.page_count ? <OriginalPages key={doc.id} token={token} documentId={doc.id} pageCount={doc.source.page_count} target={blocks.find((b) => b.id === evidenceTarget)} citation={selected?.citations.find((c) => c.block_id === evidenceTarget)} onReturn={selected ? () => document.getElementById(`finding-${selected.id}`)?.focus() : undefined} /> : <p className="hint">Text-only view. Original pagination is not available for this format.</p>}<div className="pane-heading"><h2 id="source-heading" tabIndex={-1}>Source text</h2><span>Immutable extracted evidence</span></div><div className="source-paper">{blocks.map((b) => {
              const cite = selected?.citations.find((c) => c.block_id === b.id)
              return <article key={b.id} id={`source-${b.id}`} tabIndex={-1} className={`source-block ${evidenceTarget === b.id ? 'highlighted-block' : ''}`}><h3>{b.location} <span>· {b.id}</span></h3><p>{cite ? <>{b.text.slice(0, cite.start)}<mark>{b.text.slice(cite.start, cite.end)}</mark>{b.text.slice(cite.end)}</> : b.text}</p>{canWrite && ['ready', 'partial'].includes(doc.status) && <button onClick={() => { setAnnotationBlock(b.id); setAnnotationTitle(''); setAnnotationNote(''); requestAnimationFrame(() => document.getElementById('annotation-title')?.focus()) }}>Annotate this source</button>}</article>
            })}</div><div className="actions"><button disabled={sourceOffset === 0 || busy} onClick={() => act(() => loadSource(Math.max(0, sourceOffset-10)))}>Previous text</button><button disabled={sourceNext === null || busy} onClick={() => act(() => loadSource(sourceNext))}>Next text</button>{selected && <button onClick={() => document.getElementById(`finding-${selected.id}`)?.focus()}>Back to observation</button>}</div></section>
            <section className="findings-pane" aria-labelledby="findings-heading"><div className="pane-heading"><h2 id="findings-heading">Observations <span>{findings.length}</span></h2><span>Decisions are yours</span></div>{findings.length === 0 ? <div className="pane-empty"><h3>No generated observations</h3><p>{doc.mode === 'manual' ? 'Manual mode extracts evidence without AI issue spotting.' : 'No observations are available for this scope.'} This does not establish that the contract has no issues.</p></div> : <ol className="finding-list">{findings.map((f) => <li key={f.id}><button id={`finding-${f.id}`} className={selectedId === f.id ? 'selected-finding' : ''} onClick={() => chooseFinding(f)}><span className="finding-label">{f.citations[0]?.location}</span><strong>{f.title}</strong><span>Impact: {f.impact}</span><span className="decision-label">{doc.decisions.find((d) => d.finding_id === f.id)?.status || 'Unreviewed'}</span></button></li>)}</ol>}</section>
            <section className="detail-pane" aria-labelledby="finding-heading"><h2 id="finding-heading" tabIndex={-1}>{selected ? selected.title : 'Check an observation'}</h2>{!selected ? <p>Select an observation to see its evidence, uncertainty and review actions.</p> : <><dl className="dimensions"><dt>Potential impact</dt><dd>{selected.impact}</dd><dt>Evidence</dt><dd>{selected.evidence_status}</dd><dt>Business preference</dt><dd>{selected.business_preference}</dd></dl>{selected.citations.map((c) => <div key={c.block_id}><blockquote>{c.quote}</blockquote><button className="evidence-button" onClick={() => act(() => loadSource(0, c.block_id))}>View evidence · {c.location}</button></div>)}<h3>Why this may matter</h3><p>{selected.explanation}</p><h3>What needs checking</h3><p>{selected.uncertainty}</p><h3>Suggested action</h3><p>{selected.action}</p>{selected.suggested_revision && <section aria-labelledby="suggested-revision-heading"><h3 id="suggested-revision-heading">Illustrative alternative wording</h3><p>{selected.suggested_revision}</p><p className="hint">{selected.revision_caveats}</p><p className="hint">Unapproved suggestion. Check the evidence, related clauses and negotiation objectives before using it.</p><button type="button" disabled={!canWrite || Boolean(draft.trim())} onClick={() => { setDraft(selected.suggested_revision); setDecisionStatus('edited'); document.getElementById('reviewer-draft')?.focus() }}>Use suggestion as editable draft</button>{draft.trim() && <p className="hint">Your current draft is preserved. Clear it before copying this suggestion.</p>}</section>}<form onSubmit={saveDecision} className="decision-form"><label>Your decision<select value={decisionStatus} onChange={(e) => setDecisionStatus(e.target.value)}>{['accepted', 'dismissed', 'edited', 'escalated', 'unreviewed'].map((v) => <option key={v}>{v}</option>)}</select></label><label>Reviewer note<textarea value={note} onChange={(e) => setNote(e.target.value)} maxLength={4000} required={['dismissed', 'edited', 'escalated'].includes(decisionStatus)} placeholder="Explain your decision or question" /></label><label>Draft revision for human review<textarea id="reviewer-draft" value={draft} onChange={(e) => setDraft(e.target.value)} maxLength={6000} placeholder="Optional. Does not change the original." /></label><button className="primary" disabled={busy || !canWrite || !['ready', 'partial'].includes(doc.status)}>Save decision</button><p role="status" className="hint">{saveState}</p></form><p className="hint">Accept means you agree with the observation. It is not approval to sign.</p></>}</section>
          </div>
          {annotationBlock && <section className="panel" style={{ marginTop: '1.5rem' }}><h2>Add a human note · source {annotationBlock}</h2><form onSubmit={(event) => { event.preventDefault(); act(async () => { await request(token, `/documents/${documentId}/annotations`, { method: 'POST', body: { block_id: annotationBlock, title: annotationTitle, note: annotationNote } }); setAnnotationBlock(''); await loadDocument(); setMessage('Human annotation saved with its source and author.') }) }}><label>Observation title<input id="annotation-title" required minLength={3} maxLength={160} value={annotationTitle} onChange={(e) => setAnnotationTitle(e.target.value)} /></label><label>Reviewer note<textarea required minLength={3} maxLength={4000} value={annotationNote} onChange={(e) => setAnnotationNote(e.target.value)} /></label><div className="actions"><button className="primary" disabled={busy}>Save source annotation</button><button type="button" onClick={() => setAnnotationBlock('')}>Cancel note</button></div></form></section>}
          <section className="question-panel"><div><p className="overline">Document questions</p><h2>Find support in the source</h2><p>Answers include supporting passages. Verify the meaning and ask a qualified reviewer about legal conclusions.</p></div><div><form onSubmit={ask}><label>Your question<input value={question} onChange={(e) => setQuestion(e.target.value)} required minLength={3} maxLength={1000} placeholder="What does the contract say about liability?" /></label><button disabled={busy}>{busy ? 'Finding support…' : 'Ask about this document'}</button></form>{answer && <div className="answer" role="status"><p>{answer.answer}</p>{answer.sources.map((s) => <div key={s.block_id}><blockquote>{s.quote}</blockquote><button onClick={() => act(() => loadSource(0, s.block_id))}>View {s.location}</button></div>)}</div>}</div></section>
          <section className="complete-panel"><div><h2>{doc.review_complete ? 'Human review recorded' : 'Finish your review'}</h2><p>Make or escalate each observation first. Source completeness and signing remain human responsibilities.</p></div><div><label className="checkbox"><input type="checkbox" checked={completeAck} onChange={(e) => setCompleteAck(e.target.checked)} /><span>I understand that completing this review does not approve signing or prove completeness.</span></label><button disabled={busy || !canWrite || !completeAck || Boolean(doc.review_complete)} onClick={() => act(async () => { await request(token, `/documents/${doc.id}/complete`, { method: 'POST', body: { revision: doc.revision, acknowledge_incomplete: completeAck } }); await loadDocument(); setMessage('Human review recorded.') })}>Record review completion</button></div></section>
        </>}
      </>}

      {view === 'compare' && <>
        <div className="page-heading"><div><p className="overline">Compare source versions</p><h1 ref={titleRef} tabIndex={-1}>What changed?</h1><p>Inspect changes to wording, amounts and obligations. No score-based winner.</p></div></div>
        <form className="compare-controls" onSubmit={(event) => { event.preventDefault(); act(async () => setComparison(await request(token, '/comparisons', { method: 'POST', body: { baseline_id: compareA, revised_id: compareB } }))) }}><label>Baseline<select required value={compareA} onChange={(e) => setCompareA(e.target.value)}><option value="">Choose saved document</option>{items.map((d) => <option key={d.id} value={d.id}>{d.filename} · {d.id.slice(0, 6)}</option>)}</select></label><label>Revised<select required value={compareB} onChange={(e) => setCompareB(e.target.value)}><option value="">Choose saved document</option>{items.map((d) => <option key={d.id} value={d.id}>{d.filename} · {d.id.slice(0, 6)}</option>)}</select></label><button className="primary" disabled={busy || !compareA || !compareB}>Compare source text</button></form>
        <p className="hint">Only documents you own with matching context can be compared. The selector shows the current library page.</p>
        {comparison && <><p className="notice warning">{comparison.limitations}</p>{!comparison.changes.length && <div className="empty-state"><h2>No text changes found</h2><p>This applies only to the extracted material and does not establish equal legal risk.</p></div>}{comparison.changes.map((change, i) => <section className="change" key={i}><div className="change-heading"><h2>{i+1}. {change.kind}</h2><p>{change.assessment}</p></div><div className="two-columns"><article><h3>Baseline · {comparison.baseline.filename}</h3>{change.baseline.length ? change.baseline.map((b) => <blockquote key={b.id}><span>{b.location}</span>{b.text}</blockquote>) : <p>No matched baseline text.</p>}<a href={`#review/${comparison.baseline.id}`}>Open baseline source</a></article><article><h3>Revised · {comparison.revised.filename}</h3>{change.revised.length ? change.revised.map((b) => <blockquote key={b.id}><span>{b.location}</span>{b.text}</blockquote>) : <p>No matched revised text.</p>}<a href={`#review/${comparison.revised.id}`}>Open revised source</a></article></div><p className="hint">{change.alignment}</p></section>)}</>}
      </>}

      {view === 'data' && doc && <>
        <div className="page-heading"><div><a className="back-link" href={`#review/${doc.id}`}>← Return to review</a><h1 ref={titleRef} tabIndex={-1}>Export & document data</h1><p>{doc.filename}</p></div></div>
        <div className="two-columns"><section className="panel"><p className="overline">Review snapshot</p><h2>Export the evidence trail</h2><p>Accessible HTML includes source quotes, context, run provenance, reviewer notes, drafts and limitations.</p><p><strong>{doc.review_complete ? 'Human review recorded' : 'Incomplete human review'}</strong> · Revision {doc.revision}</p><label className="checkbox"><input type="checkbox" checked={includeDismissed} onChange={(e) => setIncludeDismissed(e.target.checked)} /><span>Include dismissed observations and their reasons</span></label><button className="primary" disabled={busy || !doc.result} onClick={exportReview}>Download review record</button><p className="hint">PDF export is withheld until its rendering and accessibility gates pass. Downloaded records cannot be recalled by app deletion.</p></section><section className="panel"><p className="overline">Retention & access</p><h2>Delete this document</h2><dl><dt>Retained until</dt><dd>{new Date(doc.retention_until).toLocaleString()}</dd><dt>Backup policy</dt><dd>{session.backup_retention}</dd><dt>Provider policy</dt><dd>{['live','trial'].includes(doc.mode) ? session.provider_retention : 'No provider calls for this document.'}</dd></dl><p>Deletion revokes access and clears the review data. A worker purges remaining local source files and records a receipt.</p><button className="danger" ref={deleteButtonRef} disabled={!canWrite || busy} onClick={() => dialogRef.current.showModal()}>Review deletion scope</button></section></div>
        <dialog ref={dialogRef} aria-labelledby="delete-heading" onClose={() => deleteButtonRef.current?.focus()}><h2 id="delete-heading">Delete {doc.filename}?</h2><p>This clears extracted text, observations, decisions, notes and local source files. Comparisons are computed on demand and are not stored. Backup and provider copies follow the policies shown above.</p><p>This action cannot restore your review. Keep any export you need first.</p><div className="actions"><button autoFocus onClick={() => dialogRef.current.close()}>Keep document</button><button className="danger" disabled={busy} onClick={deleteReview}>Confirm deletion</button></div></dialog>
      </>}

      {view === 'receipt' && receipt && <section className="panel receipt"><p className="overline">Deletion receipt</p><h1 ref={titleRef} tabIndex={-1}>Access has been revoked</h1><dl><dt>Active store purge</dt><dd>{receipt.state}</dd><dt>Requested</dt><dd>{receipt.requested}</dd><dt>Backups</dt><dd>{receipt.backup_policy}</dd><dt>Provider</dt><dd>{receipt.provider_policy}</dd></dl>{receipt.error_code && <p className="notice warning">{receipt.error_code}</p>}<div className="actions"><button disabled={busy} onClick={() => act(async () => setReceipt(await request(token, `/deletions/${receipt.document_id}`)))}>Refresh purge status</button><a className="button" href="#library">Return to documents</a></div><p className="hint">A completed active-store purge does not erase external backups or downloaded copies.</p></section>}
    </main>
    <footer className="app-footer">Evidence supports your review. A qualified human remains responsible for legal decisions.</footer>
  </div>
}
