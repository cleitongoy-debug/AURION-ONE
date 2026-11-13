/* AURION Octane Controller LAB — presets e documentação local.
 * NÃO contém engine Octane. Produz configuração e materiais C4D standard.
 */
(function(){
'use strict';
const $=id=>document.getElementById(id);
const key='aurion_octane_preset_v1';
const defaults={material:'Universal',color:'#c9a227',roughness:.22,metallic:.25,ior:1.45,kernel:'Path Tracing',samples:512,denoise:true,width:1920,height:1080};
let cfg;
try{cfg=JSON.parse(localStorage.getItem(key)||'null')}catch(e){cfg=null}
if(!cfg||typeof cfg!=='object')cfg={...defaults};
function sanitize(){
 cfg.material=$('octMaterial').value;
 cfg.color=$('octColor').value;
 cfg.roughness=Number($('octRough').value);
 cfg.metallic=Number($('octMetal').value);
 cfg.ior=Number($('octIor').value);
 cfg.kernel=$('octKernel').value;
 cfg.samples=Math.max(16,Math.min(8192,Math.floor(Number($('octSamples').value)||512)));
 cfg.denoise=$('octDenoise').checked;
 cfg.width=Math.max(128,Math.min(8192,Math.floor(Number($('octWidth').value)||1920)));
 cfg.height=Math.max(128,Math.min(8192,Math.floor(Number($('octHeight').value)||1080)));
 return cfg;
}
function preview(){
 const sw=$('octSwatch');
 sw.style.background='radial-gradient(circle at 28% 19%,#fff 0%, '+cfg.color+' 22%, #070713 95%)';
 $('octInfo').textContent='Material '+cfg.material+' | '+cfg.kernel+' | '+cfg.samples+' samples | '+cfg.width+'×'+cfg.height+' | Denoise '+(cfg.denoise?'ON':'OFF')+'. PRÉ-VISUALIZAÇÃO APROXIMADA — sem render Octane.';
}
window.octCapture=()=>{sanitize();localStorage.setItem(key,JSON.stringify(cfg));preview();$('octOutput').textContent='Preset salvo somente no POCO. '+new Date().toLocaleString('pt-BR')};
window.octPreset=()=>{
 sanitize();
 const preset={
  schema:'AURION_OCTANE_PRESET_v1',
  generated_at:new Date().toISOString(),
  engine_target:'OctaneRender no Cinema 4D do PC — requer licença válida',
  status:'CONFIGURACAO_NAO_RENDERIZADA',
  material:{name:cfg.material,base_color:cfg.color,roughness:cfg.roughness,metallic:cfg.metallic,ior:cfg.ior},
  render:{kernel:cfg.kernel,max_samples:cfg.samples,denoiser:cfg.denoise,resolution:[cfg.width,cfg.height]},
  notes:'O plugin Octane 2022.1 é de desktop, não foi compilado nem executado no Android. Parâmetros devem ser importados por ponte compatível no PC.'
 };
 $('octOutput').textContent=JSON.stringify(preset,null,2);
 if(typeof Aurion!=='undefined'&&Aurion.shareText)Aurion.shareText('AURION_OCTANE_PRESET.json',JSON.stringify(preset,null,2));
};
window.octToC4d=()=>{
 sanitize();
 // Cria material C4D padrão para transportar cor e nome; NÃO cria nó Octane.
 const h=cfg.color,rgbs=[1,3,5].map(i=>Number(parseInt(h.slice(i,i+2),16)/255).toFixed(5));
 const code=[
 'import c4d',
 'from c4d import Vector',
 'doc = c4d.documents.GetActiveDocument()',
 '# Material C4D PADRAO; plugin Octane NAO disponivel no Android.',
 'mat = c4d.BaseMaterial(c4d.Mmaterial)',
 'mat.SetName('+JSON.stringify('AURION_'+cfg.material)+')',
 'mat[c4d.MATERIAL_COLOR_COLOR] = Vector('+rgbs.join(', ')+')',
 'doc.InsertMaterial(mat)',
 'c4d.EventAdd()',
 'print("Criado material C4D padrão. Configure Octane separadamente no PC.")'
 ].join('\n');
 $('code').value=code;$('scriptName').value='aurion_material_'+cfg.material.toLowerCase();
 $('editorStatus').textContent='Script criado para material C4D padrão. Configurações Octane específicas exigem plugin autorizado no PC.';
 tab('editor');
};
for(const [id,field] of [['octMaterial','material'],['octColor','color'],['octRough','roughness'],['octMetal','metallic'],['octIor','ior'],['octKernel','kernel'],['octSamples','samples'],['octWidth','width'],['octHeight','height']])$(id).value=cfg[field];
$('octDenoise').checked=!!cfg.denoise;
['octMaterial','octColor','octRough','octMetal','octIor','octKernel','octSamples','octWidth','octHeight','octDenoise'].forEach(id=>$(id).addEventListener('input',()=>{sanitize();preview()}));
preview();
})();