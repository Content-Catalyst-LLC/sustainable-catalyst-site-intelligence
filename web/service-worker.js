const RELEASE="4.55.3.2";
const CACHE=`sc-site-intelligence-web-${RELEASE}`;
const SHELL=["/","/index.html","/config.js","/app/manifest.webmanifest","/app/assets/app.css","/app/assets/app.js","/app/assets/standalone-api-bridge-v45532.js","/app/assets/standalone-functional-parity-v45532.js"];
self.addEventListener("install",e=>e.waitUntil(caches.open(CACHE).then(c=>Promise.allSettled(SHELL.map(x=>c.add(x)))).then(()=>self.skipWaiting())));
self.addEventListener("activate",e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith("sc-site-intelligence-web-")&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener("fetch",e=>{const u=new URL(e.request.url);if(e.request.method!=="GET"||u.origin!==self.location.origin)return;if(e.request.mode==="navigate"){e.respondWith(fetch(e.request).catch(()=>caches.match("/index.html")));return}e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request)))});
