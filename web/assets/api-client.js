const cfg=()=>window.__SC_SITE_INTELLIGENCE_CONFIG__||{};

export class SiteIntelligenceClient{
  constructor(){ this.base=(cfg().apiOrigin||"").replace(/\/$/,""); }
  url(path,params={}){
    const u=new URL(this.base+path);
    Object.entries(params).forEach(([k,v])=>{ if(v!==undefined&&v!==null&&v!=="") u.searchParams.set(k,String(v)); });
    return u;
  }
  async request(path,{params={},method="GET",body}={}){
    const res=await fetch(this.url(path,params),{
      method,
      credentials:cfg().apiCredentials||"include",
      headers:{"Accept":"application/json",...(body?{"Content-Type":"application/json"}:{})},
      body:body?JSON.stringify(body):undefined,
      cache:"no-store"
    });
    const text=await res.text();
    let data={};
    try{ data=text?JSON.parse(text):{}; }catch{ data={ok:false,detail:text}; }
    if(!res.ok) throw Object.assign(new Error(data.detail||`HTTP ${res.status}`),{status:res.status,data});
    return data;
  }
  get(path,params={}){ return this.request(path,{params}); }
  post(path,body={}){ return this.request(path,{method:"POST",body}); }
}

export const client=new SiteIntelligenceClient();
