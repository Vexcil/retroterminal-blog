window.RetroTabAccess = {async start(base) {
  async function check(target=base) {
    const controller=new AbortController(), timer=setTimeout(()=>controller.abort(),2500);
    let response;
    try { response=await fetch(target+'/api/session',{credentials:'include',cache:'no-store',signal:controller.signal}); }
    finally { clearTimeout(timer); }
    if(!response.ok) throw new Error('Unable to check access. Please reload.');
    return (await response.json()).authenticated;
  }
  try { if(await check()) return base; } catch(_) { /* Show a retryable sign-in form. */ }
  const tailnet='https://vex-ser.adal-fort.ts.net:11443';
  if(location.hostname==='retroterminal.net') {
    try { if(await check(tailnet)) return tailnet; } catch(_) { /* Off-tailnet or private-network access blocked. */ }
  }
  return new Promise(resolve=>{
    const gate=document.createElement('div'); gate.className='tabs-access-gate'; gate.setAttribute('role','dialog'); gate.setAttribute('aria-modal','true'); gate.setAttribute('aria-label','Private tabs sign-in');
    gate.innerHTML='<form><h1>Private tab player</h1><p>Sign in to open the library.</p><label>Username<input name="username" autocomplete="username" required></label><label>Password<input name="password" type="password" autocomplete="current-password" required></label><button type="submit">Sign in</button><p role="status"></p><p><a href="'+tailnet+'/viewer/">Open through tailnet</a></p></form>';
    document.body.append(gate); gate.querySelector('input').focus();
    gate.querySelector('form').onsubmit=async event=>{
      event.preventDefault(); const form=event.target, status=form.querySelector('[role=status]'), button=form.querySelector('button'); button.disabled=true;
      try {
        const response=await fetch(base+'/api/login',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:form.username.value,password:form.password.value})});
        if(!response.ok) throw new Error(response.status===429?'Too many attempts. Try again shortly.':'Incorrect username or password.');
        if(!await check()) throw new Error('The session could not be saved. Allow cookies for this site and try again.');
        form.password.value=''; gate.remove(); resolve(base);
      } catch(error) { status.textContent=error.message; }
      finally { button.disabled=false; }
    };
  });
}};
