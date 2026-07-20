const RELEASE="3.2.0";
const CACHE_PREFIX="scsi-";
const VERSION=`${CACHE_PREFIX}v${RELEASE}`;
const SHELL=`${VERSION}-shell`;
const DATA=`${VERSION}-data`;
const OFFLINE="/app/offline.html";
const APP_HOME="/app/";
const MAX_DATA_ENTRIES=120;
const MAX_SHELL_ENTRIES=80;
const MAX_DATA_AGE_MS=24*60*60*1000;
const SHELL_URLS=["/app/","/app/offline.html","/app/manifest.webmanifest","/app/assets/alerts-v280.css","/app/assets/alerts-v280.js","/app/assets/app.css","/app/assets/app.js","/app/assets/dossiers-v270.css","/app/assets/dossiers-v270.js","/app/assets/economics-v220.css","/app/assets/economics-v220.js","/app/assets/experience-v2120.css","/app/assets/experience-v2120.js","/app/assets/global-conditions-v210.css","/app/assets/global-conditions-v210.js","/app/assets/humanitarian-v250.css","/app/assets/humanitarian-v250.js","/app/assets/icon-192.png","/app/assets/icon-512.png","/app/assets/integration-v2110.css","/app/assets/integration-v2110.js","/app/assets/law-v230.css","/app/assets/law-v230.js","/app/assets/research-v2100.css","/app/assets/research-v2100.js","/app/assets/resources-v260.css","/app/assets/resources-v260.js","/app/assets/scenarios-v290.css","/app/assets/scenarios-v290.js","/app/assets/science-v240.css","/app/assets/science-v240.js","/app/assets/spatial-v2150.css","/app/assets/spatial-v2150.js","/app/assets/harmonization-v2160.css","/app/assets/harmonization-v2160.js","/app/assets/models-v2170.css","/app/assets/models-v2170.js","/app/assets/evidence-v2180.css","/app/assets/evidence-v2180.js","/app/assets/graph-v2190.css","/app/assets/graph-v2190.js","/app/assets/publishing-v2200.css","/app/assets/publishing-v2200.js","/app/assets/monitoring-v2210.css","/app/assets/monitoring-v2210.js","/app/assets/workspaces-v2220.css","/app/assets/workspaces-v2220.js","/app/assets/workflows-v2230.css","/app/assets/workflows-v2230.js","/app/assets/federation-v2240.css","/app/assets/federation-v2240.js","/app/assets/governance-v2250.css","/app/assets/governance-v2250.js","/app/assets/platform-v300.css","/app/assets/platform-v300.js"];

function cacheable(response){
  if(!response||!response.ok||response.type==="opaque")return false;
  const policy=(response.headers.get("Cache-Control")||"").toLowerCase();
  return !policy.includes("no-store")&&!policy.includes("private");
}

async function stamped(response){
  const body=await response.clone().blob();
  const headers=new Headers(response.headers);
  headers.set("X-SCSI-Cached-At",String(Date.now()));
  headers.set("X-SCSI-Release",RELEASE);
  return new Response(body,{status:response.status,statusText:response.statusText,headers});
}

function cachedAt(response){
  const explicit=Number(response?.headers.get("X-SCSI-Cached-At")||0);
  if(Number.isFinite(explicit)&&explicit>0)return explicit;
  const date=Date.parse(response?.headers.get("Date")||"");
  return Number.isFinite(date)?date:0;
}

async function trimCache(cacheName,maximum){
  const cache=await caches.open(cacheName);
  const requests=await cache.keys();
  if(requests.length<=maximum)return;
  const entries=await Promise.all(requests.map(async request=>({request,time:cachedAt(await cache.match(request))})));
  entries.sort((a,b)=>a.time-b.time);
  await Promise.all(entries.slice(0,Math.max(0,entries.length-maximum)).map(entry=>cache.delete(entry.request)));
}

async function putBounded(cacheName,request,response,maximum,force=false){
  if(!force&&!cacheable(response))return;
  const cache=await caches.open(cacheName);
  await cache.put(request,await stamped(response));
  await trimCache(cacheName,maximum);
}

async function cachedResponse(cacheName,request,{maximumAgeMs=Infinity,ignoreSearch=false}={}){
  const cache=await caches.open(cacheName);
  const response=await cache.match(request,{ignoreSearch});
  if(!response)return null;
  const time=cachedAt(response);
  if(Number.isFinite(maximumAgeMs)&&time&&Date.now()-time>maximumAgeMs){
    await cache.delete(request);
    return null;
  }
  return response;
}

