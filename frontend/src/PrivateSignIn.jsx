import { useState } from 'react'
import PropTypes from 'prop-types'
import { request } from './review-api'

export default function PrivateSignIn({ onAuthenticated, publicSignup = false }) {
  const [mode,setMode]=useState('login')
  const [login,setLogin]=useState('')
  const [password,setPassword]=useState('')
  const [invite,setInvite]=useState('')
  const [acknowledged,setAcknowledged]=useState(false)
  const [busy,setBusy]=useState(false)
  const [error,setError]=useState('')
  async function submit(event) {
    event.preventDefault();setBusy(true);setError('')
    try {
      const result=await request('',`/accounts/${mode==='login'?'login':mode==='register'?'register':'redeem'}`,{method:'POST',body:{login,password,acknowledged,...(mode==='invite'?{invite}:{})}})
      setPassword('');setInvite('');await onAuthenticated(result.token)
    } catch(e) { if(e.name!=='AbortError')setError(e.message) }
    finally { setBusy(false) }
  }
  return <section className="login-form"><h2>{mode==='login'?'Private reviewer sign-in':mode==='register'?'Create your trial account':'Activate your invitation'}</h2>
    <p>{publicSignup ? 'Anyone can create a private trial account.' : 'Private accounts are invitation-only.'} Sessions end after 30 minutes of inactivity or eight hours.</p>
    <form onSubmit={submit}>
      <label>Login name<input autoComplete="username" value={login} onChange={(e)=>setLogin(e.target.value)} required minLength={3} maxLength={120} pattern="[A-Za-z0-9_.@-]+" /></label>
      {mode==='invite' && <label>Invitation code<input type="password" autoComplete="off" value={invite} onChange={(e)=>setInvite(e.target.value)} required minLength={32} maxLength={100}/></label>}
      <label>{mode!=='login'?'Choose a unique passphrase':'Passphrase'}<input type="password" autoComplete={mode==='login'?'current-password':'new-password'} value={password} onChange={(e)=>setPassword(e.target.value)} required minLength={mode!=='login'?15:1} maxLength={128}/></label>
      {mode==='invite' && <p className="hint">Use at least 15 characters. Invitations expire after 48 hours; recovery codes expire after one hour. Each code can be used once.</p>}
      {mode==='register' && <label className="checkbox"><input type="checkbox" required checked={acknowledged} onChange={e=>setAcknowledged(e.target.checked)}/>I understand this is an experimental review assistant, not legal advice. Available capabilities and privacy terms are shown before upload. I will save my login and passphrase; automated account recovery is not available.</label>}
      {error && <p role="alert" className="notice error">{error}</p>}
      <button className="primary" disabled={busy}>{busy?'Opening…':mode==='login'?'Sign in privately':mode==='register'?'Create account':'Activate account'}</button>
    </form>
    {publicSignup && mode==='login' && <button disabled={busy} onClick={()=>{setMode('register');setPassword('');setError('')}}>Create a free trial account</button>}
    <button className="subtle-link" disabled={busy} onClick={()=>{setMode(mode==='login'?'invite':'login');setPassword('');setError('')}}>{mode==='login'?'I have an invitation':'Back to sign-in'}</button>
    <p className="hint">For account access or recovery, contact your workspace owner. No email messages are sent automatically.</p>
  </section>
}
PrivateSignIn.propTypes={onAuthenticated:PropTypes.func.isRequired,publicSignup:PropTypes.bool}
