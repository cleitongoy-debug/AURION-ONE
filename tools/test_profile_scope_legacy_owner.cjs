/* REGRESSION: legacy WebView storage follows the native bootstrap owner.
   Checks logical namespace isolation only; Storage.prototype is NOT an OS security boundary. */
'use strict';
const assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
const js=fs.readFileSync('android/app/src/main/assets/profile_scope.js','utf8');
const java=fs.readFileSync('android/app/src/main/java/one/aurion/app/ProfileManager.java','utf8');
assert.ok(java.includes('j.put("legacy_owner", legacyOwner());'),'Android status must provide native legacy owner');
function execute(active,legacyOwner,initial={}){
 function Storage(){this.map=new Map(Object.entries(initial))}
 Storage.prototype.getItem=function(key){return this.map.has(String(key))?this.map.get(String(key)):null};
 Storage.prototype.setItem=function(key,value){this.map.set(String(key),String(value))};
 Storage.prototype.removeItem=function(key){this.map.delete(String(key))};
 const localStorage=new Storage();
 const AurionProfiles={status:()=>JSON.stringify({
   active,legacy_owner:legacyOwner,
   people:[{id:'anark',tabs:'home,lab,dedication'},{id:'ds',tabs:'home,lab,dedication'},
     {id:'davi',tabs:'home,lab,dedication'},{id:'spectra',tabs:'home,lab'}]
 })};
 const document={addEventListener(){}};
 let failure=null;
 try{vm.runInNewContext(js,{Storage,AurionProfiles,document})}catch(e){failure=e}
 return {localStorage,failure};
}
const original={'aurionDedicationV1':'DS legacy','aurion_eu3_research_v1':'DS historical study'};
let x=execute('ds','ds',original);assert.equal(x.failure,null);
assert.equal(x.localStorage.getItem('aurionDedicationV1'),'DS legacy');
assert.equal(x.localStorage.getItem('aurion_eu3_research_v1'),'DS historical study');
x.localStorage.setItem('aurion_mentoria_ia_v1','DS mentorship');
assert.equal(x.localStorage.map.get('aurion_mentoria_ia_v1'),'DS mentorship');
x=execute('anark','ds',original);assert.equal(x.failure,null);
assert.equal(x.localStorage.getItem('aurionDedicationV1'),null);
assert.equal(x.localStorage.getItem('aurion_eu3_research_v1'),null);
x.localStorage.setItem('aurion_eu3_research_v1','ANARK new');
assert.equal(x.localStorage.map.get('aurionProfile:anark:aurion_eu3_research_v1'),'ANARK new');
assert.equal(x.localStorage.map.get('aurion_eu3_research_v1'),'DS historical study');
x=execute('davi','ds',original);assert.equal(x.failure,null);
assert.equal(x.localStorage.getItem('aurionDedicationV1'),null);
x.localStorage.setItem('aurion_mentoria_ia_v1','DAVI new');
assert.equal(x.localStorage.map.get('aurionProfile:davi:aurion_mentoria_ia_v1'),'DAVI new');
x=execute('anark','anark',{'aurionDedicationV1':'ANARK original'});
assert.equal(x.failure,null);assert.equal(x.localStorage.getItem('aurionDedicationV1'),'ANARK original');
x=execute('ds','anark',{'aurionDedicationV1':'ANARK original'});
assert.equal(x.failure,null);assert.equal(x.localStorage.getItem('aurionDedicationV1'),null);
x=execute('anark',null,original);assert.ok(x.failure,'Unverifiable owner must block silent mapping');
assert.equal(x.localStorage.map.get('aurionDedicationV1'),'DS legacy','Source untouched on failure');
console.log('PASS: native legacy-owner routing, per-profile isolation, fail closed, no old-data deletion');
