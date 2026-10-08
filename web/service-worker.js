const RELEASE="4.55.3.1";
const CACHE=`sc-site-intelligence-web-${RELEASE}`;
const SHELL=["/","/index.html","/config.js","/assets/styles.css","/assets/app.js","/assets/api-client.js","/assets/context-store.js","/assets/router.js","/assets/views.js","/assets/auth-bridge.js","/manifest.webmanifest"];
self.addEventListener("install",e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(SHELL)).then(()=>self.skipWaiting())));
self.addEventListener("activate",e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith("sc-site-intelligence-web-")&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener("fetch",e=>{
  const u=new URL(e.request.url);
  if(e.request.method!=="GET"||u.origin!==self.location.origin)return;
  if(e.request.mode==="navigate"){ e.respondWith(fetch(e.request).catch(()=>caches.match("/index.html"))); return; }
  e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request)));
});
