(()=>{
  "use strict"; const VERSION="4.55.3.2.2";
  const qs=s=>document.querySelector(s);
  async function refresh(){
    const country=String(qs("#countrySelect")?.value||new URLSearchParams(location.search).get("country")||"KEN").toUpperCase();
    try{
      const [health,parity]=await Promise.all([fetch(`/public/capability-health?probe=true&country=${encodeURIComponent(country)}`).then(r=>r.json()),fetch('/public/web-app/parity').then(r=>r.json())]);
      const bar=qs('#standaloneAuthorityBar'), text=qs('#standaloneAuthorityStatus'), ver=qs('#standaloneAuthorityVersion');
      if(bar)bar.dataset.state=health.overall_state||'unknown'; if(text)text.textContent=`Standalone parity · ${health.overall_state||'unknown'} · ${health.usable_capabilities??0} usable · ${health.unavailable_capabilities??0} unavailable`; if(ver)ver.textContent=`v${VERSION}`;
      document.documentElement.dataset.scsiParity='functional'; document.documentElement.dataset.scsiDomainState=health.overall_state||'unknown';
      window.dispatchEvent(new CustomEvent('scsi:functional-parity-ready',{detail:{version:VERSION,health,parity}}));
    }catch(error){const text=qs('#standaloneAuthorityStatus');if(text)text.textContent='Standalone parity · API state unavailable';document.documentElement.dataset.scsiParity='degraded';}
  }
  addEventListener('DOMContentLoaded',()=>{refresh();qs('#countrySelect')?.addEventListener('change',()=>setTimeout(refresh,0));});
  addEventListener('scsi:route-transition-end',()=>refresh());
  window.SCSIStandaloneParityV45532=Object.freeze({version:VERSION,refresh});
})();
