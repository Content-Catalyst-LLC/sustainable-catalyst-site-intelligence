(() => {
  const VERSION="3.4.0", API=window.SC_SITE_INTELLIGENCE_API||window.location.origin;
  const qs=s=>document.querySelector(s), esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]));
  const state={loaded:false,summary:null,series:[],standards:null};
  async function get(path,options={}){const r=await fetch(`${API}${path}`,{headers:{Accept:"application/json","Content-Type":"application/json"},...options});if(!r.ok)throw new Error(`${r.status} ${path}`);return r.json()}
  function row(title,detail){return `<div class="harmonization-row"><strong>${esc(title)}</strong><small>${esc(detail)}</small></div>`}
  function render(){
    const c=state.summary?.counts||{};
    qs("#harmSeriesCount").textContent=c.public_series??c.series??0;
    qs("#harmTransformedCount").textContent=c.transformed_series??0;
    qs("#harmUnitCount").textContent=state.standards?.units?.length??0;
    qs("#harmCurrencyCount").textContent=state.standards?.currencies?.length??0;
    const options='<option value="">Select public series</option>'+state.series.map(x=>`<option value="${esc(x.series_id)}">${esc(x.title||x.series_id)} · ${esc(x.unit_code||"")}</option>`).join("");
    qs("#harmLeftSeries").innerHTML=options;qs("#harmRightSeries").innerHTML=options;
    qs("#harmSeriesList").innerHTML=state.series.length?state.series.slice(0,20).map(x=>row(x.title||x.series_id,`${x.unit_code||"unit unavailable"} · ${x.frequency||"frequency unavailable"} · ${x.period_start||"?"}–${x.period_end||"?"}`)).join(""):row("No public comparable series","Administrators can register source series and publish reviewed transformations.");
    qs("#harmStatus").textContent="Harmonization contracts loaded. Comparability remains explicit and reviewable.";
  }
  async function load(){const p=qs("#harmonizationStudio");if(!p)return;p.setAttribute("aria-busy","true");try{const [summary,series,standards]=await Promise.all([get("/public/harmonization"),get("/public/harmonization/series"),get("/public/harmonization/standards")]);state.summary=summary;state.series=series.series||[];state.standards=standards;state.loaded=true;render()}catch(e){qs("#harmStatus").textContent="Comparable-series services could not be refreshed. Methodology remains available in the release.";console.warn(e)}finally{p.setAttribute("aria-busy","false");window.parent?.postMessage({type:"scsi-height",height:document.documentElement.scrollHeight,version:VERSION},"*")}}
  async function compare(){const l=qs("#harmLeftSeries").value,r=qs("#harmRightSeries").value,o=qs("#harmCompareOutput");if(!l||!r){o.innerHTML=row("Select two public series","Both series must be published before comparison.");return}o.innerHTML=row("Running comparability diagnostics","Units, currencies, periods, geography, and missing-data coverage are being checked.");try{const data=await get("/public/harmonization/compare",{method:"POST",body:JSON.stringify({left_series_id:l,right_series_id:r})});o.innerHTML=`<div class="harmonization-result ${data.comparable?"is-compatible":"is-blocked"}"><strong>${data.comparable?"Comparable after declared checks":"Not directly comparable"}</strong><p>${esc(data.blocking_issues)} blocking issue(s); ${esc(data.shared_periods?.length||0)} shared observed periods.</p></div>`+(data.checks||[]).map(x=>row(x.check,`${x.compatible?"compatible":x.severity}: ${x.detail}`)).join("")}catch(e){o.innerHTML=row("Comparison unavailable",e.message)}}
  function open(){const p=qs("#harmonizationStudio");if(!p)return;p.hidden=false;if(!state.loaded)load()}
  function close(){const p=qs("#harmonizationStudio");if(p)p.hidden=true}
  document.addEventListener("DOMContentLoaded",()=>qs("#harmRunCompare")?.addEventListener("click",compare));
  window.SCHarmonizationV2160={open,close,status:()=>({version:VERSION,loaded:state.loaded,series:state.series.length})};
})();
