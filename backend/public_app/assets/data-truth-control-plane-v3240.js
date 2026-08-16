(()=>{
  'use strict';
  const VERSION='4.37.0';
  const esc=value=>String(value??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[ch]));
  const label=value=>String(value||'unknown').replaceAll('_',' ');
  async function json(url){const response=await fetch(url,{cache:'no-store',headers:{Accept:'application/json'}});if(!response.ok)throw new Error(`${response.status} ${response.statusText}`);return response.json()}
  function chip(state){return `<span class="scsi-control-chip" data-state="${esc(state)}">${esc(label(state))}</span>`}
  function download(payload,filename){const blob=new Blob([JSON.stringify(payload,null,2)+'\n'],{type:'application/json;charset=utf-8'});const link=document.createElement('a');link.href=URL.createObjectURL(blob);link.download=filename;document.body.appendChild(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(link.href),3000)}
  function summaryCards(summary){const keys=['operational','degraded','review','unavailable','unknown','schema_changed','circuit_open'];return `<div class="scsi-control-summary">${keys.map(key=>`<article><span>${esc(label(key))}</span><strong>${Number(summary?.[key]||0)}</strong></article>`).join('')}</div>`}
  function sourceRows(rows){return `<div class="scsi-control-table-wrap"><table class="scsi-control-table"><thead><tr><th>Source</th><th>Attention</th><th>Presentation</th><th>Freshness</th><th>Schema</th><th>Circuit</th><th>Last success</th></tr></thead><tbody>${rows.map(row=>`<tr data-control-source="${esc(`${row.label} ${row.feed_id}`.toLowerCase())}"><th>${esc(row.label)}<small>${esc(row.feed_id)}</small></th><td>${chip(row.attention_state)}${(row.attention_reasons||[]).length?`<details><summary>${row.attention_reasons.length} reason${row.attention_reasons.length===1?'':'s'}</summary><ul>${row.attention_reasons.map(reason=>`<li>${esc(reason)}</li>`).join('')}</ul></details>`:''}</td><td>${chip(row.presentation_state)}</td><td>${esc(label(row.freshness))}</td><td>${chip(row.schema_state)}</td><td>${chip(row.circuit_state)}</td><td>${esc(row.last_success_at||'No successful retrieval recorded')}</td></tr>`).join('')}</tbody></table></div>`}
  function incidents(items){if(!items.length)return '<p class="scsi-control-empty">No current control-plane incidents were classified.</p>';return `<div class="scsi-control-incident-list">${items.map(item=>`<article><div><strong>${esc(item.label)}</strong><small>${esc(item.feed_id)}</small></div>${chip(item.incident_state)}<ul>${(item.reasons||[]).map(reason=>`<li>${esc(reason)}</li>`).join('')}</ul></article>`).join('')}</div>`}
  function drift(items){return `<div class="scsi-control-drift-list">${items.map(item=>`<article><div><strong>${esc(item.label)}</strong><small>${esc(item.feed_id)}</small></div>${chip(item.schema_state)}<p>${item.review_required?'Review required before silent field substitution.':'Declared and observed schema state does not currently require review.'}</p></article>`).join('')}</div>`}
  function workspaceCards(items){return `<div class="scsi-control-workspaces">${items.map(item=>`<article><div><strong>${esc(item.label)}</strong><small>${esc(item.workspace_id)}</small></div>${chip(item.truth_state)}<p>${Number(item.dependency_count||0)} disclosed source dependencies · limitations visible</p></article>`).join('')}</div>`}
  async function renderInto(container,country='KEN'){
    if(!container)throw new Error('Control-plane container is unavailable.');
    container.innerHTML='<p class="scsi-data-truth-loading">Loading source operations, schema drift, incidents, coverage, and workspace truth…</p>';
    const code=String(country||'KEN').toUpperCase();
    const [overview,schema,outages,workspacePayload]=await Promise.all([
      json('/public/data-truth/control-plane'),
      json('/public/data-truth/control-plane/schema-drift'),
      json('/public/data-truth/control-plane/outages'),
      json(`/public/data-truth/control-plane/workspaces?country=${encodeURIComponent(code)}`),
    ]);
    container.innerHTML=`<div class="scsi-data-truth-intro scsi-control-intro"><div><p><strong>Global Data Truth Control Plane</strong></p><p>Operational source status, schema drift, coverage gaps, and workspace dependencies. Source health does not prove country-level record availability.</p></div><button id="dataTruthControlExport" type="button" class="ghost-button">Export control-plane JSON</button></div>${summaryCards(overview.summary)}<label class="scsi-control-filter">Filter sources <input id="dataTruthControlFilter" type="search" placeholder="Source or feed ID"></label><h3>Source operations</h3>${sourceRows(overview.sources||[])}<div class="scsi-control-columns"><section><h3>Current attention register</h3>${incidents(outages.incidents||[])}</section><section><h3>Schema drift register</h3>${drift(schema.sources||[])}</section></div><h3>Cross-workspace truth · ${esc(workspacePayload.country?.name||code)}</h3>${workspaceCards(workspacePayload.workspaces||[])}<div class="scsi-control-boundaries"><h3>Boundaries</h3><ul>${(overview.boundaries||[]).map(item=>`<li>${esc(item)}</li>`).join('')}</ul><code>${esc(overview.control_plane_fingerprint||'Fingerprint unavailable')}</code></div>`;
    container.querySelector('#dataTruthControlFilter')?.addEventListener('input',event=>{const term=event.target.value.trim().toLowerCase();container.querySelectorAll('[data-control-source]').forEach(row=>row.hidden=Boolean(term&&!row.dataset.controlSource.includes(term)))});
    container.querySelector('#dataTruthControlExport')?.addEventListener('click',async()=>{const payload=await json(`/public/data-truth/control-plane/export?country=${encodeURIComponent(code)}`);download(payload,`site-intelligence-${code.toLowerCase()}-data-truth-control-plane.json`)});
    window.dispatchEvent(new CustomEvent('scsi:data-truth-control-plane-ready',{detail:{version:VERSION,country:code,sourceCount:overview.source_count,workspaceCount:workspacePayload.workspace_count}}));
    return {overview,schema,outages,workspaces:workspacePayload};
  }
  window.SCSIDataTruthControlPlaneV3240={version:VERSION,renderInto};
})();
