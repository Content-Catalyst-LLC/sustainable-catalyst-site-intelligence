(() => {
  const VERSION="3.7.2", API=window.SC_SITE_INTELLIGENCE_API||window.location.origin;
  const qs=s=>document.querySelector(s), esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]));
  const state={loaded:false,summary:null,models:[],forecasts:[],evaluations:[],warnings:null};
  async function get(path){const r=await fetch(`${API}${path}`,{headers:{Accept:"application/json"}});if(!r.ok)throw new Error(`${r.status} ${path}`);return r.json()}
  function row(title,detail,badge=""){return `<div class="model-row"><div><strong>${esc(title)}</strong><small>${esc(detail)}</small></div>${badge?`<span class="model-badge">${esc(badge)}</span>`:""}</div>`}
  function render(){
    const c=state.summary?.counts||{};
    qs("#modelCount").textContent=c.models??0;qs("#forecastCount").textContent=c.forecasts??0;qs("#evaluationCount").textContent=c.evaluations??0;qs("#warningCount").textContent=c.warning_events??0;
    qs("#modelRegistryList").innerHTML=state.models.length?state.models.slice(0,20).map(x=>row(x.title||x.model_id,`${x.model_type||"model"} · v${x.model_version||"?"} · ${x.target||"target not declared"}`,x.status||"active")).join(""):row("No published model cards","Administrators can register reviewed model cards before publishing forecasts.");
    qs("#forecastList").innerHTML=state.forecasts.length?state.forecasts.slice(-12).reverse().map(x=>row(x.forecast_id,`${x.target||"forecast"} · ${x.values?.length||0} periods · issued ${x.issued_at||"date unavailable"}`,x.scenario_label||"forecast")).join(""):row("No published forecasts","Forecasts appear only after attribution to an active model card.");
    qs("#evaluationList").innerHTML=state.evaluations.length?state.evaluations.slice(-12).reverse().map(x=>row(x.forecast_id,`MAE ${Number(x.metrics?.mae??0).toFixed(3)} · RMSE ${Number(x.metrics?.rmse??0).toFixed(3)} · coverage ${x.interval_diagnostics?.empirical_coverage??"n/a"}`,x.drift?.status||"not reviewed")).join(""):row("No public evaluations","Backtesting and calibration records appear when observed values overlap forecast periods.");
    const events=state.warnings?.events||[];
    qs("#warningList").innerHTML=events.length?events.slice(-12).reverse().map(x=>row(x.rule_id,`${x.latest_period||"period"} · value ${x.latest_value} · threshold ${x.direction} ${x.threshold}`,x.matched?x.severity:"clear")).join(""):row("No public warning events","Threshold indicators are review signals, not emergency instructions.");
    qs("#modelStatus").textContent="Model cards, forecasts, evaluations, and warning boundaries loaded.";
  }
  async function load(){const p=qs("#modelGovernanceStudio");if(!p)return;p.setAttribute("aria-busy","true");try{const [summary,models,forecasts,evaluations,warnings]=await Promise.all([get("/public/model-governance"),get("/public/models"),get("/public/forecasts"),get("/public/forecast-evaluations"),get("/public/early-warning")]);state.summary=summary;state.models=models.models||[];state.forecasts=forecasts.forecasts||[];state.evaluations=evaluations.evaluations||[];state.warnings=warnings;state.loaded=true;render()}catch(e){qs("#modelStatus").textContent="Model-governance services could not be refreshed. No forecast or warning should be treated as current without source verification.";console.warn(e)}finally{p.setAttribute("aria-busy","false");window.parent?.postMessage({type:"scsi-height",height:document.documentElement.scrollHeight,version:VERSION},"*")}}
  function open(){const p=qs("#modelGovernanceStudio");if(!p)return;p.hidden=false;if(!state.loaded)load()}
  function close(){const p=qs("#modelGovernanceStudio");if(p)p.hidden=true}
  window.SCModelsV2170={open,close,status:()=>({version:VERSION,loaded:state.loaded,models:state.models.length})};
})();
