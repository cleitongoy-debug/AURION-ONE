const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const path=require('node:path');
const base=path.join(__dirname,'../android/app/src/main/assets');
let checked=0;
for(const page of ['index.html','profiles.html']){
 const html=fs.readFileSync(path.join(base,page),'utf8');
 const scripts=[...html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi)];
 for(const [,body] of scripts)if(body.trim()){
   new vm.Script(body,{filename:page});
   checked++;
 }
}
const page=fs.readFileSync(path.join(base,'index.html'),'utf8');
for(const id of ['bootstrapLinks','bootstrapRefFile','bootstrapSummary','voiceLog','bandChannelCard']){
 assert(page.includes('id="'+id+'"'),'Missing element '+id);
}
for(const fn of ['bootstrapRenderLinks','bootstrapImportFile','window.aurionVoiceResult','bandPaintStatus']){
 assert(page.includes(fn),'Missing handler '+fn);
}
const manager=fs.readFileSync(path.join(__dirname,'../android/app/src/main/java/one/aurion/app/ProfileManager.java'),'utf8');
assert(manager.includes('AurionStartupWorker.class'),'Owner startup must queue index');
const index=fs.readFileSync(path.join(__dirname,'../android/app/src/main/java/one/aurion/app/AurionBootstrapIndex.java'),'utf8');
assert(index.includes('MAX_FILES = 120'),'Bounded SAF scan required');
assert(index.includes('getPersistedUriPermissions()'),'Never scan without SAF consent');
assert(index.includes('fingerprintMetadataSha256'),'Metadata checksums must be labeled');
const worker=fs.readFileSync(path.join(__dirname,'../android/app/src/main/java/one/aurion/app/AurionHourlyWorker.java'),'utf8');
assert(worker.includes('pageSize=100'),'Paginated Drive check required');
assert(worker.includes('driveCursor'),'Drive scan must keep cursor');
assert(worker.includes('sha=main'),'Track actual repo branch');
console.log('PASS: '+checked+' inline scripts syntactically valid; bootstrap, consent, sync, voice and band contracts present (STATIC TEST ONLY)');
