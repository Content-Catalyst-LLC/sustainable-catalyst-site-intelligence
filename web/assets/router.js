const routes=[
  ["home",/^\/$/],
  ["country",/^\/country\/([^/]+)\/?$/],
  ["dossiers",/^\/dossiers\/([^/]+)\/?$/],
  ["economics",/^\/economics\/([^/]+)\/?$/],
  ["law",/^\/law\/([^/]+)\/?$/],
  ["earth",/^\/science\/earth\/([^/]+)\/?$/],
  ["ocean",/^\/science\/ocean\/?$/],
  ["space",/^\/science\/space\/?$/],
  ["science",/^\/science\/([^/]+)\/?$/],
  ["humanitarian",/^\/humanitarian\/([^/]+)\/?$/],
  ["resources",/^\/resources\/([^/]+)\/?$/],
  ["events",/^\/events\/?$/],
  ["research",/^\/research\/?$/],
  ["packages",/^\/packages(?:\/([^/]+))?\/?$/]
];

export function resolve(path=location.pathname){
  for(const [id,re] of routes){ const m=path.match(re); if(m) return {id,param:m[1]||null,path}; }
  return {id:"not-found",param:null,path};
}

export function navigate(path,{replace=false}={}){
  (replace?history.replaceState:history.pushState).call(history,{},"",path);
  dispatchEvent(new PopStateEvent("popstate"));
}

export function countryPath(route,country){
  const c=encodeURIComponent(country);
  const map={country:`/country/${c}`,dossiers:`/dossiers/${c}`,economics:`/economics/${c}`,law:`/law/${c}`,science:`/science/${c}`,earth:`/science/earth/${c}`,humanitarian:`/humanitarian/${c}`,resources:`/resources/${c}`,research:"/research",events:"/events",ocean:"/science/ocean",space:"/science/space",packages:"/packages"};
  return map[route]||"/";
}
