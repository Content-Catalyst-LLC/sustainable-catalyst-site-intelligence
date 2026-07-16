(()=>{
  const API=window.SC_SITE_INTELLIGENCE_API||location.origin;
  const q=selector=>document.querySelector(selector);
  const STORAGE_KEY="scsi_experience_v2120";
  const RELEASE="2.12.1";
  let state={lowBandwidth:false,offlineEnabled:true};

  function read(){try{return {...state,...JSON.parse(localStorage.getItem(STORAGE_KEY)||"{}")}}catch{return {...state}}}
  function write(){try{localStorage.setItem(STORAGE_KEY,JSON.stringify(state))}catch{}}
  function setStatus(text,ready=false){const el=q("#experienceConnectionStatus");if(el){el.textContent=text;el.classList.toggle("ready",ready)}}
  async function get(path){const response=await fetch(API+path,{headers:{Accept:"application/json"},cache:"no-store"});if(!response.ok)throw new Error(String(response.status));return response.json()}
  function apply(){document.documentElement.dataset.lowBandwidth=state.lowBandwidth?"1":"0";if(q("#experienceLowBandwidth"))q("#experienceLowBandwidth").checked=state.lowBandwidth;if(q("#experienceOfflineEnabled"))q("#experienceOfflineEnabled").checked=state.offlineEnabled;write()}

  async function register(){
    if(!("serviceWorker" in navigator)||!state.offlineEnabled)return null;
    const registration=await navigator.serviceWorker.register(`/app/service-worker.js?v=${RELEASE}`,{scope:"/app/",updateViaCache:"none"});
    registration.update().catch(()=>{});
    if(registration.waiting)registration.waiting.postMessage({type:"SC_SI_ACTIVATE_UPDATE"});
    return registration;
  }

  function messageWorker(worker,message,timeout=2500){
    return new Promise((resolve,reject)=>{
      if(!worker){reject(new Error("No active service worker"));return}
      const channel=new MessageChannel();
      const timer=setTimeout(()=>reject(new Error("Service worker response timed out")),timeout);
      channel.port1.onmessage=event=>{clearTimeout(timer);resolve(event.data||{})};
      worker.postMessage(message,[channel.port2]);
    });
  }

  async function clearCaches(){
    setStatus("Clearing browser-local cache",false);
    try{
      const registration=await navigator.serviceWorker?.getRegistration("/app/");
      const worker=navigator.serviceWorker?.controller||registration?.active||registration?.waiting;
      if(worker)await messageWorker(worker,{type:"SC_SI_CLEAR_OFFLINE"}).catch(()=>{});
      if("caches" in window){for(const key of await caches.keys())if(key.startsWith("scsi-"))await caches.delete(key)}
      setStatus("Offline cache cleared",navigator.onLine);
    }catch(error){
      setStatus("Cache reset incomplete — use browser site-data controls",false);
    }
  }

  function renderLists(accessibility,performance,cache,reliability){
    q("#experienceAccessibilityList").innerHTML=(accessibility.groups||[]).map(item=>`<li><strong>${item.title}</strong> — ${item.status}</li>`).join("");
    q("#experiencePerformanceList").innerHTML=Object.entries(performance.budget_checks||{}).map(([key,value])=>`<li>${key.replaceAll("_"," ")}: <strong>${value?"within budget":"over budget"}</strong></li>`).join("");
    const strategies=Object.entries(cache.strategies||{}).map(([key,value])=>`<li><strong>${key.replaceAll("_"," ")}</strong> — ${value}</li>`);
    strategies.push(`<li><strong>Embed reliability</strong> — source-window and origin checked; ${reliability.embeds?.mobile_minimum_height||760}px mobile minimum; ${reliability.embeds?.maximum_height||2600}px maximum.</li>`);
    q("#experienceCacheList").innerHTML=strategies.join("");
    q("#experienceShellBytes").textContent=Intl.NumberFormat().format(performance.file_sizes?.first_party_shell_bytes||0);
    q("#experienceCacheEntries").textContent=String(cache.limits?.maximum_entries||"—");
  }

  async function open(){
    const panel=q("#offlineExperienceStudio");if(!panel)return;
    panel.hidden=false;panel.setAttribute("aria-busy","true");
    state=read();if(navigator.connection?.saveData)state.lowBandwidth=true;apply();
    setStatus(navigator.onLine?"Online":"Offline — cached records may be stale",navigator.onLine);
    try{
      const [overview,accessibility,performance,cache,reliability]=await Promise.all([
        get("/public/offline-experience"),
        get("/public/offline-experience/accessibility"),
        get("/public/offline-experience/performance"),
        get("/public/offline-experience/cache-plan"),
        get("/public/offline-experience/reliability")
      ]);
      q("#experienceVersion").textContent=`v${overview.version}`;
      q("#experiencePwaState").textContent=cache.enabled?"Available":"Disabled";
      q("#experienceSummary").textContent="Install the release-aligned application shell, inspect bounded cache behavior, recover browser-local offline data, and verify responsive WordPress embed delivery.";
      renderLists(accessibility,performance,cache,reliability);
      if(state.offlineEnabled)await register();
    }catch(error){
      q("#experienceSummary").textContent="The static experience controls remain available, but diagnostics could not be refreshed.";
    }finally{panel.setAttribute("aria-busy","false")}
  }

  function close(){const panel=q("#offlineExperienceStudio");if(panel)panel.hidden=true}
  function init(){
    q("#experienceLowBandwidth")?.addEventListener("change",event=>{state.lowBandwidth=event.target.checked;apply()});
    q("#experienceOfflineEnabled")?.addEventListener("change",async event=>{state.offlineEnabled=event.target.checked;apply();if(state.offlineEnabled)await register().catch(()=>setStatus("Offline shell registration failed",false))});
    q("#experienceClearCache")?.addEventListener("click",clearCaches);
    q("#experienceInstall")?.addEventListener("click",()=>{q("#experienceInstallHelp").hidden=false});
    addEventListener("online",()=>setStatus("Online",true));
    addEventListener("offline",()=>setStatus("Offline — cached records may be stale",false));
    navigator.serviceWorker?.addEventListener("message",event=>{if(event.data?.type==="SC_SI_OFFLINE_CLEARED")setStatus("Offline cache cleared",navigator.onLine)});
  }
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init,{once:true});else init();
  window.SCExperienceV2120={open,close,clearCaches};
})();
