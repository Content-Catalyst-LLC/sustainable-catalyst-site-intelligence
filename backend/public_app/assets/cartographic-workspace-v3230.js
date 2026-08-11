(function(window,document){
  "use strict";
  const VERSION="4.35.6";
  const OVERVIEW_IDS=["map"];
  let overviewLayout=null;
  let evidenceRail=null;
  let backdrop=null;
  let countryCatalog=null;

  function qs(selector,root=document){return root.querySelector(selector)}
  function qsa(selector,root=document){return Array.from(root.querySelectorAll(selector))}
  function activeRoute(){return qs('.nav-item.active[data-route]')?.dataset.route||new URLSearchParams(location.search).get('view')||'overview'}
  function mapApi(){return window.SCSIMapReliability||null}

  function buildOverviewWorkspace(){
    const main=qs('#main'),mapPanel=qs('.map-panel'),metrics=qs('.metric-grid'),content=qs('.content-grid');
    if(!main||!mapPanel||!metrics||!content||qs('#overviewLayout'))return;
    overviewLayout=document.createElement('section');
    overviewLayout.id='overviewLayout';overviewLayout.className='overview-layout';overviewLayout.setAttribute('aria-label','Live cartographic intelligence workspace');
    const mapColumn=document.createElement('div');mapColumn.className='overview-map-column';
    const strip=document.createElement('div');strip.id='mapPresentationStatus';strip.className='map-presentation-strip';strip.dataset.state='review';strip.innerHTML='<span class="status-dot" aria-hidden="true"></span><strong>Checking visible map</strong><span>Renderer, geography, dimensions, and controls are being verified.</span>';
    evidenceRail=document.createElement('aside');evidenceRail.id='overviewEvidenceRail';evidenceRail.className='overview-evidence-rail';evidenceRail.setAttribute('aria-label','Evidence and signal drawer');
    evidenceRail.innerHTML='<div class="overview-rail-head"><div><strong>Evidence drawer</strong><span>Signals, country context, and coverage</span></div><button id="closeOverviewRail" type="button">Collapse</button></div><div class="overview-rail-scroll"></div>';
    const scroll=qs('.overview-rail-scroll',evidenceRail);scroll.append(metrics,content);
    mapPanel.before(overviewLayout);overviewLayout.append(mapColumn,evidenceRail);mapColumn.append(mapPanel,strip);
    const toolbar=qs('.map-actions',mapPanel);
    if(toolbar){const button=document.createElement('button');button.id='openOverviewRail';button.type='button';button.className='ghost-button evidence-rail-toggle';button.textContent='Evidence';button.setAttribute('aria-controls','overviewEvidenceRail');button.setAttribute('aria-expanded','true');toolbar.prepend(button);button.addEventListener('click',()=>setRailOpen(!evidenceRail.classList.contains('is-open')))}
    qs('#closeOverviewRail')?.addEventListener('click',()=>setRailOpen(false));
    backdrop=document.createElement('button');backdrop.type='button';backdrop.className='overview-rail-backdrop';backdrop.hidden=true;backdrop.setAttribute('aria-label','Close evidence drawer');document.body.appendChild(backdrop);backdrop.addEventListener('click',()=>setRailOpen(false));
    if(matchMedia('(max-width:980px)').matches)setRailOpen(false);else setRailOpen(true);
  }

  function setRailOpen(open){
    if(!evidenceRail)return;
    const compact=matchMedia('(max-width:980px)').matches;
    evidenceRail.classList.toggle('is-open',Boolean(open));
    evidenceRail.classList.toggle('is-collapsed',!open&&!compact);
    if(backdrop)backdrop.hidden=!(open&&compact);
    const button=qs('#openOverviewRail');if(button)button.setAttribute('aria-expanded',open?'true':'false');
    setTimeout(()=>mapApi()?.getMap?.('map')?.invalidateSize?.(),40);
  }

  function syncRoute(){
    const route=activeRoute();document.body.dataset.activeRoute=route;
    if(overviewLayout)overviewLayout.hidden=route!=='overview';
    qsa('.nav-item[data-route]').forEach(item=>item.dataset.shortLabel=(item.querySelector('span')?.textContent||item.dataset.route).slice(0,10));
    requestAnimationFrame(()=>{
      qsa('.scsi-map-managed').forEach(container=>{if(container.getClientRects().length)mapApi()?.getMap?.(container.id)?.invalidateSize?.()});
      evaluateVisibleMaps();
    });
  }

  async function loadCountryCatalog(){
    if(countryCatalog)return countryCatalog;
    try{const response=await fetch('/public/countries',{headers:{Accept:'application/json'},cache:'no-store'});if(!response.ok)throw new Error(String(response.status));const payload=await response.json();countryCatalog=new Map((payload.countries||[]).map(item=>[item.code,item]));return countryCatalog}catch(_){return new Map()}
  }
  async function focusSelectedCountry(){
    if(activeRoute()!=='overview')return;
    const code=qs('#countrySelect')?.value||'KEN';const catalog=await loadCountryCatalog();const country=catalog.get(code);const map=mapApi()?.getMap?.('map');
    if(!map||!country||!Number.isFinite(Number(country.latitude))||!Number.isFinite(Number(country.longitude)))return;
    map.flyTo([Number(country.latitude),Number(country.longitude)],Number(country.default_zoom||5));
    const strip=qs('#mapPresentationStatus');if(strip){strip.querySelector('span:last-child').textContent=`Focused on ${country.name} with regional geographic context.`}
  }

  function evaluateVisibleMaps(){
    const strip=qs('#mapPresentationStatus');if(!strip)return;
    const visible=qsa('.scsi-map-managed').filter(item=>item.getClientRects().length);
    const active=visible.find(item=>item.id==='map')||visible[0];
    if(!active){strip.dataset.state='failed';strip.innerHTML='<span class="status-dot" aria-hidden="true"></span><strong>Map unavailable</strong><span>No visible map renderer was found for this workspace.</span>';return}
    const rect=active.getBoundingClientRect();const paths=Number(active.dataset.scsiVisibleGeography||0);const tiles=Number(active.dataset.scsiVisibleTiles||0);const controls=active.querySelectorAll('.scsi-map-controls button').length;const ready=rect.width>=300&&rect.height>=300&&(paths>0||tiles>0)&&controls>=2;
    const imagery=active.dataset.scsiImageryMode||'normal';strip.dataset.state=ready?'ready':'review';
    strip.innerHTML=`<span class="status-dot" aria-hidden="true"></span><strong>${ready?'Map presentation ready':'Map presentation incomplete'}</strong><span>${Math.round(rect.width)}×${Math.round(rect.height)} · ${paths} geography paths · ${tiles} live tiles · imagery ${imagery}</span>`;
    active.dataset.scsiPresentationHealth=ready?'ready':'review';
    window.dispatchEvent(new CustomEvent('scsi:visible-map-health',{detail:{version:VERSION,containerId:active.id,ready,width:rect.width,height:rect.height,paths,tiles,controls,imagery}}));
  }

  function bind(){
    buildOverviewWorkspace();syncRoute();
    qs('#primaryNavigation')?.addEventListener('click',()=>setTimeout(syncRoute,0));
    qsa('[data-route-link]').forEach(button=>button.addEventListener('click',()=>setTimeout(syncRoute,0)));
    qs('#countrySelect')?.addEventListener('change',()=>setTimeout(focusSelectedCountry,120));
    window.addEventListener('popstate',()=>setTimeout(syncRoute,0));
    window.addEventListener('scsi:map-local-basemap-ready',()=>{evaluateVisibleMaps();focusSelectedCountry()});
    window.addEventListener('scsi:map-recovered',evaluateVisibleMaps);
    window.addEventListener('resize',()=>{syncRoute();if(!matchMedia('(max-width:980px)').matches&&evidenceRail?.classList.contains('is-collapsed'))setRailOpen(true)});
    new MutationObserver(()=>syncRoute()).observe(qs('#primaryNavigation')||document.body,{subtree:true,attributes:true,attributeFilter:['class','aria-current']});
    setTimeout(()=>{syncRoute();focusSelectedCountry();evaluateVisibleMaps()},700);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',bind,{once:true});else bind();
  window.SCSICartographicWorkspaceV3230={version:VERSION,syncRoute,evaluateVisibleMaps,focusSelectedCountry,setRailOpen};
})(window,document);
