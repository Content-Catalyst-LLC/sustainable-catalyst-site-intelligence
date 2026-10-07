import {client} from "./api-client.js";

const esc=(v)=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const arr=(v)=>Array.isArray(v)?v:[];

function card(title,value,sub=""){
  return `<article class="metric-card"><span>${esc(title)}</span><strong>${esc(value)}</strong><small>${esc(sub)}</small></article>`;
}
function shell(kicker,title,lede,body,actions=""){
  return `<section class="view-head"><p class="eyebrow">${esc(kicker)}</p><h1>${esc(title)}</h1><p>${esc(lede)}</p>${actions?`<div class="actions">${actions}</div>`:""}</section>${body}`;
}
function statusStrip(items){ return `<div class="metric-grid">${items.join("")}</div>`; }
function errorPanel(err){ return `<section class="panel danger"><h2>Workspace data unavailable</h2><p>${esc(err?.message||err)}</p><p>The standalone application remains operational; the API/source state is shown rather than replaced with demonstration records.</p></section>`; }
function jsonPreview(data){ return `<details class="panel"><summary>Inspect response</summary><pre>${esc(JSON.stringify(data,null,2))}</pre></details>`; }
function recordsOf(data){ return arr(data?.records||data?.items||data?.results||data?.data); }
function countOf(data){ return Number(data?.count??data?.record_count??recordsOf(data).length??0)||0; }
function listRecords(rows,empty="No records returned for this context."){
  if(!rows.length) return `<div class="empty-state"><strong>No records in this response</strong><p>${esc(empty)}</p></div>`;
  return `<div class="record-list">${rows.slice(0,12).map((r,i)=>`<article><small>${esc(r.source_id||r.source||r.provider||r.record_type||"record")}</small><h3>${esc(r.title||r.name||r.indicator_name||r.indicator_code||r.official_symbol||`Record ${i+1}`)}</h3><p>${esc(r.summary||r.description||r.period||r.date||"")}</p></article>`).join("")}</div>`;
}

export async function renderHome(ctx){
  const [health,manifest]=await Promise.all([client.get("/health"),client.get("/public/web-app/manifest")]);
  const c=ctx.countryCode;
  return shell("STANDALONE APPLICATION","Site Intelligence","Independent research application. WordPress is no longer in the runtime path.",
    `${statusStrip([card("Backend",health.version,health.environment),card("Application",manifest.version,"standalone web"),card("Country context",c,"propagates across domain workspaces"),card("WordPress dependency",String(manifest.wordpress_runtime_dependency),manifest.wordpress_role)])}
    <section class="panel"><h2>Research from context</h2><p>Open a domain lens for <strong>${esc(ctx.countryName||c)}</strong>. The country code is carried in the URL and used by workspace requests.</p><div class="launch-grid">${["country","dossiers","economics","law","science","humanitarian","resources"].map(id=>`<a data-nav="${id}" href="#">${esc(id)}</a>`).join("")}</div></section>`);
}

export async function renderCountry(ctx){
  try{
    const data=await client.get("/public/intelligence-dossiers/country",{country:ctx.countryCode,limit_per_domain:12});
    const domains=data?.dossier?.domains||data?.domains||{};
    const rows=Object.entries(domains);
    return shell("COUNTRY CONTEXT",ctx.countryName||ctx.countryCode,"Canonical country context for every Site Intelligence lens.",
      `${statusStrip([card("Country",ctx.countryCode,"URL-authoritative"),card("Domain groups",rows.length,"dossier composition"),card("Source state",data?.integration?.state||data?.state||"connected","reported by API")])}
      <section class="panel"><h2>Domain coverage</h2><div class="record-list">${rows.length?rows.map(([k,v])=>`<article><small>${esc(k)}</small><h3>${esc(v?.count??arr(v?.records).length??0)} records</h3><p>${esc(v?.state||v?.message||"")}</p></article>`).join(""):`<div class="empty-state"><p>No composed domain records returned yet.</p></div>`}</div></section>${jsonPreview(data)}`);
  }catch(e){ return shell("COUNTRY CONTEXT",ctx.countryName||ctx.countryCode,"Country context remains active even if a data source is unavailable.",errorPanel(e)); }
}

