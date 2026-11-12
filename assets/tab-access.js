window.RetroTabAccess = {async start(base) {
  async function check(target=base) {
    const controller=new AbortController(), timer=setTimeout(()=>controller.abort(),2500);
    let response;
    try { response=await fetch(target+'/api/session',{credentials:'include',cache:'no-store',signal:controller.signal}); }
    finally { clearTimeout(timer); }
    if(!response.ok) throw new Error('Unable to check access. Please reload.');
    const session=await response.json();
    // Personal collections require a signed account, not just trusted-network access.
    return session.authenticated === true && typeof session.username === 'string' && session.username.length > 0;
  }
  let gate=document.querySelector('.tabs-access-gate');
  if(!gate) {
    gate=document.createElement('div'); gate.className='tabs-access-gate'; gate.setAttribute('role','dialog'); gate.setAttribute('aria-modal','true'); gate.setAttribute('aria-label','Tabs sign-in');
    gate.innerHTML='<form><h1>Tabs</h1><label for="tabs-username">Username</label><input id="tabs-username" name="username" autocomplete="username" autocapitalize="none" spellcheck="false" required><label for="tabs-password">Password</label><input id="tabs-password" name="password" type="password" autocomplete="current-password" required><button type="submit">Enter</button><p role="status" aria-live="polite"></p></form>';
    document.body.append(gate);
  }
  const submit=gate.querySelector('button'); submit.disabled=true;
  function unlock(target) {
    document.body.classList.add('tabs-authenticated');
    gate.remove();
    return target;
  }
  try { if(await check()) return unlock(base); } catch(_) { /* Show a retryable sign-in form. */ }
  const tailnet='https://vex-ser.adal-fort.ts.net:11443';
  if(location.hostname==='retroterminal.net') {
    try { if(await check(tailnet)) return unlock(tailnet); } catch(_) { /* Off-tailnet or private-network access blocked. */ }
  }
  submit.disabled=false;
  gate.querySelector('input').focus();
  return new Promise(resolve=>{
    gate.querySelector('form').onsubmit=async event=>{
      event.preventDefault(); const form=event.target, status=form.querySelector('[role=status]'), button=form.querySelector('button'); button.disabled=true;
      try {
        const response=await fetch(base+'/api/login',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:form.username.value,password:form.password.value})});
        if(!response.ok) throw new Error(response.status===429?'Too many attempts. Try again shortly.':'Incorrect username or password.');
        if(!await check()) throw new Error('The session could not be saved. Allow cookies for this site and try again.');
        form.password.value=''; resolve(unlock(base));
      } catch(error) { status.textContent=error.message; }
      finally { button.disabled=false; }
    };
  });
}};
