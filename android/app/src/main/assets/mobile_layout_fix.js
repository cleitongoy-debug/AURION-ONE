'use strict';
/* Safe display-only corrections. Does not change credentials, pairing, data or sync. */
(function(){
  const root=document.documentElement;
  const orbId='guideOrb',panelId='guidePanel';
  const $=id=>document.getElementById(id);
  function isGuideField(el){return !!(el&&el.closest&&el.closest('#guidePanel'))}
  function measure(){
    const nav=document.querySelector('.tabs');
    if(nav && !document.body.classList.contains('aurion-guide-keyboard')){
      const h=Math.ceil(nav.getBoundingClientRect().height);
      if(h>30 && h<300)root.style.setProperty('--aurion-nav-height',h+'px');
    }
    const vv=window.visualViewport;
    if(vv&&vv.height>180)root.style.setProperty('--aurion-visible-height',Math.round(vv.height)+'px');
  }
  function updateExpanded(){
    const p=$(panelId),o=$(orbId);
    if(!p||!o)return;
    o.setAttribute('aria-expanded',p.hidden?'false':'true');
    o.setAttribute('aria-controls',panelId);
    document.body.classList.toggle('aurion-guide-open',!p.hidden);
    if(p.hidden)document.body.classList.remove('aurion-guide-keyboard');
    measure();
  }
  function init(){
    const p=$(panelId),o=$(orbId),nav=document.querySelector('.tabs');
    if(!p||!o||!nav)return;
    o.setAttribute('aria-expanded',p.hidden?'false':'true');
    if(window.ResizeObserver)new ResizeObserver(measure).observe(nav);
    if(window.MutationObserver)new MutationObserver(updateExpanded).observe(p,{attributes:true,attributeFilter:['hidden']});
    document.addEventListener('focusin',e=>{
      if(isGuideField(e.target)){
        document.body.classList.add('aurion-guide-keyboard');
        measure();
        try {e.target.scrollIntoView({block:'nearest',behavior:'instant'});}catch(_){}
      }
    });
    document.addEventListener('focusout',e=>{
      if(isGuideField(e.target))setTimeout(()=>{
        if(!isGuideField(document.activeElement))document.body.classList.remove('aurion-guide-keyboard');
        measure();
      },100);
    });
    document.addEventListener('keydown',e=>{
      if(e.key==='Escape'&&!p.hidden){
        p.hidden=true;updateExpanded();o.focus();
      }
    });
    window.addEventListener('resize',measure,{passive:true});
    if(window.visualViewport)window.visualViewport.addEventListener('resize',measure,{passive:true});
    updateExpanded();
    measure();
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
