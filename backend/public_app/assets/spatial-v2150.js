(() => {
  const VERSION = "2.20.0";
  const API = window.SC_SITE_INTELLIGENCE_API || window.location.origin;
  const qs = (selector, root = document) => root.querySelector(selector);
  const escapeHtml = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]));
  const state = {loaded:false, summary:null, areas:[], datasets:[], layers:[]};
  async function get(path){const response=await fetch(`${API}${path}`,{headers:{Accept:"application/json"}});if(!response.ok)throw new Error(`${response.status} ${path}`);return response.json()}
  function row(title, detail){return `<div class="spatial-row"><strong>${escapeHtml(title)}</strong><small>${escapeHtml(detail)}</small></div>`}
  function render(){
    const summary=state.summary||{}, counts=summary.counts||{};
    qs("#spatialPublicAreas").textContent=counts.public_areas??0;
    qs("#spatialPublicDatasets").textContent=counts.public_datasets??0;
    qs("#spatialCatalogLayers").textContent=counts.catalog_layers??state.layers.length;
    qs("#spatialCrs").textContent="EPSG:4326";
    qs("#spatialLayerList").innerHTML=state.layers.length?state.layers.map(item=>row(item.title||item.id,`${(item.geometry_types||[]).join(", ")} · ${(item.source_families||[]).join(", ")}`)).join(""):row("No public catalog layers","The source-aware layer catalog is unavailable.");
    qs("#spatialMethodList").innerHTML=(summary.responsible_use||[]).map(item=>`<li>${escapeHtml(item)}</li>`).join("");
    const areaSelect=qs("#spatialAreaSelect"),datasetSelect=qs("#spatialDatasetSelect");
    areaSelect.innerHTML='<option value="">Select a public area</option>'+state.areas.map(item=>`<option value="${escapeHtml(item.area_id)}">${escapeHtml(item.name||item.area_id)}</option>`).join("");
    datasetSelect.innerHTML='<option value="">Select a public dataset</option>'+state.datasets.map(item=>`<option value="${escapeHtml(item.dataset_id)}">${escapeHtml(item.title||item.dataset_id)}</option>`).join("");
    qs("#spatialAvailability").textContent=state.areas.length&&state.datasets.length?"Public evidence selections are available.":"The studio is ready; public areas and registered datasets will appear as they are published.";
  }
  async function load(){
    const panel=qs("#spatialEvidenceStudio"); if(!panel)return;
    panel.setAttribute("aria-busy","true");
    try{
      const [summary,layers,areas,datasets]=await Promise.all([get("/public/spatial"),get("/public/spatial/layers"),get("/public/spatial/areas"),get("/public/spatial/datasets")]);
      state.summary=summary;state.layers=layers.layers||[];state.areas=areas.areas||[];state.datasets=datasets.datasets||[];state.loaded=true;render();
    }catch(error){qs("#spatialAvailability").textContent="Spatial evidence services could not be refreshed. The methodology and layer contracts remain available in the release.";console.warn("Spatial evidence load failed",error)}
    finally{panel.setAttribute("aria-busy","false");window.parent?.postMessage({type:"scsi-height",height:document.documentElement.scrollHeight,version:VERSION},"*")}
  }
  async function runEvidence(){
    const area=qs("#spatialAreaSelect").value,dataset=qs("#spatialDatasetSelect").value,out=qs("#spatialEvidenceOutput");
    if(!area||!dataset){out.innerHTML=row("Select an area and dataset","Both records must be explicitly public before evidence can be generated.");return}
    out.innerHTML=row("Running public evidence intersection","The server is preserving source and method context.");
    try{
      const data=await get(`/public/spatial/evidence?area_id=${encodeURIComponent(area)}&dataset_id=${encodeURIComponent(dataset)}`),packet=data.packet||{},features=data.geojson?.features||[];
      out.innerHTML=`<div class="spatial-method"><strong>${escapeHtml(packet.matched_feature_count??features.length)} matched features</strong><p>${escapeHtml(packet.method||"")}</p></div>`+features.slice(0,20).map(item=>row(item.properties?.title||item.properties?.name||item.id,item.geometry?.type||"Geometry")).join("")+`<details><summary>Evidence packet</summary><pre class="spatial-code">${escapeHtml(JSON.stringify(packet,null,2))}</pre></details>`;
    }catch(error){out.innerHTML=row("Public evidence unavailable",error.message)}
  }
  function open(){const panel=qs("#spatialEvidenceStudio");if(!panel)return;panel.hidden=false;if(!state.loaded)load()}
  function close(){const panel=qs("#spatialEvidenceStudio");if(panel)panel.hidden=true}
  document.addEventListener("DOMContentLoaded",()=>qs("#spatialRunEvidence")?.addEventListener("click",runEvidence));
  window.SCSpatialV2150={open,close,status:()=>({version:VERSION,loaded:state.loaded,publicAreas:state.areas.length,publicDatasets:state.datasets.length})};
})();