async function fetchAndCache(request,cacheName,maximum){
  const response=await fetch(request);
  if(cacheable(response))await putBounded(cacheName,request,response.clone(),maximum);
  return response;
}

async function installShell(){
  const results=await Promise.allSettled(SHELL_URLS.map(async url=>{
    const request=new Request(url,{cache:"reload",credentials:"same-origin"});
    const response=await fetch(request);
    if(!response.ok)throw new Error(`${url}:${response.status}`);
    await putBounded(SHELL,request,response,MAX_SHELL_ENTRIES,true);
  }));
  const available=results.filter(result=>result.status==="fulfilled").length;
  if(available===0)throw new Error("No application-shell assets could be cached.");
}

async function broadcast(message){
  const clients=await self.clients.matchAll({type:"window",includeUncontrolled:true});
  clients.forEach(client=>client.postMessage(message));
}

self.addEventListener("install",event=>{
  event.waitUntil(installShell().then(()=>self.skipWaiting()));
});

self.addEventListener("activate",event=>{
  event.waitUntil((async()=>{
    const keys=await caches.keys();
    await Promise.all(keys.filter(key=>key.startsWith(CACHE_PREFIX)&&!key.startsWith(VERSION)).map(key=>caches.delete(key)));
    if(self.registration.navigationPreload)await self.registration.navigationPreload.enable().catch(()=>{});
    await self.clients.claim();
    await broadcast({type:"SC_SI_SW_READY",version:RELEASE});
  })());
});

async function navigationResponse(event){
  const request=event.request;
  try{
    const preload=await event.preloadResponse;
    const response=preload||await fetch(request,{cache:"no-store"});
    if(response?.ok)await putBounded(DATA,request,response.clone(),MAX_DATA_ENTRIES,true);
    return response;
  }catch(error){
    const exact=await cachedResponse(DATA,request,{maximumAgeMs:MAX_DATA_AGE_MS});
    if(exact)return exact;
    const shell=await cachedResponse(SHELL,APP_HOME,{ignoreSearch:true});
    if(shell)return shell;
    return (await cachedResponse(SHELL,OFFLINE,{ignoreSearch:true}))||Response.error();
  }
}

async function staleWhileRevalidate(request){
  const cached=await cachedResponse(SHELL,request,{ignoreSearch:false});
  const network=fetchAndCache(request,SHELL,MAX_SHELL_ENTRIES).catch(()=>null);
  return cached||await network||Response.error();
}

async function networkFirstData(request){
  try{
    return await fetchAndCache(request,DATA,MAX_DATA_ENTRIES);
  }catch(error){
    const cached=await cachedResponse(DATA,request,{maximumAgeMs:MAX_DATA_AGE_MS});
    if(cached)return cached;
    throw error;
  }
}

self.addEventListener("fetch",event=>{
  const request=event.request;
  if(request.method!=="GET")return;
  const url=new URL(request.url);
  if(url.origin!==self.location.origin)return;
  if(request.mode==="navigate"){
    event.respondWith(navigationResponse(event));
    return;
  }
  if(url.pathname.startsWith("/app/assets/")||url.pathname==="/app/manifest.webmanifest"||url.pathname==="/app/offline.html"){
    event.respondWith(staleWhileRevalidate(request));
    return;
  }
  if(url.pathname.startsWith("/public/")||url.pathname.startsWith("/api/public/")){
    event.respondWith(networkFirstData(request));
  }
});

self.addEventListener("message",event=>{
  const data=event.data||{};
  if(data.type==="SC_SI_GET_VERSION"){
    event.ports?.[0]?.postMessage({ok:true,version:RELEASE,cachePrefix:VERSION});
    return;
  }
  if(data.type==="SC_SI_ACTIVATE_UPDATE"){
    event.waitUntil(self.skipWaiting());
    return;
  }
  if(data.type==="SKIP_WAITING"){
    event.waitUntil(self.skipWaiting());
    return;
  }
  if(data.type==="SC_SI_CLEAR_OFFLINE"){
    event.waitUntil((async()=>{
      const keys=await caches.keys();
      await Promise.all(keys.filter(key=>key.startsWith(CACHE_PREFIX)).map(key=>caches.delete(key)));
      event.ports?.[0]?.postMessage({ok:true,cleared:true,version:RELEASE});
      await broadcast({type:"SC_SI_OFFLINE_CLEARED",version:RELEASE});
    })());
  }
});
