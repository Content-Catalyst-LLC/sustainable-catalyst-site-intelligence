import {contextStore} from "./context-store.js";
import {client} from "./api-client.js";
import {resolve,navigate,countryPath} from "./router.js";
import * as views from "./views.js";

const $=(s)=>document.querySelector(s);
const cfg=window.__SC_SITE_INTELLIGENCE_CONFIG__||{};
let countries=[];

function routeNeedsCountry(id){ return ["country","dossiers","economics","law","science","earth","humanitarian","resources"].includes(id); }
function updateChrome(route){
  const ctx=contextStore.get();
  $("#releaseVersion").textContent=`v${cfg.release}`;
  $("#apiOrigin").textContent=new URL(cfg.apiOrigin).host;
  $("#countryCode").textContent=ctx.countryCode;
  document.querySelectorAll("[data-nav]").forEach(a=>{
    const id=a.dataset.nav;
    a.classList.toggle("active",route.id===id || (id==="science"&&["earth","ocean","space"].includes(route.id)));
    a.href=countryPath(id,ctx.countryCode);
  });
}
async function hydrateCountries(){
  try{
    const data=await client.get("/public/intelligence-dossiers/facets");
    countries=(data.countries||[]).map(x=>({code:x.code,name:x.display_name||x.name||x.code}));
  }catch{ countries=[{code:"KEN",name:"Kenya"},{code:"USA",name:"United States"},{code:"IRL",name:"Ireland"}]; }
  const sel=$("#countrySelect"); sel.innerHTML=countries.map(c=>`<option value="${c.code}">${c.name} · ${c.code}</option>`).join("");
  sel.value=contextStore.get().countryCode;
  const match=countries.find(c=>c.code===sel.value); if(match) contextStore.setCountry(match.code,match.name);
}
async function render(){
  let route=resolve();
  if(routeNeedsCountry(route.id)&&route.param&&route.param!==contextStore.get().countryCode){
    const found=countries.find(c=>c.code===String(route.param).toUpperCase());
    contextStore.setCountry(route.param,found?.name||String(route.param).toUpperCase());
  }
  updateChrome(route);
  const ctx=contextStore.get();
  const out=$("#view"); out.innerHTML='<div class="loading">Loading research context…</div>';
  try{
    const map={
      home:()=>views.renderHome(ctx), country:()=>views.renderCountry(ctx), dossiers:()=>views.renderDossiers(ctx), economics:()=>views.renderEconomics(ctx), law:()=>views.renderLaw(ctx), science:()=>views.renderScience(ctx), earth:()=>views.renderScience(ctx,"earth"), ocean:()=>views.renderOcean(), space:()=>views.renderSpace(), humanitarian:()=>views.renderHumanitarian(ctx), resources:()=>views.renderResources(ctx), events:()=>views.renderEvents(), research:()=>views.renderResearch(ctx), packages:()=>views.renderPackages(route.param)
    };
    out.innerHTML=await (map[route.id]?.()||Promise.resolve(views.renderNotFound(route.path)));
  }catch(e){ out.innerHTML=`<section class="panel danger"><h2>Application error</h2><p>${e.message}</p></section>`; }
  out.querySelectorAll("[data-nav]").forEach(a=>a.addEventListener("click",e=>{e.preventDefault();navigate(countryPath(a.dataset.nav,contextStore.get().countryCode));}));
  document.title=`Site Intelligence · ${route.id}`;
}

document.addEventListener("click",e=>{
  const a=e.target.closest("a[data-nav]"); if(!a)return; e.preventDefault(); navigate(countryPath(a.dataset.nav,contextStore.get().countryCode));
});
$("#countrySelect").addEventListener("change",e=>{
  const c=countries.find(x=>x.code===e.target.value); contextStore.setCountry(e.target.value,c?.name||e.target.value);
  const route=resolve(); navigate(routeNeedsCountry(route.id)?countryPath(route.id,e.target.value):countryPath("country",e.target.value));
});
window.addEventListener("popstate",render);
contextStore.addEventListener("change",()=>updateChrome(resolve()));

(async()=>{
  await hydrateCountries();
  const route=resolve();
  if(route.id==="home"&&location.pathname!=="/") navigate("/",{replace:true});
  await render();
  if("serviceWorker" in navigator) navigator.serviceWorker.register("/service-worker.js").catch(()=>{});
})();
