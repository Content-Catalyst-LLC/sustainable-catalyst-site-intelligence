(function(window,document){
  "use strict";
  const VERSION="4.12.0";
  const APP_ROOT=document.querySelector('#app[data-scsi-release]');
  if(!APP_ROOT||!document.querySelector('#primaryNavigation')||!document.querySelector('#main.workspace'))return;
  const ENDPOINT="/public/workspaces/production-truth";
  const CORE_ROUTES=new Set(["overview","global","economics","law","science","humanitarian","resources","dossiers","alerts","scenarios","earth","spatial","harmonization","country","events","compare","thematic","briefing","sources"]);
  const CONTROLLERS={platform:"SCConnectedPlatformV300",global:"SCGlobalConditionsV210",economics:"SCEconomicsV220",law:"SCLawV230",science:"SCScienceV240",humanitarian:"SCHumanitarianV250",resources:"SCResourcesV260",dossiers:"SCDossiersV270",alerts:"SCAlertsV280",scenarios:"SCScenariosV290",research:"SCResearchV2100",integration:"SCIntegrationV2110",experience:"SCExperienceV2120",spatial:"SCSpatialV2150",harmonization:"SCHarmonizationV2160",models:"SCModelsV2170",evidence:"SCEvidenceV2180",graph:"SCKnowledgeGraphV2190",publishing:"SCIntelligencePublishingV2200",monitoring:"SCScheduledMonitoringV2210",workspaces:"SCInstitutionalWorkspacesV2220",workflows:"SCCrossPlatformWorkflowsV2230",federation:"SCInstitutionalFederationV2240",governance:"SCProductionGovernanceV2250"};
  const NATIVE_SURFACES={overview:["#overviewLayout","#map"],observatory:["#auditablePublicObservatory"],launch:["#publicLaunchPortfolio"],earth:["#earthStudio","#earthMapA"],country:["#countryIntelligencePanel","#countryOverviewMap"],events:["#eventStudio","#eventExplorerMap"],compare:["#compareStudio","#compareMap"],thematic:["#thematicStudio","#thematicMap"],briefing:["#briefingStudio"],sources:["#sourceStudio"],saved:["#savedViewsStudio"]};
  const state={directory:null,route:null,phase:"initial",reason:"",timer:null,historyLock:false,lastRequestAt:0};
  let bar=null;

  function qs(s,r=document){return r.querySelector(s)}
  function qsa(s,r=document){return Array.from(r.querySelectorAll(s))}
  function currentRoute(){return window.SCSIRouterV3228?.current?.()||qs('.nav-item.active[data-route]')?.dataset.route||new URLSearchParams(location.search).get('view')||'overview'}
  function contract(route){return state.directory?.routes?.find(item=>item.route_id===route)||{route_id:route,label:qs(`.nav-item[data-route="${route}"] span`)?.textContent||route,completion:CORE_ROUTES.has(route)?"operational":"operational-bounded",empty_state:"No public records are available for this workspace.",degraded_state:"This workspace is partially available while public services recover.",limitation:"Public evidence remains subject to source, coverage, and methodology limits."}}
  function escapeHtml(value){return String(value??"").replace(/[&<>'"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[c]))}

  function buildBar(){
    if(bar)return bar;
    const workspace=qs('#main')||qs('.workspace');if(!workspace)return null;
    bar=document.createElement('section');bar.id='productionTruthBar';bar.className='production-truth-bar';bar.dataset.state='initial';bar.setAttribute('aria-live','polite');bar.innerHTML='<div class="truth-state"><span class="truth-dot" aria-hidden="true"></span><div><strong id="truthStateLabel">Checking workspace</strong><span id="truthStateDetail">Verifying route, surface, and public data state.</span></div></div><div class="truth-actions"><span id="truthScopeBadge" class="truth-scope">Public workspace</span><button id="truthRetry" type="button">Retry</button><button id="truthDetails" type="button" aria-expanded="false">Details</button></div><div id="truthDisclosure" class="truth-disclosure" hidden></div>';
    const head=qs('.workspace-head',workspace)||qs('.immersive-head',workspace);if(head)head.after(bar);else workspace.prepend(bar);
    qs('#truthRetry',bar).addEventListener('click',()=>retryActiveRoute());
    qs('#truthDetails',bar).addEventListener('click',event=>{const disclosure=qs('#truthDisclosure',bar);disclosure.hidden=!disclosure.hidden;event.currentTarget.setAttribute('aria-expanded',disclosure.hidden?'false':'true')});
    return bar;
  }

  function setPhase(phase,reason=""){
    buildBar();if(!bar)return;
    state.phase=phase;state.reason=reason;bar.dataset.state=phase;
    const item=contract(state.route||currentRoute());
    const labels={initial:"Opening workspace",ready:"Workspace ready",empty:"No matching public records",degraded:"Workspace partially available",unavailable:"Workspace unavailable"};
    const detail=reason||({initial:"The route is opening and its public surface is being verified.",ready:`${item.label} is operational within its published public scope.`,empty:item.empty_state,degraded:item.degraded_state,unavailable:"The required public controller or workspace surface is not available in this release."}[phase]);
    qs('#truthStateLabel',bar).textContent=labels[phase]||labels.initial;
    qs('#truthStateDetail',bar).textContent=detail;
    const badge=qs('#truthScopeBadge',bar);badge.textContent=item.completion==='operational'?'Operational':'Operational · bounded';
    const disclosure=qs('#truthDisclosure',bar);disclosure.innerHTML=`<strong>${escapeHtml(item.label)} production contract</strong><p>${escapeHtml(item.limitation||'Public evidence limits remain visible.')}</p><dl><div><dt>Route</dt><dd>${escapeHtml(item.route_id)}</dd></div><div><dt>State</dt><dd>${escapeHtml(phase)}</dd></div><div><dt>Loading</dt><dd>${item.lazy_load===false?'eager':'active route only'}</dd></div></dl>`;
    document.body.dataset.workspaceState=phase;
    document.body.dataset.workspaceRoute=state.route||currentRoute();
    window.dispatchEvent(new CustomEvent('scsi:workspace-state',{detail:{version:VERSION,route:state.route||currentRoute(),state:phase,reason:detail}}));
  }

  function surfaceFor(route){
    const item=contract(route);const selectors=[...(item.surface_selectors||[]),...(NATIVE_SURFACES[route]||[])];
    for(const selector of selectors){const node=qs(selector);if(node&&node.getClientRects().length)return node}
    const routePanel=qs('#routePanel');if(routePanel&&!routePanel.hidden&&routePanel.getClientRects().length)return routePanel;
    return null;
  }
  function controllerAvailable(route){const name=contract(route).controller||CONTROLLERS[route];return !name||Boolean(window[name])}
  function classifySurface(route){
    if(!APP_ROOT.classList.contains('app-ready'))return {phase:'initial',reason:'The Site Intelligence application is still completing its launch sequence.'};
    if(!controllerAvailable(route))return {phase:'unavailable',reason:`The ${contract(route).label} controller is not packaged in this release.`};
    const surface=surfaceFor(route);if(!surface)return {phase:'unavailable',reason:`The ${contract(route).label} route opened without a visible workspace surface.`};
    const text=(surface.textContent||'').replace(/\s+/g,' ').trim();
    const hasFailure=/failed to load|unavailable|could not load|service did not respond|temporarily unavailable/i.test(text);
    const hasLoading=/loading|preparing|connecting|checking/i.test(text);
    const meaningful=surface.querySelectorAll('article,.panel,.metric-card,.event-row,.source-row,.scsi-map-managed,canvas,svg,table,li').length>0||text.length>180;
    if(hasFailure)return {phase:'degraded',reason:contract(route).degraded_state};
    if(hasLoading&&!meaningful)return {phase:'initial',reason:'The active workspace is still connecting to its public services.'};
    if(!meaningful)return {phase:'empty',reason:contract(route).empty_state};
    return {phase:'ready',reason:''};
  }
  function evaluateRoute(delay=0){
    clearTimeout(state.timer);state.timer=setTimeout(()=>{const result=classifySurface(state.route||currentRoute());setPhase(result.phase,result.reason);if(result.phase==='initial')state.timer=setTimeout(()=>{const later=classifySurface(state.route||currentRoute());setPhase(later.phase==='initial'?'degraded':later.phase,later.phase==='initial'?contract(state.route||currentRoute()).degraded_state:later.reason)},9000)},delay);
  }

  function markNavigation(){
    qsa('.nav-item[data-route]').forEach(button=>{const route=button.dataset.route;const available=controllerAvailable(route)&&Boolean(contract(route));button.dataset.productionState=available?'available':'unavailable';button.disabled=!available;button.setAttribute('aria-disabled',available?'false':'true');button.title=available?'':`${button.querySelector('span')?.textContent||route} is unavailable in this release.`});
  }
  function focusRouteTitle(){const title=qs('#viewTitle');if(title){title.setAttribute('tabindex','-1');title.focus({preventScroll:true})}const workspace=qs('#main')||qs('.workspace');workspace?.scrollTo?.({top:0,behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'})}
  function urlFor(route){const params=new URLSearchParams(location.search);params.set('view',route);if(!params.get('country'))params.set('country',qs('#countrySelect')?.value||'KEN');return `${location.pathname}?${params.toString()}${location.hash}`}
  function beginRoute(route){state.route=route;setPhase('initial');requestAnimationFrame(()=>{focusRouteTitle();evaluateRoute(120)});}
  function retryActiveRoute(){const route=state.route||currentRoute();setPhase('initial',`Reopening ${contract(route).label} and retrying its public services.`);window.SCSIRouterV3228?.navigate?.(route).then?.(()=>evaluateRoute(300)).catch?.(()=>setPhase('degraded',contract(route).degraded_state));}

  async function loadDirectory(){
    try{const response=await fetch(`${ENDPOINT}?release=${VERSION}`,{headers:{Accept:'application/json'},cache:'no-store'});if(!response.ok)throw new Error(String(response.status));const payload=await response.json();if(payload.version!==VERSION||!Array.isArray(payload.routes))throw new Error('contract mismatch');state.directory=payload}catch(_){state.directory={version:VERSION,routes:qsa('.nav-item[data-route]').map(button=>({route_id:button.dataset.route,label:button.querySelector('span')?.textContent||button.dataset.route,completion:CORE_ROUTES.has(button.dataset.route)?'operational':'operational-bounded',lazy_load:true}))}}
    markNavigation();evaluateRoute(0);
  }

  function bindHistory(){
    document.addEventListener('click',event=>{const target=event.target.closest?.('.nav-item[data-route],[data-route-link]');if(!target)return;const route=target.dataset.route||target.dataset.routeLink;if(!route||target.disabled)return;const current=new URLSearchParams(location.search).get('view')||'overview';if(route!==current&&!state.historyLock){history.pushState({scsiRoute:route},'',urlFor(route))}beginRoute(route)},true);
    window.addEventListener('popstate',()=>{const route=new URLSearchParams(location.search).get('view')||'overview';state.historyLock=true;beginRoute(route);Promise.resolve(window.SCSIRouterV3228?.navigate?.(route)).finally(()=>{state.historyLock=false;evaluateRoute(200)})});
  }
  function bindSignals(){
    window.addEventListener('scsi:service-fallback',event=>{if(event.detail?.path||event.detail?.group)setPhase('degraded',contract(state.route||currentRoute()).degraded_state)});
    window.addEventListener('scsi:service-recovered',()=>evaluateRoute(250));
    window.addEventListener('scsi:map-recovered',()=>evaluateRoute(100));
    window.addEventListener('scsi:visible-map-health',event=>{if((state.route||currentRoute())==='overview')setPhase(event.detail?.ready?'ready':'degraded',event.detail?.ready?'':contract('overview').degraded_state)});
    window.addEventListener('error',event=>{if(event.filename&&/\/app\/assets\//.test(event.filename))setPhase('degraded','A workspace script reported an error; available public evidence remains visible.')});
    window.addEventListener('unhandledrejection',()=>setPhase('degraded','A workspace request did not complete; retry the active workspace.'));
    const root=qs('#main')||document.body;new MutationObserver(()=>evaluateRoute(180)).observe(root,{subtree:true,childList:true,attributes:true,attributeFilter:['hidden','class','data-state']});
  }
  function bind(){buildBar();state.route=currentRoute();bindHistory();bindSignals();loadDirectory();beginRoute(state.route);}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',bind,{once:true});else bind();
  window.SCSIProductionTruthV3231={version:VERSION,current:()=>({route:state.route,state:state.phase,reason:state.reason}),evaluate:()=>evaluateRoute(0),retry:retryActiveRoute,directory:()=>state.directory};
})(window,document);
