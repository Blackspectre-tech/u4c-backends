(() => {
  // utilities
  const $ = s => document.querySelector(s);
  const $$ = s => Array.from(document.querySelectorAll(s));
  const getCookie = n => (document.cookie.split('; ').find(r=>r.trim().startsWith(n+'='))||'').split('=')[1] ? decodeURIComponent((document.cookie.split('; ').find(r=>r.trim().startsWith(n+'='))||'').split('=')[1]) : null;
  const CSRF = getCookie('csrftoken');

  // notify
  const notifyRoot = $('#adminNotifyContainer');
  function esc(s){return String(s).replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]))}
  function truncate(s,n){if(!s) return ''; return s.length>n? s.slice(0,n/2)+'...'+s.slice(-n/2): s}
  function showNotify(msg, type='info', opts={}) {
    if(!notifyRoot) return;
    const id = 'n'+Date.now()+Math.floor(Math.random()*999);
    const title = opts.title || (type==='success'?'Success':type==='error'?'Error':'Notice');
    const tx = opts.tx_hash || '';
    const sticky = !!opts.sticky;
    const el = document.createElement('div');
    el.className = `admin-notify ${type}`; el.id = id;
    el.innerHTML = `<div class="notify-icon">${type==='success'?'✓':type==='error'?'⚠':'i'}</div>
      <div class="notify-body"><div class="notify-title">${esc(title)}</div><div class="notify-msg">${esc(msg)}</div>${tx?`<div class="notify-msg"><small>TX: <span class="notify-tx" data-tx="${esc(tx)}">${esc(truncate(tx,40))}</span> <button class="btn btn-sm btn-link btn-copy-tx" style="padding:0;margin-left:6px;">Copy</button></small></div>`:''}</div>
      <div class="notify-actions"><button class="notify-close" aria-label="Close">&times;</button></div>`;
    notifyRoot.prepend(el); requestAnimationFrame(()=>el.classList.add('show'));
    el.querySelector('.notify-close').addEventListener('click',()=>removeNotify(el));
    const copy = el.querySelector('.btn-copy-tx'); if(copy) copy.addEventListener('click',()=>{navigator.clipboard.writeText(el.querySelector('.notify-tx').dataset.tx); copy.textContent='Copied'; setTimeout(()=>copy.textContent='Copy',1200)});
    if(!sticky) setTimeout(()=>removeNotify(el),5400);
  }
  function removeNotify(el){ if(!el) return; el.classList.remove('show'); el.style.pointerEvents='none'; setTimeout(()=>el.remove(),240) }

  // collapse toggle
  const toggle = $('.contract-toggle'), collapse = $('#contractCollapseNative'), arrow = $('.contract-arrow');
  const cap = ()=> Math.floor(window.innerHeight * .60);
  if(toggle && collapse) {
    const open = ()=>{ collapse.classList.add('open'); const full = collapse.scrollHeight; collapse.style.maxHeight = Math.min(full,cap())+'px'; collapse.style.overflow = (full>cap())?'auto':'hidden'; collapse.setAttribute('aria-hidden','false'); toggle.setAttribute('aria-expanded','true'); arrow.classList.add('open') }
    const close = ()=>{ const full = collapse.scrollHeight; collapse.style.maxHeight = full + 'px'; requestAnimationFrame(()=> collapse.style.maxHeight = '0px'); collapse.setAttribute('aria-hidden','true'); toggle.setAttribute('aria-expanded','false'); arrow.classList.remove('open'); collapse.addEventListener('transitionend',function h(){ collapse.classList.remove('open'); collapse.style.overflow='hidden'; collapse.removeEventListener('transitionend',h) }) }
    toggle.addEventListener('click', e=>{ e.preventDefault(); const openNow = collapse.classList.contains('open') && collapse.style.maxHeight && collapse.style.maxHeight!=='0px'; openNow? close() : open() });
    toggle.addEventListener('keydown', e=>{ if(e.key==='Enter'||e.key===' ') { e.preventDefault(); toggle.click() }});
    window.addEventListener('resize', ()=>{ if(!collapse.classList.contains('open')) return; const full = collapse.scrollHeight; collapse.style.maxHeight = Math.min(full,cap())+'px'; collapse.style.overflow = (full>cap())?'auto':'hidden' });
    collapse.setAttribute('aria-hidden','true'); toggle.setAttribute('aria-expanded','false');
  }

  // helpers for forms
  const updateParentCap = parent => { const full = parent.scrollHeight; parent.style.maxHeight = Math.min(full,cap())+'px'; parent.style.overflow = (full>cap())?'auto':'hidden' };
  const scrollParentToElement = elem => { const parent = $('#contractCollapseNative'); if(!parent) return; const parentRect=parent.getBoundingClientRect(), elemRect=elem.getBoundingClientRect(), offset=12; parent.scrollTo({top: Math.max(0, (elemRect.top-parentRect.top)+parent.scrollTop-offset), behavior:'smooth'})};

  // fetch wrapper
  async function postJSON(url,data){
    const res = await fetch(url,{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':CSRF,'Accept':'application/json'},body:JSON.stringify(data||{})});
    const json = await res.json().catch(()=>({ok:false,error:'Invalid server response'}));
    return {status:res.status,ok:res.ok,body:json};
  }

  // inline form wiring
  $$('.change-fn-btn').forEach(btn=>{
    const target = btn.dataset.target, form = document.querySelector(target);
    if(!form) return;
    const save = form.querySelector('.submit-fn-btn'), cancel = form.querySelector('.cancel-fn-btn');
    const showMsg = (f,m,err=false)=>{ let el=f.querySelector('.fn-msg'); if(!el){ el=document.createElement('div'); el.className='fn-msg small mt-2'; f.appendChild(el) } el.textContent=m; el.style.color=err?'#b91c1c':'#064e3b'; setTimeout(()=>el.remove(),4000) };

    const openForm = ()=>{
      const parent = $('#contractCollapseNative');
      form.classList.add('open'); form.style.maxHeight = form.scrollHeight + 'px'; form.setAttribute('aria-hidden','false'); btn.disabled = true;
      if(parent && parent.classList.contains('open')) { requestAnimationFrame(()=>setTimeout(()=>{ updateParentCap(parent); scrollParentToElement(form); },20)); return; }
      if(parent && toggle){ let done=false; const onOpen=()=>{ if(done) return; done=true; form.style.maxHeight=form.scrollHeight+'px'; setTimeout(()=>{ updateParentCap(parent); scrollParentToElement(form); },30); parent.removeEventListener('transitionend',onOpen) }; parent.addEventListener('transitionend',onOpen); toggle.click(); setTimeout(()=>{ if(!done){ done=true; form.style.maxHeight=form.scrollHeight+'px'; updateParentCap(parent); scrollParentToElement(form); parent.removeEventListener('transitionend',onOpen) } },500) }
    };

    const closeForm = ()=>{
      form.style.maxHeight = form.scrollHeight + 'px'; requestAnimationFrame(()=> form.style.maxHeight = '0px'); form.setAttribute('aria-hidden','true');
      form.addEventListener('transitionend', function h(){ form.classList.remove('open'); btn.disabled = false; form.removeEventListener('transitionend',h); const parent = $('#contractCollapseNative'); if(parent && parent.classList.contains('open')) updateParentCap(parent) });
    };

    btn.addEventListener('click', e=>{ e.preventDefault(); const isOpen = form.classList.contains('open') && form.style.maxHeight && form.style.maxHeight!=='0px'; isOpen? closeForm(): openForm() });
    if(cancel) cancel.addEventListener('click', e=>{ e.preventDefault(); closeForm() });

    if(save) save.addEventListener('click', async e=>{
      e.preventDefault(); save.disabled = true;
      const endpoint = form.dataset.endpoint;
      if(!endpoint){ showMsg(form,'No endpoint configured',true); showNotify('No endpoint configured for that action','error'); save.disabled=false; return }
      const inputs = form.querySelectorAll('input,select,textarea'), payload={}; inputs.forEach(i=>{ if(!i.name) return; payload[i.name] = i.type==='checkbox' ? i.checked : i.value });
      showMsg(form,'Sending...');
      try{
        const res = await postJSON(endpoint,payload);
        if(res.ok){ const tx = res.body && res.body.tx_hash? res.body.tx_hash : null; showMsg(form,'Success'); showNotify(res.body && res.body.message ? res.body.message : 'Action succeeded','success',{tx_hash:tx}); setTimeout(()=>{ save.disabled=false; form.style.maxHeight = form.scrollHeight + 'px'; requestAnimationFrame(()=> form.style.maxHeight = '0px'); form.classList.remove('open'); form.setAttribute('aria-hidden','true') },700) }
        else { const err = res.body && (res.body.error||res.body.message) ? (res.body.error||res.body.message) : 'Server error'; showMsg(form,err,true); showNotify(err,'error'); save.disabled=false }
      }catch(err){ showMsg(form,'Network error',true); showNotify('Network error — check your connection','error'); save.disabled=false }
    });
  });

  // confirm actions (pause/unpause)
  const confirmModal = $('#confirmModal'), confirmTitle = $('#confirmModalTitle'), confirmMessage = $('#confirmModalMessage'), confirmOk = $('#confirmOkBtn'), confirmCancel = $('#confirmCancelBtn');
  function showConfirm(opts={}){ if(!confirmModal) return; confirmTitle.textContent = opts.title||'Confirm'; confirmMessage.textContent = opts.message||'Are you sure?'; confirmOk.textContent = opts.okText||'Yes'; confirmOk.className = 'btn btn-sm ' + (opts.okClass||'btn-danger'); confirmModal.classList.remove('d-none'); confirmModal.setAttribute('aria-hidden','false') }
  function hideConfirm(){ if(!confirmModal) return; confirmModal.classList.add('d-none'); confirmModal.setAttribute('aria-hidden','true') }
  if(confirmCancel) confirmCancel.addEventListener('click', hideConfirm);

  $$('.confirm-fn-btn').forEach(btn=>{
    btn.addEventListener('click', e=>{
      e.preventDefault();
      const action = btn.dataset.action, endpoint = btn.getAttribute('data-endpoint');
      if(!endpoint){ showNotify('No endpoint configured for this action','error'); return }
      showConfirm({title:'Confirm '+action, message:`Are you sure you want to ${action} the contract?`, okText:'Yes, '+action, okClass: action==='pause' ? 'btn-danger' : 'btn-success'});
      const onOk = ()=>{
        confirmOk.removeEventListener('click', onOk); hideConfirm();
        (async ()=>{
          btn.disabled = true;
          try{
            const res = await postJSON(endpoint,{});
            if(res.ok){ const tx = res.body && res.body.tx_hash ? res.body.tx_hash : null; const msg = res.body && res.body.message ? res.body.message : `Action ${action} executed`; showNotify(msg,'success',{tx_hash:tx}); const parent = $('#contractCollapseNative'); if(parent && parent.classList.contains('open')) updateParentCap(parent) }
            else { const err = res.body && (res.body.error||res.body.message) ? (res.body.error||res.body.message) : 'Server error'; showNotify(err,'error',{sticky:true}) }
          }catch(err){ showNotify('Network error — check your connection','error',{sticky:true}) }
          finally{ btn.disabled = false }
        })()
      };
      confirmOk.addEventListener('click', onOk);
    })
  });
  if(confirmModal) confirmModal.addEventListener('click', e=>{ if(e.target.classList.contains('confirm-modal-backdrop')) hideConfirm() });

  // responsive adjustments
  window.addEventListener('resize', ()=>{ $$('.fn-form.open').forEach(f=>f.style.maxHeight=f.scrollHeight+'px'); const p = $('#contractCollapseNative'); if(p && p.classList.contains('open')) updateParentCap(p) });
  document.addEventListener('DOMContentLoaded', ()=>{ const p = $('#contractCollapseNative'); if(p && p.classList.contains('open')) updateParentCap(p) });

})();
