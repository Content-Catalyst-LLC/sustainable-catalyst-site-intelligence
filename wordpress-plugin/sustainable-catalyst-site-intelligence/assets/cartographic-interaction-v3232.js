(function(window,document){
  "use strict";
  const VERSION="4.10.0";
  const APP_ROOT=document.querySelector('#app[data-scsi-release]');
  if(!APP_ROOT||!document.querySelector('#map'))return;
  let panel=null,button=null,summary=null,initialized=false;
  const qs=(selector,root=document)=>root.querySelector(selector);
  const qsa=(selector,root=document)=>Array.from(root.querySelectorAll(selector));
  const api=()=>window.SCSIOverviewMapV3232||null;
  const semantic=value=>{const v=String(value||'other').toLowerCase();if(v.includes('earthquake')||v.includes('seismic'))return 'earthquake';if(v.includes('fire')||v.includes('wildfire')||v.includes('thermal'))return 'wildfire';if(v.includes('storm')||v.includes('cyclone')||v.includes('hurricane')||v.includes('typhoon'))return 'storm';if(v.includes('flood'))return 'flood';if(v.includes('humanitarian')||v.includes('displacement')||v.includes('refugee'))return 'humanitarian';if(v.includes('conflict')||v.includes('violence'))return 'conflict';return 'other'};
  function setOpen(open){if(!panel||!button)return;panel.hidden=!open;button.setAttribute('aria-expanded',open?'true':'false');if(open)qs('select,input,button',panel)?.focus()}
  function copyLink(){const value=location.href;const done=()=>{const status=qs('#mapControlStatus');if(status)status.textContent='Shareable map state copied.'};if(navigator.clipboard?.writeText)navigator.clipboard.writeText(value).then(done).catch(()=>{});else{const input=document.createElement('textarea');input.value=value;document.body.appendChild(input);input.select();try{document.execCommand('copy');done()}catch(_){}input.remove()}}
  function createPanel(){
    const mapPanel=qs('.map-panel');if(!mapPanel||qs('#mapInteractionPanel'))return;
    button=document.createElement('button');button.id='mapInteractionToggle';button.className='ghost-button map-control-toggle';button.type='button';button.textContent='Layers & filters';button.setAttribute('aria-controls','mapInteractionPanel');button.setAttribute('aria-expanded','false');
    (qs('.map-actions',mapPanel)||mapPanel).prepend(button);
    panel=document.createElement('section');panel.id='mapInteractionPanel';panel.className='map-interaction-panel';panel.hidden=true;panel.setAttribute('aria-label','Map layers, filters, and share controls');panel.innerHTML=`
      <div class="map-interaction-head"><div><span>MAP CONTROL</span><strong>Layers and evidence filters</strong></div><button id="closeMapInteraction" type="button" aria-label="Close map controls">Close</button></div>
      <div class="map-interaction-grid">
        <label>Base presentation<select id="mapBaseStyle"><option value="institutional-dark">Institutional dark</option><option value="evidence-neutral">Evidence neutral</option><option value="imagery-focus">Imagery focus</option></select></label>
        <label>Imagery opacity <output id="mapOpacityValue">62%</output><input id="mapImageryOpacity" type="range" min="0" max="100" step="1" value="62"></label>
        <label>Event category<select id="mapCategoryFilter"><option value="">All categories</option></select></label>
        <label>Source<select id="mapSourceFilter"><option value="">All sources</option></select></label>
        <label>Recency<select id="mapRecencyFilter"><option value="7">7 days</option><option value="14">14 days</option><option value="30" selected>30 days</option><option value="90">90 days</option><option value="365">1 year</option></select></label>
        <div class="map-switches" role="group" aria-label="Event display options"><label><input id="mapEventsVisible" type="checkbox" checked> Show events</label><label><input id="mapClusterEvents" type="checkbox" checked> Cluster at global zoom</label></div>
      </div>
      <div id="mapSemanticLegend" class="map-semantic-legend" aria-label="Event symbol legend"></div>
      <div class="map-interaction-actions"><button id="mapFitResults" type="button">Fit results</button><button id="mapResetFilters" type="button">Reset filters</button><button id="mapShareState" type="button">Copy map link</button></div>
      <p id="mapControlStatus" class="map-control-status" aria-live="polite">Map controls ready.</p>`;
    mapPanel.appendChild(panel);
    summary=document.createElement('div');summary.id='mapFilterSummary';summary.className='map-filter-summary';summary.setAttribute('aria-live','polite');mapPanel.appendChild(summary);
    button.addEventListener('click',()=>setOpen(panel.hidden));qs('#closeMapInteraction').addEventListener('click',()=>setOpen(false));
    qs('#mapBaseStyle').addEventListener('change',event=>{api()?.setBaseStyle(event.target.value);updateSummary()});
    qs('#mapImageryOpacity').addEventListener('input',event=>{const value=Number(event.target.value);qs('#mapOpacityValue').textContent=`${value}%`;api()?.setImageryOpacity(value/100);syncOpacity(value)});
    qs('#mapCategoryFilter').addEventListener('change',event=>apply({categories:event.target.value?[event.target.value]:[]}));
    qs('#mapSourceFilter').addEventListener('change',event=>apply({source:event.target.value}));
    qs('#mapRecencyFilter').addEventListener('change',event=>apply({days:Number(event.target.value)}));
    qs('#mapEventsVisible').addEventListener('change',event=>apply({eventsVisible:event.target.checked}));
    qs('#mapClusterEvents').addEventListener('change',event=>apply({cluster:event.target.checked}));
    qs('#mapFitResults').addEventListener('click',()=>api()?.fitResults());
    qs('#mapResetFilters').addEventListener('click',reset);
    qs('#mapShareState').addEventListener('click',copyLink);
    document.addEventListener('keydown',event=>{if(event.key==='Escape'&&!panel.hidden)setOpen(false)});
    renderLegend();restoreControls();initialized=true;updateOptions();updateSummary();
  }
  function syncOpacity(value){const params=new URLSearchParams(location.search);params.set('mapOpacity',String(value));history.replaceState(null,'',`?${params.toString()}`)}
  function apply(next){api()?.setFilters(next,true);updateSummary()}
  function reset(){
    qs('#mapCategoryFilter').value='';qs('#mapSourceFilter').value='';qs('#mapRecencyFilter').value='30';qs('#mapClusterEvents').checked=true;qs('#mapEventsVisible').checked=true;qs('#mapBaseStyle').value='institutional-dark';qs('#mapImageryOpacity').value='62';qs('#mapOpacityValue').textContent='62%';
    api()?.setBaseStyle('institutional-dark');api()?.setImageryOpacity(.62);api()?.setFilters({categories:[],source:'',days:30,cluster:true,eventsVisible:true,selected:''},true);syncOpacity(62);updateSummary();
  }
  function restoreControls(){const params=new URLSearchParams(location.search),filters=api()?.getFilters?.()||{};const style=params.get('mapStyle')||'institutional-dark',opacity=Math.max(0,Math.min(100,Number(params.get('mapOpacity')||62)));qs('#mapBaseStyle').value=style;qs('#mapImageryOpacity').value=String(opacity);qs('#mapOpacityValue').textContent=`${opacity}%`;qs('#mapRecencyFilter').value=String(filters.days||params.get('mapDays')||30);qs('#mapClusterEvents').checked=filters.cluster!==false;qs('#mapEventsVisible').checked=filters.eventsVisible!==false;api()?.setBaseStyle(style);api()?.setImageryOpacity(opacity/100)}
  function updateOptions(){const features=api()?.getEvents?.()||[];const categories=[...new Set(features.map(item=>semantic(item.properties?.category)))].sort();const sources=[...new Set(features.map(item=>String(item.properties?.source||'')).filter(Boolean))].sort();const category=qs('#mapCategoryFilter'),source=qs('#mapSourceFilter');if(!category||!source)return;const currentCategory=api()?.getFilters?.().categories?.[0]||'';const currentSource=api()?.getFilters?.().source||'';category.innerHTML='<option value="">All categories</option>'+categories.map(item=>`<option value="${item}">${item.charAt(0).toUpperCase()+item.slice(1)}</option>`).join('');source.innerHTML='<option value="">All sources</option>'+sources.map(item=>`<option value="${escapeHtml(item)}">${escapeHtml(item)}</option>`).join('');category.value=currentCategory;source.value=currentSource}
  function escapeHtml(value){return String(value).replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[char]))}
  function renderLegend(){const labels={earthquake:'Earthquake',wildfire:'Fire',storm:'Storm',flood:'Flood',humanitarian:'Humanitarian',conflict:'Conflict',other:'Other'};qs('#mapSemanticLegend').innerHTML=Object.entries(labels).map(([id,label])=>`<span class="semantic-${id}"><i aria-hidden="true"></i>${label}</span>`).join('')}
  function updateSummary(){if(!summary)return;const filters=api()?.getFilters?.()||{},count=api()?.getFilteredEvents?.().length||0;const labels=[];if(filters.categories?.length)labels.push(filters.categories.join(', '));if(filters.source)labels.push(filters.source);labels.push(`${filters.days||30} days`);labels.push(filters.cluster?'clustered':'individual');summary.innerHTML=`<strong>${count} mapped records</strong><span>${labels.join(' · ')}</span>`;const status=qs('#mapControlStatus');if(status)status.textContent=`${count} records match the active map filters.`}
  function bind(){createPanel();window.addEventListener('scsi:overview-events-rendered',()=>{updateOptions();updateSummary()});window.addEventListener('scsi:map-local-basemap-ready',updateSummary);const observer=new MutationObserver(()=>{if(!initialized)createPanel()});observer.observe(document.body,{childList:true,subtree:true})}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',bind,{once:true});else bind();
  window.SCSICartographicInteractionV3232={version:VERSION,open:()=>setOpen(true),close:()=>setOpen(false),reset,updateSummary};
})(window,document);
