(()=>{"use strict";
const API=window.SC_SITE_INTELLIGENCE_API||location.origin;
const esc=x=>String(x??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
async function mount(){const host=document.querySelector("#ocean4575");if(!host||host.querySelector("#ocean4590"))return;
const box=document.createElement("details");box.id="ocean4590";box.innerHTML='<summary>Ocean science variable & source registry</summary><p id="ocean4590Status" role="status">Loading registered scientific variables…</p><div id="ocean4590Registry"></div>';
host.appendChild(box);
try{const response=await fetch(API+"/public/ocean-intelligence/variables/registry",{headers:{Accept:"application/json"},cache:"no-store"});if(!response.ok)throw Error("Registry endpoint HTTP "+response.status);const data=await response.json();if(data.schema!=="scsi-ocean-variable-registry/4.59.0"||!Array.isArray(data.variables)||!Array.isArray(data.sources))throw Error("Unexpected registry schema");
const available=data.variables.filter(v=>v.retrieval_status==="live-verified").length;
box.querySelector("#ocean4590Status").textContent=available+" live-verified variable(s); "+(data.variables.length-available)+" defined but not connected. Definitions do not imply measurements.";
box.querySelector("#ocean4590Registry").innerHTML='<table><thead><tr><th>Variable</th><th>Canonical unit</th><th>Geometry</th><th>Retrieval status</th></tr></thead><tbody>'+data.variables.map(v=>'<tr><td>'+esc(v.label)+'</td><td>'+esc(v.canonical_unit)+'</td><td>'+esc(v.geometry)+'</td><td>'+esc(v.retrieval_status)+'</td></tr>').join("")+'</tbody></table><p>Sources: '+data.sources.map(s=>esc(s.provider)+" "+esc(s.dataset_id)+" ("+esc(s.capability)+")").join("; ")+'</p>';
}catch(e){box.querySelector("#ocean4590Status").textContent="Variable registry unavailable: "+e.message+". The existing NOAA SST workflow remains independent.";}
}
window.addEventListener("scsi:ocean-surface-enter",()=>{mount()});
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",()=>{if(document.querySelector("#ocean4575"))mount()});else if(document.querySelector("#ocean4575"))mount();
})();