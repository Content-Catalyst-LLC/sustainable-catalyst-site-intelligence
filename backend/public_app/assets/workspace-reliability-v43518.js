(() => {
  "use strict";
  const VERSION = "4.38.0";
  const SURFACES = Object.freeze({
    overview:"#map",global:"#globalConditionsObservatory",events:"#eventStudio",alerts:"#alertsStudio",
    country:"#globalCountryExplorer",dossiers:"#dossierStudio",economics:"#economicsStudio",law:"#lawStudio",
    science:"#scienceStudio",humanitarian:"#humanitarianStudio",resources:"#resourceStudio",thematic:"#thematicStudio",
    compare:"#compareStudio",spatial:"#spatialEvidenceStudio",earth:"#earthStudio",harmonization:"#harmonizationStudio",
    models:"#modelGovernanceStudio",scenarios:"#scenarioStudio",platform:"#connectedPlatformStudio",observatory:"#auditablePublicObservatory",
    research:"#researchWorkflowStudio",evidence:"#evidenceSynthesisStudio",graph:"#knowledgeGraphExplorer",sources:"#sourceStudio",
    saved:"#savedViewsStudio",briefing:"#briefingStudio",publishing:"#intelligencePublishingStudio",monitoring:"#scheduledMonitoringStudio",
    workspaces:"#institutionalWorkspaceStudio",integration:"#publicDataIntegrationStudio",workflows:"#crossPlatformWorkflowStudio",
    federation:"#institutionalDataExchangeStudio",governance:"#productionGovernanceStudio",experience:"#offlineExperienceStudio",launch:"#publicLaunchPortfolio"
  });
  const states = new Map();
  const visible = el => !!el && !el.hidden && getComputedStyle(el).display !== "none" && getComputedStyle(el).visibility !== "hidden";
  const titleFor = route => document.querySelector("#viewTitle")?.textContent?.trim() || String(route||"Workspace").replaceAll("-"," ");
  const descriptionFor = () => document.querySelector("#viewDescription")?.textContent?.trim() || "The public workspace remains available while one or more optional services recover.";
  function recovery(route, reason="workspace surface unavailable"){
    const panel=document.querySelector("#routePanel");
    if(!panel)return false;
    panel.hidden=false;panel.dataset.workspaceRecovery=route;panel.classList.add("workspace-recovery");
    panel.innerHTML=`<div class="workspace-recovery-card" role="status" aria-live="polite"><p class="eyebrow">PUBLIC WORKSPACE · DEGRADED MODE</p><h2>${escapeHtml(titleFor(route))}</h2><p>${escapeHtml(descriptionFor())}</p><p class="workspace-recovery-note">This registered workspace opened in recovery mode because an optional module or data service did not complete. No missing value has been converted to zero and no upstream outage blocks the rest of Site Intelligence.</p><div class="workspace-recovery-actions"><button type="button" class="ghost-button" data-workspace-retry="${escapeHtml(route)}">Retry workspace</button><button type="button" class="ghost-button" data-workspace-sources>Sources & methods</button></div><small>${escapeHtml(reason)}</small></div>`;
    panel.querySelector("[data-workspace-retry]")?.addEventListener("click",()=>window.SCSIRouterV3228?.navigate?.(route));
    panel.querySelector("[data-workspace-sources]")?.addEventListener("click",()=>window.SCSIRouterV3228?.navigate?.("sources"));
    states.set(route,{route,state:"degraded",reason,recovered_at:new Date().toISOString()});
    document.documentElement.dataset.workspaceReliability="degraded";
    window.dispatchEvent(new CustomEvent("scsi:workspace-degraded",{detail:{version:VERSION,route,reason}}));
    return true;
  }
  function escapeHtml(value){return String(value??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]))}
  async function enforce(route,failureReason=""){
    const selector=SURFACES[route];
    if(!selector)return recovery(route,"registered route has no surface mapping");
    await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
    const el=document.querySelector(selector);
    if(visible(el)){
      const panel=document.querySelector("#routePanel");if(panel?.classList.contains("workspace-recovery")){panel.hidden=true;panel.classList.remove("workspace-recovery");panel.removeAttribute("data-workspace-recovery");panel.innerHTML=""}
      const mode=failureReason?"degraded":"ready";
      states.set(route,{route,state:mode,selector,reason:failureReason||undefined,checked_at:new Date().toISOString()});
      document.documentElement.dataset.workspaceReliability=mode;
      return true;
    }
    const reason=!el?`surface ${selector} was not created`:`surface ${selector} remained hidden`;
    const recovered=recovery(route,reason);
    if(document.readyState!=="complete")window.addEventListener("load",()=>setTimeout(()=>window.SCSIRouterV3228?.navigate?.(route),0),{once:true});
    return recovered;
  }
  window.SCSIWorkspaceReliabilityV43518={version:VERSION,surfaces:SURFACES,enforce,recover:recovery,status:route=>states.get(route)||null,allStates:()=>Object.fromEntries(states)};
  document.documentElement.dataset.workspaceReliabilityControlPlane="ready";
})();
