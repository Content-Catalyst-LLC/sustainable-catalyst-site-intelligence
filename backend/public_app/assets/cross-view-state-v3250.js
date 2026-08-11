(()=>{"use strict";
const VERSION="4.35.11";
const STORAGE_KEY="scsi_cross_view_state_v3250";
const LOCAL_KEY="scsi_cross_view_last_v3250";
const ROUTES={overview:["country","imageryLayer","imageryDate","eventDays","mapCategories"],global:["country","eventDays","mapCategories"],country:["country","indicator"],compare:["country","compare","indicator"],spatial:["country","area_id","dataset_id"],earth:["country","layer_id","date_a","date_b","imageryLayer","imageryDate"]};
const TARGETS=["global","country","compare","spatial","earth"];
const q=(s,r=document)=>r.querySelector(s);
const params=()=>new URLSearchParams(location.search);
function safeJson(value,fallback={}){try{return JSON.parse(value)||fallback}catch{return fallback}}
function clean(value){return String(value??"").trim()}
function currentRoute(){return clean(window.SCSIRouterV3228?.current?.()||params().get("view")||"overview").toLowerCase()}
function value(id){return clean(q(`#${id}`)?.value)}
function fromDom(){
  const categories=[];document.querySelectorAll('[data-map-category].active,[data-map-category][aria-pressed="true"]').forEach(el=>{if(el.dataset.mapCategory)categories.push(el.dataset.mapCategory)});
  return {
    view:currentRoute(),country:value("countrySelect")||"KEN",compare:value("compareCountryB")||"GHA",indicator:value("compareIndicatorFilter"),
    imageryLayer:q('.layer-tab.active')?.dataset.layer||value("earthLayerSelect")||"true-color",imageryDate:value("dateSelect"),
    area_id:value("spatialAreaSelect"),dataset_id:value("spatialDatasetSelect"),layer_id:value("earthLayerSelect")||"true-color",
    date_a:value("earthDateA"),date_b:value("earthDateB"),eventDays:Number(value("eventDays")||params().get("eventDays")||30),mapCategories:categories
  };
}
function fromUrl(){const p=params(),out={};for(const key of ["view","country","compare","indicator","imageryLayer","imageryDate","area_id","dataset_id","layer_id","date_a","date_b","eventDays"]){if(p.has(key))out[key]=p.get(key)}if(p.has("mapCategories"))out.mapCategories=p.get("mapCategories").split(",").filter(Boolean);return out}
function stored(){return {...safeJson(localStorage.getItem(LOCAL_KEY)),...safeJson(sessionStorage.getItem(STORAGE_KEY))}}
function normalize(raw={}){
  const merged={...stored(),...raw};
  const route=ROUTES[clean(merged.view).toLowerCase()]?clean(merged.view).toLowerCase():"overview";
  const options=[...document.querySelectorAll("#countrySelect option")].map(o=>o.value);const allowed=new Set(options);
  const country=allowed.has(clean(merged.country).toUpperCase())?clean(merged.country).toUpperCase():(allowed.has("KEN")?"KEN":options[0]||"KEN");
  let compare=allowed.has(clean(merged.compare).toUpperCase())?clean(merged.compare).toUpperCase():"GHA";if(compare===country)compare=options.find(code=>code!==country)||"GHA";
  const eventDays=Math.max(1,Math.min(365,Number(merged.eventDays)||30));
  return {view:route,country,compare,indicator:clean(merged.indicator),imageryLayer:clean(merged.imageryLayer)||"true-color",imageryDate:clean(merged.imageryDate),area_id:clean(merged.area_id),dataset_id:clean(merged.dataset_id),layer_id:clean(merged.layer_id)||"true-color",date_a:clean(merged.date_a),date_b:clean(merged.date_b),eventDays,mapCategories:Array.isArray(merged.mapCategories)?[...new Set(merged.mapCategories.map(clean).filter(Boolean))].slice(0,12):[]};
}
let state=normalize({...fromUrl(),...fromDom()});
function persist(){sessionStorage.setItem(STORAGE_KEY,JSON.stringify(state));localStorage.setItem(LOCAL_KEY,JSON.stringify({...state,view:"overview"}))}
function canonical(target=state.view){const route=ROUTES[target]?target:"overview",p=new URLSearchParams();p.set("view",route);for(const key of ROUTES[route]){const v=state[key];if(Array.isArray(v)){if(v.length)p.set(key,v.join(","))}else if(v!==""&&v!==null&&v!==undefined)p.set(key,String(v))}return `${location.pathname}?${p.toString()}`}
function syncUrl(target=state.view){history.replaceState(null,"",canonical(target));render()}
function render(){const bar=q("#crossViewStateBar");if(!bar)return;const route=q("#crossViewRoute"),country=q("#crossViewCountry"),finger=q("#crossViewFingerprint");if(route)route.textContent=state.view;if(country)country.textContent=state.country;if(finger)finger.textContent=shortFingerprint();bar.querySelectorAll("[data-cross-view-target]").forEach(button=>button.classList.toggle("is-current",button.dataset.crossViewTarget===state.view))}
function shortFingerprint(){const text=JSON.stringify(state,Object.keys(state).sort());let hash=2166136261;for(let i=0;i<text.length;i++){hash^=text.charCodeAt(i);hash=Math.imul(hash,16777619)}return (`00000000${(hash>>>0).toString(16)}`).slice(-8)}
function capture({url=true}={}){state=normalize({...state,...fromDom(),view:currentRoute()});persist();if(url)syncUrl(state.view);else render();window.dispatchEvent(new CustomEvent("scsi:cross-view-state",{detail:{version:VERSION,state:{...state},fingerprint:shortFingerprint()}}));return {...state}}
function applyToControls(){const set=(id,v)=>{const el=q(`#${id}`);if(el&&v&&[...el.options||[]].some(o=>o.value===v))el.value=v};set("countrySelect",state.country);set("compareCountryA",state.country);set("compareCountryB",state.compare);set("compareIndicatorFilter",state.indicator);set("spatialAreaSelect",state.area_id);set("spatialDatasetSelect",state.dataset_id);set("earthLayerSelect",state.layer_id);const dates=[["dateSelect",state.imageryDate],["earthDateA",state.date_a],["earthDateB",state.date_b]];for(const [id,v] of dates){const el=q(`#${id}`);if(el&&v)el.value=v}}
async function navigate(target){capture({url:false});state.view=target;persist();syncUrl(target);if(window.SCSIRouterV3228?.navigate)await window.SCSIRouterV3228.navigate(target);else q(`.nav-item[data-route="${CSS.escape(target)}"]`)?.click();applyToControls();render()}
async function copy(){const url=new URL(canonical(state.view),location.origin).href;try{await navigator.clipboard.writeText(url)}catch{const ta=document.createElement("textarea");ta.value=url;document.body.appendChild(ta);ta.select();document.execCommand("copy");ta.remove()}q("#crossViewCopy")?.setAttribute("data-copied","true");setTimeout(()=>q("#crossViewCopy")?.removeAttribute("data-copied"),1200)}
function inject(){if(q("#crossViewStateBar"))return;const bar=document.createElement("section");bar.id="crossViewStateBar";bar.className="cross-view-state-bar";bar.setAttribute("aria-label","Unified analytical state");bar.innerHTML=`<div class="cross-view-summary"><span class="cross-view-kicker">Unified analytical state</span><strong><span id="crossViewCountry">${state.country}</span> · <span id="crossViewRoute">${state.view}</span></strong><small>State <span id="crossViewFingerprint">${shortFingerprint()}</span></small></div><div class="cross-view-actions" role="group" aria-label="Open selection in another analytical workspace">${TARGETS.map(route=>`<button type="button" data-cross-view-target="${route}">${route.replace("_"," ")}</button>`).join("")}<button id="crossViewCopy" type="button">Copy analytical link</button></div>`;q("#main")?.insertAdjacentElement("afterbegin",bar);bar.querySelectorAll("[data-cross-view-target]").forEach(button=>button.addEventListener("click",()=>navigate(button.dataset.crossViewTarget)));q("#crossViewCopy")?.addEventListener("click",copy);render()}
function bind(){
  document.addEventListener("change",event=>{if(event.target.matches("#countrySelect,#compareCountryA,#compareCountryB,#compareIndicatorFilter,#spatialAreaSelect,#spatialDatasetSelect,#earthLayerSelect,#earthDateA,#earthDateB,#dateSelect,#eventDays"))capture()});
  window.addEventListener("scsi:route-transition-end",event=>{state.view=event.detail?.route||currentRoute();capture()});
  window.addEventListener("scsi:startup-hydrated",()=>{state=normalize({...stored(),...fromUrl(),...fromDom()});applyToControls();capture()},{once:true});
  window.addEventListener("popstate",()=>{state=normalize({...stored(),...fromUrl()});applyToControls();render()});
}
function init(){if(!q("#app[data-scsi-release]"))return;state=normalize({...stored(),...fromUrl(),...fromDom()});inject();applyToControls();persist();bind();render();document.documentElement.dataset.crossViewState="ready";window.dispatchEvent(new CustomEvent("scsi:cross-view-ready",{detail:{version:VERSION,state:{...state},routes:Object.keys(ROUTES)}}))}
window.SiteIntelligenceCrossViewState={version:VERSION,current:()=>({...state}),capture,canonical,target:navigate,copy,normalize};
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init,{once:true});else init();
})();
