(()=>{
  "use strict";
  const VERSION="4.55.3.2.2";
  const API=window.SC_SITE_INTELLIGENCE_API||location.origin;
  const SPECS={
    dossiers:{domain:"dossiers",controller:"SCDossiersV270",surface:"#dossierStudio",label:"Dossiers",modes:["investigation","timeline","entity-network","cross-case","evidence-review"]},
    economics:{domain:"economics",controller:"SCEconomicsV220",surface:"#economicsStudio",label:"Economics",modes:["macro-sustainability","country-comparison","time-series","trade-exposure","energy-intensity","scenario-context"]},
    law:{domain:"international-law",controller:"SCLawV230",surface:"#lawStudio",label:"International Law",modes:["authority-obligation","treaty-status","institution-comparison","legal-timeline","jurisdiction-context","subject-matrix"]},
    science:{domain:"science",controller:"SCScienceV240",surface:"#scienceStudio",label:"Science",modes:["earth-systems","ocean-systems","space-astronomy","mission-dataset","multi-variable","observation-provenance"]},
    humanitarian:{domain:"humanitarian",controller:"SCHumanitarianV250",surface:"#humanitarianStudio",label:"Humanitarian",modes:["conflict-events","displacement","humanitarian-access","population-exposure","country-comparison","event-timeline"]},
    resources:{domain:"resources",controller:"SCResourcesV260",surface:"#resourceStudio",label:"Resources",modes:["trade-flows","energy-security","critical-resources","supply-chain","counterparty-concentration","disruption-scenario"]},
  };
  const esc=value=>String(value??"").replace(/[&<>"']/g,ch=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[ch]));
  const qs=(s,r=document)=>r.querySelector(s);
  function rows(route){
    const spec=SPECS[route],status=window[spec.controller]?.status?.()||{};
    if(Array.isArray(status.records))return status.records;
    if(route==="dossiers"&&status.dossier?.domains)return Object.values(status.dossier.domains).flatMap(x=>x?.sample_records||[]);
    return [];
  }
  async function post(path,payload){const response=await fetch(API+path,{method:"POST",headers:{"Content-Type":"application/json","Accept":"application/json"},credentials:"same-origin",body:JSON.stringify(payload)});if(!response.ok)throw new Error(`Request failed (${response.status})`);return response.json()}
  function summaryHtml(result){
    const source=result.source_summary||{},analysis=result.analysis||{};
    const cards=[
      ["Records",result.record_count??0],
      ["Sources",source.source_count??0],
      ["Mode",analysis.mode||"analysis"],
      ["Digest",String(result.analysis_digest||"").slice(7,19)||"—"],
    ];
    const details=Object.entries(analysis).filter(([k,v])=>k!=="mode"&&v!==false&&v!==null&&v!==undefined).slice(0,9).map(([k,v])=>{
      const label=k.replaceAll("_"," ");
      if(Array.isArray(v))return `<article><strong>${esc(label)}</strong><span>${esc(v.length)} item${v.length===1?"":"s"}</span>${v.slice(0,4).map(x=>`<small>${esc(typeof x==="object"?JSON.stringify(x):x)}</small>`).join("")}</article>`;
      if(typeof v==="object")return `<article><strong>${esc(label)}</strong><span>${esc(JSON.stringify(v))}</span></article>`;
      return `<article><strong>${esc(label)}</strong><span>${esc(v)}</span></article>`;
    }).join("");
    return `<div class="adi-metrics">${cards.map(([a,b])=>`<article><span>${esc(a)}</span><strong>${esc(b)}</strong></article>`).join("")}</div><div class="adi-results-grid">${details||"<article><strong>No derived summary</strong><span>Load more official records or change filters.</span></article>"}</div>`;
  }
  function ensure(route){
    const spec=SPECS[route],surface=qs(spec.surface);if(!surface)return null;
    let panel=surface.querySelector(`[data-domain-intelligence="${route}"]`);if(panel)return panel;
    panel=document.createElement("section");panel.className="advanced-domain-intelligence-v4552";panel.dataset.domainIntelligence=route;
    panel.innerHTML=`<div class="adi-head"><div><p class="eyebrow">ADVANCED RESEARCH · v${VERSION}</p><h3>${esc(spec.label)} analytical workspace</h3><p>Analyze the official records already loaded above. Derived summaries preserve source boundaries and do not fabricate missing evidence.</p></div><span class="adi-badge">Advanced parity</span></div><div class="adi-controls"><label>Analysis mode<select data-adi-mode>${spec.modes.map(m=>`<option value="${esc(m)}">${esc(m.replaceAll("-"," "))}</option>`).join("")}</select></label><button type="button" class="earth-primary-button" data-adi-analyze>Analyze current records</button><button type="button" class="ghost-button" data-adi-packet>Build research packet</button></div><div class="adi-status" data-adi-status>Ready · waiting for analysis</div><div class="adi-output" data-adi-output><article><strong>Use the filters above first</strong><span>The analysis runs against the current workspace record set.</span></article></div>`;
    surface.appendChild(panel);
    panel.querySelector("[data-adi-analyze]").addEventListener("click",()=>run(route,false));
    panel.querySelector("[data-adi-packet]").addEventListener("click",()=>run(route,true));
    return panel;
  }
  async function run(route,packet){
    const spec=SPECS[route],panel=ensure(route);if(!panel)return;
    const mode=panel.querySelector("[data-adi-mode]").value,current=rows(route),status=panel.querySelector("[data-adi-status]"),output=panel.querySelector("[data-adi-output]");
    status.textContent=`Analyzing ${current.length} current record${current.length===1?"":"s"}…`;panel.setAttribute("aria-busy","true");
    try{
      const path=`/public/domain-intelligence/${spec.domain}/${packet?"packet":"analyze"}`;
      const response=await post(path,{mode,records:current,title:`${spec.label} · ${mode}`});
      if(packet){const p=response.packet;status.textContent=`Research packet ready · ${p.record_count} records · human-confirmed handoff only`;output.innerHTML=`<div class="adi-metrics"><article><span>Packet</span><strong>${esc(p.packet_id)}</strong></article><article><span>Records</span><strong>${esc(p.record_count)}</strong></article><article><span>Handoffs</span><strong>${esc((p.recommended_handoffs||[]).length)}</strong></article><article><span>Digest</span><strong>${esc(String(p.packet_digest||"").slice(7,19))}</strong></article></div><div class="adi-results-grid"><article><strong>Research workflow</strong>${(p.research_workflow||[]).map(x=>`<small>${esc(x.replaceAll("-"," "))}</small>`).join("")}</article><article><strong>Recommended handoffs</strong>${(p.recommended_handoffs||[]).map(x=>`<small>${esc(x)}</small>`).join("")}</article><article><strong>Boundaries</strong>${(p.boundaries||[]).map(x=>`<small>${esc(x.replaceAll("-"," "))}</small>`).join("")}</article></div>`}
      else{status.textContent=`Analysis ready · ${response.result.record_count} records · source boundaries preserved`;output.innerHTML=summaryHtml(response.result)}
    }catch(error){status.textContent=`Analysis unavailable · ${error.message||error}`;output.innerHTML=`<article><strong>Advanced analysis could not run</strong><span>The base workspace remains usable. No fallback evidence was invented.</span></article>`}
    finally{panel.setAttribute("aria-busy","false")}
  }
  function enhance(route){if(SPECS[route])ensure(route)}
  window.addEventListener("scsi:workspace-runtime-v4551",event=>enhance(event.detail?.route));
  document.addEventListener("DOMContentLoaded",()=>{const view=new URLSearchParams(location.search).get("view");if(SPECS[view])setTimeout(()=>enhance(view),250)});
  window.SCSIAdvancedDomainIntelligenceV4552={version:VERSION,specs:SPECS,enhance,run};
  document.documentElement.dataset.advancedDomainIntelligence="4.55.3.2.2";
})();
