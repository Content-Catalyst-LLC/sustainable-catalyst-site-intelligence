
(() => {
  const API = window.SC_SITE_INTELLIGENCE_API || window.location.origin;

  const boot={progress:10};
  function setLaunch(message,progress,retry=false){
    const m=qs("#launchMessage"),b=qs("#launchProgressBar"),r=qs("#launchRetry");
    if(m)m.textContent=message;if(b){boot.progress=Math.max(boot.progress,progress||boot.progress);b.style.width=`${Math.min(100,boot.progress)}%`}if(r)r.hidden=!retry;
  }
  function showGlobalNotice(title,text){
    console.info(`[Site Intelligence] ${title}: ${text}`);
  }
  function hideGlobalNotice(){}
  function finishLaunch(){qs("#app").classList.remove("app-loading");qs("#app").classList.add("app-ready");setLaunch("Site Intelligence is ready.",100);setTimeout(()=>qs("#launchScreen").classList.add("hidden"),320);reportHeight()}
  async function apiWithRetry(path,attempts=3,options={}){
    let last;
    for(let i=0;i<attempts;i++){
      try{return await api(path,options)}catch(e){
        if(e?.name==="AbortError")throw e;
        last=e;
        if(i<attempts-1)await new Promise(r=>setTimeout(r,700*(i+1)));
      }
    }
    throw last;
  }
  const APP_VERSION="3.6.1";
  let heightFrame=0;
  function documentHeight(){
    const body=document.body,root=document.documentElement;
    return Math.max(620,Math.min(2600,Math.ceil(Math.max(body?.scrollHeight||0,body?.offsetHeight||0,root?.scrollHeight||0,root?.offsetHeight||0,root?.getBoundingClientRect?.().height||0))));
  }
  function reportHeight(){
    if(heightFrame)cancelAnimationFrame(heightFrame);
    heightFrame=requestAnimationFrame(()=>{heightFrame=0;window.parent?.postMessage({type:"scsi-height",height:documentHeight(),version:APP_VERSION,path:location.pathname+location.search},"*")});
  }
  const reducedMotion=window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches===true;
  async function registerServiceWorkerReliably(){
    if(!("serviceWorker" in navigator))return null;
    const hadController=Boolean(navigator.serviceWorker.controller);
    const registration=await navigator.serviceWorker.register(`/app/service-worker.js?v=${encodeURIComponent(APP_VERSION)}`,{scope:"/app/",updateViaCache:"none"});
    registration.update().catch(()=>{});
    const activateWaiting=()=>registration.waiting?.postMessage({type:"SC_SI_ACTIVATE_UPDATE"});
    if(registration.waiting)activateWaiting();
    registration.addEventListener("updatefound",()=>{
      const worker=registration.installing;if(!worker)return;
      worker.addEventListener("statechange",()=>{if(worker.state==="installed"&&navigator.serviceWorker.controller)activateWaiting()});
    });
    let reloading=false;
    navigator.serviceWorker.addEventListener("controllerchange",()=>{
      if(!hadController||reloading)return;
      reloading=true;
      const key=`scsi-sw-reloaded-${APP_VERSION}`;
      if(sessionStorage.getItem(key)!=="1"){sessionStorage.setItem(key,"1");location.reload()}
    });
    navigator.serviceWorker.addEventListener("message",event=>{
      if(event.data?.type==="SC_SI_SW_READY"&&event.data.version===APP_VERSION)console.info(`[Site Intelligence] Offline shell ${APP_VERSION} active.`);
    });
    return registration;
  }
  window.addEventListener("load",()=>registerServiceWorkerReliably().catch(error=>console.warn("[Site Intelligence] Service worker registration failed.",error)),{once:true});
  if(navigator.connection?.saveData||localStorage.getItem("scsi_experience_v2120")?.includes('"lowBandwidth":true'))document.documentElement.dataset.lowBandwidth="1";
  let html2CanvasPromise=null;
  function loadScriptOnce(src,globalName){
    if(globalName&&typeof window[globalName]==="function")return Promise.resolve(window[globalName]);
    const existing=document.querySelector(`script[data-scsi-src="${src}"]`);
    if(existing)return new Promise((resolve,reject)=>{existing.addEventListener("load",()=>resolve(window[globalName]),{once:true});existing.addEventListener("error",reject,{once:true})});
    return new Promise((resolve,reject)=>{const script=document.createElement("script");script.src=src;script.defer=true;script.dataset.scsiSrc=src;script.onload=()=>resolve(globalName?window[globalName]:true);script.onerror=()=>reject(new Error(`Unable to load ${src}`));document.head.appendChild(script)});
  }
  function ensureHtml2Canvas(){
    if(typeof window.html2canvas==="function")return Promise.resolve(window.html2canvas);
    if(!html2CanvasPromise)html2CanvasPromise=loadScriptOnce("https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js","html2canvas").catch(error=>{html2CanvasPromise=null;throw error});
    return html2CanvasPromise;
  }
  function publicErrorBlock(title,text,retryAction){
    const id=`retry-${Math.random().toString(36).slice(2)}`;
    setTimeout(()=>{const b=document.getElementById(id);if(b)b.addEventListener("click",retryAction)},0);
    return `<div class="error-state"><div><strong>${escapeHtml(title)}</strong><span>${escapeHtml(text)}</span><br><button id="${id}" class="retry-button" type="button">Retry</button></div></div>`;
  }

  const state = {map:null,base:null,imagery:null,markers:null,heat:null,layers:null,events:null,country:"KEN",route:"overview"};
  const SAVED_VIEW_SCHEMA="sc-saved-view/1.0";
  const SAVED_VIEW_STORAGE_KEY="sc_site_intelligence_saved_views_v1";
  const SAVED_VIEW_LIMIT=50;
  const names = {KEN:"Kenya",GHA:"Ghana",USA:"United States",IND:"India",BRA:"Brazil"};
  const qs = (s)=>document.querySelector(s), qsa=(s)=>[...document.querySelectorAll(s)];
  const toast=(msg)=>{const el=qs("#toast");el.textContent=msg;el.classList.add("show");setTimeout(()=>el.classList.remove("show"),1800)};
  function setMobileNavigation(open,{restoreFocus=false}={}){
    const toggle=qs("#mobileNavToggle"),backdrop=qs("#mobileNavBackdrop"),main=qs("#main");
    const shouldOpen=Boolean(open)&&window.matchMedia("(max-width: 760px)").matches;
    document.body.classList.toggle("mobile-nav-open",shouldOpen);
    toggle?.setAttribute("aria-expanded",String(shouldOpen));
    if(backdrop)backdrop.hidden=!shouldOpen;
    if(main)main.inert=shouldOpen;
    if(shouldOpen)requestAnimationFrame(()=>qs("#primaryNavigation .nav-item")?.focus());
    else if(restoreFocus)toggle?.focus();
  }
  function updateActiveNavigation(route){
    qsa(".nav-item").forEach(button=>{const active=button.dataset.route===route;button.classList.toggle("active",active);if(active)button.setAttribute("aria-current","page");else button.removeAttribute("aria-current")});
    const announcement=qs("#routeAnnouncement");if(announcement)announcement.textContent=`${routeMeta(route)[1]} workspace opened`;
  }
  const cleanDate=(v)=>{if(!v)return "Date unavailable";try{return new Date(v).toLocaleDateString(undefined,{year:"numeric",month:"short",day:"numeric"})}catch{return v}};
  const api=async(path,{signal,timeout=12000}={})=>{
    const controller=new AbortController();
    const timer=setTimeout(()=>controller.abort("timeout"),timeout);
    const abort=()=>controller.abort("superseded");
    if(signal){if(signal.aborted)abort();else signal.addEventListener("abort",abort,{once:true})}
    try{
      const res=await fetch(API+path,{headers:{"Accept":"application/json"},signal:controller.signal});
      if(!res.ok){const error=new Error(`${res.status}`);error.status=res.status;throw error}
      return await res.json();
    }finally{
      clearTimeout(timer);
      if(signal)signal.removeEventListener("abort",abort);
    }
  };

  function today(){const d=new Date();d.setUTCDate(d.getUTCDate()-1);return d.toISOString().slice(0,10)}
  function initMap(){
    state.map=L.map("map",{zoomControl:true,worldCopyJump:true}).setView([12,20],2);
    state.base=L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",{attribution:"© OpenStreetMap contributors",maxZoom:19}).addTo(state.map);
    state.markers=L.layerGroup().addTo(state.map);
  }
  function markerIcon(category){
    const quake=String(category).toLowerCase().includes("earthquake");
    return L.divIcon({className:"scsi-map-marker",html:`<span class="marker-core ${quake?"quake":"natural"}"></span><span class="marker-ring ${quake?"quake":"natural"}"></span>`,iconSize:[22,22],iconAnchor:[11,11]});
  }
  async function loadLayers(){
    state.layers=await apiWithRetry("/public/geospatial/layers",3);
    return state.layers;
  }
  async function setImagery(id){
    if(!state.layers) await loadLayers();
    const layer=state.layers.satellite_layers.find(x=>x.id===id);
    if(!layer)return;
    if(state.imagery)state.map.removeLayer(state.imagery);
    const url=layer.tile_url.replace("{time}",qs("#dateSelect").value||today());
    state.imagery=L.tileLayer(url,{opacity:layer.default_opacity||.72,attribution:layer.attribution,maxZoom:9}).addTo(state.map);
    state.imagery.bringToBack();
    qs("#layerName").textContent=layer.title;
    qs("#layerDate").textContent=cleanDate(qs("#dateSelect").value);
    qs("#legendSource").textContent=`${layer.source} imagery · USGS and NASA event records`;qs("#captionDetail").textContent=`${layer.title} · ${cleanDate(qs("#dateSelect").value)}`;
    qsa(".layer-tab").forEach(b=>b.classList.toggle("active",b.dataset.layer===id));
  }
  async function loadEvents(){
    const data=await apiWithRetry("/public/geospatial/events",3);
    state.events=data;
    state.markers.clearLayers();
    data.features.forEach(f=>{
      const c=f.geometry?.coordinates||[],p=f.properties||{};
      if(c.length<2)return;
      L.marker([c[1],c[0]],{icon:markerIcon(p.category)}).bindPopup(`<div class="popup-title">${escapeHtml(p.title||"Event")}</div><div class="popup-meta">${escapeHtml(p.category||"Public record")} · ${escapeHtml(p.source||"Source")}</div>`).addTo(state.markers);
    });
    qs("#eventCount").textContent=data.count??data.features.length;
    qs("#statusText").textContent=data.data_state==="live"?"Public feeds connected":"Demonstration fallback";
    qs(".status-pill").classList.toggle("live",data.data_state==="live");
    renderEvents(data.features.slice(0,6));
  }
  function escapeHtml(s){return String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]))}
  function renderEvents(features){
    qs("#eventList").innerHTML=features.length?features.map(f=>{const p=f.properties||{};const quake=String(p.category).toLowerCase().includes("earthquake");return `<div class="event-row"><span class="event-marker ${quake?"quake":""}"></span><div><div class="event-title">${escapeHtml(p.title||"Public event")}</div><div class="event-meta">${escapeHtml(p.category||"Event")} · ${escapeHtml(p.source||"Source")}</div></div><div class="event-time">${cleanDate(p.observed_at)}</div></div>`}).join(""):`<div class="empty-state"><div><strong>No recent public events</strong><span>The selected feeds returned no mapped records for this view.</span></div></div>`;
  }
  async function loadCountry(code){
    state.country=code;const name=names[code]||code;
    qs("#countryName").textContent=name;qs("#countryCode").textContent=code;qs("#countryPanelTitle").textContent=`${name} at a glance`;
    try{
      const d=await apiWithRetry(`/public/country-intelligence/${code}`,3);
      qs("#coverageCount").textContent=d.registered_source_count??d.source_count??"—";
      const domains=d.domain_summaries||d.domains||[];
      const normalized=Array.isArray(domains)?domains:Object.values(domains||{});
      qs("#countrySummary").innerHTML=normalized.slice(0,5).map(x=>`<div class="country-stat"><span>${escapeHtml(x.title||x.label||x.domain||"Evidence domain")}</span><strong>${escapeHtml(x.summary||x.description||x.data_state||"Source context available")}</strong></div>`).join("")||`<div class="loading-block">Country evidence structure is available; validated values appear as connectors return records.</div>`;
    }catch{
      qs("#coverageCount").textContent="—";
      qs("#countrySummary").innerHTML=publicErrorBlock("Country evidence unavailable","The public country service did not respond.",()=>loadCountry(code));
    }
  }
  function routeMeta(route){
    return {
      platform:["CONNECTED PUBLIC INTELLIGENCE AND EVIDENCE PLATFORM","One public discovery and provenance layer","Search across countries, regions, events, indicators, datasets, sources, claims, models, investigations, publications, and workflows while preserving evidence type, lineage, uncertainty, and public/private boundaries."],
      global:["GLOBAL CONDITIONS AND LIVE MAP OBSERVATORY","Global public conditions","Explore Core-powered geographic records, source-aware observations, existing Site Intelligence events, and Earth-observation context in one map."],
      economics:["ECONOMICS, MARKETS, AND SUSTAINABILITY SIGNALS","Official economic conditions","Explore source-aware macroeconomic, labour, trade, energy, agriculture, demographic, company-filing, and sustainability records without hiding reporting frequency or methodological limits."],
      law:["INTERNATIONAL LAW AND GLOBAL GOVERNANCE OBSERVATORY","Official legal and governance records","Explore treaties, resolutions, judicial material, human-rights recommendations, reports, and codification work without flattening authority, procedure, or legal effect."],
      science:["SCIENTIFIC AND EARTH SYSTEMS OBSERVATORY","Scientific records and Earth-system data","Discover Earth science, atmosphere, water, hazards, space observations, biodiversity, chemistry, materials, scientific assets, map layers, STAC items, and time series with source and quality context."],
      humanitarian:["HUMANITARIAN, CONFLICT, AND DISPLACEMENT OBSERVATORY","Crisis and displacement evidence","Connect public humanitarian reports, conflict-related records, displacement context, civilian-protection evidence, and hazard exposure without fabricating records or flattening source limitations."],
      resources:["TRADE, ENERGY, AND RESOURCE SECURITY OBSERVATORY","Official resource and dependency evidence","Trace trade, energy, food, water, materials, and transition records while preserving units, periods, counterpart context, and methodological limits."],
      dossiers:["UNIFIED COUNTRY AND REGIONAL INTELLIGENCE DOSSIERS","Cross-domain country and regional evidence","Combine public conditions, indicators, economics, law, science, humanitarian evidence, and resource context without collapsing them into a score or ranking."],
      alerts:["ALERTS, MONITORING, AND LIVE INTELLIGENCE STREAMS","Watch public evidence across domains","Use reconnecting source-aware streams, browser-local rules, source freshness monitoring, and deterministic digests without server-side profiling or automated risk decisions."],
      scenarios:["COMPARATIVE INTELLIGENCE AND SCENARIO STUDIO","Compare evidence and test assumptions","Build multi-geography indicator baskets, inspect compatibility, apply transparent arithmetic scenarios, review correlation, and export reproducible packets without rankings or forecasts."],
      research:["RESEARCH PATHS, SAVED INVESTIGATIONS, AND BRIEFING WORKFLOWS","Organize evidence into reviewable research","Create browser-local investigations, capture evidence and public views, preserve notes and checkpoints, and export briefing or product handoff packets without a hosted profile."],
      integration:["PUBLIC DATA API, EMBEDS, AND INSTITUTIONAL INTEGRATION","Reuse public intelligence safely","Discover versioned read-only endpoints, portable embeds, and institutional presentation metadata while preserving attribution and credentials."],
      experience:["OFFLINE, MOBILE, ACCESSIBILITY, AND PERFORMANCE","Resilient public intelligence delivery","Install the application shell, reduce network demand, inspect accessibility contracts, and review first-party performance budgets without a hosted profile."],
      observatory:["AUDITABLE PUBLIC OBSERVATORY","Evidence, lineage, and integrity","Inspect registered public evidence records, source and methodology lineage, canonical digests, release history, and verification boundaries."],
      launch:["PUBLIC LAUNCH AND PORTFOLIO","Site Intelligence","Explore the public product, technical architecture, responsible-use boundaries, and launch materials."],
      overview:["LIVE INTELLIGENCE WORKSPACE","Climate and Human Vulnerability","Satellite context, natural events, environmental pressure, and country evidence in one navigable view."],
      earth:["EARTH OBSERVATION STUDIO","Compare the planet through time","Explore satellite-derived imagery, environmental layers, date comparison, timeline playback, and exportable visual views."],
      spatial:["GEOSPATIAL ANALYSIS AND SPATIAL EVIDENCE STUDIO","Analyze public evidence by place","Use explicit areas of interest, source-aware spatial layers, intersections, proximity, aggregation, and temporal comparisons without hiding coordinate or approximation limits."],
      harmonization:["STATISTICAL HARMONIZATION AND COMPARABLE-SERIES ENGINE","Make transformations explicit","Check units, currencies, price bases, periods, population denominators, geographic definitions, missing data, and lineage before comparing series."],
      models:["MODEL REGISTRY, FORECAST EVALUATION, AND EARLY-WARNING INDICATORS","Inspect model and forecast evidence","Review model cards, forecasts, backtests, calibration, drift, and threshold indicators without treating them as guaranteed outcomes or emergency instructions."],
      evidence:["EVIDENCE SYNTHESIS, CLAIMS, AND CONTRADICTION REVIEW","Review evidence and disagreement","Inspect approved claims, typed evidence relationships, contradictions, uncertainty, citations, and human-review decisions without fabricated sources or automatic conclusions."],
      graph:["CROSS-DOMAIN KNOWLEDGE GRAPH AND RELATIONSHIP EXPLORER","Trace evidence-backed relationships","Explore typed entities, aliases, identifiers, temporal relationships, graph paths, and evidence references without inferring causation or merging entities automatically."],
      publishing:["INTELLIGENCE PUBLISHING AND STORY MAP STUDIO","Publish source-aware intelligence","Read human-reviewed publications, story maps, timelines, charts, evidence blocks, methodology, and immutable version history."],
      monitoring:["SCHEDULED MONITORING, DIGESTS, AND PUBLIC FEEDS","Follow public evidence over time","Read human-approved digests, inspect deduplicated alerts, and subscribe through JSON, RSS, or Atom without a hosted profile."],
      workspaces:["INSTITUTIONAL WORKSPACES, COLLABORATION, AND REVIEW","Coordinate review without exposing private work","Browse human-published institutional workspaces and public source collections while membership, assignments, comments, and review notes remain private."],
      federation:["OPEN STANDARDS, FEDERATION, AND INSTITUTIONAL DATA EXCHANGE","Exchange institutional evidence through open standards","Browse public institutions, catalogs, licenses, provenance, distributions, and manifest metadata without exposing trust policies or private import operations."],
      governance:["SECURITY, PRIVACY, GOVERNANCE, AND PRODUCTION SCALE","Inspect production-readiness contracts","Review public migration, audit, backup, queue, privacy, and rate-limiting boundaries without exposing operational secrets."],
      country:["COUNTRY INTELLIGENCE",`${names[state.country]||state.country} evidence profile`,"Environmental, development, humanitarian, security, and legal context for one selected country."],
      events:["UNIFIED LIVE EVENT INTELLIGENCE","Explore public events across sources","Natural hazards, humanitarian reporting, and country-linked event context in one source-aware workspace."],
      compare:["CROSS-DOMAIN COMPARISON","Compare country contexts","Align available evidence without flattening dates, units, definitions, or missing-data states."],
      thematic:["THEMATIC INTELLIGENCE DASHBOARDS","Focused public intelligence","Explore climate and environment, human development, human security, and infrastructure through maps, indicators, trends, events, sources, and briefs."],
      briefing:["PUBLIC BRIEFING AND EXPORT STUDIO","Document public intelligence views","Generate source-aware country, comparison, event, Earth-observation, and thematic briefs with reproducible exports."],
      sources:["PROVENANCE","Sources and methods","Review the public sources, imagery services, and interpretive limits behind this workspace."],
      saved:["LOCAL RESEARCH WORKSPACE","Saved views and research paths","Preserve, reopen, export, import, and share public investigation state without an account or hosted profile."]
    }[route]||[];
  }


  let countryLineage = new Map();
  function openEvidenceDrawer(item){
    const drawer=qs("#evidenceDrawer"),backdrop=qs("#evidenceBackdrop");
    qs("#evidenceDrawerTitle").textContent=item.label||"Indicator evidence";
    const field=(label,value)=>`<div class="evidence-field"><span class="evidence-field-label">${escapeHtml(label)}</span><div class="evidence-field-value">${value||"Unavailable"}</div></div>`;
    const state=item.platform_core_state||"not-recorded";
    const verification=item.verification_url?`<a class="evidence-link" href="${escapeHtml(item.verification_url)}" target="_blank" rel="noopener">Inspect evidence record ↗</a>`:"Not yet published to Platform Core.";
    qs("#evidenceDrawerBody").innerHTML=[
      field("Displayed value",`${escapeHtml(formatCountryValue(item.value,item.format,item.unit))} · ${escapeHtml(item.unit||"")} · ${escapeHtml(item.year||item.reporting_year||"Year unavailable")}`),
      field("Source",`${escapeHtml(item.source||"Source unavailable")}${item.source_url?`<br><a class="evidence-link" href="${escapeHtml(item.source_url)}" target="_blank" rel="noopener">Open original source ↗</a>`:""}`),
      field("Platform Core state",`<span class="evidence-integrity"><span class="lineage-dot ${escapeHtml(state)}"></span>${escapeHtml(state)}</span>`),
      field("Evidence ID",escapeHtml(item.evidence_id||"Pending or integration disabled")),
      field("Source snapshot ID",escapeHtml(item.source_snapshot_id||"Pending or integration disabled")),
      field("Provenance activity",escapeHtml(item.provenance_activity_id||"Pending or integration disabled")),
      field("Transformation","Null observations removed; reporting years preserved; records sorted chronologically; latest valid observation selected; no imputation."),
      field("Verification",verification),
      field("Known limits","Reporting periods differ by indicator. Public indicators describe conditions but do not establish causality, rankings, eligibility, liability, or professional advice.")
    ].join("");
    backdrop.hidden=false;drawer.classList.add("open");drawer.setAttribute("aria-hidden","false");qs("#closeEvidenceDrawer").focus();
  }
  function closeEvidenceDrawer(){
    const drawer=qs("#evidenceDrawer"),backdrop=qs("#evidenceBackdrop");
    drawer.classList.remove("open");drawer.setAttribute("aria-hidden","true");backdrop.hidden=true;
  }



  function setEarthStatus(message,state="loading"){
    const el=qs("#earthStatus");if(!el)return;el.classList.remove("ready","error");
    if(state==="ready")el.classList.add("ready");if(state==="error")el.classList.add("error");
    const text=el.querySelector("span:last-child");if(text)text.textContent=message;
  }
  function setEarthLoading(isLoading){
    qs("#earthCapture")?.classList.toggle("is-loading",Boolean(isLoading));
    qs("#earthMapA")?.classList.toggle("is-dimmed",Boolean(isLoading));
    qs("#earthMapB")?.classList.toggle("is-dimmed",Boolean(isLoading));
  }
  function showEarthUnavailable(message){
    const box=qs("#earthUnavailable");if(!box)return;box.hidden=false;
    const text=box.querySelector("span");if(text&&message)text.textContent=message;setEarthStatus("Imagery unavailable","error");
  }
  function hideEarthUnavailable(){const box=qs("#earthUnavailable");if(box)box.hidden=true}
  function stopEarthPlayback(){
    if(earthState.timer){clearInterval(earthState.timer);earthState.timer=null}
    const play=qs("#earthPlay");if(play){play.textContent="Play";play.setAttribute("aria-pressed","false")}
  }
  function validateEarthDates(){
    const a=qs("#earthDateA").value,b=qs("#earthDateB").value;
    if(!a||!b)return {ok:false,message:"Choose both comparison dates."};
    if(a>b)return {ok:false,message:"The before date must not be later than the after date."};
    return {ok:true};
  }
  function bindTileReliability(tileLayer,label){
    return new Promise(resolve=>{
      let loaded=false,errors=0,done=false;
      const finish=(ok)=>{if(done)return;done=true;resolve({ok,errors,label})};
      tileLayer.once("load",()=>{loaded=true;finish(true)});
      tileLayer.on("tileerror",()=>{errors+=1;if(errors>=4&&!loaded)finish(false)});
      setTimeout(()=>finish(loaded||errors<4),6500);
    });
  }


  const eventState={map:null,base:null,markers:null,markerIndex:new Map(),events:[],timeline:[],timelineIndex:0,timer:null,selected:null};

  function eventMarkerColor(category){
    return {earthquake:"#ff2a2f",wildfire:"#ff8b3d",storm:"#43d6ff",flood:"#2f8cff",volcano:"#b76cff","extreme-heat":"#ffb14a",drought:"#c9a85c",humanitarian:"#f5b942",displacement:"#d27cff",conflict:"#ff5f68"}[category]||"#718091";
  }
  function setEventStudioStatus(message,state="loading"){
    const el=qs("#eventStudioStatus");if(!el)return;el.classList.remove("ready","error");
    if(state==="ready")el.classList.add("ready");if(state==="error")el.classList.add("error");
    el.querySelector("span:last-child").textContent=message;
  }
  function initEventExplorerMap(){
    if(eventState.map)return;
    eventState.map=L.map("eventExplorerMap",{zoomControl:true,worldCopyJump:true}).setView([12,20],2);
    eventState.base=L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",{attribution:"© OpenStreetMap contributors © CARTO",maxZoom:19}).addTo(eventState.map);
    eventState.markers=L.layerGroup().addTo(eventState.map);
  }
  function eventQuery(){
    const params=new URLSearchParams();
    params.set("days",qs("#eventDays").value||"14");
    params.set("limit","500");
    if(qs("#eventCategory").value)params.append("category",qs("#eventCategory").value);
    if(qs("#eventSource").value)params.append("source",qs("#eventSource").value);
    const country=qs("#eventCountry").value.trim().toUpperCase();
    if(country)params.set("country_code",country);
    return params;
  }
  async function loadEventFilters(){
    const [categories,sources]=await Promise.all([
      apiWithRetry("/public/events/categories?days=14",3),
      apiWithRetry("/public/events/sources?days=14",3)
    ]);
    qs("#eventCategory").innerHTML='<option value="">All categories</option>'+categories.categories.map(x=>`<option value="${escapeHtml(x.id)}">${escapeHtml(x.label)} (${x.count})</option>`).join("");
    qs("#eventSource").innerHTML='<option value="">All sources</option>'+sources.sources.map(x=>`<option value="${escapeHtml(x.id)}">${escapeHtml(x.name)} (${x.count})</option>`).join("");
  }
  function renderEventMarkers(events){
    eventState.markers.clearLayers();eventState.markerIndex.clear();
    const bounds=[];
    events.filter(x=>Array.isArray(x.coordinates)&&x.coordinates.length>=2).forEach(event=>{
      const marker=L.circleMarker([event.coordinates[1],event.coordinates[0]],{
        radius:event.severity==="critical"?10:event.severity==="high"?8:6,
        color:"#fff",weight:1,fillColor:eventMarkerColor(event.category),fillOpacity:.9
      }).bindPopup(`<div class="event-popup-title">${escapeHtml(event.title)}</div><div class="event-popup-meta">${escapeHtml(event.category_label)} · ${escapeHtml(event.source_name)}<br>${cleanDate(event.observed_at)}</div>`);
      marker.on("click",()=>selectEvent(event.id,true));
      marker.addTo(eventState.markers);eventState.markerIndex.set(event.id,marker);bounds.push([event.coordinates[1],event.coordinates[0]]);
    });
    qs("#eventMappedCount").textContent=`${bounds.length} mapped records`;
    if(bounds.length>1)eventState.map.fitBounds(bounds,{padding:[35,35],maxZoom:5});
    else if(bounds.length===1)eventState.map.setView(bounds[0],6);
  }
  function renderEventList(events){
    qs("#eventExplorerList").innerHTML=events.length?events.map(event=>`<article class="event-card" tabindex="0" data-event-id="${escapeHtml(event.id)}"><span class="event-card-marker ${escapeHtml(event.category)}"></span><div><div class="event-card-title">${escapeHtml(event.title)}</div><div class="event-card-meta">${escapeHtml(event.category_label)} · ${cleanDate(event.observed_at)}${event.country_code?` · ${escapeHtml(event.country_code)}`:""}</div><div class="event-card-source">${escapeHtml(event.source_name)} · ${escapeHtml(event.data_state)}</div></div></article>`).join(""):'<div class="empty-state"><div><strong>No matching event records</strong><span>Change the filters or broaden the date range.</span></div></div>';
    qsa("[data-event-id]").forEach(card=>{
      const activate=()=>selectEvent(card.dataset.eventId,true);
      card.addEventListener("click",activate);
      card.addEventListener("keydown",e=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();activate()}});
    });
  }
  function selectEvent(eventId,openDrawer=false){
    const event=eventState.events.find(x=>x.id===eventId);if(!event)return;
    eventState.selected=eventId;
    qsa("[data-event-id]").forEach(card=>card.classList.toggle("selected",card.dataset.eventId===eventId));
    const marker=eventState.markerIndex.get(eventId);
    if(marker&&event.coordinates){eventState.map.flyTo([event.coordinates[1],event.coordinates[0]],Math.max(eventState.map.getZoom(),6),{duration:.7});marker.openPopup()}
    if(openDrawer)openEventDrawer(event);
  }
  function openEventDrawer(event){
    const drawer=qs("#eventDetailDrawer"),backdrop=qs("#eventDetailBackdrop");
    qs("#eventDetailTitle").textContent=event.title;
    const field=(label,value)=>`<div class="evidence-field"><span class="evidence-field-label">${escapeHtml(label)}</span><div class="evidence-field-value">${value||"Unavailable"}</div></div>`;
    qs("#eventDetailBody").innerHTML=[
      field("Category",escapeHtml(event.category_label)),
      field("Observed",escapeHtml(cleanDate(event.observed_at))),
      field("Source",`${escapeHtml(event.source_name)}${event.source_url?`<br><a class="evidence-link" href="${escapeHtml(event.source_url)}" target="_blank" rel="noopener">Open source record ↗</a>`:""}`),
      field("Location",event.coordinates?`${event.coordinates[1].toFixed(4)}, ${event.coordinates[0].toFixed(4)}`:"Not geocoded"),
      field("Country context",escapeHtml(event.country_code||"Not assigned")),
      field("Severity or magnitude",escapeHtml(event.magnitude!=null?`${event.magnitude} · ${event.severity}`:event.severity)),
      field("Record type",escapeHtml(event.record_type)),
      field("Summary",escapeHtml(event.summary||"No summary provided.")),
      field("Interpretation","Public source record for orientation and research. Not an operational alert or professional recommendation.")
    ].join("");
    backdrop.hidden=false;drawer.classList.add("open");drawer.setAttribute("aria-hidden","false");qs("#closeEventDrawer").focus();
  }
  function closeEventDrawer(){qs("#eventDetailDrawer").classList.remove("open");qs("#eventDetailDrawer").setAttribute("aria-hidden","true");qs("#eventDetailBackdrop").hidden=true}
  function renderEventSummaries(summary){
    qs("#eventCategorySummary").innerHTML=`<div class="event-summary-list">${(summary.top_categories||[]).map(x=>`<div class="event-summary-row"><span>${escapeHtml(x.label)}</span><strong>${x.count}</strong></div>`).join("")}</div>`;
    qs("#eventSourceSummary").innerHTML=`<div class="event-summary-list">${(summary.top_sources||[]).map(x=>`<div class="event-summary-row"><span>${escapeHtml(x.name)}</span><strong>${x.count}</strong></div>`).join("")}</div>`;
    qs("#eventBoundary").textContent=summary.boundary;
  }
  async function loadEventTimeline(){
    const days=qs("#eventDays").value||"14";
    const payload=await apiWithRetry(`/public/events/timeline?days=${encodeURIComponent(days)}&interval_hours=24`,3);
    eventState.timeline=payload.buckets||[];eventState.timelineIndex=Math.max(0,eventState.timeline.length-1);
    qs("#eventTimelineRange").max=String(Math.max(0,eventState.timeline.length-1));qs("#eventTimelineRange").value=String(eventState.timelineIndex);renderEventTimelineFrame();
  }
  function renderEventTimelineFrame(){
    const bucket=eventState.timeline[eventState.timelineIndex];if(!bucket)return;
    qs("#eventTimelineLabel").textContent=`${cleanDate(bucket.start)} · ${bucket.count} records`;
    const ids=new Set(bucket.event_ids||[]);
    qsa("[data-event-id]").forEach(card=>card.style.opacity=ids.size&& !ids.has(card.dataset.eventId)?".35":"1");
    eventState.markerIndex.forEach((marker,id)=>marker.setStyle({fillOpacity:ids.size&&!ids.has(id)?.18:.9,opacity:ids.size&&!ids.has(id)?.25:1}));
  }
  function stopEventTimeline(){
    if(eventState.timer){clearInterval(eventState.timer);eventState.timer=null}
    qs("#eventTimelinePlay").textContent="Play";qs("#eventTimelinePlay").setAttribute("aria-pressed","false");
  }
  function toggleEventTimeline(){
    if(reducedMotion){stopEventTimeline();toast("Timeline autoplay is disabled by your reduced-motion preference.");return}
    if(eventState.timer){stopEventTimeline();return}
    if(!eventState.timeline.length)return;
    qs("#eventTimelinePlay").textContent="Pause";qs("#eventTimelinePlay").setAttribute("aria-pressed","true");
    eventState.timer=setInterval(()=>{eventState.timelineIndex=(eventState.timelineIndex+1)%eventState.timeline.length;qs("#eventTimelineRange").value=String(eventState.timelineIndex);renderEventTimelineFrame()},1100);
  }
  async function applyEventFilters(pushState=true){
    stopEventTimeline();setEventStudioStatus("Loading public event records","loading");
    const query=eventQuery();
    try{
      const [payload,summary]=await Promise.all([
        apiWithRetry(`/public/events?${query.toString()}`,3),
        apiWithRetry(`/public/events/summary?days=${encodeURIComponent(qs("#eventDays").value||"14")}`,3)
      ]);
      eventState.events=payload.events||[];
      renderEventMarkers(eventState.events);renderEventList(eventState.events);renderEventSummaries(summary);
      qs("#eventTotalCount").textContent=String(payload.count||0);qs("#eventDataState").textContent=payload.data_state;setEventStudioStatus("Live event view ready","ready");
      await loadEventTimeline();
      if(pushState){
        const params=new URLSearchParams(location.search);params.set("view","events");params.set("eventDays",qs("#eventDays").value);
        if(qs("#eventCategory").value)params.set("eventCategory",qs("#eventCategory").value);else params.delete("eventCategory");
        if(qs("#eventSource").value)params.set("eventSource",qs("#eventSource").value);else params.delete("eventSource");
        if(qs("#eventCountry").value.trim())params.set("eventCountry",qs("#eventCountry").value.trim().toUpperCase());else params.delete("eventCountry");
        history.replaceState(null,"",`?${params.toString()}`);
      }
    }catch{
      setEventStudioStatus("Event services unavailable","error");
      qs("#eventExplorerList").innerHTML=publicErrorBlock("Live event intelligence unavailable","The connected public event services may be waking up or temporarily unavailable.",()=>applyEventFilters(false));
    }
    setTimeout(()=>{eventState.map?.invalidateSize();reportHeight()},80);
  }
  async function openEventStudio(){
    qs("#eventStudio").hidden=false;initEventExplorerMap();
    if(!qs("#eventCategory").options.length||qs("#eventCategory").options.length===1)await loadEventFilters();
    const params=new URLSearchParams(location.search);
    qs("#eventDays").value=params.get("eventDays")||"14";qs("#eventCategory").value=params.get("eventCategory")||"";qs("#eventSource").value=params.get("eventSource")||"";qs("#eventCountry").value=params.get("eventCountry")||"";
    await applyEventFilters(false);
  }
  function closeEventStudio(){qs("#eventStudio").hidden=true;stopEventTimeline();closeEventDrawer()}


  const globalCountryState={catalog:[],regions:[],overviewMap:null,overviewBase:null,overviewMarker:null,events:[],trends:[],activeCode:"KEN",selectionController:null,searchController:null,requestSequence:0,searchTimer:null};

  async function loadCountryCatalog(){
    if(globalCountryState.catalog.length)return;
    const [catalog,regions]=await Promise.all([
      apiWithRetry("/public/countries",3),
      apiWithRetry("/public/countries/regions",3)
    ]);
    globalCountryState.catalog=catalog.countries||[];
    globalCountryState.regions=regions.regions||[];
    globalCountryState.catalog.forEach(item=>{names[item.code]=item.name});
    qs("#countrySelect").innerHTML=globalCountryState.catalog.map(item=>`<option value="${escapeHtml(item.code)}">${escapeHtml(item.name)}</option>`).join("");
    qs("#countryRegionFilter").innerHTML='<option value="">All regions</option>'+globalCountryState.regions.map(item=>`<option value="${escapeHtml(item.name)}">${escapeHtml(item.name)} (${item.country_count})</option>`).join("");
  }
  function initCountryOverviewMap(){
    if(globalCountryState.overviewMap)return;
    globalCountryState.overviewMap=L.map("countryOverviewMap",{zoomControl:true,attributionControl:true}).setView([0,20],2);
    globalCountryState.overviewBase=L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",{attribution:"© OpenStreetMap contributors © CARTO",maxZoom:19}).addTo(globalCountryState.overviewMap);
  }
  function renderGlobalTrend(trend){
    const chart=qs("#globalTrendChart"),series=trend?.series||[];
    if(!series.length){chart.innerHTML='<div class="empty-state"><div><strong>Trend unavailable</strong><span>No validated multi-year series was returned for this indicator.</span></div></div>';return}
    const values=series.map(x=>Number(x.value)),min=Math.min(...values),max=Math.max(...values),spread=Math.max(max-min,Math.abs(max)*.08,1);
    chart.innerHTML=series.map(x=>{const height=12+((Number(x.value)-min)/spread)*82;return `<div class="trend-column"><span class="trend-value">${escapeHtml(formatCountryValue(x.value,trend.format,trend.unit))}</span><span class="trend-bar" style="height:${Math.max(5,Math.min(96,height))}%"></span><span class="trend-year">${escapeHtml(x.year)}</span></div>`}).join("");
  }
  function renderCountrySearchResults(items){
    const box=qs("#countrySearchResults");box.hidden=!items.length;
    box.innerHTML=items.length?items.map(item=>`<div class="country-search-result" tabindex="0" role="button" data-country-result="${escapeHtml(item.code)}"><strong>${escapeHtml(item.name)}</strong><span>${escapeHtml(item.code)} · ${escapeHtml(item.region||"Region unavailable")}</span></div>`).join(""):'<div class="empty-state"><div><strong>No matching country</strong><span>Try a country name, ISO2, ISO3, or alternate public name.</span></div></div>';
    qsa("[data-country-result]").forEach(card=>{
      const activate=()=>selectGlobalCountry(card.dataset.countryResult,true);
      card.addEventListener("click",activate);card.addEventListener("keydown",e=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();activate()}});
    });
  }
  async function searchGlobalCountries(){
    if(globalCountryState.searchController)globalCountryState.searchController.abort();
    globalCountryState.searchController=new AbortController();
    const signal=globalCountryState.searchController.signal;
    const q=qs("#countrySearchInput").value.trim(),region=qs("#countryRegionFilter").value;
    const params=new URLSearchParams({q,region,limit:"80"});
    const box=qs("#countrySearchResults");box.hidden=false;box.innerHTML='<div class="loading-block">Searching the country catalog…</div>';
    try{
      const payload=await apiWithRetry(`/public/countries/search?${params.toString()}`,2,{signal});
      if(signal.aborted)return;
      renderCountrySearchResults(payload.countries||[]);
    }catch(error){
      if(error?.name==="AbortError")return;
      box.innerHTML=publicErrorBlock("Country search unavailable","The catalog search did not respond.",searchGlobalCountries);
    }
  }
  async function loadCountryEvents(code,signal,sequence){
    try{
      const payload=await apiWithRetry(`/public/events?country_code=${encodeURIComponent(code)}&days=30&limit=20`,2,{signal});
      if(signal.aborted||sequence!==globalCountryState.requestSequence)return;
      globalCountryState.events=payload.events||[];
      qs("#countryEventsList").innerHTML=globalCountryState.events.length?globalCountryState.events.slice(0,8).map(event=>`<div class="event-row"><span class="event-marker"></span><div><div class="event-title">${escapeHtml(event.title)}</div><div class="event-meta">${escapeHtml(event.category_label)} · ${escapeHtml(event.source_name)}${event.country_match_method?` · ${escapeHtml(event.country_match_method)}`:""}</div></div><div class="event-time">${cleanDate(event.observed_at)}</div></div>`).join(""):'<div class="empty-state"><div><strong>No country-linked events</strong><span>The connected public feeds returned no records with a retained country-match basis.</span></div></div>';
    }catch(error){
      if(error?.name==="AbortError")return;
      if(sequence===globalCountryState.requestSequence)qs("#countryEventsList").innerHTML=publicErrorBlock("Country events unavailable","The event service did not respond.",()=>selectGlobalCountry(code,false));
    }
  }
  function setCountryLoading(code){
    const country=globalCountryState.catalog.find(item=>item.code===code);
    qs("#globalCountryExplorer").setAttribute("aria-busy","true");
    qs("#globalCountryTitle").textContent=`Loading ${country?.name||code}`;
    qs("#globalCountryIntro").textContent="Retrieving validated country indicators, trends, and linked public events.";
    qs("#globalCountryMetrics").innerHTML='<div class="loading-block">Loading country indicators…</div>';
    qs("#globalTrendSelect").innerHTML="";
    qs("#globalTrendTitle").textContent="Loading trend";
    qs("#globalTrendChart").innerHTML='<div class="loading-block">Loading multi-year series…</div>';
    qs("#countryEventsList").innerHTML='<div class="loading-block">Loading country-linked events…</div>';
  }
  async function selectGlobalCountry(code,pushState=true){
    const requested=String(code||"").trim().toUpperCase();
    const supported=globalCountryState.catalog.some(item=>item.code===requested);
    const normalized=supported?requested:"KEN";
    if(!supported)toast(`Unsupported country code ${requested||"(blank)"}; showing Kenya.`);
    if(globalCountryState.selectionController)globalCountryState.selectionController.abort();
    const controller=new AbortController();globalCountryState.selectionController=controller;
    const signal=controller.signal,sequence=++globalCountryState.requestSequence;
    globalCountryState.activeCode=normalized;state.country=normalized;qs("#countrySelect").value=normalized;setCountryLoading(normalized);
    try{
      const [overview,trends]=await Promise.all([
        apiWithRetry(`/public/country/${encodeURIComponent(normalized)}/overview`,3,{signal}),
        apiWithRetry(`/public/country/${encodeURIComponent(normalized)}/trends`,3,{signal})
      ]);
      if(signal.aborted||sequence!==globalCountryState.requestSequence)return;
      const country=overview.country;
      qs("#globalCountryTitle").textContent=overview.headline;
      qs("#globalCountryIntro").textContent=overview.summary;
      qs("#countryIdentityCode").textContent=country.code;
      qs("#countryIdentityRegion").textContent=(country.region||"Region unavailable").toUpperCase();
      qs("#countryIdentityName").textContent=country.name;
      qs("#countryIdentityMeta").textContent=`Capital: ${country.capital||"Unavailable"}${country.income_level?` · ${country.income_level}`:""} · ${overview.data_state||"unknown state"}`;
      const highlights=overview.highlights||[];
      qs("#globalCountryMetrics").innerHTML=highlights.length?highlights.map(item=>`<article class="country-indicator"><span class="country-indicator-label">${escapeHtml(item.label)}</span><strong class="country-indicator-value">${escapeHtml(formatCountryValue(item.value,item.format,item.unit))}</strong><div class="country-indicator-meta">${escapeHtml(item.unit)} · ${escapeHtml(item.year)}</div><span class="country-indicator-source">${item.source_url?`<a href="${escapeHtml(item.source_url)}" target="_blank" rel="noopener">${escapeHtml(item.source)} ↗</a>`:escapeHtml(item.source)} · ${escapeHtml(item.data_state)}</span></article>`).join(""):'<div class="empty-state"><div><strong>No validated indicators</strong><span>No validated public value is currently available for this country.</span></div></div>';
      globalCountryState.trends=trends.trends||[];
      qs("#globalTrendSelect").innerHTML=globalCountryState.trends.map(item=>`<option value="${escapeHtml(item.key)}">${escapeHtml(item.label)}</option>`).join("");
      if(globalCountryState.trends.length){qs("#globalTrendTitle").textContent=globalCountryState.trends[0].label;renderGlobalTrend(globalCountryState.trends[0])}else{qs("#globalTrendTitle").textContent="Trend unavailable";renderGlobalTrend(null)}
      initCountryOverviewMap();
      const lat=country.latitude,lng=country.longitude;
      if(globalCountryState.overviewMarker){globalCountryState.overviewMap.removeLayer(globalCountryState.overviewMarker);globalCountryState.overviewMarker=null}
      if(lat!=null&&lng!=null){globalCountryState.overviewMap.setView([lat,lng],overview.map?.default_zoom||5);globalCountryState.overviewMarker=L.circleMarker([lat,lng],{radius:8,color:"#fff",weight:1,fillColor:"#43d6ff",fillOpacity:.9}).addTo(globalCountryState.overviewMap).bindPopup(`<strong>${escapeHtml(country.name)}</strong><br>${escapeHtml(country.capital||"Capital unavailable")}`)}
      else{globalCountryState.overviewMap.setView([0,20],2)}
      await loadCountryEvents(normalized,signal,sequence);
      if(signal.aborted||sequence!==globalCountryState.requestSequence)return;
      qs("#countrySearchResults").hidden=true;
      if(pushState||!supported){const params=new URLSearchParams(location.search);params.set("view","country");params.set("country",normalized);history.replaceState(null,"",`?${params.toString()}`)}
      setTimeout(()=>{globalCountryState.overviewMap.invalidateSize();reportHeight()},80);
    }catch(error){
      if(error?.name==="AbortError")return;
      if(sequence!==globalCountryState.requestSequence)return;
      qs("#globalCountryMetrics").innerHTML=publicErrorBlock("Country intelligence unavailable","The country service may be waking up or temporarily unavailable.",()=>selectGlobalCountry(normalized,false));
      qs("#globalTrendChart").innerHTML='<div class="empty-state"><div><strong>Trend unavailable</strong><span>Retry the country request to load a validated series.</span></div></div>';
      qs("#countryEventsList").innerHTML='<div class="empty-state"><div><strong>Events unavailable</strong><span>Country indicator failure does not imply that no events exist.</span></div></div>';
    }finally{
      if(sequence===globalCountryState.requestSequence)qs("#globalCountryExplorer").setAttribute("aria-busy","false");
    }
  }
  async function openGlobalCountryExplorer(){
    qs("#globalCountryExplorer").hidden=false;
    try{await loadCountryCatalog()}catch(error){
      qs("#globalCountryMetrics").innerHTML=publicErrorBlock("Country catalog unavailable","The global catalog did not respond.",openGlobalCountryExplorer);return;
    }
    const params=new URLSearchParams(location.search);const code=params.get("country")||state.country||"KEN";
    await selectGlobalCountry(code,false);
  }
  function closeGlobalCountryExplorer(){qs("#globalCountryExplorer").hidden=true;if(globalCountryState.selectionController)globalCountryState.selectionController.abort()}

  const compareState={data:null,brief:null,controller:null,sequence:0,activeView:"table",map:null,base:null,markers:null,rows:[],trends:[],lastError:null};
  const compareViews=new Set(["table","chart","map","brief","export"]);

  async function prepareCompareSelectors(){
    await loadCountryCatalog();
    const options=globalCountryState.catalog.map(item=>`<option value="${escapeHtml(item.code)}">${escapeHtml(item.name)}</option>`).join("");
    if(!qs("#compareCountryA").options.length)qs("#compareCountryA").innerHTML=options;
    if(!qs("#compareCountryB").options.length)qs("#compareCountryB").innerHTML=options;
  }
  function compareCountryName(code){return globalCountryState.catalog.find(item=>item.code===code)?.name||names[code]||code}
  function compareSelection(){return {a:qs("#compareCountryA").value,b:qs("#compareCountryB").value}}
  function showCompareValidation(message,type="error"){
    const box=qs("#compareValidation");box.hidden=!message;box.className=`compare-validation ${type}`;box.textContent=message||"";
  }
  function validateCompareSelection(a,b){
    const codes=new Set(globalCountryState.catalog.map(item=>item.code));
    if(!codes.has(a)||!codes.has(b))return {ok:false,message:"Select two supported countries from the catalog."};
    if(a===b)return {ok:false,message:"Choose two different countries before running the comparison."};
    return {ok:true,message:""};
  }
  function compareCompatibilityLabel(value){return String(value||"unavailable").replaceAll("-"," ")}
  function setCompareLoading(a,b){
    compareState.data=null;compareState.brief=null;compareState.rows=[];compareState.trends=[];compareState.lastError=null;
    qs("#compareStudio").setAttribute("aria-busy","true");showCompareValidation("");
    qs("#compareStudioTitle").textContent=`Loading ${compareCountryName(a)} and ${compareCountryName(b)}`;
    qs("#compareStudioIntro").textContent="Retrieving aligned indicators, trends, public events, source attribution, and methodological metadata.";
    qs("#compareTableBody").innerHTML='<tr><td colspan="4"><div class="loading-block">Loading comparative intelligence…</div></td></tr>';
    qs("#compareTrendChart").innerHTML='<div class="loading-block">Loading synchronized trends…</div>';
    qs("#compareTrendTable").innerHTML="";
    qs("#compareBriefBody").innerHTML='<div class="loading-block">Preparing source-aware comparison brief…</div>';
    ["compareIndicatorCount","compareAlignedCount","compareConflictCount","compareTrendCount","compareEventCountA","compareEventCountB"].forEach(id=>qs(`#${id}`).textContent="—");
  }
  function compareSourceMarkup(record){
    if(!record)return "";
    const label=escapeHtml(record.source||"Source unavailable");
    const link=record.source_url?`<a href="${escapeHtml(record.source_url)}" target="_blank" rel="noopener">${label} ↗</a>`:label;
    const sourceId=record.source_id?` · ${escapeHtml(record.source_id)}`:"";
    const retrieved=record.retrieved_at?` · retrieved ${escapeHtml(cleanDate(record.retrieved_at))}`:"";
    return `<span class="compare-source">${link}${sourceId}${retrieved}</span>`;
  }
  function compareValueMarkup(record,format){
    if(!record)return '<div class="compare-value unavailable"><strong>Unavailable</strong><span>No validated public value is currently available.</span></div>';
    const stateText=[record.data_state,record.cache_state&&record.cache_state!==record.data_state?record.cache_state:null,record.stale?"stale":null].filter(Boolean).join(" · ");
    return `<div class="compare-value"><strong>${escapeHtml(formatCountryValue(record.value,format,record.unit))}</strong><span>${escapeHtml(record.unit||"Unit unavailable")} · ${escapeHtml(record.year||"Year unavailable")}</span><span>${escapeHtml(stateText||"state unavailable")}</span>${compareSourceMarkup(record)}</div>`;
  }
  function syncCompareUrl(){
    const {a,b}=compareSelection();const params=new URLSearchParams(location.search);
    params.set("view","compare");params.set("country",a);params.set("compare",b);params.set("compareView",compareState.activeView);
    const indicator=qs("#compareIndicatorFilter").value,trend=qs("#compareTrendSelect").value;
    if(indicator)params.set("indicator",indicator);else params.delete("indicator");
    if(trend)params.set("trend",trend);else params.delete("trend");
    history.replaceState(null,"",`?${params.toString()}`);
  }
  function renderCompareRows(syncUrl=false){
    const filter=qs("#compareIndicatorFilter").value;
    const rows=(compareState.rows||[]).filter(row=>!filter||row.id===filter);
    const leftName=compareState.data?.scope?.primary_country?.name||"Primary";
    const rightName=compareState.data?.scope?.comparison_country?.name||"Comparison";
    qs("#compareTableBody").innerHTML=rows.length?rows.map(row=>{
      const warnings=(row.warnings||[]).map(item=>`<span class="compare-warning">${escapeHtml(item)}</span>`).join("");
      const difference=row.calculation_eligible&&row.absolute_difference!=null?`<span class="compare-difference">Difference: ${escapeHtml(formatCountryValue(row.absolute_difference,row.format,row.unit))}${row.percent_difference==null?"":` · ${escapeHtml(row.percent_difference.toFixed(1))}%`}</span>`:"";
      return `<tr data-compatibility="${escapeHtml(row.compatibility)}"><td data-label="Indicator"><div class="compare-indicator-name"><strong>${escapeHtml(row.label)}</strong><span>${escapeHtml(row.id)} · ${escapeHtml(row.domain||"Public indicator")}</span></div></td><td data-label="${escapeHtml(leftName)}">${compareValueMarkup(row.primary,row.format)}</td><td data-label="${escapeHtml(rightName)}">${compareValueMarkup(row.comparison,row.format)}</td><td data-label="Compatibility"><span class="compare-compatibility ${escapeHtml(row.compatibility)}">${escapeHtml(compareCompatibilityLabel(row.compatibility))}</span>${difference}${warnings}</td></tr>`;
    }).join(""):'<tr class="compare-empty-row"><td colspan="4"><div class="empty-state"><div><strong>No indicators match this filter</strong><span>Choose another indicator or reset the filter.</span></div></div></td></tr>';
    if(syncUrl)syncCompareUrl();reportHeight();
  }
  function renderCompareTrend(trend,syncUrl=false){
    const chart=qs("#compareTrendChart"),table=qs("#compareTrendTable");
    if(!trend){
      qs("#compareTrendTitle").textContent="Trend unavailable";
      chart.innerHTML='<div class="empty-state"><div><strong>Trend unavailable</strong><span>No indicator trend is available for this comparison.</span></div></div>';table.innerHTML="";
      if(syncUrl)syncCompareUrl();return;
    }
    qs("#compareTrendTitle").textContent=trend.label;
    const leftName=compareState.data?.scope?.primary_country?.name||"Primary";
    const rightName=compareState.data?.scope?.comparison_country?.name||"Comparison";
    qs("#compareLegendPrimary").textContent=leftName;qs("#compareLegendSecondary").textContent=rightName;
    chart.setAttribute("aria-label",`${trend.label} trend comparing ${leftName} and ${rightName}`);
    if(!trend.chartable){
      chart.innerHTML=`<div class="empty-state"><div><strong>Synchronized chart unavailable</strong><span>${escapeHtml(trend.chart_warning||"The series cannot be plotted together without overstating comparability.")}</span></div></div>`;
    }else{
      const aligned=trend.aligned_series||[];
      const values=aligned.flatMap(item=>[item.primary_value,item.comparison_value]).filter(value=>Number.isFinite(Number(value))).map(Number);
      const min=Math.min(...values),max=Math.max(...values),spread=Math.max(max-min,Math.abs(max)*.08,1);
      const height=value=>Math.max(4,Math.min(100,8+((Number(value)-min)/spread)*88));
      chart.innerHTML=aligned.map(item=>`<div class="compare-trend-year">${item.primary_value==null?'<span class="compare-trend-gap primary" title="Primary value unavailable"></span>':`<span class="compare-trend-bar primary" style="height:${height(item.primary_value)}%" title="${escapeHtml(leftName)}: ${escapeHtml(formatCountryValue(item.primary_value,trend.format,trend.unit))}"></span>`}${item.comparison_value==null?'<span class="compare-trend-gap secondary" title="Comparison value unavailable"></span>':`<span class="compare-trend-bar secondary" style="height:${height(item.comparison_value)}%" title="${escapeHtml(rightName)}: ${escapeHtml(formatCountryValue(item.comparison_value,trend.format,trend.unit))}"></span>`}<small>${escapeHtml(item.year)}</small></div>`).join("");
    }
    const aligned=trend.aligned_series||[];
    table.innerHTML=aligned.length?`<div class="compare-trend-note">${escapeHtml(trend.comparison_note||"")} Common reporting years: ${escapeHtml(trend.common_year_count||0)}.</div><div class="compare-trend-table-shell"><table><thead><tr><th>Year</th><th>${escapeHtml(leftName)}</th><th>${escapeHtml(rightName)}</th></tr></thead><tbody>${aligned.map(item=>`<tr><th scope="row">${escapeHtml(item.year)}</th><td>${item.primary_value==null?"Unavailable":escapeHtml(formatCountryValue(item.primary_value,trend.format,trend.unit))}</td><td>${item.comparison_value==null?"Unavailable":escapeHtml(formatCountryValue(item.comparison_value,trend.format,trend.unit))}</td></tr>`).join("")}</tbody></table></div>`:"";
    if(syncUrl)syncCompareUrl();reportHeight();
  }
  function initCompareMap(){
    if(compareState.map)return;
    compareState.map=L.map("compareMap",{zoomControl:true,worldCopyJump:true}).setView([10,20],2);
    compareState.base=L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",{attribution:"© OpenStreetMap contributors © CARTO",maxZoom:19}).addTo(compareState.map);
    compareState.markers=L.layerGroup().addTo(compareState.map);
  }
  function renderCompareMap(){
    initCompareMap();compareState.markers.clearLayers();
    const countries=[compareState.data?.scope?.primary_country,compareState.data?.scope?.comparison_country].filter(Boolean);const points=[];
    countries.forEach((country,index)=>{const lat=Number(country.latitude),lng=Number(country.longitude);if(!Number.isFinite(lat)||!Number.isFinite(lng))return;points.push([lat,lng]);L.circleMarker([lat,lng],{radius:9,color:"#fff",weight:1,fillColor:index===0?"#43d6ff":"#ff8b5c",fillOpacity:.9}).addTo(compareState.markers).bindPopup(`<strong>${escapeHtml(country.name)}</strong><br>${escapeHtml(country.capital||"Capital unavailable")}`)});
    if(points.length===2)compareState.map.fitBounds(points,{padding:[55,55],maxZoom:5});else if(points.length===1)compareState.map.setView(points[0],4);else compareState.map.setView([10,20],2);
    qs("#compareMapTitle").textContent=countries.map(item=>item.name).join(" and ")||"Two-country context";
    qs("#compareMapNote").textContent=points.length===2?"Both country reference points are available.":points.length===1?"One country lacks a validated map reference point.":"Validated country reference points are unavailable for this pair.";
    setTimeout(()=>compareState.map.invalidateSize(),80);
  }
  function renderCompareBrief(){
    const brief=compareState.brief;if(!brief){qs("#compareBriefBody").innerHTML='<div class="empty-state"><div><strong>Brief unavailable</strong><span>No source-aware comparison brief was returned.</span></div></div>';return}
    qs("#compareBriefTitle").textContent=brief.title;qs("#compareBriefGenerated").textContent=`Generated ${cleanDate(brief.generated_at)}`;
    const evidence=(brief.latest_available_indicators||[]).slice(0,16).map(item=>{const a=item.primary,b=item.comparison;return `<div><strong>${escapeHtml(item.indicator)}</strong><span>${a?`${escapeHtml(formatCountryValue(a.value,a.format,a.unit))} (${escapeHtml(a.year)})`:"Unavailable"} · ${b?`${escapeHtml(formatCountryValue(b.value,b.format,b.unit))} (${escapeHtml(b.year)})`:"Unavailable"}<br>${escapeHtml(compareCompatibilityLabel(item.compatibility))}</span></div>`}).join("");
    const caveats=(brief.methodological_caveats||[]).slice(0,18).map(item=>`<li>${escapeHtml(item)}</li>`).join("");
    const gaps=(brief.data_gaps||[]).slice(0,12).map(item=>`<li><strong>${escapeHtml(item.indicator)}</strong>: ${escapeHtml(compareCompatibilityLabel(item.compatibility))}</li>`).join("");
    const sources=(brief.source_list||[]).map(item=>`<li>${item.url?`<a href="${escapeHtml(item.url)}" target="_blank" rel="noopener">${escapeHtml(item.name)} ↗</a>`:escapeHtml(item.name)}${item.source_id?` · ${escapeHtml(item.source_id)}`:""}</li>`).join("");
    qs("#compareBriefBody").innerHTML=`<section class="compare-brief-section"><h3>Comparison scope</h3><p>${escapeHtml(brief.comparison_scope.primary_country.name)} and ${escapeHtml(brief.comparison_scope.comparison_country.name)} · ${escapeHtml(brief.comparison_scope.indicator_count)} indicator records.</p></section><section class="compare-brief-section"><h3>Latest available indicators</h3><div class="compare-brief-evidence">${evidence||"No validated public values are currently available."}</div></section><section class="compare-brief-section"><h3>Data gaps and conflicts</h3><ul>${gaps||"<li>No unresolved comparison conflicts were reported.</li>"}</ul></section><section class="compare-brief-section"><h3>Methodological caveats</h3><ul>${caveats}</ul></section><section class="compare-brief-section"><h3>Sources</h3><ul>${sources||"<li>Source records unavailable.</li>"}</ul></section><section class="compare-brief-section"><h3>Responsible-use boundary</h3><p>${escapeHtml(brief.boundary)}</p></section>`;
  }
  function renderComparison(){
    const data=compareState.data,indicators=data.indicators||{},left=data.scope.primary_country,right=data.scope.comparison_country;
    qs("#compareStudioTitle").textContent=data.title;qs("#compareStudioIntro").textContent=`Compare ${left.name} and ${right.name} with source, unit, reporting-year, definition, and data-state differences kept visible.`;
    qs("#compareTableHeadA").textContent=left.name;qs("#compareTableHeadB").textContent=right.name;
    qs("#compareIndicatorCount").textContent=data.summary.available_indicator_count;qs("#compareAlignedCount").textContent=data.summary.aligned_indicator_count;qs("#compareConflictCount").textContent=data.summary.conflict_count;qs("#compareTrendCount").textContent=data.summary.chartable_trend_count;
    qs("#compareEventLabelA").textContent=`${left.name} events`;qs("#compareEventLabelB").textContent=`${right.name} events`;qs("#compareEventCountA").textContent=data.summary.primary_event_count;qs("#compareEventCountB").textContent=data.summary.comparison_event_count;
    compareState.rows=indicators.rows||[];compareState.trends=data.trends?.trends||[];
    const params=new URLSearchParams(location.search);const requestedIndicator=params.get("indicator")||qs("#compareIndicatorFilter").value;const requestedTrend=params.get("trend")||qs("#compareTrendSelect").value;
    qs("#compareIndicatorFilter").innerHTML='<option value="">All indicators</option>'+compareState.rows.map(row=>`<option value="${escapeHtml(row.id)}">${escapeHtml(row.label)}</option>`).join("");
    qs("#compareIndicatorFilter").value=compareState.rows.some(row=>row.id===requestedIndicator)?requestedIndicator:"";renderCompareRows(false);
    qs("#compareTrendSelect").innerHTML=compareState.trends.length?compareState.trends.map(item=>`<option value="${escapeHtml(item.id)}">${escapeHtml(item.label)}${item.chartable?"":" — limited"}</option>`).join(""):'<option value="">No trend series available</option>';
    const activeTrend=compareState.trends.find(item=>item.id===requestedTrend)||compareState.trends.find(item=>item.chartable)||compareState.trends[0]||null;if(activeTrend)qs("#compareTrendSelect").value=activeTrend.id;renderCompareTrend(activeTrend,false);
    renderCompareMap();renderCompareBrief();qs("#compareMethodology p").textContent=(data.boundaries||[]).join(" ");showCompareValidation(data.summary.event_data_state==="partial"?"Some optional event context is temporarily unavailable. Indicator comparison remains available.":"",data.summary.event_data_state==="partial"?"notice":"error");reportHeight();
  }
  async function loadComparison(pushState=true){
    await prepareCompareSelectors();const {a,b}=compareSelection();const validation=validateCompareSelection(a,b);
    if(!validation.ok){showCompareValidation(validation.message);qs("#compareTableBody").innerHTML='<tr><td colspan="4"><div class="empty-state"><div><strong>Comparison not started</strong><span>Choose two different supported countries.</span></div></div></td></tr>';qs("#compareStudio").setAttribute("aria-busy","false");return}
    if(compareState.controller)compareState.controller.abort();const controller=new AbortController();compareState.controller=controller;const signal=controller.signal,sequence=++compareState.sequence;setCompareLoading(a,b);
    try{
      const query=new URLSearchParams({country:a,compare:b,include_brief:"true",include_events:"true"});
      const data=await apiWithRetry(`/public/compare?${query.toString()}`,3,{signal,timeout:45000});
      if(signal.aborted||sequence!==compareState.sequence)return;
      compareState.data=data;compareState.brief=data.brief||null;state.country=a;renderComparison();if(pushState)syncCompareUrl();
    }catch(error){
      if(error?.name==="AbortError")return;compareState.lastError=error;showCompareValidation("The comparison could not be completed. Retry after the service finishes waking up.");qs("#compareTableBody").innerHTML=`<tr><td colspan="4">${publicErrorBlock("Comparison unavailable","The comparative intelligence service may be waking up or temporarily unavailable.",()=>loadComparison(false))}</td></tr>`;qs("#compareTrendChart").innerHTML='<div class="empty-state"><div><strong>Trend unavailable</strong><span>Retry the comparison to load synchronized trend records.</span></div></div>';qs("#compareBriefBody").innerHTML='<div class="empty-state"><div><strong>Brief unavailable</strong><span>Retry the comparison to generate a source-aware brief.</span></div></div>';
    }finally{if(sequence===compareState.sequence)qs("#compareStudio").setAttribute("aria-busy","false");reportHeight()}
  }
  async function openCompareStudio(){
    qs("#compareStudio").hidden=false;await prepareCompareSelectors();const params=new URLSearchParams(location.search);const validCodes=new Set(globalCountryState.catalog.map(item=>item.code));const a=validCodes.has(params.get("country"))?params.get("country"):(validCodes.has(state.country)?state.country:"KEN");const b=validCodes.has(params.get("compare"))?params.get("compare"):"GHA";qs("#compareCountryA").value=a;qs("#compareCountryB").value=b;const requestedView=params.get("compareView");setCompareView(compareViews.has(requestedView)?requestedView:"table",false);await loadComparison(false)
  }
  function closeCompareStudio(){qs("#compareStudio").hidden=true;if(compareState.controller)compareState.controller.abort()}
  function setCompareView(view,sync=true){
    const normalized=compareViews.has(view)?view:"table";compareState.activeView=normalized;qsa(".compare-tab").forEach(button=>{const active=button.dataset.compareView===normalized;button.classList.toggle("active",active);button.setAttribute("aria-selected",active?"true":"false")});["table","chart","map","brief","export"].forEach(name=>{qs(`#compare${name[0].toUpperCase()+name.slice(1)}View`).hidden=name!==normalized});if(normalized==="map")setTimeout(()=>compareState.map?.invalidateSize(),80);if(sync&&compareState.data)syncCompareUrl();reportHeight()
  }
  async function copyComparisonView(){
    if(compareState.data)syncCompareUrl();const value=location.href;
    try{await navigator.clipboard.writeText(value)}catch{const field=document.createElement("textarea");field.value=value;field.setAttribute("readonly","");field.style.position="fixed";field.style.opacity="0";document.body.appendChild(field);field.select();document.execCommand("copy");field.remove()}
    toast("Comparison view link copied");
  }
  async function downloadComparison(format){
    if(!compareState.data){toast("Run a comparison before exporting.");return}
    const a=compareState.data.scope.primary_country.code,b=compareState.data.scope.comparison_country.code;const params=new URLSearchParams({country:a,compare:b,format});const indicator=qs("#compareIndicatorFilter").value;if(indicator)params.set("indicator",indicator);toast(`Preparing ${format.toUpperCase()} export…`);
    try{const response=await fetch(`${API}/public/compare/export?${params.toString()}`,{headers:{Accept:"*/*"}});if(!response.ok)throw new Error(String(response.status));const blob=await response.blob();const disposition=response.headers.get("Content-Disposition")||"";const match=disposition.match(/filename="?([^";]+)"?/i);const extension=format==="print"?"html":format;const filename=match?.[1]||`site-intelligence-comparison-${a}-${b}.${extension}`;const link=document.createElement("a");link.href=URL.createObjectURL(blob);link.download=filename;document.body.appendChild(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(link.href),1200);toast("Comparison export downloaded")}catch{toast("Comparison export is temporarily unavailable.")}
  }

  const earthState={mapA:null,mapB:null,baseA:null,baseB:null,layerA:null,layerB:null,layers:[],frames:[],frameIndex:0,timer:null,activeLayer:"true-color",opacity:.72};

  function earthDate(daysAgo){const d=new Date();d.setUTCDate(d.getUTCDate()-daysAgo);return d.toISOString().slice(0,10)}
  function earthLayer(id){return earthState.layers.find(x=>x.id===id)||earthState.layers[0]}
  function syncEarthMaps(source,target){if(!source||!target)return;const c=source.getCenter(),z=source.getZoom();target.setView(c,z,{animate:false})}
  function initEarthMaps(){
    if(earthState.mapA)return;
    earthState.mapA=L.map("earthMapA",{zoomControl:true,worldCopyJump:true}).setView([12,20],2);
    earthState.mapB=L.map("earthMapB",{zoomControl:false,worldCopyJump:true,attributionControl:false}).setView([12,20],2);
    earthState.baseA=L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",{attribution:"© OpenStreetMap contributors © CARTO",maxZoom:19,crossOrigin:true}).addTo(earthState.mapA);
    earthState.baseB=L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",{maxZoom:19,crossOrigin:true}).addTo(earthState.mapB);
    let syncing=false;
    const sync=(a,b)=>{if(syncing)return;syncing=true;syncEarthMaps(a,b);syncing=false};
    earthState.mapA.on("move zoom",()=>sync(earthState.mapA,earthState.mapB));
    earthState.mapB.on("move zoom",()=>sync(earthState.mapB,earthState.mapA));
  }
  async function loadEarthLayers(){
    const payload=await apiWithRetry("/public/earth-observation/layers",3);
    earthState.layers=payload.layers||[];
    qs("#earthLayerSelect").innerHTML=earthState.layers.map(x=>`<option value="${escapeHtml(x.id)}">${escapeHtml(x.title)}</option>`).join("");
  }
  function setEarthClip(value){
    const v=Math.max(0,Math.min(100,Number(value)));
    qs("#earthMapBWrap").style.clipPath=`inset(0 0 0 ${v}%)`;
    qs("#earthSwipeLine").style.left=`${v}%`;
  }
  function addEarthTile(map,existing,layer,dateValue){
    if(existing)map.removeLayer(existing);
    const url=layer.tile_url.replace("{time}",dateValue);
    return L.tileLayer(url,{opacity:earthState.opacity,attribution:layer.attribution||layer.source,maxZoom:9,crossOrigin:true,errorTileUrl:""}).addTo(map);
  }
  function renderEarthMetadata(layer){
    const rows=[
      ["Source",layer.source],["Observation type",layer.observation_type],["Temporal resolution",layer.temporal_resolution],
      ["Spatial resolution",layer.spatial_resolution],["Availability",layer.status],["Attribution",layer.attribution],
      ["Description",layer.description],["Known limits",layer.limits]
    ];
    qs("#earthMetaTitle").textContent=layer.title;
    qs("#earthMetadata").innerHTML=`<div class="earth-meta-grid">${rows.map(([a,b])=>`<div class="earth-meta-item"><span>${escapeHtml(a)}</span><strong>${escapeHtml(b||"Source dependent")}</strong></div>`).join("")}</div>`;
  }
  async function applyEarthComparison(pushState=true){
    initEarthMaps();stopEarthPlayback();
    const validation=validateEarthDates();if(!validation.ok){showEarthUnavailable(validation.message);return}
    hideEarthUnavailable();setEarthLoading(true);setEarthStatus("Loading imagery","loading");
    const layer=earthLayer(qs("#earthLayerSelect").value);
    const dateA=qs("#earthDateA").value,dateB=qs("#earthDateB").value;
    earthState.activeLayer=layer.id;earthState.opacity=Number(qs("#earthOpacity").value)/100;
    earthState.layerA=addEarthTile(earthState.mapA,earthState.layerA,layer,dateA);
    earthState.layerB=addEarthTile(earthState.mapB,earthState.layerB,layer,dateB);
    earthState.layerA.bringToFront();earthState.layerB.bringToFront();
    qs("#earthBadgeA").textContent=dateA;qs("#earthBadgeB").textContent=dateB;renderEarthMetadata(layer);
    const tileResults=await Promise.all([bindTileReliability(earthState.layerA,"before"),bindTileReliability(earthState.layerB,"after")]);
    if(tileResults.some(x=>!x.ok)){showEarthUnavailable("One or both imagery dates did not return enough tiles. Try a nearby date or another layer.")}
    else{setEarthStatus("Imagery ready","ready")}
    try{
      const compare=await apiWithRetry(`/public/earth-observation/compare?layer=${encodeURIComponent(layer.id)}&date_a=${encodeURIComponent(dateA)}&date_b=${encodeURIComponent(dateB)}`,2);
      qs("#earthBoundary").textContent=compare.comparison_boundary;
    }catch{showGlobalNotice("Earth metadata is temporarily unavailable","The imagery comparison can still be used while metadata retries.")}
    if(pushState){
      const params=new URLSearchParams(location.search);
      params.set("view","earth");params.set("earthLayer",layer.id);params.set("dateA",dateA);params.set("dateB",dateB);
      params.set("opacity",String(Math.round(earthState.opacity*100)));params.set("swipe",String(qs("#earthSwipe").value));
      history.replaceState(null,"",`?${params.toString()}`);
    }
    setEarthLoading(false);setTimeout(()=>{earthState.mapA.invalidateSize();earthState.mapB.invalidateSize();reportHeight()},80);
  }
  async function loadEarthTimeline(){
    const payload=await apiWithRetry(`/public/earth-observation/timeline?layer=${encodeURIComponent(earthState.activeLayer)}&end_date=${encodeURIComponent(qs("#earthDateB").value)}&days=14`,2);
    earthState.frames=payload.frames||[];earthState.frameIndex=Math.max(0,earthState.frames.length-1);
    qs("#earthTimelineRange").max=String(Math.max(0,earthState.frames.length-1));qs("#earthTimelineRange").value=String(earthState.frameIndex);
    updateEarthFrame();
  }
  function updateEarthFrame(){
    const frame=earthState.frames[earthState.frameIndex];if(!frame)return;
    qs("#earthTimelineDate").textContent=frame.date;qs("#earthDateB").value=frame.date;
    const layer=earthLayer(earthState.activeLayer);earthState.layerB=addEarthTile(earthState.mapB,earthState.layerB,layer,frame.date);qs("#earthBadgeB").textContent=frame.date;
  }
  function toggleEarthPlayback(){
    if(reducedMotion){stopEarthPlayback();toast("Timeline autoplay is disabled by your reduced-motion preference.");return}
    if(earthState.timer){stopEarthPlayback();return}
    if(!earthState.frames.length)return;
    qs("#earthPlay").textContent="Pause";qs("#earthPlay").setAttribute("aria-pressed","true");
    earthState.timer=setInterval(()=>{earthState.frameIndex=(earthState.frameIndex+1)%earthState.frames.length;qs("#earthTimelineRange").value=String(earthState.frameIndex);qs("#earthFrameState").textContent=`Frame ${earthState.frameIndex+1} of ${earthState.frames.length}`;updateEarthFrame()},1200);
  }
  function earthManifestUrl(){
    const center=earthState.mapA?.getCenter()||{lat:12,lng:20};const zoom=earthState.mapA?.getZoom()||2;
    return `${API}/public/earth-observation/export-manifest?layer=${encodeURIComponent(earthState.activeLayer)}&date_a=${encodeURIComponent(qs("#earthDateA").value)}&date_b=${encodeURIComponent(qs("#earthDateB").value)}&latitude=${center.lat}&longitude=${center.lng}&zoom=${zoom}&opacity=${earthState.opacity}`;
  }
  async function downloadEarthManifest(){
    const data=await apiWithRetry(earthManifestUrl().replace(API,""),2);const blob=new Blob([JSON.stringify(data,null,2)],{type:"application/json"});
    const a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download=`site-intelligence-earth-${earthState.activeLayer}-${qs("#earthDateB").value}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);
  }
  async function exportEarthPNG(){
    toast("Loading the optional PNG capture tool…");
    try{
      const capture=await ensureHtml2Canvas();
      toast("Preparing Earth view image…");
      const canvas=await capture(qs("#earthCapture"),{backgroundColor:"#05080c",useCORS:true,allowTaint:false,scale:1.5,logging:false});
      const a=document.createElement("a");a.href=canvas.toDataURL("image/png");a.download=`site-intelligence-earth-${earthState.activeLayer}-${qs("#earthDateB").value}.png`;a.click();
    }catch{toast("PNG export could not include all imagery. Use Print view or the JSON manifest.")}
  }
  async function openEarthStudio(){
    qs("#earthStudio").hidden=false;
    if(!earthState.layers.length)await loadEarthLayers();
    const params=new URLSearchParams(location.search);
    qs("#earthLayerSelect").value=params.get("earthLayer")||"true-color";
    qs("#earthDateA").value=params.get("dateA")||earthDate(8);qs("#earthDateB").value=params.get("dateB")||earthDate(1);
    qs("#earthOpacity").value=params.get("opacity")||"72";
    qs("#earthSwipe").value=params.get("swipe")||"50";setEarthClip(qs("#earthSwipe").value);
    await applyEarthComparison(false);await loadEarthTimeline();
  }
  function closeEarthStudio(){qs("#earthStudio").hidden=true;stopEarthPlayback()}

  const formatCountryValue=(value,format,unit)=>{
    if(value===null||value===undefined)return "Unavailable";
    if(format==="compact")return new Intl.NumberFormat(undefined,{notation:"compact",maximumFractionDigits:1}).format(value);
    if(format==="currency")return new Intl.NumberFormat(undefined,{style:"currency",currency:"USD",maximumFractionDigits:0}).format(value);
    if(format==="percent")return `${Number(value).toFixed(1)}%`;
    return Number(value).toLocaleString(undefined,{maximumFractionDigits:1});
  };
  function renderTrend(trend){
    const chart=qs("#trendChart");const series=trend?.series||[];
    if(!series.length){chart.innerHTML='<div class="loading-block">A live multi-year trend is not available for this indicator.</div>';return}
    const values=series.map(x=>Number(x.value));const min=Math.min(...values),max=Math.max(...values),spread=Math.max(max-min,Math.abs(max)*.08,1);
    chart.innerHTML=series.map(x=>{
      const height=12+((Number(x.value)-min)/spread)*82;
      return `<div class="trend-column"><span class="trend-value">${escapeHtml(formatCountryValue(x.value,trend.format,trend.unit))}</span><span class="trend-bar" style="height:${Math.max(5,Math.min(96,height))}%"></span><span class="trend-year">${escapeHtml(x.year)}</span></div>`;
    }).join("");
  }
  async function loadLiveCountry(code){
    const panel=qs("#countryIntelligencePanel");panel.hidden=false;
    qs("#countryIndicatorGrid").innerHTML='<div class="skeleton-stack"><span></span><span></span><span></span></div>';
    try{
      const [profile,trends]=await Promise.all([apiWithRetry(`/public/country/${code}`,3),apiWithRetry(`/public/country/${code}/trends`,3)]);
      qs("#liveCountryTitle").textContent=`${profile.country.name} intelligence`;
      qs("#liveCountrySummary").textContent=profile.summary;
      const stateLabel=profile.data_state==="live"?"Live public indicators":profile.data_state==="reference-snapshot"?"Reference snapshot":"Source unavailable";
      qs("#countryDataState").textContent=stateLabel;
      qs("#countryDataState").classList.toggle("reference",profile.data_state!=="live");
      countryLineage=new Map((profile.highlights||[]).map(item=>[item.key,item]));
      qs("#countryIndicatorGrid").innerHTML=(profile.highlights||[]).map(item=>{
        const lineage=item.lineage||{},state=lineage.platform_core_state||"not-recorded";
        return `<article class="country-indicator" tabindex="0" role="button" data-evidence-key="${escapeHtml(item.key)}" aria-label="Inspect evidence for ${escapeHtml(item.label)}"><span class="country-indicator-label">${escapeHtml(item.label)}</span><strong class="country-indicator-value">${escapeHtml(formatCountryValue(item.value,item.format,item.unit))}</strong><div class="country-indicator-meta">${escapeHtml(item.unit)} · ${escapeHtml(item.year)}</div><span class="country-indicator-source">${escapeHtml(item.source)} · ${escapeHtml(item.data_state)}</span><span class="country-indicator-lineage"><i class="lineage-dot ${escapeHtml(state)}"></i>${escapeHtml(state==="recorded"||state==="existing"?"Evidence recorded":state==="queued"?"Evidence queued":"Evidence details")}</span></article>`;
      }).join("")||'<div class="loading-block">Validated country indicators are unavailable.</div>';
      qsa("[data-evidence-key]").forEach(card=>{
        const activate=()=>openEvidenceDrawer(countryLineage.get(card.dataset.evidenceKey)||{});
        card.addEventListener("click",activate);
        card.addEventListener("keydown",e=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();activate()}});
      });
      const options=(trends.trends||[]);
      qs("#trendSelect").innerHTML=options.map((item,i)=>`<option value="${escapeHtml(item.key)}">${escapeHtml(item.label)}</option>`).join("");
      if(options.length){qs("#trendTitle").textContent=options[0].label;renderTrend(options[0])}
      qs("#trendSelect").onchange=e=>{const item=options.find(x=>x.key===e.target.value);if(item){qs("#trendTitle").textContent=item.label;renderTrend(item)}};
      qs("#countryEvidenceNotes").innerHTML=[
        "Reporting years differ by indicator and remain visible.",
        "The latest non-null public observation is used; missing values are not imputed.",
        "Reference snapshots are explicitly labeled when the live source cannot be reached.",
        "Indicators describe conditions but do not establish causes, rankings, or legal conclusions."
      ].map(x=>`<div class="evidence-note">${escapeHtml(x)}</div>`).join("");
    }catch{
      qs("#countryIndicatorGrid").innerHTML=publicErrorBlock("Live country intelligence unavailable","The country indicator service may be waking up or temporarily unavailable.",()=>loadLiveCountry(code));
      qs("#countryDataState").textContent="Unavailable";qs("#countryDataState").classList.add("reference");
    }
  }


  const thematicState={data:null,directory:null,layerRegistry:[],controller:null,sequence:0,map:null,base:null,imagery:null,markers:null,countryMarker:null};

  function thematicValue(item){
    if(item?.value===null||item?.value===undefined)return "No validated public value is currently available.";
    return formatCountryValue(item.value,item.format,item.unit);
  }
  function thematicParams(format=""){
    const params=new URLSearchParams({
      country:qs("#thematicCountry").value||state.country||"KEN",
      days:qs("#thematicDays").value||"30"
    });
    if(format)params.set("format",format);
    return params;
  }
  function syncThematicUrl(){
    const params=new URLSearchParams(location.search);
    params.set("view","thematic");
    params.set("dashboard",qs("#thematicDashboard").value||"climate-environment");
    params.set("country",qs("#thematicCountry").value||"KEN");
    params.set("thematicDays",qs("#thematicDays").value||"30");
    params.set("thematicLayer",qs("#thematicLayer").value||"");
    history.replaceState(null,"",`?${params.toString()}`);
  }
  async function prepareThematicStudio(){
    await loadCountryCatalog();
    if(!thematicState.directory){
      const [directory,layerRegistry]=await Promise.all([
        apiWithRetry("/public/thematic-dashboards",2),
        apiWithRetry("/public/earth-observation/layers",2)
      ]);
      thematicState.directory=directory;
      thematicState.layerRegistry=layerRegistry.layers||[];
    }
    const dashboardOptions=(thematicState.directory?.dashboards||[]).map(item=>`<option value="${escapeHtml(item.id)}">${escapeHtml(item.title)}</option>`).join("");
    const countryOptions=globalCountryState.catalog.map(item=>`<option value="${escapeHtml(item.code)}">${escapeHtml(item.name)}</option>`).join("");
    if(!qs("#thematicDashboard").options.length)qs("#thematicDashboard").innerHTML=dashboardOptions;
    if(!qs("#thematicCountry").options.length)qs("#thematicCountry").innerHTML=countryOptions;
  }
  function initThematicMap(){
    if(thematicState.map)return;
    thematicState.map=L.map("thematicMap",{zoomControl:true,worldCopyJump:true}).setView([12,20],2);
    thematicState.base=L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",{attribution:"© OpenStreetMap contributors © CARTO",maxZoom:19}).addTo(thematicState.map);
    thematicState.markers=L.layerGroup().addTo(thematicState.map);
  }
  function activeThematicLayer(){
    const id=qs("#thematicLayer").value;
    return thematicState.layerRegistry.find(item=>item.id===id)||thematicState.layerRegistry[0]||null;
  }
  function setThematicImagery(layerId){
    const layer=thematicState.layerRegistry.find(item=>item.id===layerId);
    if(!layer||!thematicState.map)return;
    if(thematicState.imagery)thematicState.map.removeLayer(thematicState.imagery);
    if(layer.tile_url){
      const url=layer.tile_url.replace("{time}",qs("#dateSelect").value||today());
      thematicState.imagery=L.tileLayer(url,{opacity:layer.default_opacity||.68,attribution:layer.attribution,maxZoom:9}).addTo(thematicState.map);
      thematicState.imagery.bringToBack();
    }
    qsa(".thematic-layer-card").forEach(card=>card.classList.toggle("is-active",card.dataset.layerId===layerId));
  }
  function renderThematicMap(data){
    initThematicMap();
    thematicState.markers.clearLayers();
    if(thematicState.countryMarker){thematicState.map.removeLayer(thematicState.countryMarker);thematicState.countryMarker=null}
    const country=data.country||{},lat=country.latitude,lng=country.longitude;
    if(lat!=null&&lng!=null){
      thematicState.map.setView([lat,lng],data.map?.default_zoom||5);
      thematicState.countryMarker=L.circleMarker([lat,lng],{radius:9,color:"#fff",weight:1,fillColor:"#43d6ff",fillOpacity:.92}).addTo(thematicState.map).bindPopup(`<strong>${escapeHtml(country.name||country.code)}</strong><br>${escapeHtml(country.capital||"Capital unavailable")}`);
    }else thematicState.map.setView([12,20],2);
    (data.events?.records||[]).forEach(item=>{
      const c=item.coordinates||[];if(c.length<2)return;
      L.marker([c[1],c[0]],{icon:markerIcon(item.category)}).bindPopup(`<div class="popup-title">${escapeHtml(item.title||"Public event")}</div><div class="popup-meta">${escapeHtml(item.category_label||item.category||"Event")} · ${escapeHtml(item.source||"Source")}</div>`).addTo(thematicState.markers);
    });
    const availableIds=new Set((data.earth_layers||[]).map(item=>item.id));
    const requested=qs("#thematicLayer").value;
    const layerId=availableIds.has(requested)?requested:(data.earth_layers?.[0]?.id||"");
    if(layerId){qs("#thematicLayer").value=layerId;setThematicImagery(layerId)}
    setTimeout(()=>thematicState.map?.invalidateSize(),80);
  }
  function renderThematicTrend(trend){
    const chart=qs("#thematicTrendChart"),table=qs("#thematicTrendTable"),series=trend?.series||[];
    if(!series.length){
      qs("#thematicTrendTitle").textContent=trend?.label||"Trend unavailable";
      chart.innerHTML='<div class="empty-state"><div><strong>Trend unavailable</strong><span>No validated multi-year series was returned for this indicator.</span></div></div>';table.innerHTML="";return;
    }
    qs("#thematicTrendTitle").textContent=trend.label;
    const values=series.map(item=>Number(item.value)),min=Math.min(...values),max=Math.max(...values),spread=Math.max(max-min,Math.abs(max)*.08,1);
    chart.innerHTML=series.map(item=>{const height=10+((Number(item.value)-min)/spread)*88;return `<div class="thematic-trend-column"><span class="thematic-trend-value">${escapeHtml(formatCountryValue(item.value,trend.format,trend.unit))}</span><span class="thematic-trend-bar" style="height:${Math.max(5,Math.min(98,height))}%"></span><span class="thematic-trend-year">${escapeHtml(item.year)}</span></div>`}).join("");
    table.innerHTML=`<table><thead><tr><th>Year</th><th>${escapeHtml(trend.label)}</th><th>Unit</th></tr></thead><tbody>${series.map(item=>`<tr><th scope="row">${escapeHtml(item.year)}</th><td>${escapeHtml(formatCountryValue(item.value,trend.format,trend.unit))}</td><td>${escapeHtml(trend.unit||"Unit unavailable")}</td></tr>`).join("")}</tbody></table>${(trend.gap_years||[]).length?`<p class="thematic-note">Missing reporting years: ${escapeHtml(trend.gap_years.join(", "))}.</p>`:""}`;
  }
  function renderThematic(data){
    thematicState.data=data;const dashboard=data.dashboard||{},country=data.country||{},summary=data.summary||{};
    qs("#thematicStudioTitle").textContent=dashboard.title||"Thematic Intelligence";
    qs("#thematicStudioIntro").textContent=`${dashboard.summary||""} Selected country: ${country.name||country.code||"Unavailable"}.`;
    qs("#thematicMaturity").textContent=dashboard.maturity||"Public beta";
    qs("#thematicStatus").textContent=`Dashboard ready · ${data.data_state||"state unavailable"} · generated ${cleanDate(data.generated_at)}`;qs("#thematicStatus").dataset.state="ready";
    qs("#thematicIndicatorMetric").textContent=`${summary.available_indicator_count||0}/${summary.indicator_count||0}`;
    qs("#thematicTrendMetric").textContent=summary.chartable_trend_count||0;qs("#thematicEventMetric").textContent=summary.event_count||0;qs("#thematicLayerMetric").textContent=summary.layer_count||0;qs("#thematicSourceMetric").textContent=summary.source_count||0;qs("#thematicGapMetric").textContent=(data.missing_data||[]).length;
    qs("#thematicMapTitle").textContent=`${country.name||country.code||"Country"} geographic context`;qs("#thematicMapNote").textContent=data.map?.note||"Mapped evidence remains source-aware.";
    qs("#thematicIndicatorTitle").textContent=`${dashboard.title||"Thematic"} indicators`;
    qs("#thematicIndicatorGrid").innerHTML=(data.indicators||[]).map(item=>`<article class="thematic-indicator-card ${item.available?"":"is-missing"}"><span class="label">${escapeHtml(item.label||item.id)}</span><strong>${escapeHtml(thematicValue(item))}</strong><span class="meta">${escapeHtml(item.unit||"Unit unavailable")} · ${escapeHtml(item.reporting_year||"Year unavailable")}</span><span class="source">${item.source_url?`<a href="${escapeHtml(item.source_url)}" target="_blank" rel="noopener">${escapeHtml(item.source||"Source")} ↗</a>`:escapeHtml(item.source||"Source unavailable")}</span><span class="state">${escapeHtml(item.data_state||"unavailable")}</span></article>`).join("")||'<div class="empty-state"><div><strong>No thematic indicators</strong><span>No validated public value is currently available.</span></div></div>';
    qs("#thematicLayer").innerHTML=(data.earth_layers||[]).map(item=>`<option value="${escapeHtml(item.id)}">${escapeHtml(item.title)}</option>`).join("");
    qs("#thematicLayerList").innerHTML=(data.earth_layers||[]).map(item=>`<div class="thematic-layer-card" role="button" tabindex="0" data-layer-id="${escapeHtml(item.id)}"><strong>${escapeHtml(item.title)}</strong><span>${escapeHtml(item.source||"Source unavailable")} · ${escapeHtml(item.temporal_resolution||"time varies")}</span><span>${escapeHtml(item.limits||"")}</span></div>`).join("")||'<div class="empty-state"><div><strong>No Earth layers registered</strong><span>Layer metadata is temporarily unavailable.</span></div></div>';
    qsa(".thematic-layer-card").forEach(card=>{const activate=()=>{qs("#thematicLayer").value=card.dataset.layerId;setThematicImagery(card.dataset.layerId);syncThematicUrl()};card.addEventListener("click",activate);card.addEventListener("keydown",event=>{if(event.key==="Enter"||event.key===" "){event.preventDefault();activate()}})});
    const trends=data.trends||[];qs("#thematicTrendSelect").innerHTML=trends.length?trends.map(item=>`<option value="${escapeHtml(item.id)}">${escapeHtml(item.label)}${item.chartable?"":" — limited"}</option>`).join(""):'<option value="">No trends available</option>';renderThematicTrend(trends.find(item=>item.chartable)||trends[0]||null);
    qs("#thematicEventList").innerHTML=(data.events?.records||[]).length?(data.events.records||[]).slice(0,16).map(item=>`<article class="thematic-event-card"><strong>${escapeHtml(item.title||"Public event")}</strong><span>${escapeHtml(item.category_label||item.category||"Event")} · ${escapeHtml(item.source||"Source")} · ${escapeHtml(cleanDate(item.observed_at))}</span><span>${escapeHtml(item.country_match_method||"country match unavailable")}${item.country_match_confidence!=null?` · confidence ${escapeHtml(item.country_match_confidence)}`:""}</span></article>`).join(""):`<div class="empty-state"><div><strong>No recent country-linked records</strong><span>${escapeHtml(data.events?.data_state==="temporarily-unavailable"?"Optional event context is temporarily unavailable.":"The selected public feeds returned no matching records for this window.")}</span></div></div>`;
    qs("#thematicSourceList").innerHTML=(data.sources||[]).map(item=>`<article class="thematic-source-record"><strong>${escapeHtml(item.name||"Source")}</strong><span>${escapeHtml((item.record_types||[]).join(" · "))} · ${escapeHtml((item.data_states||[]).join(" · "))}</span>${item.url?`<a href="${escapeHtml(item.url)}" target="_blank" rel="noopener">${escapeHtml(item.url)}</a>`:""}</article>`).join("")||'<p>No source records were returned.</p>';
    qs("#thematicMethodology").innerHTML=`<ul>${(data.methodology||[]).map(item=>`<li>${escapeHtml(item)}</li>`).join("")}</ul><div class="thematic-boundary">${escapeHtml([...(data.interpretation_limits||[]),data.responsible_use].filter(Boolean).join(" "))}</div>`;
    renderThematicMap(data);syncThematicUrl();reportHeight();
  }
  async function loadThematicDashboard(pushState=true){
    if(thematicState.controller)thematicState.controller.abort();const controller=new AbortController();thematicState.controller=controller;const sequence=++thematicState.sequence;
    qs("#thematicStudio").setAttribute("aria-busy","true");qs("#thematicStatus").textContent="Loading indicators, trends, event context, Earth layers, and source records…";qs("#thematicStatus").dataset.state="loading";
    qs("#thematicIndicatorGrid").innerHTML='<div class="loading-block">Loading thematic indicators…</div>';
    try{
      const dashboard=qs("#thematicDashboard").value||"climate-environment";const query=thematicParams();
      const data=await apiWithRetry(`/public/thematic-dashboard/${encodeURIComponent(dashboard)}?${query.toString()}`,2,{signal:controller.signal,timeout:45000});
      if(controller.signal.aborted||sequence!==thematicState.sequence)return;
      state.country=data.country?.code||qs("#thematicCountry").value;renderThematic(data);if(pushState)syncThematicUrl();
    }catch(error){if(error?.name==="AbortError")return;qs("#thematicStatus").textContent="Thematic dashboard unavailable";qs("#thematicStatus").dataset.state="error";qs("#thematicIndicatorGrid").innerHTML=publicErrorBlock("Thematic dashboard unavailable","The selected public evidence services may be waking up or temporarily unavailable.",()=>loadThematicDashboard(false));}
    finally{if(sequence===thematicState.sequence)qs("#thematicStudio").setAttribute("aria-busy","false");reportHeight()}
  }
  async function downloadThematic(format){
    if(!thematicState.data){toast("Load a thematic dashboard before exporting.");return}
    const dashboard=thematicState.data.dashboard.id;const response=await fetch(`${API}/public/thematic-dashboard/${encodeURIComponent(dashboard)}/export?${thematicParams(format).toString()}`,{headers:{Accept:"*/*"}});if(!response.ok){toast("Thematic export unavailable");return}const blob=await response.blob();const disposition=response.headers.get("content-disposition")||"";const match=disposition.match(/filename="?([^";]+)"?/i);const name=match?.[1]||`site-intelligence-${dashboard}.${format}`;const link=document.createElement("a");link.href=URL.createObjectURL(blob);link.download=name;document.body.appendChild(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(link.href),5000);toast("Thematic export downloaded");
  }
  async function openThematicStudio(){
    qs("#thematicStudio").hidden=false;await prepareThematicStudio();initThematicMap();const params=new URLSearchParams(location.search);const dashboards=new Set((thematicState.directory?.dashboards||[]).map(item=>item.id));const countries=new Set(globalCountryState.catalog.map(item=>item.code));
    qs("#thematicDashboard").value=dashboards.has(params.get("dashboard"))?params.get("dashboard"):"climate-environment";qs("#thematicCountry").value=countries.has(params.get("country"))?params.get("country"):(countries.has(state.country)?state.country:"KEN");qs("#thematicDays").value=["7","14","30","90"].includes(params.get("thematicDays"))?params.get("thematicDays"):"30";await loadThematicDashboard(false);if(params.get("thematicLayer")&&[...qs("#thematicLayer").options].some(option=>option.value===params.get("thematicLayer"))){qs("#thematicLayer").value=params.get("thematicLayer");setThematicImagery(params.get("thematicLayer"))}
  }
  function closeThematicStudio(){qs("#thematicStudio").hidden=true;if(thematicState.controller)thematicState.controller.abort()}

  const briefingState={data:null,controller:null,sequence:0,directory:null};
  function briefingType(){return qs("#briefingType").value||"country"}
  function updateBriefingFields(){
    const type=briefingType();
    qsa("[data-brief-field]").forEach(field=>{const allowed=String(field.dataset.briefField||"").split(/\s+/);field.hidden=!allowed.includes(type)});
  }
  function briefingDate(offset){const value=new Date();value.setUTCDate(value.getUTCDate()-offset);return value.toISOString().slice(0,10)}
  async function prepareBriefingStudio(){
    await loadCountryCatalog();
    const options=globalCountryState.catalog.map(item=>`<option value="${escapeHtml(item.code)}">${escapeHtml(item.name)}</option>`).join("");
    if(!qs("#briefingCountry").options.length)qs("#briefingCountry").innerHTML=options;
    if(!qs("#briefingCompare").options.length)qs("#briefingCompare").innerHTML=options;
    if(!briefingState.directory)briefingState.directory=await apiWithRetry("/public/briefing-studio",3);
    if(!qs("#briefingDateA").value)qs("#briefingDateA").value=briefingDate(8);
    if(!qs("#briefingDateB").value)qs("#briefingDateB").value=briefingDate(1);
  }
  function briefingParams(includeFormat){
    const type=briefingType(),params=new URLSearchParams();
    params.set("type",type);
    if(includeFormat)params.set("format",includeFormat);
    if(["country","comparison","event","thematic"].includes(type))params.set("country",qs("#briefingCountry").value||"KEN");
    if(["comparison","thematic"].includes(type))params.set("compare",qs("#briefingCompare").value||"GHA");
    if(["country","comparison","event"].includes(type))params.set("days",qs("#briefingDays").value||"14");
    if(type==="event"&&qs("#briefingEventId").value.trim())params.set("event_id",qs("#briefingEventId").value.trim());
    if(type==="thematic")params.set("dashboard_id",qs("#briefingDashboard").value||"climate-environment");
    if(type==="earth"){
      params.set("layer_id",qs("#briefingLayer").value||"true-color");params.set("date_a",qs("#briefingDateA").value);params.set("date_b",qs("#briefingDateB").value);
      const center=state.map?.getCenter?.();params.set("latitude",String(center?.lat??12));params.set("longitude",String(center?.lng??20));params.set("zoom",String(state.map?.getZoom?.()??2));params.set("opacity","0.72");
    }
    return params;
  }
  function syncBriefingUrl(){
    const params=briefingParams();params.set("view","briefing");params.set("briefType",briefingType());
    history.replaceState(null,"",`?${params.toString()}`);
  }
  function briefingEvidenceCount(data){
    const evidence=data?.evidence||{};return ["indicators","trends","events","layers","thematic_items"].reduce((sum,key)=>sum+(Array.isArray(evidence[key])?evidence[key].length:0),0)
  }
  function briefingRecordMarkup(item,group){
    const label=item.label||item.title||item.id||group.replaceAll("_"," ");
    const value=item.value===0?"0":item.value??item.description??item.value_status??item.observation_type??"Source-aware record";
    const meta=[item.country_name||item.country_code,item.reporting_year||item.observed_at,item.unit,item.data_state,item.compatibility].filter(Boolean).join(" · ");
    const source=item.source_url?`<a href="${escapeHtml(item.source_url)}" target="_blank" rel="noopener">${escapeHtml(item.source||"Open source")} ↗</a>`:escapeHtml(item.source||"");
    return `<article class="briefing-record"><span>${escapeHtml(group.replaceAll("_"," "))}</span><strong>${escapeHtml(label)}</strong><p>${escapeHtml(typeof value==="object"?JSON.stringify(value):String(value))}</p>${meta?`<small>${escapeHtml(meta)}</small>`:""}${source?`<small>${source}</small>`:""}</article>`;
  }
  function renderBriefing(data){
    briefingState.data=data;
    qs("#briefingStudioTitle").textContent=data.title;qs("#briefingStudioIntro").textContent=data.summary;
    qs("#briefingDocumentTitle").textContent=data.title;qs("#briefingDocumentSummary").textContent=data.summary;
    qs("#briefingTypeMetric").textContent=String(data.brief_type||"—").replaceAll("-"," ");
    qs("#briefingRecordMetric").textContent=briefingEvidenceCount(data);qs("#briefingSourceMetric").textContent=(data.source_records||[]).length;qs("#briefingGapMetric").textContent=(data.missing_data||[]).length;
    qs("#briefingDocumentMeta").innerHTML=`<strong>${escapeHtml(data.brief_id||"")}</strong><span>Generated ${escapeHtml(cleanDate(data.generated_at))}</span><span>Schema ${escapeHtml(data.schema_version||"")}</span><span>Methodology ${escapeHtml(data.methodology_version||"")}</span>`;
    const sections=(data.sections||[]).map(item=>`<section class="briefing-section"><h3>${escapeHtml(item.heading||"Section")}</h3>${item.text?`<p>${escapeHtml(item.text)}</p>`:""}${item.item_count!=null?`<span>${escapeHtml(item.item_count)} record${Number(item.item_count)===1?"":"s"}</span>`:""}</section>`).join("");
    const evidence=data.evidence||{};const records=[];["indicators","trends","events","layers","thematic_items"].forEach(group=>(evidence[group]||[]).slice(0,24).forEach(item=>records.push(briefingRecordMarkup(item,group))));
    const gaps=(data.missing_data||[]).length?`<section class="briefing-section"><h3>Explicit data gaps</h3><ul>${data.missing_data.slice(0,18).map(item=>`<li>${escapeHtml(item.label||item.id||item.record_type||"Record")}: ${escapeHtml(item.reason||item.compatibility||"Unavailable or methodologically constrained")}</li>`).join("")}</ul></section>`:"";
    const methods=`<section class="briefing-section"><h3>Methodology and interpretation limits</h3><ul>${[...(data.methodology_notes||[]),...(data.interpretation_limits||[])].map(item=>`<li>${escapeHtml(item)}</li>`).join("")}</ul></section>`;
    qs("#briefingDocumentBody").innerHTML=`<div class="briefing-section-grid">${sections}</div>${records.length?`<div class="briefing-record-grid">${records.join("")}</div>`:'<div class="empty-state"><div><strong>No evidence records returned</strong><span>The brief still preserves the selected scope and data state.</span></div></div>'}${gaps}${methods}`;
    qs("#briefingSourceList").innerHTML=(data.source_records||[]).length?(data.source_records||[]).map(item=>`<article><strong>${escapeHtml(item.name||"Source")}</strong><span>${escapeHtml((item.data_states||[]).join(" · ")||"state unavailable")}</span>${item.url?`<a href="${escapeHtml(item.url)}" target="_blank" rel="noopener">${escapeHtml(item.url)}</a>`:""}</article>`).join(""):'<p>No linked source record was returned for this brief.</p>';
    qs("#briefingBoundary").textContent=data.responsible_use||"Verify consequential findings against cited authoritative sources.";
    qs("#briefingStatus").textContent=`Brief generated · ${briefingEvidenceCount(data)} evidence records · ${(data.source_records||[]).length} sources`;
    syncBriefingUrl();reportHeight();
  }
  async function loadBriefing(){
    if(briefingState.controller)briefingState.controller.abort();const controller=new AbortController();briefingState.controller=controller;const sequence=++briefingState.sequence;
    qs("#briefingStudio").setAttribute("aria-busy","true");qs("#briefingStatus").textContent="Generating deterministic source-aware brief…";qs("#briefingDocumentBody").innerHTML='<div class="loading-block">Collecting available public evidence, sources, data states, and interpretation limits…</div>';
    try{const data=await apiWithRetry(`/public/briefing-studio/brief?${briefingParams().toString()}`,2,{signal:controller.signal,timeout:30000});if(controller.signal.aborted||sequence!==briefingState.sequence)return;renderBriefing(data)}
    catch(error){if(error?.name==="AbortError")return;qs("#briefingStatus").textContent="Brief generation unavailable";qs("#briefingDocumentBody").innerHTML=publicErrorBlock("Brief unavailable","The selected public evidence services did not complete the brief.",loadBriefing)}
    finally{if(sequence===briefingState.sequence)qs("#briefingStudio").setAttribute("aria-busy","false")}
  }
  async function downloadBriefing(format){
    if(format==="png"){await downloadBriefingPng();return}
    const url=`${API}/public/briefing-studio/export?${briefingParams(format).toString()}`;const response=await fetch(url,{headers:{Accept:"*/*"}});if(!response.ok){toast("Brief export unavailable");return}const blob=await response.blob();const disposition=response.headers.get("content-disposition")||"";const match=disposition.match(/filename="([^"]+)"/);const name=match?.[1]||`site-intelligence-brief.${format}`;const link=document.createElement("a");link.href=URL.createObjectURL(blob);link.download=name;document.body.appendChild(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(link.href),5000)
  }
  async function downloadBriefingPng(){
    if(!briefingState.data){toast("Generate a brief before capturing it");return}
    if(typeof html2canvas!=="function"){toast("PNG capture is unavailable in this browser");return}
    qs("#briefingStatus").textContent="Rendering PNG capture…";const canvas=await html2canvas(qs("#briefingCapture"),{backgroundColor:"#080c12",scale:Math.min(2,window.devicePixelRatio||1),useCORS:true});const link=document.createElement("a");link.download=`site-intelligence-${briefingState.data.brief_type}-${briefingState.data.brief_id}.png`;link.href=canvas.toDataURL("image/png");link.click();qs("#briefingStatus").textContent="PNG capture downloaded · verify linked sources in the evidence manifest."
  }
  async function openBriefingStudio(){
    qs("#briefingStudio").hidden=false;await prepareBriefingStudio();const params=new URLSearchParams(location.search);const requested=params.get("briefType")||params.get("type");if(["country","comparison","event","earth","thematic"].includes(requested))qs("#briefingType").value=requested;
    const codes=new Set(globalCountryState.catalog.map(item=>item.code));const country=params.get("country");const compare=params.get("compare");qs("#briefingCountry").value=codes.has(country)?country:(codes.has(state.country)?state.country:"KEN");qs("#briefingCompare").value=codes.has(compare)?compare:"GHA";
    if(params.get("days"))qs("#briefingDays").value=params.get("days");if(params.get("dashboard_id"))qs("#briefingDashboard").value=params.get("dashboard_id");if(params.get("event_id"))qs("#briefingEventId").value=params.get("event_id");if(params.get("layer_id"))qs("#briefingLayer").value=params.get("layer_id");if(params.get("date_a"))qs("#briefingDateA").value=params.get("date_a");if(params.get("date_b"))qs("#briefingDateB").value=params.get("date_b");updateBriefingFields();await loadBriefing()
  }
  function closeBriefingStudio(){qs("#briefingStudio").hidden=true;if(briefingState.controller)briefingState.controller.abort()}

  const sourceStudioState={data:null,methods:null,diagnostics:null,controller:null,sequence:0,activeSource:null};
  function sourceFilterParams(){
    const params=new URLSearchParams();
    const query=qs("#sourceSearch").value.trim(),domain=qs("#sourceDomain").value,stateValue=qs("#sourceState").value,feature=qs("#sourceFeature").value;
    if(query)params.set("query",query);if(domain)params.set("domain",domain);if(stateValue)params.set("state",stateValue);if(feature)params.set("feature",feature);
    params.set("include_health","false");return params;
  }
  function syncSourceUrl(){
    const params=sourceFilterParams();params.delete("include_health");params.set("view","sources");
    if(sourceStudioState.activeSource)params.set("source",sourceStudioState.activeSource);
    history.replaceState(null,"",`?${params.toString()}`);
  }
  function sourceStateClass(value){return String(value||"temporarily-unavailable").replace(/[^a-z0-9-]+/g,"-")}
  function populateSourceFilters(data){
    const domain=qs("#sourceDomain"),feature=qs("#sourceFeature"),stateSelect=qs("#sourceState");
    const selectedDomain=domain.value,selectedFeature=feature.value,selectedState=stateSelect.value;
    domain.innerHTML='<option value="">All domains</option>'+((data.domains||[]).map(item=>`<option value="${escapeHtml(item)}">${escapeHtml(item.replaceAll("-"," "))}</option>`).join(""));
    feature.innerHTML='<option value="">All features</option>'+((data.features||[]).map(item=>`<option value="${escapeHtml(item)}">${escapeHtml(item.replaceAll("-"," "))}</option>`).join(""));
    stateSelect.innerHTML='<option value="">All states</option>'+Object.entries(data.states||{}).map(([id,item])=>`<option value="${escapeHtml(id)}">${escapeHtml(item.label||id)}</option>`).join("");
    domain.value=selectedDomain;feature.value=selectedFeature;stateSelect.value=selectedState;
  }
  function renderSourceRegistry(data){
    const records=data.sources||[];qs("#sourceCountMetric").textContent=data.total_registered??records.length;
    const filters=[qs("#sourceSearch").value.trim(),qs("#sourceDomain").value,qs("#sourceState").value,qs("#sourceFeature").value].filter(Boolean).length;qs("#sourceFilterMetric").textContent=filters;
    qs("#sourceRegistryList").innerHTML=records.length?records.map(item=>`<button class="source-record-card ${item.id===sourceStudioState.activeSource?"active":""}" type="button" data-source-record="${escapeHtml(item.id)}"><span class="source-record-state ${sourceStateClass(item.state)}">${escapeHtml(item.state_label||item.state)}</span><strong>${escapeHtml(item.name)}</strong><small>${escapeHtml(item.publisher)}</small><p>${escapeHtml(item.public_notes||item.connector)}</p><span>${escapeHtml((item.domains||[]).slice(0,3).join(" · "))}</span></button>`).join(""):'<div class="empty-state"><div><strong>No matching sources</strong><span>Change the search, domain, state, or feature filter.</span></div></div>';
    qsa("[data-source-record]").forEach(button=>button.addEventListener("click",()=>selectSourceRecord(button.dataset.sourceRecord,true)));
  }
  function sourceMethodRecords(source){
    const ids=new Set(source?.methodology_ids||[]);return (sourceStudioState.methods?.methods||[]).filter(item=>ids.has(item.id));
  }
  function renderSourceDetail(source){
    if(!source){qs("#sourceDetailTitle").textContent="Choose a source";qs("#sourceDetailBody").innerHTML='<div class="empty-state"><div><strong>No source selected</strong><span>Select a source from the registry.</span></div></div>';return}
    qs("#sourceDetailTitle").textContent=source.name;
    const methods=sourceMethodRecords(source);
    const fields=[
      ["Publisher",source.publisher],["Public state",source.state_label||source.state],["Connector",source.connector],["Update frequency",source.update_frequency],["Geographic coverage",source.geographic_coverage],["Temporal coverage",source.temporal_coverage],["License",source.license]
    ];
    qs("#sourceDetailBody").innerHTML=`<div class="source-detail-meta">${fields.map(([label,value])=>`<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value||"Not documented")}</strong></div>`).join("")}</div><div class="source-detail-section"><h4>Data types</h4><div class="source-chip-list">${(source.data_types||[]).map(item=>`<span>${escapeHtml(item)}</span>`).join("")}</div></div><div class="source-detail-section"><h4>Features using this source</h4><div class="source-chip-list">${(source.features||[]).map(item=>`<span>${escapeHtml(item.replaceAll("-"," "))}</span>`).join("")}</div></div><div class="source-detail-section"><h4>Known limitations</h4><ul>${(source.known_limits||[]).map(item=>`<li>${escapeHtml(item)}</li>`).join("")}</ul></div><div class="source-detail-section"><h4>Related methodology</h4>${methods.length?`<ul>${methods.map(item=>`<li><button type="button" class="source-method-link" data-source-method="${escapeHtml(item.id)}">${escapeHtml(item.title)}</button></li>`).join("")}</ul>`:"<p>No linked method record.</p>"}</div><a class="source-official-link" href="${escapeHtml(source.official_url)}" target="_blank" rel="noopener">Open authoritative source ↗</a>`;
    qsa("[data-source-method]").forEach(button=>button.addEventListener("click",()=>{document.getElementById(`method-${button.dataset.sourceMethod}`)?.scrollIntoView({behavior:"smooth",block:"center"})}));
  }
  function selectSourceRecord(sourceId,sync=false){
    const source=(sourceStudioState.data?.sources||[]).find(item=>item.id===sourceId)||null;sourceStudioState.activeSource=source?.id||null;renderSourceRegistry(sourceStudioState.data||{sources:[]});renderSourceDetail(source);if(sync)syncSourceUrl();
  }
  function renderMethodology(data){
    qs("#methodCountMetric").textContent=data.total_registered??(data.methods||[]).length;
    qs("#methodologyRegistryList").innerHTML=(data.methods||[]).map(item=>`<details id="method-${escapeHtml(item.id)}" class="methodology-record"><summary><span>${escapeHtml(item.title)}</span><small>${escapeHtml((item.applies_to||[]).join(" · "))}</small></summary><p>${escapeHtml(item.summary)}</p><h4>Rules</h4><ul>${(item.rules||[]).map(rule=>`<li>${escapeHtml(rule)}</li>`).join("")}</ul><h4>Known limits</h4><ul>${(item.limitations||[]).map(rule=>`<li>${escapeHtml(rule)}</li>`).join("")}</ul><div class="source-chip-list">${(item.source_ids||[]).map(sourceId=>`<button type="button" data-method-source="${escapeHtml(sourceId)}">${escapeHtml(sourceId)}</button>`).join("")}</div></details>`).join("");
    qsa("[data-method-source]").forEach(button=>button.addEventListener("click",()=>selectSourceRecord(button.dataset.methodSource,true)));
  }
  async function refreshSourceDiagnostics(sequence,controller){
    try{
      const data=await apiWithRetry("/public/source-methodology/diagnostics",1,{signal:controller.signal,timeout:30000});
      if(controller.signal.aborted||sequence!==sourceStudioState.sequence)return;
      sourceStudioState.diagnostics=data;qs("#sourceIssueMetric").textContent=data.issues?.length||0;
      qs("#sourceStatus").textContent=`${sourceStudioState.data?.count||0} matching sources · ${sourceStudioState.methods?.total_registered||0} documented methods · ${data.issues?.length||0} diagnostic issues`;
      reportHeight();
    }catch(error){
      if(error?.name==="AbortError")return;qs("#sourceIssueMetric").textContent="—";qs("#sourceStatus").textContent=`${sourceStudioState.data?.count||0} matching sources · ${sourceStudioState.methods?.total_registered||0} documented methods · connector diagnostics temporarily unavailable`;
    }
  }
  async function loadSourceStudio(pushState=false){
    if(sourceStudioState.controller)sourceStudioState.controller.abort();const controller=new AbortController();sourceStudioState.controller=controller;const sequence=++sourceStudioState.sequence;
    qs("#sourceStudio").setAttribute("aria-busy","true");qs("#sourceStatus").textContent="Loading public source and methodology records…";qs("#sourceRegistryList").innerHTML='<div class="loading-block">Loading source records…</div>';
    const params=sourceFilterParams();
    try{
      const [sourcesResult,methodsResult]=await Promise.allSettled([
        apiWithRetry(`/public/sources?${params.toString()}`,2,{signal:controller.signal,timeout:18000}),
        apiWithRetry("/public/methodology",2,{signal:controller.signal,timeout:12000})
      ]);
      if(controller.signal.aborted||sequence!==sourceStudioState.sequence)return;
      if(sourcesResult.status!=="fulfilled")throw sourcesResult.reason;
      sourceStudioState.data=sourcesResult.value;sourceStudioState.methods=methodsResult.status==="fulfilled"?methodsResult.value:{methods:[],total_registered:0};sourceStudioState.diagnostics=null;
      populateSourceFilters(sourceStudioState.data);renderMethodology(sourceStudioState.methods);qs("#sourceIssueMetric").textContent="…";
      const requested=new URLSearchParams(location.search).get("source");const first=sourceStudioState.data.sources?.[0]?.id;const requestedAvailable=(sourceStudioState.data.sources||[]).some(item=>item.id===requested);sourceStudioState.activeSource=requestedAvailable?requested:first||null;if(requested&&!requestedAvailable)toast("Requested source record is unavailable; showing an available source instead.");renderSourceRegistry(sourceStudioState.data);renderSourceDetail((sourceStudioState.data.sources||[]).find(item=>item.id===sourceStudioState.activeSource));
      qs("#sourceStatus").textContent=`${sourceStudioState.data.count} matching sources · ${sourceStudioState.methods.total_registered||0} documented methods · checking connector diagnostics…`;
      if(pushState)syncSourceUrl();reportHeight();void refreshSourceDiagnostics(sequence,controller);
    }catch(error){if(error?.name==="AbortError")return;qs("#sourceStatus").textContent="Source registry unavailable";qs("#sourceRegistryList").innerHTML=publicErrorBlock("Source registry unavailable","The public source and methodology service did not complete.",()=>loadSourceStudio(false))}
    finally{if(sequence===sourceStudioState.sequence)qs("#sourceStudio").setAttribute("aria-busy","false")}
  }
  async function openSourceStudio(){
    qs("#sourceStudio").hidden=false;const params=new URLSearchParams(location.search);qs("#sourceSearch").value=params.get("query")||"";await loadSourceStudio(false);qs("#sourceDomain").value=params.get("domain")||"";qs("#sourceState").value=params.get("state")||"";qs("#sourceFeature").value=params.get("feature")||"";if(params.get("domain")||params.get("state")||params.get("feature"))await loadSourceStudio(false)
  }
  function closeSourceStudio(){qs("#sourceStudio").hidden=true;if(sourceStudioState.controller)sourceStudioState.controller.abort()}
  async function downloadSourceRegistry(format){
    const response=await fetch(`${API}/public/source-methodology/export?format=${encodeURIComponent(format)}&include_health=true`,{headers:{Accept:"*/*"}});if(!response.ok){toast("Source registry export unavailable");return}const blob=await response.blob();const disposition=response.headers.get("content-disposition")||"";const match=disposition.match(/filename="?([^";]+)"?/i);const link=document.createElement("a");link.href=URL.createObjectURL(blob);link.download=match?.[1]||`site-intelligence-sources.${format}`;document.body.appendChild(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(link.href),5000);toast("Source registry export downloaded")
  }



  const savedViewsState={items:[],storageAvailable:true,pendingManifest:null};
  const savedViewDefinitions={
    global:{label:"Global Conditions",keys:["domain","observed","mapLat","mapLng","mapZoom"]},
    economics:{label:"Economics and Sustainability",keys:["family","source_id","geography_code","indicator_code","frequency","query","mapLat","mapLng","mapZoom"]},
    law:{label:"International Law and Governance",keys:["lawAuthority","lawType","lawBody","lawCountry","lawSubject","lawQuery","mapLat","mapLng","mapZoom"]},
    science:{label:"Scientific and Earth Systems",keys:["scienceFamily","scienceType","scienceDiscipline","scienceSource","scienceMission","scienceQuery","scienceSeries","scienceFormat","mapLat","mapLng","mapZoom"]},
    humanitarian:{label:"Humanitarian, Conflict, and Displacement",keys:["country","category","source_id","query","days","mapLat","mapLng","mapZoom"]},
    resources:{label:"Trade, Energy, and Resource Security",keys:["family","source_id","geography_code","counterpart_code","indicator_code","query","mapLat","mapLng","mapZoom"]},
    dossiers:{label:"Unified Country and Regional Dossiers",keys:["dossierMode","country","compare","region","mapLat","mapLng","mapZoom"]},
    alerts:{label:"Alerts, Monitoring, and Live Streams",keys:["alertFamily","alertCountry","alertSource","alertFreshness","alertQuery"]},
    scenarios:{label:"Comparative Intelligence and Scenario Studio",keys:["scenarioGeographies","scenarioIndicators","scenarioDomain","scenarioStart","scenarioEnd"]},
    research:{label:"Research Paths and Investigations",keys:[]},
    platform:{label:"Connected Public Intelligence",keys:["q","record_type"]},
    observatory:{label:"Auditable Public Observatory",keys:[]},
    overview:{label:"Overview",keys:["country","imageryLayer","imageryDate","mapLat","mapLng","mapZoom"]},
    earth:{label:"Earth Observation",keys:["earthLayer","dateA","dateB","opacity","swipe","mapLat","mapLng","mapZoom"]},
    spatial:{label:"Spatial Evidence",keys:["spatialArea","spatialDataset"]},
    harmonization:{label:"Comparable Series",keys:["harmLeft","harmRight"]},
    country:{label:"Country Intelligence",keys:["country","trend","mapLat","mapLng","mapZoom"]},
    events:{label:"Live Event Intelligence",keys:["eventDays","eventCategory","eventSource","eventCountry","mapLat","mapLng","mapZoom"]},
    compare:{label:"Comparative Intelligence",keys:["country","compare","compareView","indicator","trend","mapLat","mapLng","mapZoom"]},
    thematic:{label:"Thematic Intelligence",keys:["dashboard","country","thematicDays","thematicLayer","thematicTrend","mapLat","mapLng","mapZoom"]},
    briefing:{label:"Public Briefing Studio",keys:["briefType","type","country","compare","days","event_id","dashboard_id","layer_id","date_a","date_b","latitude","longitude","zoom","opacity"]},
    federation:{label:"Institutional Data Exchange",keys:[]},
    governance:{label:"Production Governance",keys:[]},
    sources:{label:"Source and Methodology Studio",keys:["source","domain","state","feature","query"]}
  };
  const sensitiveSavedKey=/(api[_-]?key|password|secret|token|authorization|cookie|session|private[_-]?url|stack[_-]?trace|environment|diagnostics)/i;
  function savedViewId(){return `sv-${globalThis.crypto?.randomUUID?.()||`${Date.now()}-${Math.random().toString(36).slice(2)}`}`}
  function savedIso(){return new Date().toISOString()}
  function copyPublicText(value,message){
    const fallback=()=>{const area=document.createElement("textarea");area.value=value;area.setAttribute("readonly","");area.style.position="fixed";area.style.opacity="0";document.body.appendChild(area);area.select();document.execCommand("copy");area.remove()};
    return (navigator.clipboard?.writeText?navigator.clipboard.writeText(value).catch(fallback):Promise.resolve(fallback())).then(()=>toast(message));
  }
  function activeSavedMap(route){
    if(route==="global")return window.SCGlobalConditionsV210?.status?.().map||null;
    if(route==="economics")return window.SCEconomicsV220?.status?.().map||null;
    if(route==="law")return window.SCLawV230?.status?.().map||null;
    if(route==="science")return window.SCScienceV240?.status?.().map||null;
    if(route==="humanitarian")return window.SCHumanitarianV250?.status?.().map||null;
    if(route==="resources")return window.SCResourcesV260?.status?.().map||null;
    if(route==="dossiers")return window.SCDossiersV270?.status?.().map||null;
    if(route==="alerts")return null;
    if(route==="scenarios")return null;
    if(route==="overview")return state.map;
    if(route==="earth")return earthState.mapA;
    if(route==="country")return globalCountryState.overviewMap;
    if(route==="events")return eventState.map;
    if(route==="compare")return compareState.map;
    if(route==="thematic")return thematicState.map;
    return null;
  }
  function addSavedViewport(route,viewState){
    const map=activeSavedMap(route);if(!map?.getCenter)return viewState;
    const center=map.getCenter(),zoom=map.getZoom();
    if(Number.isFinite(center?.lat)&&Number.isFinite(center?.lng)){viewState.mapLat=String(Number(center.lat.toFixed(6)));viewState.mapLng=String(Number(center.lng.toFixed(6)));viewState.mapZoom=String(zoom)}
    return viewState;
  }
  function currentSavedState(){
    const route=state.route;if(!savedViewDefinitions[route])return null;
    let values={};
    if(route==="global")values={domain:qs("#gcDomain")?.value||"",observed:qs("#gcObservedAfter")?.value||""};
    if(route==="economics")values={family:qs("#economicsFamily")?.value||"",source_id:qs("#economicsSource")?.value||"",geography_code:qs("#economicsCountry")?.value||"",indicator_code:qs("#economicsIndicator")?.value||"",frequency:qs("#economicsFrequency")?.value||"",query:qs("#economicsSearch")?.value?.trim?.()||""};
    if(route==="law")values={lawAuthority:qs("#lawAuthority")?.value||"",lawType:qs("#lawType")?.value||"",lawBody:qs("#lawBody")?.value||"",lawCountry:qs("#lawCountry")?.value||"",lawSubject:qs("#lawSubject")?.value||"",lawQuery:qs("#lawSearch")?.value?.trim?.()||""};
    if(route==="science")values={scienceFamily:qs("#scienceFamily")?.value||"",scienceType:qs("#scienceType")?.value||"",scienceDiscipline:qs("#scienceDiscipline")?.value||"",scienceSource:qs("#scienceSource")?.value||"",scienceMission:qs("#scienceMission")?.value||"",scienceQuery:qs("#scienceSearch")?.value?.trim?.()||"",scienceSeries:qs("#scienceSeriesSelect")?.value||"",scienceFormat:qs("#scienceAssetFormat")?.value||""};
    if(route==="humanitarian")values={country:qs("#humanitarianCountry")?.value||"",category:qs("#humanitarianCategory")?.value||"",source_id:qs("#humanitarianSource")?.value||"",query:qs("#humanitarianSearch")?.value?.trim?.()||"",days:qs("#humanitarianDays")?.value||"30"};
    if(route==="resources")values={family:qs("#resourceFamily")?.value||"",source_id:qs("#resourceSource")?.value||"",geography_code:qs("#resourceCountry")?.value||"",counterpart_code:qs("#resourceCounterpart")?.value||"",indicator_code:qs("#resourceIndicator")?.value||"",query:qs("#resourceSearch")?.value?.trim?.()||""};
    if(route==="dossiers")values={dossierMode:qs("#dossierMode")?.value||"country",country:qs("#dossierCountry")?.value||"",compare:qs("#dossierCompare")?.value||"",region:qs("#dossierRegion")?.value||""};
    if(route==="alerts")values={alertFamily:qs("#alertsFamily")?.value||"",alertCountry:qs("#alertsCountry")?.value||"",alertSource:qs("#alertsSource")?.value||"",alertFreshness:qs("#alertsFreshness")?.value||"",alertQuery:qs("#alertsQuery")?.value?.trim?.()||""};
    if(route==="scenarios")values={scenarioGeographies:qs("#scenarioGeographies")?.value||"",scenarioIndicators:qs("#scenarioIndicators")?.value||"",scenarioDomain:qs("#scenarioDomain")?.value||"",scenarioStart:qs("#scenarioStart")?.value||"",scenarioEnd:qs("#scenarioEnd")?.value||""};
    if(route==="overview")values={country:state.country,imageryLayer:qs(".layer-tab.active")?.dataset.layer||"true-color",imageryDate:qs("#dateSelect").value};
    if(route==="earth")values={earthLayer:qs("#earthLayerSelect").value,dateA:qs("#earthDateA").value,dateB:qs("#earthDateB").value,opacity:qs("#earthOpacity").value,swipe:qs("#earthSwipe").value};
    if(route==="spatial")values={spatialArea:qs("#spatialAreaSelect")?.value||"",spatialDataset:qs("#spatialDatasetSelect")?.value||""};
    if(route==="country")values={country:globalCountryState.activeCode||state.country,trend:qs("#globalTrendSelect").value};
    if(route==="events")values={eventDays:qs("#eventDays").value,eventCategory:qs("#eventCategory").value,eventSource:qs("#eventSource").value,eventCountry:qs("#eventCountry").value.trim().toUpperCase()};
    if(route==="compare")values={country:qs("#compareCountryA").value,compare:qs("#compareCountryB").value,compareView:compareState.activeView,indicator:qs("#compareIndicatorFilter").value,trend:qs("#compareTrendSelect").value};
    if(route==="thematic")values={dashboard:qs("#thematicDashboard").value,country:qs("#thematicCountry").value,thematicDays:qs("#thematicDays").value,thematicLayer:qs("#thematicLayer").value,thematicTrend:qs("#thematicTrendSelect").value};
    if(route==="briefing")values=Object.fromEntries(briefingParams().entries());
    if(route==="sources")values={source:sourceStudioState.activeSource||"",domain:qs("#sourceDomain").value,state:qs("#sourceState").value,feature:qs("#sourceFeature").value,query:qs("#sourceSearch").value.trim()};
    const allowed=new Set(savedViewDefinitions[route].keys);const clean={};
    Object.entries(values).forEach(([key,value])=>{if(allowed.has(key)&&value!==null&&value!==undefined&&String(value)!==""&&!sensitiveSavedKey.test(key))clean[key]=String(value)});
    return addSavedViewport(route,clean);
  }
  function suggestedSavedName(route,viewState){
    const label=savedViewDefinitions[route]?.label||"Site Intelligence";
    const country=viewState.country||viewState.eventCountry;
    const focus=viewState.dashboard||viewState.source||viewState.earthLayer||viewState.briefType;
    return [country,focus,label].filter(Boolean).join(" · ").replaceAll("-"," ");
  }
  function buildSavedManifest(name){
    const view=state.route,stateValue=currentSavedState();if(!stateValue)return null;
    const now=savedIso();return {schema:SAVED_VIEW_SCHEMA,application_version:APP_VERSION,id:savedViewId(),name:String(name||"").trim().slice(0,120),view,state:stateValue,created_at:now,updated_at:now};
  }
  function sanitizeLocalManifest(manifest){
    if(!manifest||typeof manifest!=="object"||Array.isArray(manifest))return null;
    if(manifest.schema!==SAVED_VIEW_SCHEMA||!savedViewDefinitions[manifest.view]||typeof manifest.state!=="object"||Array.isArray(manifest.state))return null;
    if(!manifest.name||String(manifest.name).length>120)return null;
    const allowed=new Set(savedViewDefinitions[manifest.view].keys),cleanState={};
    for(const [key,value] of Object.entries(manifest.state)){if(sensitiveSavedKey.test(key))return null;if(allowed.has(key)&&["string","number"].includes(typeof value)&&String(value).length<=180)cleanState[key]=String(value)}
    return {schema:SAVED_VIEW_SCHEMA,application_version:String(manifest.application_version||APP_VERSION).slice(0,32),id:/^[A-Za-z0-9._:-]{6,128}$/.test(String(manifest.id||""))?String(manifest.id):savedViewId(),name:String(manifest.name).trim().slice(0,120),view:manifest.view,state:cleanState,created_at:String(manifest.created_at||savedIso()),updated_at:String(manifest.updated_at||manifest.created_at||savedIso())};
  }
  function storageMessage(text,stateValue="ready"){
    const el=qs("#savedStorageStatus");if(!el)return;el.className=`saved-storage-status ${stateValue}`;el.textContent=text;
  }
  function loadSavedViewsStorage(){
    try{
      const probe="__scsi_saved_view_probe__";localStorage.setItem(probe,"1");localStorage.removeItem(probe);
      const parsed=JSON.parse(localStorage.getItem(SAVED_VIEW_STORAGE_KEY)||"[]");const records=Array.isArray(parsed)?parsed:[];let rejected=0;const ids=new Set();
      savedViewsState.items=records.map(sanitizeLocalManifest).filter(item=>{if(!item){rejected+=1;return false}if(ids.has(item.id)){rejected+=1;return false}ids.add(item.id);return true}).slice(0,SAVED_VIEW_LIMIT);
      savedViewsState.storageAvailable=true;storageMessage(`${savedViewsState.items.length} local view${savedViewsState.items.length===1?"":"s"} available in this browser${rejected?` · ${rejected} invalid record${rejected===1?"":"s"} ignored`:""}.`);
    }catch(error){savedViewsState.items=[];savedViewsState.storageAvailable=false;storageMessage("Browser storage is unavailable. Shared links and JSON exports still work, but local saves are disabled.","error")}
    return savedViewsState.items;
  }
  function persistSavedViews(){
    if(!savedViewsState.storageAvailable)throw new Error("Browser storage is unavailable.");
    try{localStorage.setItem(SAVED_VIEW_STORAGE_KEY,JSON.stringify(savedViewsState.items.slice(0,SAVED_VIEW_LIMIT)))}catch(error){storageMessage("The browser could not store this view. Storage may be disabled or full.","error");throw error}
  }
  function uniqueSavedName(name,excludeId=""){
    const base=String(name||"Saved view").trim().slice(0,120)||"Saved view";const existing=new Set(savedViewsState.items.filter(item=>item.id!==excludeId).map(item=>item.name.toLowerCase()));if(!existing.has(base.toLowerCase()))return base;
    let index=2;while(existing.has(`${base} (${index})`.toLowerCase()))index+=1;return `${base} (${index})`.slice(0,120);
  }
  function savedViewUrl(manifest){
    const url=new URL(location.href);url.hash="";url.search="";url.searchParams.set("view",manifest.view);Object.entries(manifest.state||{}).forEach(([key,value])=>{if(savedViewDefinitions[manifest.view]?.keys.includes(key)&&!sensitiveSavedKey.test(key))url.searchParams.set(key,String(value))});return url.toString();
  }
  function savedStateSummary(manifest){
    const labels=[];const values=manifest.state||{};
    if(values.country)labels.push(values.country);if(values.compare)labels.push(`vs ${values.compare}`);if(values.dashboard)labels.push(values.dashboard.replaceAll("-"," "));if(values.source)labels.push(values.source.replaceAll("-"," "));if(values.earthLayer)labels.push(values.earthLayer.replaceAll("-"," "));if(values.eventDays)labels.push(`${values.eventDays} days`);return labels.join(" · ")||"Public view state";
  }
  function downloadSavedJson(payload,filename){const blob=new Blob([JSON.stringify(payload,null,2)+"\n"],{type:"application/json;charset=utf-8"});const link=document.createElement("a");link.href=URL.createObjectURL(blob);link.download=filename;document.body.appendChild(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(link.href),3000)}
  function renderSavedViews(){
    const list=qs("#savedViewsList");if(!list)return;qs("#savedViewCount").textContent=String(savedViewsState.items.length);
    if(!savedViewsState.items.length){list.innerHTML='<div class="empty-state"><div><strong>No locally saved views</strong><span>Open a public intelligence view and choose Save view. You can also import a validated JSON manifest.</span></div></div>';reportHeight();return}
    list.innerHTML=savedViewsState.items.map(item=>`<article class="saved-view-card" data-saved-id="${escapeHtml(item.id)}"><div class="saved-view-card-head"><div><span>${escapeHtml(savedViewDefinitions[item.view]?.label||item.view)}</span><h3>${escapeHtml(item.name)}</h3></div><small>${escapeHtml(cleanDate(item.updated_at||item.created_at))}</small></div><p>${escapeHtml(savedStateSummary(item))}</p><code>${escapeHtml(new URL(savedViewUrl(item)).search)}</code><div class="saved-view-card-actions"><button class="earth-primary-button" type="button" data-saved-action="open">Open</button><button class="ghost-button" type="button" data-saved-action="copy">Copy link</button><button class="ghost-button" type="button" data-saved-action="export">Export</button><button class="ghost-button" type="button" data-saved-action="rename">Rename</button><button class="ghost-button" type="button" data-saved-action="duplicate">Duplicate</button><button class="ghost-button danger-button" type="button" data-saved-action="delete">Delete</button></div></article>`).join("");
    qsa("[data-saved-id]").forEach(card=>card.addEventListener("click",event=>{const button=event.target.closest("[data-saved-action]");if(!button)return;const item=savedViewsState.items.find(record=>record.id===card.dataset.savedId);if(item)handleSavedAction(button.dataset.savedAction,item)}));reportHeight();
  }
  function handleSavedAction(action,item){
    if(action==="open"){location.assign(savedViewUrl(item));return}
    if(action==="copy"){copyPublicText(savedViewUrl(item),"Research path link copied");return}
    if(action==="export"){downloadSavedJson(item,`site-intelligence-saved-view-${item.id}.json`);return}
    if(action==="rename"){const proposed=prompt("Rename saved view",item.name);if(proposed&&proposed.trim()){item.name=uniqueSavedName(proposed,item.id);item.updated_at=savedIso();try{persistSavedViews();renderSavedViews();toast("Saved view renamed")}catch{}}return}
    if(action==="duplicate"){const copy=JSON.parse(JSON.stringify(item));copy.id=savedViewId();copy.name=uniqueSavedName(`${item.name} copy`);copy.created_at=savedIso();copy.updated_at=copy.created_at;savedViewsState.items.unshift(copy);try{persistSavedViews();renderSavedViews();toast("Saved view duplicated")}catch{}return}
    if(action==="delete"&&confirm(`Delete “${item.name}” from this browser?`)){savedViewsState.items=savedViewsState.items.filter(record=>record.id!==item.id);try{persistSavedViews();renderSavedViews();toast("Saved view deleted")}catch{}}
  }
  function saveCurrentManifest(name){
    const manifest=buildSavedManifest(uniqueSavedName(name));if(!manifest){toast("Open a research view before saving");return false}
    if(!manifest.name){toast("Enter a name for this view");return false}
    savedViewsState.items.unshift(manifest);savedViewsState.items=savedViewsState.items.slice(0,SAVED_VIEW_LIMIT);
    try{persistSavedViews();renderSavedViews();toast("View saved in this browser");return true}catch{savedViewsState.items=savedViewsState.items.filter(item=>item.id!==manifest.id);return false}
  }
  function openSaveViewDialog(){
    if(!savedViewDefinitions[state.route]){toast("Open a public research view before saving");return}
    const manifest=buildSavedManifest("Pending");const input=qs("#saveViewName");input.value=suggestedSavedName(manifest.view,manifest.state);qs("#saveViewDialogSummary").textContent=`${savedViewDefinitions[manifest.view].label} will be stored only in this browser.`;
    const dialog=qs("#saveViewDialog");if(typeof dialog.showModal==="function"){dialog.showModal();setTimeout(()=>input.select(),30)}else{const name=prompt("Name this saved view",input.value);if(name)saveCurrentManifest(name)}
  }
  async function validateImportedSavedManifest(candidate){
    const response=await fetch(`${API}/public/saved-views/validate`,{method:"POST",headers:{"Accept":"application/json","Content-Type":"application/json"},body:JSON.stringify(candidate)});
    if(!response.ok)throw new Error(String(response.status));return await response.json();
  }
  async function importSavedViewFile(file){
    const result=qs("#savedImportResult");if(!file)return;
    if(file.size>524288){result.textContent="Import rejected: the file exceeds the 512 KB collection limit.";result.className="saved-import-result error";return}
    let parsed;try{parsed=JSON.parse(await file.text())}catch{result.textContent="Import rejected: the file is not valid JSON.";result.className="saved-import-result error";return}
    const collection=parsed?.schema==="sc-saved-view-collection/1.0"&&Array.isArray(parsed.views);const candidates=collection?parsed.views.slice(0,SAVED_VIEW_LIMIT):[parsed];
    if(!candidates.length){result.textContent="Import rejected: the collection contains no saved views.";result.className="saved-import-result error";return}
    let imported=0,migrated=0;const errors=[];
    try{
      for(const candidate of candidates){
        const validation=await validateImportedSavedManifest(candidate);
        if(!validation.valid||!validation.manifest){errors.push((validation.errors||["manifest validation failed"])[0]);continue}
        const manifest=sanitizeLocalManifest(validation.manifest);if(!manifest){errors.push("Normalized manifest is unsupported by this application.");continue}
        if(savedViewsState.items.some(item=>item.id===manifest.id))manifest.id=savedViewId();manifest.name=uniqueSavedName(manifest.name);manifest.updated_at=savedIso();savedViewsState.items.unshift(manifest);imported+=1;if(validation.migrated_from)migrated+=1;
      }
      if(!imported){result.textContent=`Import rejected: ${errors[0]||"no valid saved views were found."}`;result.className="saved-import-result error";return}
      savedViewsState.items=savedViewsState.items.slice(0,SAVED_VIEW_LIMIT);persistSavedViews();renderSavedViews();result.textContent=`Imported ${imported} saved view${imported===1?"":"s"}${migrated?` · ${migrated} migrated to ${SAVED_VIEW_SCHEMA}`:""}${errors.length?` · ${errors.length} rejected`:""}.`;result.className="saved-import-result ready";toast(imported===1?"Saved view imported":"Saved views imported")
    }catch(error){result.textContent="Import validation is temporarily unavailable. No unvalidated file was stored.";result.className="saved-import-result error"}
  }
  function applySharedViewport(route,params){
    const lat=Number(params.get("mapLat")),lng=Number(params.get("mapLng")),zoom=Number(params.get("mapZoom"));if(!Number.isFinite(lat)||!Number.isFinite(lng)||!Number.isFinite(zoom)||Math.abs(lat)>90||Math.abs(lng)>180||zoom<0||zoom>20)return;
    const map=activeSavedMap(route);map?.setView?.([lat,lng],zoom);if(route==="earth")earthState.mapB?.setView?.([lat,lng],zoom)
  }
  function applySharedControlState(route,params){
    if(route==="country"&&params.get("trend")&&qs("#globalTrendSelect")?.querySelector(`option[value="${CSS.escape(params.get("trend"))}"]`)){qs("#globalTrendSelect").value=params.get("trend");const item=globalCountryState.trends.find(x=>x.key===params.get("trend"));if(item)renderGlobalTrend(item)}
    if(route==="thematic"&&params.get("thematicTrend")&&qs("#thematicTrendSelect")?.querySelector(`option[value="${CSS.escape(params.get("thematicTrend"))}"]`)){qs("#thematicTrendSelect").value=params.get("thematicTrend");renderThematicTrend((thematicState.data?.trends||[]).find(item=>item.id===params.get("thematicTrend"))||null)}
    applySharedViewport(route,params)
  }
  async function openSavedViews(){qs("#savedViewsStudio").hidden=false;qs("#saveViewButton").disabled=true;loadSavedViewsStorage();renderSavedViews()}
  function closeSavedViews(){const panel=qs("#savedViewsStudio");if(panel)panel.hidden=true;const button=qs("#saveViewButton");if(button)button.disabled=false}
  async function openPublicLaunchPortfolio(){
    const panel=qs("#publicLaunchPortfolio");if(!panel)return;panel.hidden=false;panel.setAttribute("aria-busy","true");document.body.classList.add("portfolio-route");qs("#saveViewButton").disabled=true;
    try{const payload=await apiWithRetry("/public/launch-profile",2);qs("#launchPortfolioVersion").textContent=`v${payload.application_version||APP_VERSION}`;qs("#launchWorkspaceCount").textContent=String((payload.workspaces||[]).length||9);qs("#launchPortfolioStatus").textContent=`Public launch profile loaded · ${(payload.workspaces||[]).length||9} research workspaces · ${payload.release_status||"public-release"}.`}
    catch{qs("#launchPortfolioStatus").textContent="The static portfolio is available. The optional launch-profile endpoint could not be refreshed."}
    finally{panel.setAttribute("aria-busy","false");reportHeight()}
  }
  function closePublicLaunchPortfolio(){const panel=qs("#publicLaunchPortfolio");if(panel)panel.hidden=true;document.body.classList.remove("portfolio-route");const button=qs("#saveViewButton");if(button)button.disabled=false}

  function renderObservatoryAuditCatalog(records){
    const target=qs("#observatoryAuditCatalog");if(!target)return;
    if(!records?.length){target.innerHTML='<div class="empty-state"><div><strong>No audit records are registered</strong><span>The public evidence ledger is temporarily unavailable.</span></div></div>';return}
    target.innerHTML=records.map(record=>`<article class="observatory-audit-card"><div class="saved-view-card-head"><div><span>${escapeHtml(record.artifact_type||"audit record")}</span><h3>${escapeHtml(record.title||record.artifact_id)}</h3></div><small>${escapeHtml(record.verification_level||"registered")}</small></div><p>${escapeHtml((record.limitations||[])[0]||"Public audit contract")}</p><div class="observatory-audit-meta"><span>${(record.source_ids||[]).length} sources</span><span>${(record.methodology_ids||[]).length} methods</span><a href="${escapeHtml(record.route||"/app/?view=observatory")}">Open workspace</a></div><code title="Full SHA-256 digest">${escapeHtml(record.integrity?.digest||"Digest unavailable")}</code></article>`).join("")
  }
  async function openAuditablePublicObservatory(){
    const panel=qs("#auditablePublicObservatory");if(!panel)return;panel.hidden=false;panel.setAttribute("aria-busy","true");document.body.classList.add("portfolio-route");qs("#saveViewButton").disabled=true;
    try{
      const [profile,catalog,lineage,verification,ledger]=await Promise.all([
        apiWithRetry("/public/observatory",2),apiWithRetry("/public/observatory/catalog",2),apiWithRetry("/public/observatory/lineage",2),apiWithRetry("/public/observatory/verification",2),apiWithRetry("/public/observatory/release-ledger",2)
      ]);
      qs("#observatoryVersion").textContent=`v${profile.application_version||APP_VERSION}`;qs("#observatoryRecordCount").textContent=String(profile.counts?.audit_artifacts??catalog.record_count??"—");qs("#observatorySourceCount").textContent=String(profile.counts?.registered_sources??"—");qs("#observatoryMethodCount").textContent=String(profile.counts?.methodology_records??"—");
      renderObservatoryAuditCatalog(catalog.records||[]);qs("#observatoryLineageSummary").textContent=`${lineage.nodes?.length||0} public nodes and ${lineage.edges?.length||0} documented lineage relationships are registered in the current release.`;qs("#observatoryVerificationSummary").textContent=`${verification.algorithm?.toUpperCase()||"SHA-256"} digests use ${verification.canonicalization||"canonical JSON"}. Submitted verification payloads are not persisted.`;qs("#observatoryReleaseLedger").innerHTML=(ledger.entries||[]).map(item=>`<div class="observatory-ledger-row"><strong>v${escapeHtml(item.version)}</strong><span>${escapeHtml(item.title)}</span><small>${escapeHtml(item.audit_contribution)}</small></div>`).join("");qs("#observatoryStatus").textContent=`Observatory profile loaded · ${profile.counts?.workspaces||10} workspaces · ${catalog.record_count||0} audit records · ${profile.release_status||"auditable-public-observatory"}.`;
    }catch{qs("#observatoryStatus").textContent="The static observatory workspace is available. One or more public audit endpoints could not be refreshed.";renderObservatoryAuditCatalog([])}
    finally{panel.setAttribute("aria-busy","false");reportHeight()}
  }
  function closeAuditablePublicObservatory(){const panel=qs("#auditablePublicObservatory");if(panel)panel.hidden=true;const button=qs("#saveViewButton");if(button)button.disabled=false}

  async function setRoute(route){
    qs("#main").classList.remove("route-enter");void qs("#main").offsetWidth;qs("#main").classList.add("route-enter");
    state.route=route;
    updateActiveNavigation(route);setMobileNavigation(false);
    const [e,t,d]=routeMeta(route);qs("#viewEyebrow").textContent=e;qs("#viewTitle").textContent=t;qs("#viewDescription").textContent=d;
    const panel=qs("#routePanel");
    if(route!=="global")window.SCGlobalConditionsV210?.close?.();
    if(route!=="economics")window.SCEconomicsV220?.close?.();
    if(route!=="law")window.SCLawV230?.close?.();
    if(route!=="science")window.SCScienceV240?.close?.();
    if(route!=="humanitarian")window.SCHumanitarianV250?.close?.();
    if(route!=="resources")window.SCResourcesV260?.close?.();
    if(route!=="dossiers")window.SCDossiersV270?.close?.();
    if(route!=="alerts")window.SCAlertsV280?.close?.();
    if(route!=="scenarios")window.SCScenariosV290?.close?.();
    if(route!=="research")window.SCResearchV2100?.close?.();
    if(route!=="integration")window.SCIntegrationV2110?.close?.();
    if(route!=="experience")window.SCExperienceV2120?.close?.();
    if(route!=="spatial")window.SCSpatialV2150?.close?.();
    if(route!=="harmonization")window.SCHarmonizationV2160?.close?.();
    if(route!=="models")window.SCModelsV2170?.close?.();
    if(route!=="evidence")window.SCEvidenceV2180?.close?.();
    if(route!=="graph")window.SCKnowledgeGraphV2190?.close?.();
    if(route!=="publishing")window.SCIntelligencePublishingV2200?.close?.();
    if(route!=="monitoring")window.SCScheduledMonitoringV2210?.close?.();
    if(route!=="workspaces")window.SCInstitutionalWorkspacesV2220?.close?.();
    if(route!=="workflows")window.SCCrossPlatformWorkflowsV2230?.close?.();
    if(route!=="federation")window.SCInstitutionalFederationV2240?.close?.();
    if(route!=="governance")window.SCProductionGovernanceV2250?.close?.();
    if(route!=="platform")window.SCConnectedPlatformV300?.close?.();
    if(route==="platform"){
      panel.hidden=true;qs("#countryIntelligencePanel").hidden=true;
      closeEarthStudio();closeEventStudio();closeGlobalCountryExplorer();closeCompareStudio();
      closeThematicStudio();closeBriefingStudio();closeSourceStudio();closeSavedViews();
      closePublicLaunchPortfolio();closeAuditablePublicObservatory();
      await window.SCConnectedPlatformV300?.open?.();return;
    }
    if(route==="global"){
      panel.hidden=true;qs("#countryIntelligencePanel").hidden=true;
      closeEarthStudio();closeEventStudio();closeGlobalCountryExplorer();closeCompareStudio();
      closeThematicStudio();closeBriefingStudio();closeSourceStudio();closeSavedViews();
      closePublicLaunchPortfolio();closeAuditablePublicObservatory();
      await window.SCGlobalConditionsV210?.open?.();return;
    }
    if(route==="economics"){
      panel.hidden=true;qs("#countryIntelligencePanel").hidden=true;
      closeEarthStudio();closeEventStudio();closeGlobalCountryExplorer();closeCompareStudio();
      closeThematicStudio();closeBriefingStudio();closeSourceStudio();closeSavedViews();
      closePublicLaunchPortfolio();closeAuditablePublicObservatory();
      await window.SCEconomicsV220?.open?.();return;
    }
    if(route==="law"){
      panel.hidden=true;qs("#countryIntelligencePanel").hidden=true;
      closeEarthStudio();closeEventStudio();closeGlobalCountryExplorer();closeCompareStudio();
      closeThematicStudio();closeBriefingStudio();closeSourceStudio();closeSavedViews();
      closePublicLaunchPortfolio();closeAuditablePublicObservatory();
      await window.SCLawV230?.open?.();return;
    }
    if(route==="science"){
      panel.hidden=true;qs("#countryIntelligencePanel").hidden=true;
      closeEarthStudio();closeEventStudio();closeGlobalCountryExplorer();closeCompareStudio();
      closeThematicStudio();closeBriefingStudio();closeSourceStudio();closeSavedViews();
      closePublicLaunchPortfolio();closeAuditablePublicObservatory();
      await window.SCScienceV240?.open?.();return;
    }
    if(route==="humanitarian"){
      panel.hidden=true;qs("#countryIntelligencePanel").hidden=true;
      closeEarthStudio();closeEventStudio();closeGlobalCountryExplorer();closeCompareStudio();
      closeThematicStudio();closeBriefingStudio();closeSourceStudio();closeSavedViews();
      closePublicLaunchPortfolio();closeAuditablePublicObservatory();
      await window.SCHumanitarianV250?.open?.();return;
    }
    if(route==="resources"){
      panel.hidden=true;qs("#countryIntelligencePanel").hidden=true;
      closeEarthStudio();closeEventStudio();closeGlobalCountryExplorer();closeCompareStudio();
      closeThematicStudio();closeBriefingStudio();closeSourceStudio();closeSavedViews();
      closePublicLaunchPortfolio();closeAuditablePublicObservatory();
      await window.SCResourcesV260?.open?.();return;
    }
    if(route==="dossiers"){
      panel.hidden=true;qs("#countryIntelligencePanel").hidden=true;
      closeEarthStudio();closeEventStudio();closeGlobalCountryExplorer();closeCompareStudio();
      closeThematicStudio();closeBriefingStudio();closeSourceStudio();closeSavedViews();
      closePublicLaunchPortfolio();closeAuditablePublicObservatory();
      await window.SCDossiersV270?.open?.();return;
    }
    if(route==="alerts"){
      panel.hidden=true;qs("#countryIntelligencePanel").hidden=true;
      closeEarthStudio();closeEventStudio();closeGlobalCountryExplorer();closeCompareStudio();
      closeThematicStudio();closeBriefingStudio();closeSourceStudio();closeSavedViews();
      closePublicLaunchPortfolio();closeAuditablePublicObservatory();
      await window.SCAlertsV280?.open?.();return;
    }
    if(route==="scenarios"){
      panel.hidden=true;qs("#countryIntelligencePanel").hidden=true;
      closeEarthStudio();closeEventStudio();closeGlobalCountryExplorer();closeCompareStudio();
      closeThematicStudio();closeBriefingStudio();closeSourceStudio();closeSavedViews();
      closePublicLaunchPortfolio();closeAuditablePublicObservatory();
      await window.SCScenariosV290?.open?.();return;
    }
    if(route==="research"){
      panel.hidden=true;qs("#countryIntelligencePanel").hidden=true;
      closeEarthStudio();closeEventStudio();closeGlobalCountryExplorer();closeCompareStudio();
      closeThematicStudio();closeBriefingStudio();closeSourceStudio();closeSavedViews();
      closePublicLaunchPortfolio();closeAuditablePublicObservatory();
      await window.SCResearchV2100?.open?.();return;
    }
    if(route==="integration"){
      panel.hidden=true;qs("#countryIntelligencePanel").hidden=true;
      closeEarthStudio();closeEventStudio();closeGlobalCountryExplorer();closeCompareStudio();
      closeThematicStudio();closeBriefingStudio();closeSourceStudio();closeSavedViews();
      closePublicLaunchPortfolio();closeAuditablePublicObservatory();
      await window.SCIntegrationV2110?.open?.();return;
    }
    if(route==="experience"){
      panel.hidden=true;qs("#countryIntelligencePanel").hidden=true;
      closeEarthStudio();closeEventStudio();closeGlobalCountryExplorer();closeCompareStudio();
      closeThematicStudio();closeBriefingStudio();closeSourceStudio();closeSavedViews();
      closePublicLaunchPortfolio();closeAuditablePublicObservatory();
      await window.SCExperienceV2120?.open?.();return;
    }
    if(route==="spatial"){
      panel.hidden=true;qs("#countryIntelligencePanel").hidden=true;
      closeEarthStudio();closeEventStudio();closeGlobalCountryExplorer();closeCompareStudio();
      closeThematicStudio();closeBriefingStudio();closeSourceStudio();closeSavedViews();
      closePublicLaunchPortfolio();closeAuditablePublicObservatory();
      await window.SCSpatialV2150?.open?.();return;
    }
    if(route==="harmonization"){
      panel.hidden=true;qs("#countryIntelligencePanel").hidden=true;
      closeEarthStudio();closeEventStudio();closeGlobalCountryExplorer();closeCompareStudio();
      closeThematicStudio();closeBriefingStudio();closeSourceStudio();closeSavedViews();
      closePublicLaunchPortfolio();closeAuditablePublicObservatory();
      await window.SCHarmonizationV2160?.open?.();return;
    }
    if(route==="models"){
      panel.hidden=true;qs("#countryIntelligencePanel").hidden=true;
      closeEarthStudio();closeEventStudio();closeGlobalCountryExplorer();closeCompareStudio();
      closeThematicStudio();closeBriefingStudio();closeSourceStudio();closeSavedViews();
      closePublicLaunchPortfolio();closeAuditablePublicObservatory();
      await window.SCModelsV2170?.open?.();return;
    }
    if(route==="evidence"){
      panel.hidden=true;qs("#countryIntelligencePanel").hidden=true;
      closeEarthStudio();closeEventStudio();closeGlobalCountryExplorer();closeCompareStudio();
      closeThematicStudio();closeBriefingStudio();closeSourceStudio();closeSavedViews();
      closePublicLaunchPortfolio();closeAuditablePublicObservatory();
      await window.SCEvidenceV2180?.open?.();return;
    }
    if(route==="publishing"){
      panel.hidden=true;qs("#countryIntelligencePanel").hidden=true;
      closeEarthStudio();closeEventStudio();closeGlobalCountryExplorer();closeCompareStudio();
      closeThematicStudio();closeBriefingStudio();closeSourceStudio();closeSavedViews();
      closePublicLaunchPortfolio();closeAuditablePublicObservatory();
      await window.SCIntelligencePublishingV2200?.open?.();return;
    }
    if(route==="monitoring"){
      panel.hidden=true;qs("#countryIntelligencePanel").hidden=true;
      closeEarthStudio();closeEventStudio();closeGlobalCountryExplorer();closeCompareStudio();
      closeThematicStudio();closeBriefingStudio();closeSourceStudio();closeSavedViews();
      closePublicLaunchPortfolio();closeAuditablePublicObservatory();
      await window.SCScheduledMonitoringV2210?.open?.();return;
    }
    if(route==="workflows"){
      panel.hidden=true;qs("#countryIntelligencePanel").hidden=true;
      closeEarthStudio();closeEventStudio();closeGlobalCountryExplorer();closeCompareStudio();
      closeThematicStudio();closeBriefingStudio();closeSourceStudio();closeSavedViews();
      closePublicLaunchPortfolio();closeAuditablePublicObservatory();
      await window.SCCrossPlatformWorkflowsV2230?.open?.();return;
    }
    if(route==="federation"){
      panel.hidden=true;qs("#countryIntelligencePanel").hidden=true;
      closeEarthStudio();closeEventStudio();closeGlobalCountryExplorer();closeCompareStudio();
      closeThematicStudio();closeBriefingStudio();closeSourceStudio();closeSavedViews();
      closePublicLaunchPortfolio();closeAuditablePublicObservatory();
      await window.SCInstitutionalFederationV2240?.open?.();return;
    }
    if(route==="governance"){
      panel.hidden=true;qs("#countryIntelligencePanel").hidden=true;
      closeEarthStudio();closeEventStudio();closeGlobalCountryExplorer();closeCompareStudio();
      closeThematicStudio();closeBriefingStudio();closeSourceStudio();closeSavedViews();
      closePublicLaunchPortfolio();closeAuditablePublicObservatory();
      await window.SCProductionGovernanceV2250?.open?.();return;
    }
    if(route==="workspaces"){
      panel.hidden=true;qs("#countryIntelligencePanel").hidden=true;
      closeEarthStudio();closeEventStudio();closeGlobalCountryExplorer();closeCompareStudio();
      closeThematicStudio();closeBriefingStudio();closeSourceStudio();closeSavedViews();
      closePublicLaunchPortfolio();closeAuditablePublicObservatory();
      await window.SCInstitutionalWorkspacesV2220?.open?.();return;
    }
    if(route==="graph"){
      panel.hidden=true;qs("#countryIntelligencePanel").hidden=true;
      closeEarthStudio();closeEventStudio();closeGlobalCountryExplorer();closeCompareStudio();
      closeThematicStudio();closeBriefingStudio();closeSourceStudio();closeSavedViews();
      closePublicLaunchPortfolio();closeAuditablePublicObservatory();
      await window.SCKnowledgeGraphV2190?.open?.();return;
    }
    if(route!=="launch")closePublicLaunchPortfolio();
    if(route!=="observatory")closeAuditablePublicObservatory();

    if(route==="observatory"){
      panel.hidden=true;qs("#countryIntelligencePanel").hidden=true;closeEarthStudio();closeEventStudio();closeGlobalCountryExplorer();closeCompareStudio();closeThematicStudio();closeBriefingStudio();closeSourceStudio();closeSavedViews();await openAuditablePublicObservatory();return;
    }
    if(route==="launch"){
      panel.hidden=true;qs("#countryIntelligencePanel").hidden=true;closeEarthStudio();closeEventStudio();closeGlobalCountryExplorer();closeCompareStudio();closeThematicStudio();closeBriefingStudio();closeSourceStudio();closeSavedViews();await openPublicLaunchPortfolio();return;
    }
    if(route==="overview"){
      panel.hidden=true;qs("#countryIntelligencePanel").hidden=true;closeEarthStudio();closeEventStudio();closeGlobalCountryExplorer();closeCompareStudio();closeThematicStudio();closeBriefingStudio();closeSourceStudio();closeSavedViews();return;
    }
    if(route==="earth"){
      panel.hidden=true;qs("#countryIntelligencePanel").hidden=true;closeEventStudio();closeGlobalCountryExplorer();closeCompareStudio();closeThematicStudio();closeBriefingStudio();closeSourceStudio();closeSavedViews();await openEarthStudio();return;
    }
    if(route==="events"){
      panel.hidden=true;qs("#countryIntelligencePanel").hidden=true;closeEarthStudio();closeGlobalCountryExplorer();closeCompareStudio();closeThematicStudio();closeBriefingStudio();closeSourceStudio();closeSavedViews();await openEventStudio();return;
    }
    if(route==="country"){
      panel.hidden=true;qs("#countryIntelligencePanel").hidden=true;closeEarthStudio();closeEventStudio();closeCompareStudio();closeThematicStudio();closeBriefingStudio();closeSourceStudio();closeSavedViews();await openGlobalCountryExplorer();return;
    }

    closeEarthStudio();closeEventStudio();closeGlobalCountryExplorer();closeCompareStudio();closeThematicStudio();closeBriefingStudio();closeSourceStudio();closeSavedViews();qs("#countryIntelligencePanel").hidden=true;
    panel.hidden=false;panel.innerHTML=`<div class="loading-block">Loading ${escapeHtml(route)} view…</div>`;
    if(route==="country-legacy"){
      qs("#countryIntelligencePanel").hidden=false;panel.hidden=true;await loadLiveCountry(state.country);return;
    }
    if(route==="events-legacy"){
      const rows=(state.events?.features||[]).slice(0,30);
      panel.innerHTML=`<p class="eyebrow">PUBLIC EVENT RECORDS</p><h2>Latest mapped events</h2><div class="event-list">${rows.map(f=>{const p=f.properties||{};return `<div class="event-row"><span class="event-marker"></span><div><div class="event-title">${escapeHtml(p.title||"Event")}</div><div class="event-meta">${escapeHtml(p.category||"Event")} · ${escapeHtml(p.source||"Source")}</div></div><div class="event-time">${cleanDate(p.observed_at)}</div></div>`}).join("")}</div>`;
    }else if(route==="compare"){
      panel.hidden=true;await openCompareStudio();return;
    }else if(route==="thematic"){
      panel.hidden=true;await openThematicStudio();return;
    }else if(route==="briefing"){
      panel.hidden=true;await openBriefingStudio();return;
    }else if(route==="sources"){
      panel.hidden=true;await openSourceStudio();return;
    }else if(route==="saved"){
      panel.hidden=true;await openSavedViews();return;
    }else{
      panel.innerHTML=`<p class="eyebrow">PUBLIC WORKSPACE</p><h2>View unavailable</h2><p>The requested public workspace is not registered.</p>`;
    }
  }
  async function init(){setLaunch("Preparing the map and public evidence services.",18);
    qs("#dateSelect").value=today();initMap();setLaunch("Loading map layers.",34);
    qsa(".layer-tab").forEach(b=>b.addEventListener("click",()=>setImagery(b.dataset.layer)));
    qsa(".nav-item").forEach(b=>b.addEventListener("click",()=>{history.replaceState(null,"",`?country=${encodeURIComponent(state.country)}&view=${encodeURIComponent(b.dataset.route)}`);setRoute(b.dataset.route)}));
    qs("#mobileNavToggle")?.addEventListener("click",()=>setMobileNavigation(!document.body.classList.contains("mobile-nav-open")));
    qs("#mobileNavBackdrop")?.addEventListener("click",()=>setMobileNavigation(false,{restoreFocus:true}));
    qsa("[data-route-link]").forEach(b=>b.addEventListener("click",()=>{const route=b.dataset.routeLink;history.replaceState(null,"",`?country=${encodeURIComponent(state.country)}&view=${encodeURIComponent(route)}`);setRoute(route)}));
    qs("#countrySelect").addEventListener("change",async e=>{state.country=e.target.value;if(state.route==="country"){await selectGlobalCountry(e.target.value,true)}else if(state.route==="thematic"){qs("#thematicCountry").value=e.target.value;await loadThematicDashboard(true)}else{await loadCountry(e.target.value);history.replaceState(null,"",`?country=${encodeURIComponent(e.target.value)}&view=${encodeURIComponent(state.route)}`)}});
    qs("#dateSelect").addEventListener("change",()=>setImagery(qs(".layer-tab.active").dataset.layer));
    qs("#eventsToggle").addEventListener("change",e=>e.target.checked?state.markers.addTo(state.map):state.map.removeLayer(state.markers));
    qs("#heatToggle").addEventListener("change",e=>toast(e.target.checked?"Density layer enabled for supported records":"Density layer hidden"));
    qs("#fullscreenButton").addEventListener("click",()=>{const p=qs(".map-panel");if(document.fullscreenElement)document.exitFullscreen();else p.requestFullscreen?.()});
    qs("#saveViewButton").addEventListener("click",openSaveViewDialog);qs("#shareButton").addEventListener("click",()=>copyPublicText(location.href,"View link copied"));qs("#openNewButton").addEventListener("click",()=>window.open(location.href,"_blank","noopener"));qs("#launchRetry").addEventListener("click",()=>location.reload());qs("#countrySearchButton").addEventListener("click",searchGlobalCountries);
    qs("#countrySearchInput").addEventListener("keydown",e=>{if(e.key==="Enter")searchGlobalCountries()});
    qs("#countrySearchInput").addEventListener("input",()=>{clearTimeout(globalCountryState.searchTimer);globalCountryState.searchTimer=setTimeout(searchGlobalCountries,320)});
    qs("#countryRegionFilter").addEventListener("change",searchGlobalCountries);
    qs("#globalTrendSelect").addEventListener("change",e=>{const item=globalCountryState.trends.find(x=>x.key===e.target.value);if(item){qs("#globalTrendTitle").textContent=item.label;renderGlobalTrend(item)}});
    qs("#countryShare").addEventListener("click",async()=>{await navigator.clipboard.writeText(location.href);toast("Country view link copied")});
    qs("#countryOpenEarth").addEventListener("click",()=>setRoute("earth"));
    qs("#countryOpenEvents").addEventListener("click",()=>{qs("#eventCountry").value=globalCountryState.activeCode;setRoute("events")});
    qs("#eventApply").addEventListener("click",()=>applyEventFilters(true));
    qs("#eventReset").addEventListener("click",async()=>{qs("#eventDays").value="14";qs("#eventCategory").value="";qs("#eventSource").value="";qs("#eventCountry").value="";await applyEventFilters(true)});
    qs("#eventShare").addEventListener("click",async()=>{await navigator.clipboard.writeText(location.href);toast("Event view link copied")});
    qs("#eventTimelinePlay").addEventListener("click",toggleEventTimeline);
    qs("#eventTimelineRange").addEventListener("input",e=>{stopEventTimeline();eventState.timelineIndex=Number(e.target.value);renderEventTimelineFrame()});
    qs("#closeEventDrawer").addEventListener("click",closeEventDrawer);
    qs("#eventDetailBackdrop").addEventListener("click",closeEventDrawer);
    qs("#earthSwipe").addEventListener("input",e=>{setEarthClip(e.target.value);e.target.setAttribute("aria-valuetext",`${e.target.value} percent`)});
    qs("#earthApply").addEventListener("click",async()=>{stopEarthPlayback();await applyEarthComparison(true);await loadEarthTimeline()});
    qs("#earthOpacity").addEventListener("input",e=>{stopEarthPlayback();earthState.opacity=Number(e.target.value)/100;if(earthState.layerA)earthState.layerA.setOpacity(earthState.opacity);if(earthState.layerB)earthState.layerB.setOpacity(earthState.opacity)});
    qs("#earthReset").addEventListener("click",async()=>{stopEarthPlayback();qs("#earthLayerSelect").value="true-color";qs("#earthDateA").value=earthDate(8);qs("#earthDateB").value=earthDate(1);qs("#earthOpacity").value="72";qs("#earthSwipe").value="50";setEarthClip(50);await applyEarthComparison(true);await loadEarthTimeline()});
    qs("#earthUnavailableRetry").addEventListener("click",()=>applyEarthComparison(false));
    qs("#earthLayerSelect").addEventListener("change",stopEarthPlayback);
    qs("#earthDateA").addEventListener("change",stopEarthPlayback);
    qs("#earthDateB").addEventListener("change",stopEarthPlayback);
    qs("#earthPlay").addEventListener("click",toggleEarthPlayback);
    qs("#earthTimelineRange").addEventListener("input",e=>{earthState.frameIndex=Number(e.target.value);updateEarthFrame()});
    qs("#earthShare").addEventListener("click",async()=>{await navigator.clipboard.writeText(location.href);toast("Earth view link copied")});
    qs("#earthExport").addEventListener("click",exportEarthPNG);
    qs("#earthPrint").addEventListener("click",()=>{document.body.classList.add("earth-print-mode");window.print();setTimeout(()=>document.body.classList.remove("earth-print-mode"),300)});
    qs("#earthDownloadManifest").addEventListener("click",downloadEarthManifest);
    qs("#compareApply").addEventListener("click",()=>loadComparison(true));
    qs("#compareReset").addEventListener("click",()=>{qs("#compareCountryA").value="KEN";qs("#compareCountryB").value="GHA";qs("#compareIndicatorFilter").value="";setCompareView("table",false);loadComparison(true)});
    qs("#compareSwap").addEventListener("click",()=>{const a=qs("#compareCountryA").value;qs("#compareCountryA").value=qs("#compareCountryB").value;qs("#compareCountryB").value=a;loadComparison(true)});
    qs("#compareCountryA").addEventListener("change",()=>{const {a,b}=compareSelection();const validation=validateCompareSelection(a,b);showCompareValidation(validation.ok?"":validation.message)});
    qs("#compareCountryB").addEventListener("change",()=>{const {a,b}=compareSelection();const validation=validateCompareSelection(a,b);showCompareValidation(validation.ok?"":validation.message)});
    qs("#compareShare").addEventListener("click",copyComparisonView);
    qs("#comparePrint").addEventListener("click",()=>{setCompareView("brief");setTimeout(()=>window.print(),120)});
    qs("#compareIndicatorFilter").addEventListener("change",()=>renderCompareRows(true));
    qs("#compareTrendSelect").addEventListener("change",e=>renderCompareTrend(compareState.trends.find(item=>item.id===e.target.value)||null,true));
    qsa(".compare-tab").forEach(button=>button.addEventListener("click",()=>setCompareView(button.dataset.compareView)));
    qsa("[data-compare-export]").forEach(button=>button.addEventListener("click",()=>downloadComparison(button.dataset.compareExport)));

    qs("#thematicApply").addEventListener("click",()=>loadThematicDashboard(true));
    qs("#thematicReset").addEventListener("click",()=>{qs("#thematicDashboard").value="climate-environment";qs("#thematicCountry").value="KEN";qs("#thematicDays").value="30";loadThematicDashboard(true)});
    qs("#thematicDashboard").addEventListener("change",()=>loadThematicDashboard(true));
    qs("#thematicCountry").addEventListener("change",()=>loadThematicDashboard(true));
    qs("#thematicDays").addEventListener("change",()=>loadThematicDashboard(true));
    qs("#thematicLayer").addEventListener("change",event=>{setThematicImagery(event.target.value);syncThematicUrl()});
    qs("#thematicTrendSelect").addEventListener("change",event=>renderThematicTrend((thematicState.data?.trends||[]).find(item=>item.id===event.target.value)||null));
    qs("#thematicShare").addEventListener("click",async()=>{syncThematicUrl();await navigator.clipboard.writeText(location.href);toast("Thematic dashboard link copied")});
    qs("#thematicPrint").addEventListener("click",()=>{document.body.classList.add("thematic-print-mode");window.print();setTimeout(()=>document.body.classList.remove("thematic-print-mode"),300)});
    qsa("[data-thematic-export]").forEach(button=>button.addEventListener("click",()=>downloadThematic(button.dataset.thematicExport)));
    qs("#thematicOpenBrief").addEventListener("click",()=>{const params=new URLSearchParams({view:"briefing",briefType:"thematic",type:"thematic",country:qs("#thematicCountry").value,dashboard_id:qs("#thematicDashboard").value});history.replaceState(null,"",`?${params.toString()}`);setRoute("briefing")});

    qs("#briefingType").addEventListener("change",updateBriefingFields);
    qs("#briefingApply").addEventListener("click",loadBriefing);
    qs("#briefingReset").addEventListener("click",()=>{qs("#briefingType").value="country";qs("#briefingCountry").value="KEN";qs("#briefingCompare").value="GHA";qs("#briefingDays").value="14";qs("#briefingEventId").value="";qs("#briefingDashboard").value="climate-environment";qs("#briefingLayer").value="true-color";qs("#briefingDateA").value=briefingDate(8);qs("#briefingDateB").value=briefingDate(1);updateBriefingFields();loadBriefing()});
    qs("#briefingShare").addEventListener("click",async()=>{syncBriefingUrl();await navigator.clipboard.writeText(location.href);toast("Brief view link copied")});
    qs("#briefingPrint").addEventListener("click",()=>{document.body.classList.add("briefing-print-mode");window.print();setTimeout(()=>document.body.classList.remove("briefing-print-mode"),300)});
    qsa("[data-briefing-export]").forEach(button=>button.addEventListener("click",()=>downloadBriefing(button.dataset.briefingExport)));
    qs("#sourceApply").addEventListener("click",()=>loadSourceStudio(true));
    qs("#sourceReset").addEventListener("click",()=>{qs("#sourceSearch").value="";qs("#sourceDomain").value="";qs("#sourceState").value="";qs("#sourceFeature").value="";sourceStudioState.activeSource=null;loadSourceStudio(true)});
    qs("#sourceSearch").addEventListener("keydown",event=>{if(event.key==="Enter")loadSourceStudio(true)});
    qs("#sourceDomain").addEventListener("change",()=>loadSourceStudio(true));
    qs("#sourceState").addEventListener("change",()=>loadSourceStudio(true));
    qs("#sourceFeature").addEventListener("change",()=>loadSourceStudio(true));
    qs("#sourceShare").addEventListener("click",async()=>{syncSourceUrl();await navigator.clipboard.writeText(location.href);toast("Source view link copied")});
    qsa("[data-source-export]").forEach(button=>button.addEventListener("click",()=>downloadSourceRegistry(button.dataset.sourceExport)));
    qs("#savedCreate").addEventListener("click",openSaveViewDialog);qs("#savedImport").addEventListener("click",()=>qs("#savedImportFile").click());qs("#savedImportFile").addEventListener("change",event=>{const file=event.target.files?.[0];importSavedViewFile(file);event.target.value=""});qs("#savedExportAll").addEventListener("click",()=>downloadSavedJson({schema:"sc-saved-view-collection/1.0",application_version:APP_VERSION,exported_at:savedIso(),views:savedViewsState.items},"site-intelligence-saved-views.json"));qs("#savedClearAll").addEventListener("click",()=>{if(!savedViewsState.items.length)return;if(confirm("Delete all locally saved Site Intelligence views from this browser?")){savedViewsState.items=[];try{persistSavedViews();renderSavedViews();toast("Local saved views cleared")}catch{}}});qs("#saveViewCancel").addEventListener("click",()=>qs("#saveViewDialog").close());qs("#saveViewForm").addEventListener("submit",event=>{event.preventDefault();if(saveCurrentManifest(qs("#saveViewName").value))qs("#saveViewDialog").close()});
    qs("#closeEvidenceDrawer").addEventListener("click",closeEvidenceDrawer);qs("#evidenceBackdrop").addEventListener("click",closeEvidenceDrawer);document.addEventListener("keydown",e=>{if(e.key==="Escape"){closeEvidenceDrawer();setMobileNavigation(false,{restoreFocus:true})}});
    window.matchMedia("(max-width: 760px)").addEventListener?.("change",event=>{if(!event.matches)setMobileNavigation(false)});
    const params=new URLSearchParams(location.search);const initialCountry=params.get("country")||"KEN";const requestedView=params.get("view")||"overview";const initialView=[...Object.keys(savedViewDefinitions),"saved","launch","observatory"].includes(requestedView)?requestedView:"overview";const invalidRequestedView=requestedView!==initialView;qs("#countrySelect").value=names[initialCountry]?initialCountry:"KEN";if(params.get("imageryDate"))qs("#dateSelect").value=params.get("imageryDate");try{setLaunch("Loading satellite imagery.",50);await loadLayers();await setImagery(params.get("imageryLayer")||"true-color");setLaunch("Connecting to live events and country evidence.",68);await Promise.all([loadEvents(),loadCountry(qs("#countrySelect").value)]);setLaunch("Preparing the workspace.",88);await setRoute(initialView);applySharedControlState(initialView,params);finishLaunch();if(invalidRequestedView)toast("The requested view is unavailable; Overview was opened instead.")}
    catch(e){qs("#statusText").textContent="Partial public data";toast("Some optional public data is temporarily unavailable.");finishLaunch()}
  }
  document.addEventListener("DOMContentLoaded",init);
})();

const visualStyle=document.createElement("style");
visualStyle.textContent=`
.scsi-map-marker{position:relative}
.marker-core{position:absolute;left:6px;top:6px;width:10px;height:10px;border-radius:50%;border:2px solid #fff;z-index:2;box-shadow:0 0 12px rgba(255,255,255,.4)}
.marker-core.quake{background:#ff2a2f}.marker-core.natural{background:#43d6ff}
.marker-ring{position:absolute;left:1px;top:1px;width:20px;height:20px;border-radius:50%;border:1px solid;animation:markerPulse 2.2s ease-out infinite}
.marker-ring.quake{border-color:rgba(255,42,47,.7)}.marker-ring.natural{border-color:rgba(67,214,255,.7)}
@keyframes markerPulse{0%{transform:scale(.5);opacity:.9}100%{transform:scale(1.45);opacity:0}}
.route-enter{animation:routeFade .3s ease both}@keyframes routeFade{from{opacity:.55;transform:translateY(4px)}to{opacity:1;transform:none}}
@media(prefers-reduced-motion:reduce){.marker-ring{animation:none}}
`;
document.head.appendChild(visualStyle);

window.addEventListener("load",reportHeight,{once:true});window.addEventListener("resize",reportHeight,{passive:true});window.visualViewport?.addEventListener("resize",reportHeight,{passive:true});window.addEventListener("message",event=>{if(event.data?.type==="SC_SI_REQUEST_HEIGHT")reportHeight()});if("ResizeObserver" in window)new ResizeObserver(reportHeight).observe(document.body);

/* v3.6.1 publishing integration: window.SCIntelligencePublishingV2200 */
/* v3.6.1 scheduled monitoring integration: window.SCScheduledMonitoringV2210 */
