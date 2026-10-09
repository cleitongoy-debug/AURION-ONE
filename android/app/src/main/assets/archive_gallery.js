'use strict';
/* AURION ONE · Biblioteca e Portfólio visuais.
   Livro = domínio canônico, não arquivo remoto confirmado.
   Capas = armazenamento IndexedDB no aparelho, sem upload automático.
   Status de leitura/aprendizado exige fonte; scans locais não contam como horas.
*/
(function(){
  const BOOKS=[
    {id:1,name:'CONHECIMENTO',icon:'◈',desc:'Saberes, princípios, algoritmos e fontes de estudo'},
    {id:2,name:'VIVÊNCIA',icon:'✧',desc:'Experiências documentadas e operações observadas'},
    {id:3,name:'ERROS',icon:'⚑',desc:'Falhas, reprodução, causas e correções comprovadas'},
    {id:4,name:'PROGRAMAS',icon:'⌘',desc:'Código, projetos, workflows, versões e validações'},
    {id:5,name:'ASSINATURAS',icon:'◇',desc:'Provas de integridade e certificados; nunca senhas ou chaves privadas'},
    {id:6,name:'DEPOIMENTOS',icon:'❝',desc:'Depoimentos reais, passagens e relatos de serviços'},
    {id:7,name:'HISTÓRICO',icon:'◷',desc:'Linha do tempo, fatos, fontes e versões'},
    {id:8,name:'AGENTES',icon:'✦',desc:'Papéis de CHINA, LOVART, FALCÃO e ÁGUIA, cada um com recibos próprios'},
    {id:9,name:'CLIENTES',icon:'▣',desc:'Projetos e entregas; dados pessoais ficam privados'},
    {id:10,name:'ESTUDOS',icon:'▤',desc:'Cursos, professores, sessões medidas, provas e aplicações'}
  ];
  const SERVICES=[
    {id:'foto',name:'Fotografia & RAW',icon:'◉',desc:'Tratamento, revelação e entrega com provas'},
    {id:'video',name:'Vídeo & Motion',icon:'▶',desc:'Captação, edição, áudio e finalização'},
    {id:'3d',name:'3D & VFX',icon:'⬡',desc:'Cena, personagem, C4D, Octane e composição'},
    {id:'design',name:'Design & Identidade',icon:'✳',desc:'Identidade visual, arte, social e impressão'},
    {id:'dev',name:'Software & IA',icon:'⌘',desc:'Programação, aplicativos e automações'},
    {id:'assistencia',name:'Assistência técnica',icon:'✹',desc:'Diagnóstico e serviço técnico documentado'},
    {id:'solar',name:'Apresentações & Energia',icon:'☀',desc:'Material visual e projetos, sujeitos a provas'}
  ];
  const $=id=>document.getElementById(id);
  const KEY='aurion_gallery_catalog_v1';
  const NOTE='Capas salvas apenas neste aparelho. Não sincronizadas no Drive/PC nem incluídas automaticamente no backup SQLite.';
  const safe=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const scrub=s=>String(s||'').trim().slice(0,2500);
  const suspicious=s=>/(?:sk-[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9_-]{12,}|github_pat_[A-Za-z0-9_-]{12,}|hf_[A-Za-z0-9_-]{18,}|gsk_[A-Za-z0-9_-]{12,}|nvapi-[A-Za-z0-9_-]{12,}|\b(?:password|passwd|senha|token|secret|api[_ -]?key|access[_ -]?token|refresh[_ -]?token|authorization|cookie)\s*[:=]\s*\S+)/i.test(String(s));
  const profile=()=>typeof AURION_ID==='string'&&AURION_ID?AURION_ID:'local';
  const globalState=()=>{
    try{
      const o=JSON.parse(localStorage.getItem(KEY)||'{}');
      return o&&typeof o==='object'&&!Array.isArray(o)?o:{};
    }catch(e){return{};}
  };
  const read=()=>{const s=globalState();const id=profile();const x=s[id];return x&&typeof x==='object'?x:{books:[],reports:[]};};
  const save=(x)=>{
    const all=globalState();all[profile()]=x;
    try{localStorage.setItem(KEY,JSON.stringify(all));return true;}catch(e){setStatus('ESPAÇO LOCAL INDISPONÍVEL; nenhuma gravação confirmada.');return false;}
  };
  const setStatus=t=>{const e=$('libraryStatus');if(e)e.textContent=t;};
  const formatDate=s=>{try{return new Date(s).toLocaleString('pt-BR',{dateStyle:'short',timeStyle:'short'})}catch(e){return 'sem data confirmada'}};
  function dbOpen(){
    return new Promise((resolve,reject)=>{
      if(!window.indexedDB)return reject(Error('IndexedDB não disponível'));
      const r=indexedDB.open('aurion_local_covers_v1',1);
      r.onupgradeneeded=()=>{if(!r.result.objectStoreNames.contains('covers'))r.result.createObjectStore('covers',{keyPath:'id'});};
      r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(Error('Falha de acesso à galeria local'));
    });
  }
  async function dbCover(id,blob){
    const db=await dbOpen();
    try{
      return await new Promise((resolve,reject)=>{
        const t=db.transaction('covers',blob?'readwrite':'readonly');
        const req=blob?t.objectStore('covers').put({id,blob,at:new Date().toISOString()}):t.objectStore('covers').get(id);
        req.onsuccess=()=>resolve(blob||req.result?.blob||null);
        req.onerror=()=>reject(Error('Falha de gravação/leitura da capa'));
        t.onabort=()=>reject(Error('Transação de capa abortada'));
      });
    }finally{db.close();}
  }
  function coverId(key){return profile()+':'+key;}
  const displayUrls=new Map();
  async function hydrateCovers(scope){
    (displayUrls.get(scope)||[]).forEach(u=>URL.revokeObjectURL(u));
    const urls=[];displayUrls.set(scope,urls);
    const images=Array.from(scope.querySelectorAll('[data-cover]'));
    for(const el of images){
      try{
        const id=coverId(el.dataset.cover),blob=await dbCover(id);
        if(!blob)continue;
        const u=URL.createObjectURL(blob);urls.push(u);
        const image=document.createElement('img');image.alt='Capa escolhida pelo operador';image.loading='lazy';image.src=u;
        if(el.isConnected){el.querySelector('.symbol')?.remove();el.prepend(image);}
      }catch(e){/* sem capa: o marcador visual continua e o app não trava */ }
    }
  }
  async function compressImage(file){
    if(!/^image\/(jpeg|png|webp)$/.test(file.type)||file.size>12*1024*1024)throw Error('Use JPEG/PNG/WebP até 12 MB.');
    const temp=URL.createObjectURL(file);
    try{return await new Promise((resolve,reject)=>{
      const img=new Image();img.onload=()=>{
        try{
          const scale=Math.min(1,1000/Math.max(img.naturalWidth,img.naturalHeight));
          const w=Math.max(1,Math.round(img.naturalWidth*scale)),h=Math.max(1,Math.round(img.naturalHeight*scale));
          const cv=document.createElement('canvas');cv.width=w;cv.height=h;
          const ctx=cv.getContext('2d');
          if(!ctx)throw Error('Canvas indisponível');
          ctx.drawImage(img,0,0,w,h);
          cv.toBlob(blob=>blob?resolve(blob):reject(Error('Não foi possível converter a capa')),'image/jpeg',.84);
        }catch(e){reject(e);}
      };
      img.onerror=()=>reject(Error('Arquivo de imagem não legível'));
      img.src=temp;
    });}finally{URL.revokeObjectURL(temp);}
  }
  let coverTarget=null;
  window.galleryPickCover=function(target){
    if(!/^book-(?:[1-9]|10)$/.test(target)&&!/^case-[a-z0-9_-]{1,110}$/i.test(target)&&!/^service-[a-z0-9_-]{1,40}$/i.test(target))return;
    coverTarget=target;
    const picker=$('galleryCoverInput');if(picker){picker.value='';picker.click();}
  };
  window.galleryReceiveCover=async function(input){
    const file=input?.files?.[0];if(!file||!coverTarget)return;
    const target=coverTarget;coverTarget=null;
    try{
      const blob=await compressImage(file);
      await dbCover(coverId(target),blob);
      setStatus('CAPA GRAVADA NO POCO para '+target+'. Não enviada ao Drive. '+NOTE);
      render();
    }catch(e){setStatus('CAPA BLOQUEADA: '+e.message);}
  };
  const card=(id,n,title,icon,subtitle,label,extra,coverKey)=>{
    const pick=String(coverKey||id).replace(/'/g,'');
    return '<article class="gallery-tile"><div class="gallery-cover" data-cover="'+safe(pick)+'"><span class="number">'+safe(n)+'</span><span class="symbol" aria-hidden="true">'+safe(icon)+'</span></div>'+
      '<div class="gallery-details"><h2>'+safe(title)+'</h2><p>'+safe(subtitle)+'</p><span class="gallery-label">'+safe(label)+'</span>'+
      (extra||'')+'<div class="gallery-mini-action"><button type="button" onclick="galleryPickCover(\''+safe(pick)+'\')">+ CAPA</button>'+
      '<button class="primary" type="button" onclick="galleryOpen(\''+safe(id)+'\')">ABRIR</button></div></div></article>';
  };
  let selectedBook=1;
  window.galleryOpen=function(id){
    if(id.startsWith('book-')){
      const n=Number(id.substring(5));if(!BOOKS.some(x=>x.id===n))return;
      selectedBook=n;
      if($('libraryBookSelect'))$('libraryBookSelect').value=String(n);
      renderBookDetails();
      $('libraryBookPanel')?.scrollIntoView({behavior:'smooth',block:'start'});
    }else if(id.startsWith('service-')){
      const s=SERVICES.find(x=>'service-'+x.id===id);
      if(s){$('libraryServiceSelect').value=s.name; $('libraryServicePanel')?.scrollIntoView({behavior:'smooth',block:'start'});}
    }else if(id.startsWith('case-')){
      window.go?.('portfolio');
      $('portfolioCases')?.scrollIntoView({behavior:'smooth',block:'start'});
    }
  };
  window.galleryFilter=function(){
    const needle=$('libraryFilter')?.value.toLocaleLowerCase('pt-BR').trim()||'';
    const books=BOOKS.filter(b=>[b.name,b.desc,String(b.id)].join(' ').toLocaleLowerCase('pt-BR').includes(needle));
    renderBooks(books);
  };
  function renderBooks(books=BOOKS){
    const el=$('libraryBookGrid');if(!el)return;
    const s=read(),entries=Array.isArray(s.books)?s.books:[];
    el.innerHTML=books.map(b=>{
      const count=entries.filter(e=>e.bookId===b.id).length;
      return card('book-'+b.id,'LIVRO '+b.id,b.name,b.icon,b.desc,
        count+' referência(s) local(is), leitura remota NÃO VERIFICADA','', 'book-'+b.id);
    }).join('')||'<div class="gallery-empty">Nenhum livro coincide com a busca.</div>';
    hydrateCovers(el);
    const e=$('librarySourceCount');if(e)e.textContent=String(entries.length);
  }
  function renderBookDetails(){
    const b=BOOKS.find(x=>x.id===selectedBook)||BOOKS[0];
    const title=$('librarySelectedBook'),details=$('libraryBookEntries');
    if(title)title.textContent='LIVRO '+b.id+' · '+b.name;
    if(details){
      const src=(read().books||[]).filter(x=>x.bookId===b.id).slice().reverse();
      details.innerHTML=src.map(e=>'<div class="gallery-entry"><b>'+safe(e.title)+'</b>'+
        '<small>Origem informada: '+safe(e.ref)+' · '+safe(formatDate(e.at))+'</small>'+
        '<small>'+safe(e.observation||'Referência cadastrada; leitura ainda não testada.')+'</small>'+
        '<small>STATUS: METADADOS LOCAIS, arquivo não importado automaticamente</small></div>').join('')||
        '<div class="gallery-empty">Livro sem referências locais nesta instalação. Você pode anexar fonte ou link sem alterar os originais do Drive.</div>';
    }
  }
  window.gallerySaveBookRef=function(){
    const n=Number($('libraryBookSelect')?.value),b=BOOKS.find(x=>x.id===n);
    const title=scrub($('librarySourceTitle')?.value).slice(0,180);
    const ref=scrub($('librarySourceRef')?.value).slice(0,480);
    const observation=scrub($('librarySourceObservation')?.value).slice(0,1000);
    if(!b||!title||!ref){setStatus('Informe livro, título e referência ou ID original.');return;}
    if(suspicious(title+' '+ref+' '+observation)){setStatus('BLOQUEADO: possível credencial no texto. Não registre segredos.');return;}
    const s=read();if(!Array.isArray(s.books))s.books=[];
    const unique=[n,title.toLowerCase(),ref.toLowerCase()].join('|');
    if(s.books.some(e=>e.unique===unique)){setStatus('REFERÊNCIA REPETIDA: nenhuma cópia criada.');return;}
    s.books.push({bookId:n,title,ref,observation,unique,at:new Date().toISOString(),evidence:'REFERENCIA_DECLARADA'});
    if(!save(s))return;
    selectedBook=n;
    $('librarySourceTitle').value='';$('librarySourceRef').value='';$('librarySourceObservation').value='';
    setStatus('REFERÊNCIA GRAVADA LOCALMENTE. Livro '+n+' recebeu metadados; leitura, estudo e Drive ainda NÃO CONFIRMADOS.');
    renderBooks();renderBookDetails();
  };
  function casesRead(){
    if(typeof getMemories!=='function')return [];
    try{return getMemories('portfolio_case','',500).map(r=>{
      let d;try{d=JSON.parse(r.body||'{}')}catch{return null;}
      return {id:String(r.id||''),title:String(r.title||d.project||'Case sem título'),data:d};
    }).filter(Boolean)}catch(e){return []}
  }
  function stableCaseId(c){
    let x=(c.id||'').replace(/[^a-zA-Z0-9_-]/g,'');
    if(x.length>=3)return 'case-'+x.slice(0,106);
    let raw=[c.title,c.data?.createdAt,c.data?.category].join('|'),hash=2166136261;
    for(let i=0;i<raw.length;i++){hash^=raw.charCodeAt(i);hash=Math.imul(hash,16777619);}
    return 'case-'+(hash>>>0).toString(16);
  }
  function renderPortfolio(){
    const root=$('portfolioVisualGrid');if(!root)return;
    const cases=casesRead();
    const count=$('portfolioVisualCount');if(count)count.textContent=String(cases.length);
    root.innerHTML=cases.map((c,i)=>{
      const d=c.data||{},hasProof=!!String(d.proof||'').trim(),publicApproved=!!d.public&&hasProof;
      const state=publicApproved?'LIBERADO POR VOCÊ · FONTE INFORMADA':'PRIVADO · NÃO PUBLICAR';
      const short=[d.role,d.tools].filter(Boolean).join(' · ').slice(0,130);
      return card(stableCaseId(c),String(i+1).padStart(2,'0'),c.title,'◆',
        short||String(d.category||'Case registrado'),
        state+(hasProof?' · prova cadastrada':' · PROVA PENDENTE'),
        '<div class="gallery-case-meta"><span>'+safe(d.category||'CASE')+'</span><span>'+safe(d.year||'DATA PENDENTE')+'</span></div>',stableCaseId(c));
    }).join('')||'<div class="gallery-empty">Nenhum case encontrado na memória SQLite deste perfil. Cadastre o primeiro na seção NOVO CASE COM PROVA.</div>';
    hydrateCovers(root);
  }
  function renderServices(){
    const root=$('servicesGallery');if(!root)return;
    const reports=Array.isArray(read().reports)?read().reports:[];
    root.innerHTML=SERVICES.map((s,i)=>card('service-'+s.id,String(i+1).padStart(2,'0'),s.name,s.icon,
      s.desc,reports.filter(x=>x.category===s.name).length+' registro(s) local(is) · entregas não presumidas','',
      'service-'+s.id)).join('');
    hydrateCovers(root);
    const count=$('servicesReportCount');if(count)count.textContent=String(reports.length);
    const entries=$('serviceReportEntries');
    if(entries)entries.innerHTML=reports.slice(-12).reverse().map(x=>
      '<div class="gallery-entry"><b>'+safe(x.category)+' · '+safe(x.title)+'</b>'+
      '<small>'+safe(formatDate(x.at))+' · '+safe(x.evidence||'RELATO_OPERADOR')+'</small>'+
      '<small>Aplicação: '+safe(x.learning||'não informada')+'</small>'+
      '<small>Referência: '+safe(x.ref||'não informada')+'</small></div>'
    ).join('')||'<div class="gallery-empty">Nenhum serviço relatado nesta instalação.</div>';
  }
  window.gallerySaveService=function(){
    const category=$('libraryServiceSelect')?.value||'';
    const title=scrub($('serviceReportTitle')?.value).slice(0,180);
    const ref=scrub($('serviceReportRef')?.value).slice(0,500);
    const learning=scrub($('serviceReportLearning')?.value).slice(0,800);
    if(!SERVICES.some(x=>x.name===category)||!title||!ref){setStatus('Informe serviço, o que foi feito e referência.');return;}
    if(suspicious([category,title,ref,learning].join(' '))){setStatus('BLOQUEADO: possível segredo; nenhum registro criado.');return;}
    const state=read();if(!Array.isArray(state.reports))state.reports=[];
    const unique=[category,title,ref].join('|').toLowerCase();
    if(state.reports.some(e=>e.unique===unique)){setStatus('RELATO REPETIDO: nenhum registro duplicado.');return;}
    const record={category,title,ref,learning,unique,at:new Date().toISOString(),evidence:'RELATO_OPERADOR_NAO_AUDITADO'};
    if(state.reports.length>=500){setStatus('Limite local de 500 relatos. Exportação/backup necessário antes de continuar.');return;}
    state.reports.push(record);
    if(!save(state))return;
    const engine=window.AurionMemoryEngine;
    if(engine?.addSource){
      const body='Serviço: '+title+'\nAplicação do aprendizado: '+(learning||'não informada')+'\nReferência: '+ref;
      // Apenas memória local aditiva, nunca declara sync com Drive.
      try{engine.addSource('depoimento_servico',title,body,ref,'RELATO_HISTORICO')}catch(e){}
    }
    $('serviceReportTitle').value='';$('serviceReportRef').value='';$('serviceReportLearning').value='';
    setStatus('DEPOIMENTO LOCAL GRAVADO. Registro do operador; prova e sincronização remota ainda pendentes.');
    renderServices();
  };
  function renderStudies(){
    const e=$('galleryStudyInfo');if(!e)return;
    let items=[];
    try{if(typeof dedMerged==='function')items=dedMerged()||[];}catch(err){}
    const sessions=items.filter(x=>x.kind==='session'),progress=items.filter(x=>x.kind==='progress'),milestones=items.filter(x=>x.kind==='milestone');
    e.innerHTML='<div class="gallery-measures"><span>'+sessions.length+' sessões registradas</span><span>'+progress.length+' registros de progresso</span><span>'+milestones.length+' marcos</span></div>'+
      '<p class="gallery-note">Contagem de eventos ≠ horas comprovadas. As horas são calculadas exclusivamente na aba Dedicação a partir dos intervalos reais; progresso de curso só vale com fonte.</p>'+
      '<button type="button" onclick="go(\'dedication\')">ABRIR ESTUDOS E CRONÔMETRO</button>';
  }
  window.galleryRender=function(){render();};
  function render(){
    renderBooks();renderBookDetails();renderPortfolio();renderServices();renderStudies();
    const s=read();const e=$('libraryStatus');
    if(e&&!e.textContent.trim())e.textContent='LOCAL, offline. Fontes Drive não sincronizadas. '+NOTE;
  }
  function init(){
    if(!$('library'))return;
    const x=$('libraryBookSelect');
    if(x&&!x.options.length)x.innerHTML=BOOKS.map(b=>'<option value="'+b.id+'">LIVRO '+b.id+' · '+safe(b.name)+'</option>').join('');
    const y=$('libraryServiceSelect');
    if(y&&!y.options.length)y.innerHTML=SERVICES.map(s=>'<option>'+safe(s.name)+'</option>').join('');
    x?.addEventListener('change',()=>{selectedBook=Number(x.value);renderBookDetails();});
    $('libraryFilter')?.addEventListener('input',window.galleryFilter);
    const oldGo=window.go;
    if(typeof oldGo==='function'){
      window.go=function(id){oldGo(id);if(id==='library'||id==='portfolio')setTimeout(render,30);}
    }
    const oldPf=window.portfolioRender;
    if(typeof oldPf==='function'){
      window.portfolioRender=function(){oldPf();setTimeout(renderPortfolio,40);};
    }
    render();
  }
  window.AurionVisualArchive={books:BOOKS,services:SERVICES,render:()=>render(),localState:()=>read()};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();