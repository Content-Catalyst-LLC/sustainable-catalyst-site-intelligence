
(() => {
  const API = window.SC_SITE_INTELLIGENCE_API || window.location.origin;
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
    state.layers=await api("/public/geospatial/layers");
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
    const data=await api("/public/geospatial/events");
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
    qs("#eventList").innerHTML=features.length?features.map(f=>{const p=f.properties||{};const quake=String(p.category).toLowerCase().includes("earthquake");return `<div class="event-row"><span class="event-marker ${quake?"quake":""}"></span><div><div class="event-title">${escapeHtml(p.title||"Public event")}</div><div class="event-meta">${escapeHtml(p.category||"Event")} · ${escapeHtml(p.source||"Source")}</div></div><div class="event-time">${cleanDate(p.observed_at)}</div></div>`}).join(""):`<div class="loading-block">No recent event records are available.</div>`;
  }
  async function loadCountry(code){
    state.country=code;const name=names[code]||code;
    qs("#countryName").textContent=name;qs("#countryCode").textContent=code;qs("#countryPanelTitle").textContent=`${name} at a glance`;
    try{
      const d=await api(`/public/country-intelligence/${code}`);
      qs("#coverageCount").textContent=d.registered_source_count??d.source_count??"—";
      const domains=d.domain_summaries||d.domains||[];
      const normalized=Array.isArray(domains)?domains:Object.values(domains||{});
      qs("#countrySummary").innerHTML=normalized.slice(0,5).map(x=>`<div class="country-stat"><span>${escapeHtml(x.title||x.label||x.domain||"Evidence domain")}</span><strong>${escapeHtml(x.summary||x.description||x.data_state||"Source context available")}</strong></div>`).join("")||`<div class="loading-block">Country evidence structure is available; validated values appear as connectors return records.</div>`;
    }catch{
      qs("#coverageCount").textContent="—";
      qs("#countrySummary").innerHTML=`<div class="loading-block">Country evidence is temporarily unavailable.</div>`;
    }
  }
  function routeMeta(route){
    return {
      overview:["LIVE INTELLIGENCE WORKSPACE","Climate and Human Vulnerability","Satellite context, natural events, environmental pressure, and country evidence in one navigable view."],
      country:["COUNTRY INTELLIGENCE",`${names[state.country]||state.country} evidence profile`,"Environmental, development, humanitarian, security, and legal context for one selected country."],
      events:["LIVE EVENT STREAM","Recent public event records","Natural hazards and Earth-system events collected from public feeds and displayed with source context."],
      compare:["CROSS-DOMAIN COMPARISON","Compare country contexts","Align available evidence without flattening dates, units, definitions, or missing-data states."],
      sources:["PROVENANCE","Sources and methods","Review the public sources, imagery services, and interpretive limits behind this workspace."]
    }[route]||[];
  }

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
      const [profile,trends]=await Promise.all([api(`/public/country/${code}`),api(`/public/country/${code}/trends`)]);
      qs("#liveCountryTitle").textContent=`${profile.country.name} intelligence`;
      qs("#liveCountrySummary").textContent=profile.summary;
      const stateLabel=profile.data_state==="live"?"Live public indicators":profile.data_state==="reference-snapshot"?"Reference snapshot":"Source unavailable";
      qs("#countryDataState").textContent=stateLabel;
      qs("#countryDataState").classList.toggle("reference",profile.data_state!=="live");
      qs("#countryIndicatorGrid").innerHTML=(profile.highlights||[]).map(item=>`<article class="country-indicator"><span class="country-indicator-label">${escapeHtml(item.label)}</span><strong class="country-indicator-value">${escapeHtml(formatCountryValue(item.value,item.format,item.unit))}</strong><div class="country-indicator-meta">${escapeHtml(item.unit)} · ${escapeHtml(item.year)}</div><span class="country-indicator-source">${escapeHtml(item.source)} · ${escapeHtml(item.data_state)}</span></article>`).join("")||'<div class="loading-block">Validated country indicators are unavailable.</div>';
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
      qs("#countryIndicatorGrid").innerHTML='<div class="loading-block">Live country intelligence is temporarily unavailable.</div>';
      qs("#countryDataState").textContent="Unavailable";qs("#countryDataState").classList.add("reference");
    }
  }

  async function setRoute(route){
    qs("#main").classList.remove("route-enter");void qs("#main").offsetWidth;qs("#main").classList.add("route-enter");
    state.route=route;
    qsa(".nav-item").forEach(b=>b.classList.toggle("active",b.dataset.route===route));
    const [e,t,d]=routeMeta(route);qs("#viewEyebrow").textContent=e;qs("#viewTitle").textContent=t;qs("#viewDescription").textContent=d;
    const panel=qs("#routePanel");
    if(route==="overview"){panel.hidden=true;qs("#countryIntelligencePanel").hidden=true;return}
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
  async function init(){
    qs("#dateSelect").value=today();initMap();
    qsa(".layer-tab").forEach(b=>b.addEventListener("click",()=>setImagery(b.dataset.layer)));
    qsa(".nav-item").forEach(b=>b.addEventListener("click",()=>{history.replaceState(null,"",`?country=${encodeURIComponent(state.country)}&view=${encodeURIComponent(b.dataset.route)}`);setRoute(b.dataset.route)}));
    qsa("[data-route-link]").forEach(b=>b.addEventListener("click",()=>setRoute(b.dataset.routeLink)));
    qs("#countrySelect").addEventListener("change",async e=>{await loadCountry(e.target.value);history.replaceState(null,"",`?country=${encodeURIComponent(e.target.value)}&view=${encodeURIComponent(state.route)}`);if(state.route==="country"){await loadLiveCountry(e.target.value);setRoute("country")}});
    qs("#dateSelect").addEventListener("change",()=>setImagery(qs(".layer-tab.active").dataset.layer));
    qs("#eventsToggle").addEventListener("change",e=>e.target.checked?state.markers.addTo(state.map):state.map.removeLayer(state.markers));
    qs("#heatToggle").addEventListener("change",e=>toast(e.target.checked?"Density layer enabled for supported records":"Density layer hidden"));
    qs("#fullscreenButton").addEventListener("click",()=>{const p=qs(".map-panel");if(document.fullscreenElement)document.exitFullscreen();else p.requestFullscreen?.()});
    qs("#shareButton").addEventListener("click",async()=>{await navigator.clipboard.writeText(location.href);toast("View link copied")});
    const params=new URLSearchParams(location.search);const initialCountry=params.get("country")||"KEN";const initialView=params.get("view")||"overview";qs("#countrySelect").value=names[initialCountry]?initialCountry:"KEN";try{await loadLayers();await setImagery("true-color");await Promise.all([loadEvents(),loadCountry(qs("#countrySelect").value)]);await setRoute(initialView)}
    catch(e){qs("#statusText").textContent="Some feeds unavailable";toast("The interface loaded, but one or more public feeds are unavailable.")}
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
