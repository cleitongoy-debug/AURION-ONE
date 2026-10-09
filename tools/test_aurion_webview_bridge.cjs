'use strict';
// Source-contract regression: DOES NOT exercise Android WebView or verify device behavior.
const fs=require('node:fs'),assert=require('node:assert/strict'),path=require('node:path');
const java=fs.readFileSync(path.join(__dirname,'../android/app/src/main/java/one/aurion/app/MainActivity.java'),'utf8');
const start=java.indexOf('@Override public boolean shouldOverrideUrlLoading');
const end=java.indexOf('web.loadUrl("file:///android_asset/profiles.html")',start);
assert.ok(start>=0&&end>start,'Navigation handler missing');
const nav=java.slice(start,end);
const panelStart=java.indexOf('@JavascriptInterface public void openPanel(');
const panelEnd=java.indexOf('@JavascriptInterface public void testPanel(',panelStart);
assert.ok(panelStart>=0&&panelEnd>panelStart,'Native openPanel missing');
const panel=java.slice(panelStart,panelEnd);
let checks=0;
function test(msg,fn){fn();checks++;console.log('PASS '+msg);}
test('privileged WebView only allows canonical app documents',()=>{
 assert.match(java,/private boolean isTrustedAppDocument\(String url\)/);
 assert.match(java,/"file:\/\/\/android_asset\/profiles\.html"\.equals\(url\)/);
 assert.match(java,/"file:\/\/\/android_asset\/index\.html"\.equals\(url\)/);
});
test('non-main-frame navigations blocked',()=>assert.match(nav,/if\s*\(!request\.isForMainFrame\(\)\)\s*return true/));
test('only trusted app document remains in privileged WebView',()=>assert.match(nav,/if \(isTrustedAppDocument\(uri\.toString\(\)\)\) return false/));
test('all remote navigation exits through ACTION_VIEW',()=>{
 assert.match(nav,/new Intent\(Intent\.ACTION_VIEW, uri\)/);
 assert.doesNotMatch(nav,/isAllowedPanelHost\(uri\.getHost\(\)\)\s*\)\s*return false/);
});
test('file and script URLs cannot leave the allowlist',()=>{
 assert.match(nav,/scheme\.equals\("http"\)/);
 assert.match(nav,/scheme\.equals\("https"\)/);
 assert.match(nav,/Navegação bloqueada/);
});
test('owner panel opens external browser, never privileged WebView',()=>{
 assert.match(panel,/new Intent\(Intent\.ACTION_VIEW, u\)/);
 assert.doesNotMatch(panel,/web\.loadUrl\(/);
 assert.match(panel,/isAllowedPanelHost\(u\.getHost\(\)\)/);
});
test('mixed content and file origin escalation disabled',()=>{
 assert.match(java,/MIXED_CONTENT_NEVER_ALLOW/);
 assert.match(java,/setAllowFileAccessFromFileURLs\(false\)/);
 assert.match(java,/setAllowUniversalAccessFromFileURLs\(false\)/);
 assert.doesNotMatch(java,/MIXED_CONTENT_ALWAYS_ALLOW/);
});
test('bridge attached only to authorized local app page',()=>{
 assert.match(java,/if \(isTrustedAppDocument\(url\)\)/);
 assert.match(java,/if \(url\.equals\("file:\/\/\/android_asset\/index\.html"\) && profiles\.signedIn\(\)\)/);
});
test('Android user profiles are not assumed from web profile selector',()=>{
 assert.match(java,/private ProfileManager profiles;/);
 assert.doesNotMatch(java,/pm uninstall --user/);
});
console.log('PASS '+checks+'/'+checks+' security source checks (static only).');
