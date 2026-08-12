(() => {
  const VERSION = "4.35.24";
  const API = window.SC_SITE_INTELLIGENCE_API || window.location.origin;
  const qs = (selector, root = document) => root.querySelector(selector);
  const escapeHtml = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]));
  const state = {loaded:false, summary:null, areas:[], datasets:[], layers:[], contextFeatures:[], map:null, base:null, areaLayer:null, evidenceLayer:null, contextLayer:null};

  async function get(path){
    const response=await fetch(`${API}${path}`,{headers:{Accept:"application/json"}});
    if(!response.ok)throw new Error(`${response.status} ${path}`);
    return response.json();
  }
  function row(title, detail){return `<div class="spatial-row"><strong>${escapeHtml(title)}</strong><small>${escapeHtml(detail)}</small></div>`}
  function mapStatus(message){const target=qs("#spatialMapStatus");if(target)target.textContent=message}
  function coordinates(value,out=[]){
    if(!Array.isArray(value))return out;
    if(value.length>=2&&Number.isFinite(Number(value[0]))&&Number.isFinite(Number(value[1]))){out.push([Number(value[1]),Number(value[0])]);return out}
    value.forEach(item=>coordinates(item,out));return out;
  }
  function fit(points,maxZoom=6){
    if(!state.map||!points.length)return;
    if(points.length===1)state.map.setView(points[0],Math.min(maxZoom,5));
    else state.map.fitBounds(points,{padding:[28,28],maxZoom});
  }
  function ensureMap(){
    if(state.map||!window.L||!qs("#spatialEvidenceMap"))return;
    state.map=L.map("spatialEvidenceMap",{worldCopyJump:true,zoomControl:true}).setView([12,20],2);
    state.base=L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",{attribution:"© OpenStreetMap contributors",maxZoom:19,crossOrigin:true}).addTo(state.map);
    state.contextLayer=L.layerGroup().addTo(state.map);
    state.areaLayer=L.layerGroup().addTo(state.map);
    state.evidenceLayer=L.layerGroup().addTo(state.map);
    if(window.L.__scsiFirstParty)mapStatus("First-party interactive map active; evidence geometries remain fully available."); else if(window.L.__scsiFallback)mapStatus("Geographic fallback active; evidence geometries remain interactive.");
  }
  function renderContext(){
    ensureMap();if(!state.contextLayer)return;
    state.contextLayer.clearLayers();
    let count=0;
    state.contextFeatures.slice(0,120).forEach(feature=>{
      const c=feature?.geometry?.coordinates;if(!Array.isArray(c)||c.length<2)return;
      count+=1;
      L.circleMarker([Number(c[1]),Number(c[0])],{radius:4,weight:1,color:"#d8eef8",fillColor:"#578ca8",fillOpacity:.45,opacity:.72})
        .bindPopup(`<strong>${escapeHtml(feature.properties?.title||"Public context record")}</strong><br><small>Geographic orientation only · ${escapeHtml(feature.properties?.source||"public source")}</small>`)
        .addTo(state.contextLayer);
    });
    if(count&&!state.areas.length)mapStatus(`${count} public context locations shown. Publish a public area and dataset to run spatial evidence.`);
    else if(!count&&!state.areas.length)mapStatus("Map ready. Published public areas and datasets will appear here.");
  }
  function selectedArea(){return state.areas.find(item=>item.area_id===qs("#spatialAreaSelect")?.value)}
  function renderArea(){
    ensureMap();if(!state.areaLayer)return;
    state.areaLayer.clearLayers();
    const area=selectedArea();
    if(!area?.geometry){if(state.areas.length)mapStatus("Select a public area to preview its geometry.");return}
    const feature={type:"Feature",id:area.area_id,properties:{name:area.name||area.area_id},geometry:area.geometry};
    L.geoJSON(feature,{style:{color:"#ffcf57",weight:2.5,fillColor:"#ffcf57",fillOpacity:.16},pointToLayer:(_f,ll)=>L.circleMarker(ll,{radius:9,color:"#ffcf57",fillColor:"#ffcf57",fillOpacity:.25})})
      .bindPopup?.(`<strong>${escapeHtml(area.name||area.area_id)}</strong><br><small>Public area of interest · ${escapeHtml(area.geometry.type||"geometry")}</small>`)
      .addTo(state.areaLayer);
    const points=coordinates(area.geometry.coordinates);
    if(Array.isArray(area.bbox)&&area.bbox.length===4)fit([[area.bbox[1],area.bbox[0]],[area.bbox[3],area.bbox[2]]],7);else fit(points,7);
    mapStatus(`${area.name||area.area_id} is mapped. Select a public dataset to run the intersection.`);
  }
  function renderEvidence(data){
    ensureMap();if(!state.evidenceLayer)return;
    state.evidenceLayer.clearLayers();
    const collection=data?.geojson||{type:"FeatureCollection",features:[]};
    const features=collection.features||[];
    L.geoJSON(collection,{
      style:{color:"#ff4e55",weight:2.2,fillColor:"#ff4e55",fillOpacity:.28},
      pointToLayer:(feature,ll)=>L.circleMarker(ll,{radius:7,color:"#ffffff",weight:1.4,fillColor:"#ff4e55",fillOpacity:.9}),
      onEachFeature:(feature,layer)=>layer.bindPopup?.(`<strong>${escapeHtml(feature.properties?.title||feature.properties?.name||feature.id||"Matched feature")}</strong><br><small>${escapeHtml(feature.geometry?.type||"Geometry")} · registered evidence</small>`)
    }).addTo(state.evidenceLayer);
    const area=selectedArea();
    const points=[...(area?.geometry?coordinates(area.geometry.coordinates):[]),...features.flatMap(feature=>coordinates(feature.geometry?.coordinates))];
    fit(points,7);
    mapStatus(features.length?`${features.length} matched evidence geometr${features.length===1?"y":"ies"} mapped with the selected public area.`:"The analysis completed with no matched geometries.");
  }
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
    qs("#spatialAvailability").textContent=state.areas.length&&state.datasets.length?"Public evidence selections are available.":"The map and method catalog are ready; public areas and registered datasets will appear as they are published.";
    renderContext();renderArea();setTimeout(()=>state.map?.invalidateSize(),80);
  }
  async function load(){
    const panel=qs("#spatialEvidenceStudio"); if(!panel)return;
    panel.setAttribute("aria-busy","true");ensureMap();
    try{
      const [summary,layers,areas,datasets,context]=await Promise.all([
        get("/public/spatial"),get("/public/spatial/layers"),get("/public/spatial/areas"),get("/public/spatial/datasets"),
        get("/public/geospatial/events").catch(()=>({features:[]}))
      ]);
      state.summary=summary;state.layers=layers.layers||[];state.areas=areas.areas||[];state.datasets=datasets.datasets||[];state.contextFeatures=context.features||[];state.loaded=true;render();
    }catch(error){
      qs("#spatialAvailability").textContent="Spatial evidence services could not be refreshed. The methodology and layer contracts remain available in the release.";
      mapStatus("Spatial services are unavailable; the map remains in diagnostic mode.");console.warn("Spatial evidence load failed",error)
    }finally{
      panel.setAttribute("aria-busy","false");setTimeout(()=>state.map?.invalidateSize(),100);
      if(!window.SCSI_FIXED_WORDPRESS_EMBED)window.parent?.postMessage({type:"scsi-height",height:document.documentElement.scrollHeight,version:VERSION},"*")
    }
  }
  async function runEvidence(){
    const area=qs("#spatialAreaSelect").value,dataset=qs("#spatialDatasetSelect").value,out=qs("#spatialEvidenceOutput");
    if(!area||!dataset){out.innerHTML=row("Select an area and dataset","Both records must be explicitly public before evidence can be generated.");renderArea();return}
    out.innerHTML=row("Running public evidence intersection","The server is preserving source and method context.");
    try{
      const data=await get(`/public/spatial/evidence?area_id=${encodeURIComponent(area)}&dataset_id=${encodeURIComponent(dataset)}`),packet=data.packet||{},features=data.geojson?.features||[];
      renderEvidence(data);
      out.innerHTML=`<div class="spatial-method"><strong>${escapeHtml(packet.matched_feature_count??features.length)} matched features</strong><p>${escapeHtml(packet.method||"")}</p></div>`+features.slice(0,20).map(item=>row(item.properties?.title||item.properties?.name||item.id,item.geometry?.type||"Geometry")).join("")+`<details><summary>Evidence packet</summary><pre class="spatial-code">${escapeHtml(JSON.stringify(packet,null,2))}</pre></details>`;
    }catch(error){out.innerHTML=row("Public evidence unavailable",error.message);mapStatus("The selected public evidence result could not be generated.")}
  }
  function open(){const panel=qs("#spatialEvidenceStudio");if(!panel)return;panel.hidden=false;ensureMap();if(!state.loaded)load();else setTimeout(()=>state.map?.invalidateSize(),80)}
  function close(){const panel=qs("#spatialEvidenceStudio");if(panel)panel.hidden=true}
  document.addEventListener("DOMContentLoaded",()=>{
    qs("#spatialRunEvidence")?.addEventListener("click",runEvidence);
    qs("#spatialAreaSelect")?.addEventListener("change",()=>{state.evidenceLayer?.clearLayers();renderArea()});
  });
  window.SCSpatialV2150={open,close,status:()=>({version:VERSION,loaded:state.loaded,publicAreas:state.areas.length,publicDatasets:state.datasets.length,mapMode:window.L?.__scsiFirstParty?"first-party-interactive":window.L?.__scsiFallback?"geographic-fallback":"leaflet",map:state.map})};
})();
