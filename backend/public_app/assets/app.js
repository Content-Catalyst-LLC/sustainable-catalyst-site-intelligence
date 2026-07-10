
(() => {
  const API = window.SC_SITE_INTELLIGENCE_API || window.location.origin;

  const boot={progress:10};
  function setLaunch(message,progress,retry=false){
    const m=qs("#launchMessage"),b=qs("#launchProgressBar"),r=qs("#launchRetry");
    if(m)m.textContent=message;if(b){boot.progress=Math.max(boot.progress,progress||boot.progress);b.style.width=`${Math.min(100,boot.progress)}%`}if(r)r.hidden=!retry;
  }
  function showGlobalNotice(title,text){qs("#globalNoticeTitle").textContent=title;qs("#globalNoticeText").textContent=text;qs("#globalNotice").hidden=false}
  function hideGlobalNotice(){qs("#globalNotice").hidden=true}
  function finishLaunch(){qs("#app").classList.remove("app-loading");qs("#app").classList.add("app-ready");setLaunch("Site Intelligence is ready.",100);setTimeout(()=>qs("#launchScreen").classList.add("hidden"),320);reportHeight()}
  async function apiWithRetry(path,attempts=3){let last;for(let i=0;i<attempts;i++){try{return await api(path)}catch(e){last=e;if(i<attempts-1)await new Promise(r=>setTimeout(r,700*(i+1)))}}throw last}
  function reportHeight(){window.parent?.postMessage({type:"scsi-height",height:Math.max(document.body.scrollHeight,document.documentElement.scrollHeight)},"*")}
  function publicErrorBlock(title,text,retryAction){
    const id=`retry-${Math.random().toString(36).slice(2)}`;
    setTimeout(()=>{const b=document.getElementById(id);if(b)b.addEventListener("click",retryAction)},0);
    return `<div class="error-state"><div><strong>${escapeHtml(title)}</strong><span>${escapeHtml(text)}</span><br><button id="${id}" class="retry-button" type="button">Retry</button></div></div>`;
  }

  const state = {map:null,base:null,imagery:null,markers:null,heat:null,layers:null,events:null,country:"KEN",route:"overview"};
  const names = {KEN:"Kenya",GHA:"Ghana",USA:"United States",IND:"India",BRA:"Brazil"};
  const qs = (s)=>document.querySelector(s), qsa=(s)=>[...document.querySelectorAll(s)];
  const toast=(msg)=>{const el=qs("#toast");el.textContent=msg;el.classList.add("show");setTimeout(()=>el.classList.remove("show"),1800)};
  const cleanDate=(v)=>{if(!v)return "Date unavailable";try{return new Date(v).toLocaleDateString(undefined,{year:"numeric",month:"short",day:"numeric"})}catch{return v}};
  const api=async(path)=>{const res=await fetch(API+path,{headers:{"Accept":"application/json"}});if(!res.ok)throw new Error(`${res.status}`);return res.json()};

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
      qs("#countrySummary").innerHTML=publicErrorBlock("Country evidence unavailable","The public country service did not respond.",()=>loadCountry(code));showGlobalNotice("Country evidence is temporarily unavailable","The map and other public feeds remain available.");
    }
  }
  function routeMeta(route){
    return {
      overview:["LIVE INTELLIGENCE WORKSPACE","Climate and Human Vulnerability","Satellite context, natural events, environmental pressure, and country evidence in one navigable view."],
      earth:["EARTH OBSERVATION STUDIO","Compare the planet through time","Explore satellite-derived imagery, environmental layers, date comparison, timeline playback, and exportable visual views."],
      country:["COUNTRY INTELLIGENCE",`${names[state.country]||state.country} evidence profile`,"Environmental, development, humanitarian, security, and legal context for one selected country."],
      events:["LIVE EVENT STREAM","Recent public event records","Natural hazards and Earth-system events collected from public feeds and displayed with source context."],
      compare:["CROSS-DOMAIN COMPARISON","Compare country contexts","Align available evidence without flattening dates, units, definitions, or missing-data states."],
      sources:["PROVENANCE","Sources and methods","Review the public sources, imagery services, and interpretive limits behind this workspace."]
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
    if(typeof html2canvas!=="function"){toast("PNG export library is unavailable.");return}
    toast("Preparing Earth view image…");
    try{
      const canvas=await html2canvas(qs("#earthCapture"),{backgroundColor:"#05080c",useCORS:true,allowTaint:false,scale:1.5,logging:false});
      const a=document.createElement("a");a.href=canvas.toDataURL("image/png");a.download=`site-intelligence-earth-${earthState.activeLayer}-${qs("#earthDateB").value}.png`;a.click();
    }catch{showGlobalNotice("PNG export could not include all imagery","Some external map tiles restrict browser capture. Use Print view or download the view manifest instead.")}
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
      qs("#countryIndicatorGrid").innerHTML=publicErrorBlock("Live country intelligence unavailable","The country indicator service may be waking up or temporarily unavailable.",()=>loadLiveCountry(code));showGlobalNotice("Country indicators are temporarily unavailable","Retry in a moment while the public service wakes up.");
      qs("#countryDataState").textContent="Unavailable";qs("#countryDataState").classList.add("reference");
    }
  }

  async function setRoute(route){
    qs("#main").classList.remove("route-enter");void qs("#main").offsetWidth;qs("#main").classList.add("route-enter");
    state.route=route;
    qsa(".nav-item").forEach(b=>b.classList.toggle("active",b.dataset.route===route));
    const [e,t,d]=routeMeta(route);qs("#viewEyebrow").textContent=e;qs("#viewTitle").textContent=t;qs("#viewDescription").textContent=d;
    const panel=qs("#routePanel");
    if(route==="overview"){panel.hidden=true;qs("#countryIntelligencePanel").hidden=true;closeEarthStudio();return}
    if(route==="earth"){panel.hidden=true;qs("#countryIntelligencePanel").hidden=true;await openEarthStudio();return}
    closeEarthStudio();
    qs("#countryIntelligencePanel").hidden=route!=="country";
    panel.hidden=false;panel.innerHTML=`<div class="loading-block">Loading ${escapeHtml(route)} view…</div>`;
    if(route==="country"){await loadLiveCountry(state.country)}
    if(route==="events"){
      const rows=(state.events?.features||[]).slice(0,30);
      panel.innerHTML=`<p class="eyebrow">PUBLIC EVENT RECORDS</p><h2>Latest mapped events</h2><div class="event-list">${rows.map(f=>{const p=f.properties||{};return `<div class="event-row"><span class="event-marker"></span><div><div class="event-title">${escapeHtml(p.title||"Event")}</div><div class="event-meta">${escapeHtml(p.category||"Event")} · ${escapeHtml(p.source||"Source")}</div></div><div class="event-time">${cleanDate(p.observed_at)}</div></div>`}).join("")}</div>`;
    }else if(route==="country"){
      panel.innerHTML=`<p class="eyebrow">COUNTRY PROFILE</p><h2>${escapeHtml(names[state.country]||state.country)}</h2><div class="route-grid"><div class="route-card"><h3>Environmental context</h3><p>Satellite imagery, environmental pressure, natural events, land, water, and climate context.</p></div><div class="route-card"><h3>Human development</h3><p>Health, education, poverty, food security, water, sanitation, and decent-work evidence.</p></div><div class="route-card"><h3>Human security</h3><p>Conflict, displacement, civilian protection, humanitarian access, and source-specific limits.</p></div></div>`;
    }else if(route==="compare"){
      const other=state.country==="GHA"?"KEN":"GHA";
      panel.innerHTML=`<p class="eyebrow">COMPARISON VIEW</p><h2>${escapeHtml(names[state.country]||state.country)} and ${escapeHtml(names[other])}</h2><div class="route-grid"><div class="route-card"><h3>Human development</h3><p>Validated connector values remain separate by country, year, unit, and source definition.</p></div><div class="route-card"><h3>Environmental pressure</h3><p>Satellite and indicator context can be aligned without creating a proprietary score.</p></div><div class="route-card"><h3>Humanitarian conditions</h3><p>Missing records remain explicit and do not imply the absence of real-world conditions.</p></div></div>`;
    }else{
      const sources=["NASA GIBS","NASA EONET","USGS","World Bank","WHO","UNESCO","FAOSTAT","UN-Water","UNHCR","ReliefWeb","UCDP","ACLED"];
      panel.innerHTML=`<p class="eyebrow">PUBLIC SOURCE LAYER</p><h2>Connected evidence services</h2><div class="source-list">${sources.map(s=>`<div class="source-chip">${escapeHtml(s)}</div>`).join("")}</div>`;
    }
  }
  async function init(){setLaunch("Preparing the map and public evidence services.",18);
    qs("#dateSelect").value=today();initMap();setLaunch("Loading map layers.",34);
    qsa(".layer-tab").forEach(b=>b.addEventListener("click",()=>setImagery(b.dataset.layer)));
    qsa(".nav-item").forEach(b=>b.addEventListener("click",()=>{history.replaceState(null,"",`?country=${encodeURIComponent(state.country)}&view=${encodeURIComponent(b.dataset.route)}`);setRoute(b.dataset.route)}));
    qsa("[data-route-link]").forEach(b=>b.addEventListener("click",()=>setRoute(b.dataset.routeLink)));
    qs("#countrySelect").addEventListener("change",async e=>{await loadCountry(e.target.value);history.replaceState(null,"",`?country=${encodeURIComponent(e.target.value)}&view=${encodeURIComponent(state.route)}`);if(state.route==="country"){await loadLiveCountry(e.target.value);setRoute("country")}});
    qs("#dateSelect").addEventListener("change",()=>setImagery(qs(".layer-tab.active").dataset.layer));
    qs("#eventsToggle").addEventListener("change",e=>e.target.checked?state.markers.addTo(state.map):state.map.removeLayer(state.markers));
    qs("#heatToggle").addEventListener("change",e=>toast(e.target.checked?"Density layer enabled for supported records":"Density layer hidden"));
    qs("#fullscreenButton").addEventListener("click",()=>{const p=qs(".map-panel");if(document.fullscreenElement)document.exitFullscreen();else p.requestFullscreen?.()});
    qs("#shareButton").addEventListener("click",async()=>{await navigator.clipboard.writeText(location.href);toast("View link copied")});qs("#openNewButton").addEventListener("click",()=>window.open(location.href,"_blank","noopener"));qs("#dismissNotice").addEventListener("click",hideGlobalNotice);qs("#launchRetry").addEventListener("click",()=>location.reload());qs("#earthSwipe").addEventListener("input",e=>{setEarthClip(e.target.value);e.target.setAttribute("aria-valuetext",`${e.target.value} percent`)});
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
    qs("#closeEvidenceDrawer").addEventListener("click",closeEvidenceDrawer);qs("#evidenceBackdrop").addEventListener("click",closeEvidenceDrawer);document.addEventListener("keydown",e=>{if(e.key==="Escape")closeEvidenceDrawer()});
    const params=new URLSearchParams(location.search);const initialCountry=params.get("country")||"KEN";const initialView=params.get("view")||"overview";qs("#countrySelect").value=names[initialCountry]?initialCountry:"KEN";try{setLaunch("Loading satellite imagery.",50);await loadLayers();await setImagery("true-color");setLaunch("Connecting to live events and country evidence.",68);await Promise.all([loadEvents(),loadCountry(qs("#countrySelect").value)]);setLaunch("Preparing the workspace.",88);await setRoute(initialView);finishLaunch()}
    catch(e){qs("#statusText").textContent="Partial public data";showGlobalNotice("Some public feeds are unavailable","The interface is open with partial data. Retry after the service finishes waking up.");finishLaunch()}
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

window.addEventListener("load",reportHeight);window.addEventListener("resize",()=>setTimeout(reportHeight,120));new ResizeObserver(()=>reportHeight()).observe(document.body);
