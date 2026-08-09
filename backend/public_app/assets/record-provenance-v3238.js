(()=>{
  'use strict';
  const VERSION='4.1.0';
  const root=document.querySelector('#app')||document.body;
  let panel=null,body=null,previousFocus=null,currentRecord=null;
  const esc=value=>String(value??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[ch]));
  const label=value=>String(value||'unknown').replaceAll('_',' ');
  const selectedCountry=()=>document.querySelector('#countrySelect')?.value||new URLSearchParams(location.search).get('country')||'KEN';
  async function json(url,options={}){const response=await fetch(url,{cache:'no-store',headers:{Accept:'application/json','Content-Type':'application/json',...(options.headers||{})},...options});if(!response.ok)throw new Error(`${response.status} ${response.statusText}`);return response.json()}
  function create(){
    if(panel)return;
    panel=document.createElement('aside');panel.id='recordTruthPanel';panel.className='scsi-record-truth-panel';panel.hidden=true;panel.setAttribute('aria-label','Record provenance and indicator truth');
    panel.innerHTML=`<header class="scsi-record-truth-head"><div><p class="eyebrow">RECORD PROVENANCE · v${VERSION}</p><h2>Record truth</h2><p>Source, dates, units, transformations, fingerprint, and limitations for the selected public record.</p></div><button id="recordTruthClose" type="button" class="icon-button" aria-label="Close record truth">×</button></header><div class="scsi-record-truth-actions"><button id="recordTruthDownload" type="button" class="ghost-button" disabled>Export record JSON</button><button id="recordTruthManifest" type="button" class="ghost-button">Export country manifest</button></div><div id="recordTruthBody" aria-live="polite"><p>Select a record with a <strong>Truth</strong> control.</p></div>`;
    root.appendChild(panel);body=panel.querySelector('#recordTruthBody');panel.querySelector('#recordTruthClose').addEventListener('click',close);panel.querySelector('#recordTruthDownload').addEventListener('click',()=>currentRecord&&download(currentRecord,`${safeName(currentRecord.record_id||'record-truth')}.json`));panel.querySelector('#recordTruthManifest').addEventListener('click',exportManifest);document.addEventListener('keydown',event=>{if(event.key==='Escape'&&!panel.hidden)close()});
  }
  function safeName(value){return String(value||'record-truth').toLowerCase().replace(/[^a-z0-9._-]+/g,'-').replace(/^-+|-+$/g,'').slice(0,120)||'record-truth'}
  function download(payload,filename){const blob=new Blob([JSON.stringify(payload,null,2)+'\n'],{type:'application/json;charset=utf-8'});const link=document.createElement('a');link.href=URL.createObjectURL(blob);link.download=filename;document.body.appendChild(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(link.href),3000)}
  function field(term,value){return `<div><dt>${esc(term)}</dt><dd>${value==null||value===''?'Not disclosed':esc(value)}</dd></div>`}
  function linkField(term,value){return `<div><dt>${esc(term)}</dt><dd>${value?`<a href="${esc(value)}" target="_blank" rel="noopener">Open source ↗</a>`:'Not disclosed'}</dd></div>`}
  function render(record){
    currentRecord=record;panel.querySelector('#recordTruthDownload').disabled=false;
    const dates=record.dates||{},source=record.source||{},units=record.units||{},value=record.value||{},fingerprint=record.fingerprint||{},country=record.country||{};
    const transformations=(record.transformations||[]).map(step=>`<li><strong>${esc(label(step.operation))}</strong><span>${esc(step.detail||'')}</span></li>`).join('');
    const limitations=(record.limitations||[]).filter(Boolean).map(item=>`<li>${esc(item)}</li>`).join('');
    body.innerHTML=`<section class="scsi-record-truth-summary"><div><span class="scsi-record-truth-state" data-state="${esc(record.truth_state)}">${esc(label(record.truth_state))}</span><p class="eyebrow">${esc(label(record.record_type))}</p><h3>${esc(record.title||record.record_id||'Public record')}</h3><p>${esc(record.assertion||'No additional assertion is supplied.')}</p></div><code title="Complete record identifier">${esc(record.record_id||'Record identifier unavailable')}</code></section><dl class="scsi-record-truth-grid">${field('Country',[country.name,country.code].filter(Boolean).join(' · '))}${field('Presentation state',label(record.presentation_state))}${field('Value',value.available===false?'Missing':value.text??value.number)}${field('Original unit',units.original)}${field('Display unit',units.display)}${field('Observation date',dates.observation_at||dates.observation_year)}${field('Retrieved at',dates.retrieved_at)}${field('Publisher',source.publisher)}${field('Source identifier',source.indicator_id||source.feed_id)}${linkField('Primary source',source.url)}</dl><section><h3>Transformation ledger</h3><ol class="scsi-record-transformations">${transformations||'<li>No transformation steps were disclosed.</li>'}</ol></section><section><h3>Fingerprint</h3><p>${esc(fingerprint.meaning||'Fingerprint meaning unavailable.')}</p><code class="scsi-record-fingerprint">${esc(fingerprint.value||'Fingerprint unavailable')}</code></section><section><h3>Limitations</h3><ul class="scsi-record-limitations">${limitations||'<li>No limitations were disclosed.</li>'}</ul></section>`;
    window.dispatchEvent(new CustomEvent('scsi:record-truth-ready',{detail:{version:VERSION,recordId:record.record_id,recordType:record.record_type,truthState:record.truth_state}}));
  }
  function loading(message){create();body.innerHTML=`<p class="scsi-record-truth-loading">${esc(message)}</p>`}
  function failure(error){body.innerHTML=`<div class="scsi-record-truth-error"><strong>Record truth unavailable</strong><p>${esc(error?.message||error)}</p></div>`}
  async function openWith(loader,message='Loading record truth…'){
    create();previousFocus=document.activeElement;panel.hidden=false;loading(message);panel.querySelector('#recordTruthClose').focus();try{render(await loader())}catch(error){failure(error)}
  }
  function close(){if(!panel)return;panel.hidden=true;previousFocus?.focus?.()}
  function openIndicator(country,indicator){return openWith(()=>json(`/public/record-truth/indicator/${encodeURIComponent(country||selectedCountry())}/${encodeURIComponent(indicator)}`),'Loading indicator provenance…')}
  function openLayer(layer,date){return openWith(()=>json(`/public/record-truth/map-layer/${encodeURIComponent(layer)}${date?`?date=${encodeURIComponent(date)}`:''}`),'Loading map-layer provenance…')}
  function openRecord(record){return openWith(()=>json('/public/record-truth/resolve',{method:'POST',body:JSON.stringify(record||{})}),'Normalizing public record provenance…')}
  async function exportManifest(){try{const code=selectedCountry();const manifest=await json(`/public/record-truth/manifest?country=${encodeURIComponent(code)}`);download(manifest,`site-intelligence-${code.toLowerCase()}-record-provenance-manifest.json`)}catch(error){failure(error)}}
  document.addEventListener('click',event=>{
    const indicator=event.target.closest('[data-record-truth-indicator]');if(indicator){event.preventDefault();openIndicator(indicator.dataset.recordTruthCountry||selectedCountry(),indicator.dataset.recordTruthIndicator);return}
    const layer=event.target.closest('[data-record-truth-layer]');if(layer){event.preventDefault();openLayer(layer.dataset.recordTruthLayer,layer.dataset.recordTruthDate||'');return}
  });
  window.addEventListener('scsi:record-truth',event=>{const detail=event.detail||{};if(detail.indicatorId)return openIndicator(detail.country||selectedCountry(),detail.indicatorId);if(detail.layerId)return openLayer(detail.layerId,detail.date);if(detail.record)return openRecord(detail.record)});
  create();
  window.SCSIRecordProvenanceV3238={version:VERSION,openIndicator,openLayer,openRecord,exportManifest,close,getCurrent:()=>currentRecord};
})();