export async function renderEconomics(ctx){
  try{
    const [records,facets]=await Promise.all([
      client.get("/public/economics-sustainability/records",{geography_code:ctx.countryCode,limit:80}),
      client.get("/public/economics-sustainability/facets",{geography_code:ctx.countryCode})
    ]);
    const rows=recordsOf(records);
    return shell("ECONOMICS","Economics · "+ctx.countryCode,"Official macroeconomic, trade, energy and sustainability evidence for the active country context.",
      `${statusStrip([card("Records",countOf(records),"current context"),card("Sources",arr(facets?.sources).length,"visible providers"),card("Indicators",arr(facets?.indicators).length,"published series"),card("Country",ctx.countryCode,"propagated from route")])}<section class="panel"><h2>Current records</h2>${listRecords(rows,"No economics records are currently flowing for this country. v4.55.4 will activate domain data rather than mask the gap.")}</section>`);
  }catch(e){ return shell("ECONOMICS","Economics · "+ctx.countryCode,"Standalone workspace",errorPanel(e)); }
}

export async function renderLaw(ctx){
  try{
    const [records,profile]=await Promise.all([
      client.get("/public/international-law-observatory/records",{country:ctx.countryCode,limit:80}),
      client.get("/public/international-law-observatory/country-profile",{country:ctx.countryCode,limit:80})
    ]);
    const rows=recordsOf(records);
    return shell("INTERNATIONAL LAW","Law & governance · "+ctx.countryCode,"Treaties, resolutions, courts, authority and procedural context without automatic legal conclusions.",
      `${statusStrip([card("Records",countOf(records),"country-related"),card("Bodies",arr(profile?.legal_bodies||profile?.bodies).length,"issuing institutions"),card("Subjects",arr(profile?.subjects).length,"legal topics"),card("Country",ctx.countryCode,"route context")])}<section class="panel"><h2>Legal evidence</h2>${listRecords(rows,"No country-linked legal records were returned by the current source bridge.")}</section>`);
  }catch(e){ return shell("INTERNATIONAL LAW","Law & governance · "+ctx.countryCode,"Standalone workspace",errorPanel(e)); }
}

export async function renderScience(ctx,sub="science"){
  try{
    const params={limit:80};
    if(sub==="earth") params.family="earth";
    const [discovery,records]=await Promise.all([
      client.get("/public/scientific-earth-systems/discovery"),
      client.get("/public/scientific-earth-systems/records",params)
    ]);
    const rows=recordsOf(records);
    return shell("SCIENCE",`${sub==="earth"?"Earth systems":"Science"} · ${ctx.countryCode}`,"Scientific records, assets, observations and time-series discovery through the independent application.",
      `${statusStrip([card("Records",countOf(records),"visible science records"),card("Sources",arr(discovery?.sources).length,"discovery providers"),card("Missions",arr(discovery?.missions).length,"missions"),card("Country",ctx.countryCode,"research context")])}<section class="panel"><h2>Scientific evidence</h2>${listRecords(rows,"No matching scientific records are currently published through the Core bridge.")}</section>`);
  }catch(e){ return shell("SCIENCE","Science · "+ctx.countryCode,"Standalone workspace",errorPanel(e)); }
}

export async function renderOcean(){
  try{ const data=await client.get("/public/ocean-observation"); return shell("SCIENCE · OCEAN","Ocean intelligence","Marine observations and ocean systems retain their independent analytical surface.",`${statusStrip([card("Runtime",data?.ok===false?"degraded":"available","API response"),card("Version",data?.version||"current","ocean contract")])}${jsonPreview(data)}`); }
  catch(e){ return shell("SCIENCE · OCEAN","Ocean intelligence","Standalone workspace",errorPanel(e)); }
}
export async function renderSpace(){
  try{ const data=await client.get("/public/space-observation"); return shell("SCIENCE · SPACE","Space intelligence","Orbital, planetary and astronomical intelligence through the shared API client.",`${statusStrip([card("Runtime",data?.ok===false?"degraded":"available","API response"),card("Version",data?.version||"current","space contract")])}${jsonPreview(data)}`); }
  catch(e){ return shell("SCIENCE · SPACE","Space intelligence","Standalone workspace",errorPanel(e)); }
}

