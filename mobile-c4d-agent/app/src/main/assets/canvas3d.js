/* AURION Canvas3D: projeção local simples, sem dependências de rede.
 * MVP experimental: primitivas, câmera orbital, transforms, materiais e export C4D.
 */
(()=>{'use strict';
const C=document.getElementById('view3d'); if(!C)return;
const g=C.getContext('2d',{alpha:false});
let scene=JSON.parse(localStorage.getItem('aurion_scene_v1')||'null');
if(!scene||!Array.isArray(scene.objects))scene={version:1,objects:[
 {name:'Cubo',type:'cube',p:[-1,0,0],s:[1,1,1],r:0,color:'#547bff'},
 {name:'Esfera',type:'sphere',p:[1,0,0],s:[1,1,1],r:0,color:'#df57e4'}
]};
let selected=0,yaw=.55,pitch=.36,zoom=9,drag=null,frame=0,playing=false;
const v=(a,b)=>[a[0]-b[0],a[1]-b[1],a[2]-b[2]];
const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
const norm=a=>{let l=Math.hypot(...a)||1;return a.map(x=>x/l)};
const c=(x,y,z)=>[x,y,z], polys={};
function cube(){const p=[c(-.5,-.5,-.5),c(.5,-.5,-.5),c(.5,.5,-.5),c(-.5,.5,-.5),c(-.5,-.5,.5),c(.5,-.5,.5),c(.5,.5,.5),c(-.5,.5,.5)];
 return [[0,3,2,1],[4,5,6,7],[0,4,7,3],[1,2,6,5],[3,7,6,2],[0,1,5,4]].map(f=>f.map(i=>p[i]));}
function globe(torus){const rings=torus?12:9,segs=16,verts=[],quads=[];
 for(let i=0;i<=rings;i++){let phi=Math.PI*i/rings;
 for(let j=0;j<=segs;j++){let a=2*Math.PI*j/segs;
 verts.push(torus?c((.65+.23*Math.cos(phi))*Math.cos(a),.23*Math.sin(phi),(.65+.23*Math.cos(phi))*Math.sin(a)):
 c(.5*Math.sin(phi)*Math.cos(a),.5*Math.cos(phi),.5*Math.sin(phi)*Math.sin(a)));}}
 for(let i=0;i<rings;i++)for(let j=0;j<segs;j++){
 let k=i*(segs+1)+j;quads.push([verts[k],verts[k+1],verts[k+1+segs+1],verts[k+segs+1]])}
 return quads;}
function cylinder(){const faces=[],N=16;for(let i=0;i<N;i++){let a=i*Math.PI*2/N,b=(i+1)*Math.PI*2/N;
 faces.push([c(.5*Math.cos(a),-.5,.5*Math.sin(a)),c(.5*Math.cos(b),-.5,.5*Math.sin(b)),c(.5*Math.cos(b),.5,.5*Math.sin(b)),c(.5*Math.cos(a),.5,.5*Math.sin(a))]);}
 let top=[],bottom=[];for(let i=0;i<N;i++){let a=i*Math.PI*2/N;top.push(c(.5*Math.cos(a),.5,.5*Math.sin(a)));bottom.unshift(c(.5*Math.cos(a),-.5,.5*Math.sin(a)));}return faces.concat([top,bottom]);}
polys.cube=cube();polys.sphere=globe(false);polys.torus=globe(true);polys.cylinder=cylinder();polys.plane=[[c(-.6,0,-.6),c(.6,0,-.6),c(.6,0,.6),c(-.6,0,.6)]];
function transform(q,o){const a=o.r*Math.PI/180,co=Math.cos(a),si=Math.sin(a);let x=q[0]*o.s[0],y=q[1]*o.s[1],z=q[2]*o.s[2];return [co*x-si*z+o.p[0],y+o.p[1],si*x+co*z+o.p[2]];}
function camera(q){let x=q[0],y=q[1],z=q[2];const cy=Math.cos(yaw),sy=Math.sin(yaw);let X=cy*x+sy*z,Z=-sy*x+cy*z;
 const cp=Math.cos(pitch),sp=Math.sin(pitch);return [X,cp*y-sp*Z,sp*y+cp*Z+zoom];}
function projected(q,w,h){let z=Math.max(.3,q[2]);let f=Math.min(w,h)*1.25;return [w/2+q[0]*f/z,h/2-q[1]*f/z];}
function rgb(hex){let n=parseInt(hex.slice(1),16);return [(n>>16)&255,(n>>8)&255,n&255];}
function color(rgb,shade){return 'rgb('+rgb.map(x=>Math.round(Math.max(0,Math.min(255,x*shade)))).join(',')+')'}
function draw(){
 const w=C.width,h=C.height;g.fillStyle='#101321';g.fillRect(0,0,w,h);
 // perspectiva do grid, eixo x/z
 g.lineWidth=1;for(let i=-10;i<=10;i++){
  for(let axis=0;axis<2;axis++){
   let a=axis===0?[-10,-1.05,i]:[i,-1.05,-10],b=axis===0?[10,-1.05,i]:[i,-1.05,10];
   let A=projected(camera(a),w,h),B=projected(camera(b),w,h);
   g.strokeStyle=(i===0?'#3c5b87':'#2b3245');g.beginPath();g.moveTo(...A);g.lineTo(...B);g.stroke();
  }
 }
 const faces=[];scene.objects.forEach((o,idx)=>{
  const ps=polys[o.type]||polys.cube;
  for(const f of ps){const pts=f.map(q=>camera(transform(q,o)));if(pts.some(p=>p[2]<.2))continue;
   const n=norm(cross(v(pts[1],pts[0]),v(pts[2],pts[0])));
   let shade=.5+.5*Math.abs(n[0]*.35+n[1]*.72+n[2]*.55);
   faces.push({z:pts.reduce((s,p)=>s+p[2],0)/pts.length,pts:pts.map(q=>projected(q,w,h)),idx,fill:color(rgb(o.color),shade)});}
 });
 faces.sort((a,b)=>b.z-a.z);
 faces.forEach(f=>{g.beginPath();f.pts.forEach((p,i)=>i?g.lineTo(...p):g.moveTo(...p));g.closePath();g.fillStyle=f.fill;g.fill();
  g.strokeStyle=f.idx===selected?'#93eaff':'#080c1c';g.lineWidth=f.idx===selected?1.4:.45;g.stroke()});
 let o=scene.objects[selected];if(o){let p=projected(camera(o.p),w,h);g.strokeStyle='#ffe284';g.lineWidth=2;g.beginPath();g.arc(p[0],p[1],5,0,Math.PI*2);g.stroke();}
 g.fillStyle='#a1a8c4';g.font='12px system-ui';g.fillText('AURION 3D • OFFLINE • '+scene.objects.length+' objetos',12,22);
}
function refresh(){
 const list=document.getElementById('hierarchy');list.textContent='';
 scene.objects.forEach((o,i)=>{let b=document.createElement('button');b.className='secondary'+(i===selected?' picked':'');b.textContent=(i===selected?'◆ ':'◇ ')+o.name;b.onclick=()=>{selected=i;refresh()};list.appendChild(b)});
 const o=scene.objects[selected];document.getElementById('objectSettings').style.display=o?'block':'none';
 if(o){document.getElementById('objName').value=o.name;document.getElementById('objColor').value=o.color;
 ['p0','p1','p2','s0','s1','s2'].forEach(k=>{document.getElementById(k).value=o[k[0]][+k[1]]});
 document.getElementById('rotY').value=o.r;}
 draw();
}
window.modelAdd=type=>{scene.objects.push({name:type[0].toUpperCase()+type.slice(1)+' '+(scene.objects.length+1),type,p:[0,0,0],s:[1,1,1],r:0,color:'#57a9f5'});selected=scene.objects.length-1;refresh();};
window.modelDelete=()=>{if(scene.objects.length){scene.objects.splice(selected,1);selected=Math.max(0,scene.objects.length-1);refresh()}};
window.modelChange=()=>{let o=scene.objects[selected];if(!o)return;o.name=document.getElementById('objName').value.substring(0,60);o.color=document.getElementById('objColor').value;
 ['p0','p1','p2','s0','s1','s2'].forEach(k=>o[k[0]][+k[1]]=Math.max(-20,Math.min(20,Number(document.getElementById(k).value)||0)));
 o.r=Number(document.getElementById('rotY').value)||0;draw();refreshListOnly()};
function refreshListOnly(){const b=document.getElementById('hierarchy').querySelectorAll('button');b.forEach((x,i)=>x.textContent=(i===selected?'◆ ':'◇ ')+scene.objects[i].name)}
window.modelSave=()=>{localStorage.setItem('aurion_scene_v1',JSON.stringify(scene));document.getElementById('sceneStatus').textContent='Cena salva offline neste aparelho: '+scene.objects.length+' objetos.';};
window.modelReset=()=>{if(confirm('Limpar cena atual?')){scene.objects=[];selected=0;refresh()}};
window.modelJson=()=>{document.getElementById('sceneStatus').textContent=JSON.stringify(scene,null,2)};
window.modelToC4D=()=>{
 const types={cube:'Ocube',sphere:'Osphere',cylinder:'Ocylinder',torus:'Otorus',plane:'Oplane'};
 let s=['import c4d','from c4d import Vector','doc=c4d.documents.GetActiveDocument()','doc.StartUndo()','try:'];
 scene.objects.forEach(o=>{let col=rgb(o.color).map(x=>(x/255).toFixed(4)),pos=o.p.map(x=>Number(x*100).toFixed(3)),sc=o.s.map(x=>Number(x).toFixed(3));
 s.push('    obj = c4d.BaseObject(c4d.'+(types[o.type]||'Ocube')+')');
 s.push('    obj.SetName('+JSON.stringify(o.name)+')');
 s.push('    obj.SetAbsPos(Vector('+pos.join(', ')+'))');
 s.push('    obj.SetAbsScale(Vector('+sc.join(', ')+'))');
 s.push('    obj.SetAbsRot(Vector(0, '+(o.r*Math.PI/180).toFixed(6)+', 0))');
 s.push('    obj[c4d.ID_BASEOBJECT_USECOLOR] = c4d.ID_BASEOBJECT_USECOLOR_ALWAYS');
 s.push('    obj[c4d.ID_BASEOBJECT_COLOR] = Vector('+col.join(', ')+')');
 s.push('    doc.InsertObject(obj)');
 s.push('    doc.AddUndo(c4d.UNDOTYPE_NEWOBJ, obj)');});
 s.push('finally:','    doc.EndUndo()','    c4d.EventAdd()');
 document.getElementById('code').value=s.join('\n');document.getElementById('scriptName').value='aurion_cena_3d';
 tab('editor');document.getElementById('editorStatus').textContent='Cena convertida para script Cinema 4D. Salve ou envie ao PC para revisão.';
};
function resize(){const r=C.getBoundingClientRect(),d=Math.min(2,window.devicePixelRatio||1);C.width=Math.max(50,Math.floor(r.width*d));C.height=Math.max(50,Math.floor(r.height*d));draw()}
C.addEventListener('pointerdown',e=>{drag={x:e.clientX,y:e.clientY,yaw,pitch};C.setPointerCapture(e.pointerId)});
C.addEventListener('pointermove',e=>{if(!drag)return;yaw=drag.yaw+(e.clientX-drag.x)*.008;pitch=Math.max(-1.1,Math.min(1.1,drag.pitch+(e.clientY-drag.y)*.008));draw()});
C.addEventListener('pointerup',()=>drag=null);
C.addEventListener('wheel',e=>{e.preventDefault();zoom=Math.max(3,Math.min(30,zoom+e.deltaY*.007));draw()},{passive:false});
window.modelZoom=delta=>{zoom=Math.max(3,Math.min(30,zoom+delta));draw()};
window.modelFrame=(n)=>{frame=n;const o=scene.objects[selected];if(o){o.r=(n/90)*360;document.getElementById('rotY').value=o.r;draw()}};
window.addEventListener('resize',resize);
setTimeout(()=>{refresh();resize()},200);
})();