(()=>{
  'use strict';
  const VERSION='3.23.6.1';
  const ROOT_SELECTOR=`#app[data-scsi-release="${VERSION}"]`;
  const root=()=>document.querySelector(ROOT_SELECTOR);
  const launch=()=>document.querySelector('#launchScreen');
  const message=()=>document.querySelector('#launchMessage');
  const progress=()=>document.querySelector('#launchProgressBar');
  const retry=()=>document.querySelector('#launchRetry');
  const state={version:VERSION,startedAt:performance.now(),ready:false,limited:false,workerState:'not-started',controllerAtStart:Boolean(navigator.serviceWorker?.controller),reloadScheduled:false};
  let deadlineTimer=0;
  let workerPromise=null;

  function announce(text,percent){
    if(message())message().textContent=text;
    if(progress()&&Number.isFinite(percent))progress().style.width=`${Math.max(0,Math.min(100,percent))}%`;
  }
  function reveal(mode='ready',text='Site Intelligence is ready.'){
    if(state.ready&&mode==='ready')return;
    state.ready=true;state.limited=mode!=='ready';
    clearTimeout(deadlineTimer);
    const app=root();
    if(app){app.classList.remove('app-loading');app.classList.add('app-ready');app.dataset.startupState=mode;app.removeAttribute('aria-busy')}
    announce(text,100);
    const screen=launch();if(screen){screen.classList.add('hidden');screen.setAttribute('aria-hidden','true')}
    if(retry())retry().hidden=true;
    window.dispatchEvent(new CustomEvent('scsi:bootstrap-state',{detail:{version:VERSION,state:mode,workerState:state.workerState}}));
    window.parent?.postMessage({type:'scsi-bootstrap-ready',version:VERSION,state:mode},'*');
  }
  function failOpen(reason){
    console.warn('[Site Intelligence] Startup recovered in limited mode.',reason||'startup deadline');
    reveal('limited','Site Intelligence opened with limited services. Maps and evidence can recover independently.');
  }
  function scheduleReload(){
    if(!state.controllerAtStart||state.reloadScheduled)return;
    const key=`scsi-bootstrap-reloaded-${VERSION}`;
    if(sessionStorage.getItem(key)==='1')return;
    state.reloadScheduled=true;
    const reload=()=>{if(sessionStorage.getItem(key)==='1')return;sessionStorage.setItem(key,'1');location.reload()};
    if(state.ready)setTimeout(reload,150);else window.addEventListener('scsi:application-ready',()=>setTimeout(reload,150),{once:true});
    setTimeout(()=>{if(!state.ready)failOpen('service worker changed during startup')},2500);
  }
  async function ensureWorker(){
    if(workerPromise)return workerPromise;
    if(!('serviceWorker' in navigator)){state.workerState='unsupported';return null}
    workerPromise=(async()=>{
      try{
        state.workerState='registering';
        const registration=await navigator.serviceWorker.register(`/app/service-worker.js?v=${encodeURIComponent(VERSION)}`,{scope:'/app/',updateViaCache:'none'});
        state.workerState='registered';
        registration.update().catch(()=>{});
        const activate=()=>{if(registration.waiting){state.workerState='update-ready';registration.waiting.postMessage({type:'SC_SI_ACTIVATE_UPDATE'})}};
        if(registration.waiting)activate();
        registration.addEventListener?.('updatefound',()=>{
          const worker=registration.installing;if(!worker)return;
          worker.addEventListener?.('statechange',()=>{if(worker.state==='installed'&&navigator.serviceWorker.controller)activate()});
        });
        return registration;
      }catch(error){
        state.workerState='failed';
        console.warn('[Site Intelligence] Offline shell unavailable; continuing without it.',error);
        return null;
      }
    })();
    return workerPromise;
  }
  function init(){
    if(!root())return;
    root().setAttribute('aria-busy','true');
    const requested=Number(root().dataset.scsiStartupDeadlineMs||document.documentElement.dataset.scsiStartupDeadlineMs||9000);
    const deadline=Math.max(250,Math.min(15000,requested));
    deadlineTimer=setTimeout(()=>failOpen('startup deadline exceeded'),deadline);
    retry()?.addEventListener('click',()=>location.reload(),{once:true});
    window.addEventListener('scsi:application-ready',event=>{
      const detail=event.detail||{};
      reveal(detail.state==='limited'?'limited':'ready',detail.message||'Site Intelligence is ready.');
    });
    window.addEventListener('error',event=>{if(!state.ready)console.warn('[Site Intelligence] Startup script error isolated.',event.error||event.message)});
    window.addEventListener('unhandledrejection',event=>{if(!state.ready)console.warn('[Site Intelligence] Startup promise rejection isolated.',event.reason)});
    navigator.serviceWorker?.addEventListener?.('controllerchange',scheduleReload);
    navigator.serviceWorker?.addEventListener?.('message',event=>{
      if(event.data?.type==='SC_SI_SW_READY'){
        state.workerState=event.data.version===VERSION?'active':'update-ready';
        window.dispatchEvent(new CustomEvent('scsi:bootstrap-state',{detail:{version:VERSION,state:state.ready?(state.limited?'limited':'ready'):'starting',workerState:state.workerState}}));
      }
    });
    // Offline capability is optional and never blocks the application.
    if(document.readyState==='complete')ensureWorker();else window.addEventListener('load',()=>ensureWorker(),{once:true});
    window.SCSIBootstrapV32361={version:VERSION,ensureWorker,reveal,failOpen,getState:()=>({...state})};
    window.dispatchEvent(new CustomEvent('scsi:bootstrap-ready',{detail:{version:VERSION}}));
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
