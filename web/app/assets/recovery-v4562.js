/* Site Intelligence v4.56.2 targeted standalone recovery */
(()=>{'use strict';
const API='https://site-intelligence-api.sustainablecatalyst.com';
const qs=s=>document.querySelector(s);
let loading=false;
const notice=(message,error=false)=>{
 let el=qs('#scsiRecoveryNotice');
 if(!el){el=document.createElement('div');el.id='scsiRecoveryNotice';el.setAttribute('role','status');const select=qs('#countrySelect');select?.parentElement?.appendChild(el);}
 if(el){el.textContent=message;el.dataset.error=error?'true':'false';}
};
async function catalog(){
 for(const origin of ['',API]){
  for(const path of ['/public/countries','/public/data-truth/countries']){
   try{const response=await fetch(origin+path,{headers:{Accept:'application/json'},cache:'no-store'});if(!response.ok)throw Error('HTTP '+response.status);
   const data=await response.json();
   if(Array.isArray(data.countries)&&data.countries.length>50)return data.countries;
   }catch(e){console.warn('[SCSI recovery] country catalog',origin+path,String(e));}
  }
 }
 throw Error('No supported country catalog endpoint returned a usable country list');
}
async function recover(force=false){
 const select=qs('#countrySelect');if(!select||loading||(!force&&select.options.length>50))return;
 loading=true;notice('Loading country catalog…');
 try{
 const original=new URLSearchParams(location.search).get('country')||select.value||'KEN';
 const items=await catalog();
 const previous=String(original).toUpperCase();
 select.replaceChildren(...items.filter(x=>x.code&&x.name).map(x=>new Option(x.name,x.code)));
 select.value=Array.from(select.options).some(o=>o.value===previous)?previous:select.options[0]?.value;
 notice(select.options.length+' countries and territories available');
 window.dispatchEvent(new CustomEvent('scsi:country-catalog-recovered',{detail:{count:select.options.length,country:select.value}}));
 if(select.value!==previous)select.dispatchEvent(new Event('change',{bubbles:true}));
 }catch(e){notice('Country catalog unavailable — retry country list',true);const el=qs('#scsiRecoveryNotice');if(el){el.tabIndex=0;el.setAttribute('role','button');el.onclick=()=>recover(true)}console.error('[SCSI recovery]',e);}
 finally{loading=false;}
}
function auditWorkspace(){
 const bar=qs('#productionTruthBar');const route=window.SCSIRouterV3228?.current?.()||new URLSearchParams(location.search).get('view')||'overview';
 const surfaces={economics:'#economicsStudio',law:'#lawStudio',science:'#scienceStudio',humanitarian:'#humanitarianStudio',resources:'#resourceStudio',dossiers:'#dossierStudio'};
 const panel=qs(surfaces[route]);if(!bar||!panel)return;
 const visible=!panel.hidden&&panel.getClientRects().length>0;
 if(visible&&bar.dataset.state==='unavailable'){
  const detail=qs('#truthStateDetail',bar);
  if(detail&&/without a visible workspace surface/i.test(detail.textContent)){
   const label=qs('#truthStateLabel',bar);if(label)label.textContent='Workspace displayed · verifying data';
   detail.textContent='Workspace content is visible. Data retrieval and record coverage must be checked separately.';
   bar.dataset.state='degraded';
  }
 }
}
function boot(){setTimeout(()=>recover(),1200);setTimeout(()=>recover(),5500);
 document.addEventListener('click',e=>{if(e.target.closest?.('#scsiRecoveryNotice[data-error="true"]'))recover(true)});
 window.addEventListener('scsi:route-transition-end',()=>setTimeout(auditWorkspace,200));
 setInterval(auditWorkspace,2500);
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
window.SCSIRecoveryV4562={recover};
})();