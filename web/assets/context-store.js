const config=()=>window.__SC_SITE_INTELLIGENCE_CONFIG__||{};
const KEY="sc-site-intelligence-context-v4553";

function normalizeCountry(value){
  const v=String(value||"").trim().toUpperCase();
  return /^[A-Z0-9-]{2,20}$/.test(v)?v:(config().defaultCountry||"KEN");
}

class ContextStore extends EventTarget{
  constructor(){
    super();
    let stored={};
    try{ stored=JSON.parse(sessionStorage.getItem(KEY)||"{}"); }catch{}
    this.state={countryCode:normalizeCountry(stored.countryCode),countryName:stored.countryName||"Kenya",researchContextId:stored.researchContextId||null};
  }
  get(){ return {...this.state}; }
  setCountry(countryCode,countryName=""){
    this.state.countryCode=normalizeCountry(countryCode);
    if(countryName) this.state.countryName=countryName;
    sessionStorage.setItem(KEY,JSON.stringify(this.state));
    this.dispatchEvent(new CustomEvent("change",{detail:this.get()}));
  }
  setResearchContext(id){
    this.state.researchContextId=id||null;
    sessionStorage.setItem(KEY,JSON.stringify(this.state));
    this.dispatchEvent(new CustomEvent("change",{detail:this.get()}));
  }
}
export const contextStore=new ContextStore();
