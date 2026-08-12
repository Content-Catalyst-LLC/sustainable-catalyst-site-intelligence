(()=>{
  'use strict';
  const VERSION='4.35.13';
  const SHELL_TARGET_MS=1500;
  const HARD_FAIL_OPEN_MS=4500;
  const startedAt=performance.now();
  const state={version:VERSION,phase:'script-ready',shellReady:false,applicationReady:false,hydrated:false,hardFailOpen:false,routeTransitions:0,routeFailures:0,workerUpdates:0,lastReason:'script-ready'};
  const qs=(selector)=>document.querySelector(selector);
  function dispatch(type,detail={}){window.dispatchEvent(new CustomEvent(type,{detail:{version:VERSION,...detail}}))}
  function markPhase(phase,reason=phase){state.phase=phase;state.lastReason=reason;const app=qs('#app');if(app)app.dataset.scsiStartupPhase=phase;dispatch('scsi:startup-phase',{phase,reason,elapsedMs:Math.round(performance.now()-startedAt)})}
  function revealShell(reason='shell-ready',mode='limited'){
    if(state.shellReady)return false;
    state.shellReady=true;state.hardFailOpen=reason==='hard-fail-open';markPhase('shell-ready',reason);
    const app=qs('#app');if(app){app.classList.remove('app-loading');app.classList.add('app-ready');app.dataset.startupState=app.dataset.startupState||mode;app.removeAttribute('aria-busy')}
    const launch=qs('#launchScreen');if(launch){launch.classList.add('hidden');launch.setAttribute('aria-hidden','true')}
    const retry=qs('#launchRetry');if(retry)retry.hidden=true;
    window.parent?.postMessage({type:'scsi-shell-ready',version:VERSION,state:mode,reason},'*');
    dispatch('scsi:shell-ready',{state:mode,reason,elapsedMs:Math.round(performance.now()-startedAt)});
    return true;
  }
  function applicationReady(event){state.applicationReady=true;state.shellReady=true;markPhase('application-ready',event?.detail?.state||'ready')}
  function hydrated(event){state.hydrated=true;markPhase('hydrated',event?.detail?.state||'settled')}
  function routeStart(){state.routeTransitions+=1;document.documentElement.dataset.scsiRouteBusy='true'}
  function routeEnd(event){document.documentElement.dataset.scsiRouteBusy='false';if(event?.detail?.ok===false)state.routeFailures+=1}
  function init(){
    const app=qs('#app[data-scsi-release]');if(!app||app.dataset.scsiRelease!==VERSION)return;
    markPhase('dom-ready');
    window.addEventListener('scsi:application-ready',applicationReady);
    window.addEventListener('scsi:startup-hydrated',hydrated);
    window.addEventListener('scsi:route-transition-start',routeStart);
    window.addEventListener('scsi:route-transition-end',routeEnd);
    window.addEventListener('scsi:bootstrap-state',event=>{if(event.detail?.workerState==='update-ready')state.workerUpdates+=1});
    setTimeout(()=>{if(!state.shellReady&&!state.applicationReady)revealShell('shell-target-exceeded','limited')},SHELL_TARGET_MS);
    setTimeout(()=>{if(!state.shellReady&&!state.applicationReady)revealShell('hard-fail-open','limited')},HARD_FAIL_OPEN_MS);
    window.SCSIStartupStabilityV32364={version:VERSION,revealShell,markPhase,getState:()=>({...state,elapsedMs:Math.round(performance.now()-startedAt)})};
    dispatch('scsi:startup-stability-ready',{shellTargetMs:SHELL_TARGET_MS,hardFailOpenMs:HARD_FAIL_OPEN_MS});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
