'use strict';
window.AurionMemoryUI={
 open(){document.querySelectorAll('.page').forEach(x=>x.classList.remove('active'));document.getElementById('memorylab').classList.add('active');this.render();window.scrollTo(0,0)},
 add(){const t=document.getElementById('amTitle').value.trim(),r=document.getElementById('amRef').value.trim(),b=document.getElementById('amBody').value.trim();if(!b){alert('Cole o conteúdo da fonte antes de adicionar.');return}const x=AurionMemoryEngine.addSource('referencia',t||'Fonte',b,r);document.getElementById('amStatus').textContent=x.duplicate?'Fonte já catalogada.':'Fonte adicionada à caixa.';this.render()},
 study(){const s=AurionMemoryEngine.study();document.getElementById('amStatus').textContent=JSON.stringify(s,null,2);this.render()},
 render(){const s=AurionMemoryEngine.state();document.getElementById('amMemories').textContent=(s.memories||[]).map(x=>x.type+' · '+x.title+'\n'+x.summary+'\nOrigem: '+x.origin).join('\n\n')||'Nenhuma memória consolidada.';document.getElementById('amNotes').textContent=(s.notes||[]).slice(-20).map(x=>x.at+' · '+x.text).join('\n')||'Sem ciclos de estudo.'},
 export(){const blob=new Blob([AurionMemoryEngine.export()],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='AURION_MENTE_BACKUP.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),2000)}
};
