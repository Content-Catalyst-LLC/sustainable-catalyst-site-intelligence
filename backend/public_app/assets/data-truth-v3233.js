(function(){
  "use strict";
  const VERSION="3.23.6.4";
  const root=document.querySelector('#app[data-scsi-release]');
  if(!root)return;
  let payload=null;
  let panel=null;
  let toggle=null;
  let previousFocus=null;
  const esc=value=>String(value??"").replace(/[&<>"']/g,char=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char]));
  const label=value=>String(value||"unknown").replaceAll('_',' ');
  function create(){
    if(panel)return;
    toggle=document.createElement('button');
    toggle.type='button';
    toggle.id='dataTruthToggle';
    toggle.className='ghost-button scsi-data-truth-toggle';
    toggle.setAttribute('aria-controls','dataTruthPanel');
    toggle.setAttribute('aria-expanded','false');
    toggle.innerHTML='<span>Data truth</span><small id="dataTruthBadge">checking</small>';
    const controls=root.querySelector('.topbar-controls')||root.querySelector('.map-actions')||root;
    controls.insertBefore(toggle,controls.firstChild);
    panel=document.createElement('aside');
    panel.id='dataTruthPanel';
    panel.className='scsi-data-truth-panel';
    panel.hidden=true;
    panel.setAttribute('aria-label','Data freshness, coverage, and source truth');
    panel.innerHTML='<div class="scsi-data-truth-head"><div><p class="eyebrow">SOURCE TRUTH · v3.23.6.4</p><h2>Data condition and coverage</h2></div><button id="dataTruthClose" type="button" class="icon-button" aria-label="Close data truth panel">×</button></div><div id="dataTruthBody" aria-live="polite"><p>Checking public source contracts…</p></div>';
    root.appendChild(panel);
    toggle.addEventListener('click',()=>panel.hidden?open():close());
    panel.querySelector('#dataTruthClose').addEventListener('click',close);
    document.addEventListener('keydown',event=>{if(event.key==='Escape'&&!panel.hidden)close();});
  }
  function summary(data){
    const s=data.summary||{};
    return `<div class="scsi-data-truth-summary">
      <article><span>Live</span><strong>${Number(s.live||0)}</strong></article>
      <article><span>Cached</span><strong>${Number(s.recently_cached||0)}</strong></article>
      <article><span>Historical</span><strong>${Number(s.historical_snapshot||0)}</strong></article>
      <article><span>Demonstration</span><strong>${Number(s.demonstration||0)}</strong></article>
      <article><span>Context only</span><strong>${Number(s.context_only||0)}</strong></article>
      <article><span>Unavailable</span><strong>${Number(s.unavailable||0)}</strong></article>
    </div>`;
  }
  function sourceRow(source){
    const state=source.data_state||{};
    const retrieval=source.retrieval||{};
    const completeness=source.completeness||{};
    const schema=source.schema||{};
    const coverage=source.coverage||{};
    const license=source.license||{};
    const stale=state.stale_marker_required?'<span class="scsi-truth-warning">stale marker required</span>':'';
    const lastSuccess=retrieval.last_success_at?new Date(retrieval.last_success_at).toLocaleString():'No successful retrieval recorded';
    return `<article class="scsi-data-source" data-truth-state="${esc(state.presentation)}">
      <div class="scsi-data-source-title"><div><strong>${esc(source.label)}</strong><small>${esc(source.publisher)}</small></div><span class="scsi-truth-state">${esc(label(state.presentation))}</span></div>
      <p>${esc(state.reason)}</p>${stale}
      <dl>
        <div><dt>Last success</dt><dd>${esc(lastSuccess)}</dd></div>
        <div><dt>Refresh</dt><dd>${Number(source.refresh_policy?.refresh_minutes||0)} min · stale after ${Number(source.refresh_policy?.stale_after_minutes||0)} min</dd></div>
        <div><dt>Coverage</dt><dd>${esc(coverage.geographic||'Not declared')} · ${esc(coverage.temporal||'Not declared')}</dd></div>
        <div><dt>License</dt><dd>${esc(license.name||'Not declared')}</dd></div>
        <div><dt>Metadata</dt><dd>${esc(String(completeness.score_percent??0))}% complete</dd></div>
        <div><dt>Schema</dt><dd>${esc(label(schema.status))}</dd></div>
      </dl>
      <details><summary>Endpoint and method</summary><p><code>${esc(source.endpoint?.url||'Not declared')}</code></p><p>${esc(source.quality?.limitations||source.public_note||'No additional limitation note.')}</p></details>
    </article>`;
  }
  function render(data){
    payload=data;
    const body=panel.querySelector('#dataTruthBody');
    const badge=document.querySelector('#dataTruthBadge');
    const summaryData=data.summary||{};
    const qualified=Number(summaryData.live||0);
    const nonLive=Number(data.source_count||0)-qualified;
    badge.textContent=qualified?`${qualified} live · ${nonLive} qualified`:`${nonLive} non-live`;
    body.innerHTML=`<div class="scsi-data-truth-intro"><p><strong>Application mode:</strong> ${esc(label(data.application_mode))}</p><p>Cached, historical, demonstration, context-only, and unavailable records are not presented as live.</p></div>${summary(data)}<div class="scsi-data-source-list">${(data.sources||[]).map(sourceRow).join('')}</div>`;
    window.dispatchEvent(new CustomEvent('scsi:data-truth-ready',{detail:{version:VERSION,sourceCount:data.source_count,summary:data.summary}}));
  }
  async function refresh(){
    create();
    try{
      const response=await fetch('/public/data-truth',{headers:{Accept:'application/json'},cache:'no-store'});
      if(!response.ok)throw new Error(`Data truth request failed (${response.status})`);
      const data=await response.json();
      if(!data.ok||data.version!==VERSION)throw new Error('Data truth contract is not aligned to the active release.');
      render(data);
      return data;
    }catch(error){
      const badge=document.querySelector('#dataTruthBadge');
      if(badge)badge.textContent='unavailable';
      const body=panel?.querySelector('#dataTruthBody');
      if(body)body.innerHTML=`<div class="scsi-data-truth-error"><strong>Source truth unavailable</strong><p>${esc(error.message||error)}</p><button id="dataTruthRetry" type="button" class="ghost-button">Retry</button></div>`;
      body?.querySelector('#dataTruthRetry')?.addEventListener('click',refresh);
      return null;
    }
  }
  function open(){
    create();
    previousFocus=document.activeElement;
    panel.hidden=false;
    toggle.setAttribute('aria-expanded','true');
    panel.querySelector('#dataTruthClose').focus();
    if(!payload)refresh();
  }
  function close(){
    if(!panel)return;
    panel.hidden=true;
    toggle?.setAttribute('aria-expanded','false');
    previousFocus?.focus?.();
  }
  create();
  refresh();
  window.SCSIDataTruthV3233={version:VERSION,open,close,refresh,render,getPayload:()=>payload};
})();