export async function renderHumanitarian(ctx){
  try{ const data=await client.get("/public/humanitarian-conflict-displacement/records",{country:ctx.countryCode,limit:80}); const rows=recordsOf(data); return shell("HUMANITARIAN","Humanitarian · "+ctx.countryCode,"Conflict, displacement, protection, hazards and humanitarian evidence with source limitations preserved.",`${statusStrip([card("Records",countOf(data),"current country"),card("Country",ctx.countryCode,"route context"),card("Targeting","disabled","responsible data")])}<section class="panel"><h2>Current evidence</h2>${listRecords(rows,"No matching humanitarian records are currently available for this context.")}</section>`); }
  catch(e){ return shell("HUMANITARIAN","Humanitarian · "+ctx.countryCode,"Standalone workspace",errorPanel(e)); }
}
export async function renderResources(ctx){
  try{ const [data,profile]=await Promise.all([client.get("/public/trade-energy-resources/records",{geography_code:ctx.countryCode,limit:80}),client.get("/public/trade-energy-resources/country-profile",{country:ctx.countryCode,limit:80})]); const rows=recordsOf(data); return shell("RESOURCES","Trade, energy & resources · "+ctx.countryCode,"Trade flows, energy systems and resource-security evidence without automatic dependency or vulnerability claims.",`${statusStrip([card("Records",countOf(data),"current country"),card("Trade",arr(profile?.trade).length,"flow context"),card("Energy",arr(profile?.energy).length,"system context"),card("Country",ctx.countryCode,"route context")])}<section class="panel"><h2>Resource evidence</h2>${listRecords(rows,"No resource records are currently flowing for this context.")}</section>`); }
  catch(e){ return shell("RESOURCES","Trade, energy & resources · "+ctx.countryCode,"Standalone workspace",errorPanel(e)); }
}
export async function renderDossiers(ctx){
  try{ const data=await client.get("/public/intelligence-dossiers/country",{country:ctx.countryCode,limit_per_domain:20}); return shell("DOSSIERS","Intelligence dossier · "+ctx.countryCode,"Cross-domain country dossier composed without hiding source state.",`${statusStrip([card("Country",ctx.countryCode,"active context"),card("Status",data?.ok===false?"degraded":"available","dossier service")])}${jsonPreview(data)}`); }
  catch(e){ return shell("DOSSIERS","Intelligence dossier · "+ctx.countryCode,"Standalone workspace",errorPanel(e)); }
}
export async function renderEvents(){
  try{ const data=await client.get("/public/events",{limit:40}); const rows=recordsOf(data); return shell("LIVE INTELLIGENCE","Events","Recent public event records and geospatial fusion.",`<section class="panel"><h2>Recent events</h2>${listRecords(rows,"No events returned in the current public window.")}</section>`); }
  catch(e){ return shell("LIVE INTELLIGENCE","Events","Standalone workspace",errorPanel(e)); }
}
export async function renderResearch(ctx){
  return shell("RESEARCH","Research context · "+ctx.countryCode,"A persistent standalone research surface ready for project, evidence, package, and cross-product handoffs.",`<section class="panel"><h2>Foundation state</h2><p>v4.55.3 moves routing, context and API transport out of WordPress. Persistent hosted research projects remain governed by their existing backend contracts.</p></section>`);
}
export async function renderPackages(id){
  try{ const data=await client.get("/public/reproducible-spatial-packages/registry"); return shell("REPRODUCIBILITY",id?`Package ${id}`:"Packages","Reproducible spatial intelligence package contracts.",jsonPreview(data)); }
  catch(e){ return shell("REPRODUCIBILITY","Packages","Standalone workspace",errorPanel(e)); }
}
export function renderNotFound(path){ return shell("ROUTING","Not found",`No Site Intelligence route matches ${path}.`,`<section class="panel"><a href="/">Return home</a></section>`); }
