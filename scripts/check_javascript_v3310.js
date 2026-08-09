#!/usr/bin/env node
"use strict";
const fs=require("fs");
const path=require("path");
const vm=require("vm");
const roots=process.argv.slice(2);
if(!roots.length){console.error("Usage: check_javascript_v3310.js <path>...");process.exit(2)}
const files=[];
function walk(target){
  const stat=fs.statSync(target);
  if(stat.isDirectory()){
    for(const name of fs.readdirSync(target))walk(path.join(target,name));
  }else if(target.endsWith(".js"))files.push(target);
}
for(const root of roots)walk(root);
files.sort();
for(const file of files){
  const source=fs.readFileSync(file,"utf8");
  try{new vm.Script(source,{filename:file,displayErrors:true})}
  catch(error){console.error(error.stack||String(error));process.exit(1)}
}
console.log(`Validated ${files.length} JavaScript files.`);
