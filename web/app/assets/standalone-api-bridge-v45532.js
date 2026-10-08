(()=>{
  "use strict";
  const RELEASE="4.56.0";
  const cfg=window.__SC_SITE_INTELLIGENCE_CONFIG__||{};
  const apiOrigin=String(cfg.apiOrigin||"https://site-intelligence-api.sustainablecatalyst.com").replace(/\/$/,"");
  const appOrigin=String(cfg.appOrigin||location.origin||"").replace(/\/$/,"");
  const API_PREFIXES=["/public/","/api/","/health","/ready","/openapi.json","/docs"];
  const reliable=[
    ["/public/economics-sustainability/records","/public/reliable/economics/records"],
    ["/public/international-law-observatory/records","/public/reliable/law/records"],
    ["/public/scientific-earth-systems/records","/public/reliable/science/records"],
    ["/public/humanitarian-conflict-displacement/records","/public/reliable/humanitarian/records"],
    ["/public/trade-energy-resources/records","/public/reliable/resources/records"],
    ["/public/intelligence-dossiers/country","/public/reliable/dossiers/country"]
  ];
  function rewritePath(path){for(const [from,to] of reliable){if(path===from||path.startsWith(from+"?"))return to+path.slice(from.length)}return path}
  function toApi(value){
    try{
      const raw=typeof value==="string"?value:value instanceof URL?value.href:value?.url;
      if(!raw)return null;
      const u=new URL(raw,appOrigin||location.href);
      if(!raw.startsWith("/")&&u.origin!==appOrigin&&u.origin!==location.origin)return null;
      if(!API_PREFIXES.some(p=>u.pathname===p||u.pathname.startsWith(p)))return null;
      return apiOrigin+rewritePath(u.pathname)+(u.search||"");
    }catch{return null}
  }
  const nativeFetch=window.fetch.bind(window);
  window.fetch=(input,init)=>{const target=toApi(input);if(!target)return nativeFetch(input,init);const opts={credentials:cfg.apiCredentials||"include",...(init||{})};return nativeFetch(target,opts)};
  const NativeXHR=window.XMLHttpRequest;
  if(NativeXHR){const open=NativeXHR.prototype.open;NativeXHR.prototype.open=function(method,url,...rest){const target=toApi(url);return open.call(this,method,target||url,...rest)}}
  const aliases={country:"country",dossiers:"dossiers",economics:"economics",law:"law",science:"science",humanitarian:"humanitarian",resources:"resources",events:"events",research:"research",packages:"research",earth:"earth",ocean:"science",space:"science"};
  const parts=location.pathname.split("/").filter(Boolean);
  if(parts[0]!=="app"&&parts.length){
    let key=parts[0],country="";
    if(key==="science"&&parts[1]==="earth"){key="science";country=parts[2]||""}else country=parts[1]||"";
    const view=aliases[key];
    if(view){
      const q=new URLSearchParams(location.search);
      if(!q.has("view"))q.set("view",view);
      if(country&&!q.has("country"))q.set("country",country.toUpperCase());
      const resolved=String(country||q.get("country")||"").toUpperCase();
      if(resolved&&["economics","science","resources"].includes(view)&&!q.has("geography_code"))q.set("geography_code",resolved);
      if(resolved&&["law","humanitarian","dossiers"].includes(view)&&!q.has("country"))q.set("country",resolved);
      try{history.replaceState(null,"",location.pathname+"?"+q.toString())}catch{}
    }
  }
  window.SCSIStandaloneBridgeV45532=Object.freeze({version:RELEASE,apiOrigin,appOrigin,rewritePath,toApi});
  window.SCSIStandaloneBridgeV455321=window.SCSIStandaloneBridgeV45532;
  window.dispatchEvent(new CustomEvent("scsi:standalone-api-bridge-ready",{detail:{version:RELEASE,apiOrigin}}));
})();
