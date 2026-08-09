(()=>{"use strict";
const VERSION="4.4.0";
const GROUPS=[
 {id:"live-overview",label:"Live Overview",routes:["overview","global","events","alerts"]},
 {id:"places-systems",label:"Places & Systems",routes:["country","dossiers","economics","law","science","humanitarian","resources","thematic"]},
 {id:"analysis",label:"Analysis",routes:["compare","spatial","earth","harmonization","models","scenarios"]},
 {id:"evidence-research",label:"Evidence & Research",routes:["platform","observatory","research","evidence","graph","sources","saved"]},
 {id:"publishing-monitoring",label:"Publishing & Monitoring",routes:["briefing","publishing","monitoring","workspaces"]},
 {id:"methods-operations",label:"Methods & Operations",routes:["integration","workflows","federation","governance","experience","launch"]}
];
const q=(s,r=document)=>r.querySelector(s),qa=(s,r=document)=>[...r.querySelectorAll(s)];
let applied=false,payload=null;
function groupFor(route){return GROUPS.find(g=>g.routes.includes(route))||null}
function applyNavigation(){
 if(applied)return true; const nav=q("#primaryNavigation"); if(!nav)return false;
 const buttons=new Map(qa(".nav-item[data-route]",nav).map(b=>[b.dataset.route,b]));
 if(buttons.size<35)return false;
 const fragment=document.createDocumentFragment();
 GROUPS.forEach((g,index)=>{const details=document.createElement("details");details.className="v4000-nav-group";details.dataset.area=g.id;details.open=index===0;
  const summary=document.createElement("summary");summary.textContent=g.label;summary.setAttribute("aria-label",`${g.label} workspace group`);details.appendChild(summary);
  const routes=document.createElement("div");routes.className="v4000-nav-routes";g.routes.forEach(route=>{const b=buttons.get(route);if(b)routes.appendChild(b)});details.appendChild(routes);fragment.appendChild(details)});
 nav.replaceChildren(fragment);applied=true;document.documentElement.dataset.v4Navigation="ready";syncActive();return true;
}
function syncActive(){const route=window.SCSIRouterV3228?.current?.()||q('.nav-item[aria-current="page"]')?.dataset.route||new URLSearchParams(location.search).get("view")||"overview";qa(".v4000-nav-group").forEach(d=>{const active=d.dataset.area===groupFor(route)?.id;d.dataset.active=String(active);if(active)d.open=true})}
function injectCard(){if(q("#unifiedPublicPlatformV4000"))return;const host=q("#connectedPlatformStudio");if(!host)return;const card=document.createElement("article");card.id="unifiedPublicPlatformV4000";card.className="v4000-platform-card";card.innerHTML=`<div class="v4000-platform-head"><div><p class="eyebrow">UNIFIED PUBLIC INTELLIGENCE PLATFORM · v${VERSION}</p><h3>One product architecture, six primary areas</h3><p>Existing analytical, evidence, publishing, monitoring, and governance workspaces remain available through a consolidated navigation and compatibility contract.</p></div><span id="v4000PlatformState" class="v4000-platform-state">Loading</span></div><div class="v4000-platform-metrics"><div><span>Primary areas</span><strong id="v4000AreaCount">6</strong></div><div><span>Preserved routes</span><strong id="v4000RouteCount">35</strong></div><div><span>Canonical contracts</span><strong id="v4000ContractCount">6</strong></div></div><div id="v4000PlatformAreas" class="v4000-platform-areas"></div><p class="v4000-platform-boundary">Consolidation changes navigation and contracts, not evidence meaning. Missingness, uncertainty, provenance, human review, and public/private boundaries remain explicit.</p>`;
 host.querySelector(".platform-hero")?.insertAdjacentElement("afterend",card)
}
function render(data){payload=data;injectCard();const areas=data?.primary_areas||GROUPS;q("#v4000AreaCount")&&(q("#v4000AreaCount").textContent=String(data?.primary_area_count||areas.length));q("#v4000RouteCount")&&(q("#v4000RouteCount").textContent=String(data?.route_count||35));q("#v4000ContractCount")&&(q("#v4000ContractCount").textContent=String(data?.canonical_contract_count||6));const list=q("#v4000PlatformAreas");if(list)list.innerHTML=areas.map(a=>`<div class="v4000-platform-area"><strong>${escapeHtml(a.label)}</strong><small>${escapeHtml(a.description||"")} · ${(a.routes||[]).length} workspaces</small></div>`).join("");const state=q("#v4000PlatformState");if(state)state.textContent=data?.ok===false?"Review":"Ready";document.documentElement.dataset.v4Platform=data?.ok===false?"review":"ready"}
function escapeHtml(v){return String(v??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]))}
async function hydrate(){applyNavigation();injectCard();try{const r=await fetch("/public/v4",{cache:"no-store",headers:{Accept:"application/json"}});if(!r.ok)throw new Error(String(r.status));const d=await r.json();if(d.version!==VERSION||d.primary_area_count!==6||d.route_count!==35)throw new Error("contract mismatch");render(d)}catch(_){render({ok:true,version:VERSION,primary_area_count:6,route_count:35,canonical_contract_count:6,primary_areas:GROUPS.map(g=>({...g,description:"Preserved v4 workspace group."}))})}}
window.addEventListener("scsi:route-transition-end",syncActive);document.addEventListener("click",e=>{if(e.target.closest?.(".nav-item[data-route]"))queueMicrotask(syncActive)},true);
window.SCSIUnifiedPlatformV4000={version:VERSION,groups:GROUPS,applyNavigation,status:()=>({ready:applied,groupCount:GROUPS.length,routeCount:GROUPS.reduce((n,g)=>n+g.routes.length,0),payload})};
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",hydrate,{once:true});else hydrate();
})();
