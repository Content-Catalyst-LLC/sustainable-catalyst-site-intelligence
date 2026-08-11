(()=>{
  'use strict';
  const VERSION='4.35.6';
  const ROOT_SELECTOR=`#app[data-scsi-release="${VERSION}"]`;
  const root=()=>document.querySelector(ROOT_SELECTOR),launch=()=>document.querySelector('#launchScreen'),message=()=>document.querySelector('#launchMessage'),progress=()=>document.querySelector('#launchProgressBar'),retry=()=>document.querySelector('#launchRetry');
  const state={version:VERSION,startedAt:performance.now(),ready:false,limited:false,workerState:'not-started',controllerAtStart:Boolean(navigator.serviceWorker?.controller),reloadScheduled:false,automaticReloads:0};
  let deadlineTimer=0,workerPromise=null;
  function announce(text,percent){if(message())message().textContent=text;if(progress()&&Number.isFinite(percent))progress().style.width=`${Math.max(0,Math.min(100,percent))}%`}
  function publish(){window.dispatchEvent(new CustomEvent('scsi:bootstrap-state',{detail:{version:VERSION,state:state.ready?(state.limited?'limited':'ready'):'starting',workerState:state.workerState,automaticReloads:state.automaticReloads}}))}
  function reveal(mode='ready',text='Site Intelligence is ready.'){
    if(state.ready)return;state.ready=true;state.limited=mode!=='ready';clearTimeout(deadlineTimer);
    const app=root();if(app){app.classList.remove('app-loading');app.classList.add('app-ready');app.dataset.startupState=mode;app.removeAttribute('aria-busy')}
    announce(text,100);const screen=launch();if(screen){screen.classList.add('hidden');screen.setAttribute('aria-hidden','true')}if(retry())retry().hidden=true;publish();window.parent?.postMessage({type:'scsi-bootstrap-ready',version:VERSION,state:mode},'*');
  }
  function failOpen(reason){console.warn('[Site Intelligence] Startup recovered in limited mode.',reason||'startup deadline');reveal('limited','Site Intelligence opened with limited services. Data workspaces recover independently.')}
  function updateReady(reason='service-worker-update') {state.workerState='update-ready';publish();window.dispatchEvent(new CustomEvent('scsi:service-worker-update-ready',{detail:{version:VERSION,reason,automaticReload:false}}))}
  async function activateWaitingWorker(){const registration=await ensureWorker();if(!registration?.waiting)return false;registration.waiting.postMessage({type:'SC_SI_ACTIVATE_UPDATE'});return true}
  async function ensureWorker(){
    if(workerPromise)return workerPromise;if(!('serviceWorker' in navigator)){state.workerState='unsupported';publish();return null}
    workerPromise=(async()=>{try{state.workerState='registering';publish();const registration=await navigator.serviceWorker.register(`/app/service-worker.js?v=${encodeURIComponent(VERSION)}`,{scope:'/app/',updateViaCache:'none'});state.workerState='registered';publish();registration.update().catch(()=>{});if(registration.waiting)updateReady('waiting-at-registration');registration.addEventListener?.('updatefound',()=>{const worker=registration.installing;if(!worker)return;worker.addEventListener?.('statechange',()=>{if(worker.state==='installed'&&navigator.serviceWorker.controller)updateReady('new-worker-installed')})});return registration}catch(error){state.workerState='failed';publish();console.warn('[Site Intelligence] Offline shell unavailable; continuing without it.',error);return null}})();return workerPromise;
  }
  function scheduleWorker(){const run=()=>ensureWorker();if('requestIdleCallback'in window)requestIdleCallback(run,{timeout:2500});else setTimeout(run,600)}
  function init(){
    if(!root())return;root().setAttribute('aria-busy','true');const requested=Number(root().dataset.scsiStartupDeadlineMs||4500);const deadline=Math.max(750,Math.min(6000,requested));deadlineTimer=setTimeout(()=>failOpen('startup deadline exceeded'),deadline);
    retry()?.addEventListener('click',()=>location.reload(),{once:true});window.addEventListener('scsi:application-ready',event=>{const detail=event.detail||{};reveal(detail.state==='limited'?'limited':'ready',detail.message||'Site Intelligence is ready.')});
    window.addEventListener('error',event=>{if(!state.ready)console.warn('[Site Intelligence] Startup script error isolated.',event.error||event.message)});window.addEventListener('unhandledrejection',event=>{if(!state.ready)console.warn('[Site Intelligence] Startup promise rejection isolated.',event.reason)});
    navigator.serviceWorker?.addEventListener?.('controllerchange',()=>{state.workerState='active';publish();window.dispatchEvent(new CustomEvent('scsi:service-worker-controller-changed',{detail:{version:VERSION,automaticReload:false}}))});
    navigator.serviceWorker?.addEventListener?.('message',event=>{if(event.data?.type==='SC_SI_SW_READY'){state.workerState=event.data.version===VERSION?'active':'update-ready';publish()}});
    if(document.readyState==='complete')scheduleWorker();else window.addEventListener('load',scheduleWorker,{once:true});
    window.SCSIBootstrapV32361={version:VERSION,ensureWorker,activateWaitingWorker,reveal,failOpen,getState:()=>({...state})};window.dispatchEvent(new CustomEvent('scsi:bootstrap-ready',{detail:{version:VERSION,automaticReload:false}}));
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
