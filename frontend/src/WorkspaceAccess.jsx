import { useEffect, useState } from 'react'
import PropTypes from 'prop-types'
import { request } from './review-api'

export default function WorkspaceAccess({ token }) {
  const [accounts,setAccounts]=useState([])
  const [login,setLogin]=useState('')
  const [role,setRole]=useState('reviewer')
  const [invitation,setInvitation]=useState(null)
  const [error,setError]=useState('')
  const [busy,setBusy]=useState(false)
  async function refresh(signal) { const result=await request(token,'/accounts',{signal});setAccounts(result.accounts) }
  useEffect(()=>{const controller=new AbortController();request(token,'/accounts',{signal:controller.signal}).then(r=>setAccounts(r.accounts)).catch(e=>{if(e.name!=='AbortError')setError(e.message)});return()=>controller.abort()},[token])
  async function invite(event) {
    event.preventDefault();setBusy(true);setError('');setInvitation(null)
    try {setInvitation(await request(token,'/accounts/invites',{method:'POST',body:{login,role}}))}
    catch(e){if(e.name!=='AbortError')setError(e.message)} finally{setBusy(false)}
  }
  async function recover(account) {
    if(!window.confirm(`Suspend ${account.login} and issue a one-hour recovery code? Current sessions will end immediately.`))return
    setBusy(true);setError('');setInvitation(null)
    try {setInvitation(await request(token,`/accounts/${account.id}/reset`,{method:'POST'}));await refresh()}
    catch(e){if(e.name!=='AbortError')setError(e.message)}finally{setBusy(false)}
  }
  async function revoke(account) {
    if(!window.confirm(`Revoke sign-in and all sessions for ${account.login}? Their documents stay private and follow retention policy.`))return
    setBusy(true);setError('')
    try {await request(token,`/accounts/${account.id}/revoke`,{method:'POST'});await refresh()}
    catch(e){if(e.name!=='AbortError')setError(e.message)}finally{setBusy(false)}
  }
  return <><div className="page-heading"><div><h1>Workspace access</h1><p>Invite reviewers and revoke access. Documents remain scoped to their individual owner.</p></div></div>
    {error&&<p role="alert" className="notice error">{error}</p>}
    <div className="two-columns"><section className="panel"><h2>Create an invitation</h2><form onSubmit={invite}>
      <label>Reviewer login name<input required minLength={3} maxLength={120} pattern="[A-Za-z0-9_.@-]+" value={login} onChange={e=>setLogin(e.target.value)}/></label>
      <label>Access role<select value={role} onChange={e=>setRole(e.target.value)}><option value="reviewer">Reviewer — create and review own documents</option><option value="viewer">Viewer — read own documents only</option></select></label>
      <button className="primary" disabled={busy}>Create invitation</button></form>
      {invitation&&<div className="notice" role="status"><p>Invitation for <strong>{invitation.login}</strong>. Expires in {invitation.expires_in / 3600} hours. Share through your approved private channel.</p><label>One-time invitation code<input readOnly value={invitation.invite} onFocus={e=>e.target.select()} autoComplete="off"/></label><p>This code is shown once. No message has been sent.</p><button onClick={()=>setInvitation(null)}>Hide invitation</button></div>}
    </section><section className="panel"><h2>Registered reviewers</h2>{!accounts.length?<p>No invited accounts have been activated.</p>:<ul className="account-list">{accounts.map(account=><li key={account.id}><strong>{account.login}</strong><p>{account.role} · {account.disabled?'Access revoked':'Active'}</p><button className="danger" disabled={busy||Boolean(account.disabled)} onClick={()=>revoke(account)}>Revoke access</button><button disabled={busy} onClick={()=>recover(account)}>Issue recovery code</button></li>)}</ul>}</section></div>
  </>
}
WorkspaceAccess.propTypes={token:PropTypes.string.isRequired}
