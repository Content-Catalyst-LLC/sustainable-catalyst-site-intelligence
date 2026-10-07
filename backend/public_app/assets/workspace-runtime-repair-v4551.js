(()=>{
  "use strict";
  const VERSION="4.55.1";
  const ROUTES=Object.freeze({
    economics:{controller:"SCEconomicsV220",surface:"#economicsStudio",status:"#economicsStatus",label:"Economics"},
    law:{controller:"SCLawV230",surface:"#lawStudio",status:"#lawStatus",label:"International law"},
    science:{controller:"SCScienceV240",surface:"#scienceStudio",status:"#scienceStatus",label:"Science"},
    humanitarian:{controller:"SCHumanitarianV250",surface:"#humanitarianStudio",status:"#humanitarianStatus",label:"Humanitarian"},
    resources:{controller:"SCResourcesV260",surface:"#resourceStudio",status:"#resourceStatus",label:"Resources"},
    dossiers:{controller:"SCDossiersV270",surface:"#dossierStudio",status:"#dossierStatus",label:"Dossiers"},
  });
  const state=new Map();
  const qs=s=>document.querySelector(s);
  function setStatus(spec,message){const el=qs(spec.status);if(!el)return;el.dataset.state="fallback";const target=el.querySelector("span:last-child")||el.querySelector("span")||el;target.textContent=message}
  function ensureNote(route,spec,error){const panel=qs(spec.surface);if(!panel)return;let note=panel.querySelector(`[data-workspace-runtime-repair="${route}"]`);if(!note){note=document.createElement("section");note.className="workspace-runtime-repair-note";note.dataset.workspaceRuntimeRepair=route;note.innerHTML=`<strong>${spec.label} workspace recovery</strong><span></span><button type="button">Retry workspace</button>`;note.querySelector("button").addEventListener("click",()=>open(route));panel.prepend(note)}note.querySelector("span").textContent=error?`Optional startup service did not complete (${String(error.message||error)}). The workspace shell remains usable.`:"Workspace runtime recovered."}
  async function open(route){const spec=ROUTES[route];if(!spec)throw new Error(`Unknown workspace ${route}`);const panel=qs(spec.surface);if(!panel)throw new Error(`Missing workspace surface ${spec.surface}`);panel.hidden=false;panel.setAttribute("aria-busy","true");panel.dataset.workspaceRuntimeVersion=VERSION;const controller=window[spec.controller];if(!controller?.open){const error=new Error(`${spec.controller} is not loaded`);setStatus(spec,`${spec.label} workspace controller is unavailable.`);ensureNote(route,spec,error);panel.setAttribute("aria-busy","false");state.set(route,{state:"degraded",reason:error.message});return true}try{const result=await Promise.resolve(controller.open());panel.hidden=false;panel.dataset.workspaceRuntimeState="ready";panel.querySelector(`[data-workspace-runtime-repair="${route}"]`)?.remove();state.set(route,{state:"ready"});return result===false?true:result}catch(error){console.warn(`[Site Intelligence] ${route} runtime recovery`,error);panel.hidden=false;panel.dataset.workspaceRuntimeState="degraded";setStatus(spec,`${spec.label} workspace opened with limited services.`);ensureNote(route,spec,error);state.set(route,{state:"degraded",reason:String(error?.message||error)});return true}finally{panel.hidden=false;panel.setAttribute("aria-busy","false");window.dispatchEvent(new CustomEvent("scsi:workspace-runtime-v4551",{detail:{version:VERSION,route,...(state.get(route)||{})}}))}}
  function audit(){return Object.fromEntries(Object.entries(ROUTES).map(([route,spec])=>[route,{controller:Boolean(window[spec.controller]),surface:Boolean(qs(spec.surface)),surface_id:spec.surface,controller_name:spec.controller,state:state.get(route)||null}]))}
  window.SCSIWorkspaceRuntimeRepairV4551={version:VERSION,routes:ROUTES,open,audit,status:route=>state.get(route)||null};
  document.documentElement.dataset.workspaceRuntimeRepair="4.55.1";
})();
