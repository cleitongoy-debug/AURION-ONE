package one.aurion.mobileai;

import android.app.*;
import android.content.*;
import android.database.Cursor;
import android.net.Uri;
import android.os.*;
import android.provider.OpenableColumns;
import android.view.*;
import android.widget.*;

import androidx.documentfile.provider.DocumentFile;

import org.json.*;

import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

/**
 * AURION Life Hub v3
 *
 * Módulos persistentes e offline-first:
 * - Depósitos escolhidos pelo operador via Storage Access Framework;
 * - conversas sempre registradas internamente e exportáveis;
 * - estudos/cursos/assuntos com cronômetro persistente;
 * - clientes/projetos com cronômetro de trabalho;
 * - Canon T8i: preservação do CR3/MP4 original + integração opcional com o Super Studio no PC.
 *
 * Nenhuma pasta é varrida sem escolha do operador e nenhum original é sobrescrito.
 */
public final class AurionLifeHub {
  private AurionLifeHub(){}

  static final int TREE_MASTER=179, TREE_CONVERSATIONS=180, TREE_T8I_RAW=181, TREE_T8I_EXPORTS=182,
      TREE_STUDIES=183, TREE_CLIENTS=184, TREE_BACKUPS=185, PICK_T8I=186;

  private static final String DATA_DIR="aurion_lifehub";
  private static final String CONVERSATIONS="conversations.jsonl";
  private static final String STUDIES="study_sessions.jsonl";
  private static final String CLIENTS="clients.jsonl";
  private static final String T8I="t8i_assets.jsonl";
  private static final String EVENTS="events.jsonl";

  private static final Map<Integer,String> TREE_KEYS=new LinkedHashMap<>();
  private static final Map<String,String> TREE_NAMES=new LinkedHashMap<>();
  static {
    TREE_KEYS.put(TREE_CONVERSATIONS,"conversations");
    TREE_KEYS.put(TREE_T8I_RAW,"t8i_raw");
    TREE_KEYS.put(TREE_T8I_EXPORTS,"t8i_exports");
    TREE_KEYS.put(TREE_STUDIES,"studies");
    TREE_KEYS.put(TREE_CLIENTS,"clients");
    TREE_KEYS.put(TREE_BACKUPS,"backups");
    TREE_NAMES.put("conversations","AURION_CONVERSAS");
    TREE_NAMES.put("t8i_raw","AURION_T8I_RAW");
    TREE_NAMES.put("t8i_exports","AURION_T8I_EXPORTS");
    TREE_NAMES.put("studies","AURION_ESTUDOS");
    TREE_NAMES.put("clients","AURION_CLIENTES");
    TREE_NAMES.put("backups","AURION_BACKUPS");
  }

  private static final Handler TIMER_HANDLER=new Handler(Looper.getMainLooper());
  private static Runnable studyTicker, clientTicker;
  private static TextView studyClock, clientClock, t8iStatus;

  static void addDashboardCards(MainActivity a){
    long studySec=totalSeconds(a,STUDIES,"study_finish");
    long clientSec=totalSeconds(a,CLIENTS,"client_finish");
    a.body.addView(a.card("ESTUDOS",formatSeconds(studySec)+" registrados • cronômetro retoma após reiniciar o app"));
    a.body.addView(a.card("CLIENTES",formatSeconds(clientSec)+" de trabalho registrados localmente"));
    String last=a.secrets.getString("t8i_last_name","nenhum arquivo selecionado");
    a.body.addView(a.card("CANON T8i",last+" • originais preservados"));
  }

  static void showDeposits(MainActivity a){
    a.clear("Depósitos, pastas e backup");
    a.body.addView(a.tv("Escolha onde cada tipo de dado será guardado. O Android concede acesso somente às pastas que você selecionar. O app continua mantendo uma cópia interna dos registros mesmo sem depósito externo.",14));

    Button master=a.btn("🗂 Escolher RAIZ MESTRE e criar todas as pastas");
    master.setOnClickListener(v->pickTree(a,TREE_MASTER));
    a.body.addView(master);

    for(Map.Entry<String,String> e:TREE_NAMES.entrySet()){
      String key=e.getKey();
      int req=requestForKey(key);
      LinearLayout row=new LinearLayout(a); row.setOrientation(LinearLayout.VERTICAL);
      row.addView(a.card(e.getValue(),folderState(a,key)));
      Button b=a.btn("Escolher / criar local de "+e.getValue());
      b.setOnClickListener(v->pickTree(a,req));
      row.addView(b);
      a.body.addView(row);
    }

    Button backup=a.btn("💾 EXPORTAR BACKUP COMPLETO AGORA");
    backup.setOnClickListener(v->exportBackup(a));
    a.body.addView(backup);

    Button conv=a.btn("Salvar conversas no depósito");
    conv.setOnClickListener(v->exportConversations(a));
    a.body.addView(conv);

    Button stud=a.btn("Salvar relatório de estudos");
    stud.setOnClickListener(v->exportJsonl(a,"studies",STUDIES,"estudos"));
    a.body.addView(stud);

    Button cli=a.btn("Salvar relatório de clientes");
    cli.setOnClickListener(v->exportJsonl(a,"clients",CLIENTS,"clientes"));
    a.body.addView(cli);

    a.body.addView(a.tv("Backup não inclui chaves de API. Ele contém somente registros AURION, tempos, clientes, estudos, T8i e configuração de depósitos.",12));
  }

  static void showStudies(MainActivity a){
    a.clear("Estudos · horas · assuntos");
    a.body.addView(a.tv("O relógio mede apenas o tempo entre INICIAR e FINALIZAR. Progresso, conclusão e carga horária total só são registrados quando você informar.",14));

    studyClock=a.tv(activeTimerText(a,"study"),28);
    a.body.addView(studyClock);

    EditText title=a.field("Curso / livro / treinamento");
    EditText teacher=a.field("Professor / escola / plataforma");
    EditText subject=a.field("Assunto principal");
    EditText topic=a.field("Módulo / capítulo / tópico");
    EditText url=a.field("Link oficial (opcional)");
    EditText total=a.field("Carga horária total informada, ex.: 20");
    EditText progress=a.field("Progresso informado 0–100");
    EditText notes=a.field("Anotações / o que aprendeu / aplicação em projeto");
    CheckBox completed=new CheckBox(a); completed.setText("Concluído por mim"); completed.setTextColor(a.FG);

    prefillActive(a,"study",title,teacher,subject,topic,url,total,progress,notes,completed);

    a.body.addView(title);a.body.addView(teacher);a.body.addView(subject);a.body.addView(topic);a.body.addView(url);
    a.body.addView(total);a.body.addView(progress);a.body.addView(notes);a.body.addView(completed);

    LinearLayout buttons=new LinearLayout(a); buttons.setOrientation(LinearLayout.VERTICAL);
    Button start=a.btn("▶ INICIAR / RETOMAR CRONÔMETRO");
    start.setOnClickListener(v->{
      if(title.getText().toString().trim().isEmpty()){a.toast("Informe o curso ou estudo.");return;}
      startTimer(a,"study",title,teacher,subject,topic,url,total,progress,notes,completed);
      startStudyTicker(a);
      renderStudyHistory(a);
    });
    Button finish=a.btn("■ FINALIZAR SESSÃO E SALVAR TUDO");
    finish.setOnClickListener(v->{
      finishStudy(a,title,teacher,subject,topic,url,total,progress,notes,completed);
      renderStudyHistory(a);
      startStudyTicker(a);
    });
    Button note=a.btn("＋ SALVAR PROGRESSO SEM CRONÔMETRO");
    note.setOnClickListener(v->{saveStudyNote(a,title,teacher,subject,topic,url,total,progress,notes,completed);renderStudyHistory(a);});
    Button export=a.btn("💾 EXPORTAR ESTUDOS");
    export.setOnClickListener(v->exportJsonl(a,"studies",STUDIES,"estudos"));
    buttons.addView(start);buttons.addView(finish);buttons.addView(note);buttons.addView(export);
    a.body.addView(buttons);

    renderStudyHistory(a);
    startStudyTicker(a);
  }

  static void showClients(MainActivity a){
    a.clear("Clientes · projetos · horas");
    a.body.addView(a.tv("Cadastro local. Nada é publicado. Registre cliente, projeto, tarefa, entrega e tempo real trabalhado.",14));
    clientClock=a.tv(activeTimerText(a,"client"),28); a.body.addView(clientClock);

    EditText client=a.field("Cliente");
    EditText project=a.field("Projeto");
    EditText service=a.field("Serviço / tarefa atual");
    EditText status=a.field("Status: briefing, produção, revisão, entregue...");
    EditText deadline=a.field("Prazo / data combinada");
    EditText notes=a.field("Notas, entregas, valores ou referências que você decidir registrar");

    prefillClientActive(a,client,project,service,status,deadline,notes);

    a.body.addView(client);a.body.addView(project);a.body.addView(service);a.body.addView(status);a.body.addView(deadline);a.body.addView(notes);

    Button save=a.btn("＋ SALVAR REGISTRO DO CLIENTE");
    save.setOnClickListener(v->{saveClientNote(a,client,project,service,status,deadline,notes);renderClientHistory(a);});
    Button start=a.btn("▶ INICIAR TEMPO DE TRABALHO");
    start.setOnClickListener(v->{startClientTimer(a,client,project,service,status,deadline,notes);startClientTicker(a);});
    Button finish=a.btn("■ FINALIZAR TRABALHO E SALVAR HORAS");
    finish.setOnClickListener(v->{finishClient(a,client,project,service,status,deadline,notes);renderClientHistory(a);startClientTicker(a);});
    Button export=a.btn("💾 EXPORTAR CLIENTES");
    export.setOnClickListener(v->exportJsonl(a,"clients",CLIENTS,"clientes"));
    a.body.addView(save);a.body.addView(start);a.body.addView(finish);a.body.addView(export);
    renderClientHistory(a);
    startClientTicker(a);
  }

  static void showT8i(MainActivity a){
    a.clear("Canon T8i · RAW CR3 · vídeo");
    a.body.addView(a.tv("CR3 de fotografia é RAW de sensor, não C-Log. O fluxo preserva o original, cria cópia de depósito e pode enviar o CR3 ao Super Studio do PC para revelação via rawpy/LibRaw. MP4 permanece separado para fluxo de vídeo/cor.",14));

    String last=a.secrets.getString("t8i_last_name","Nenhum CR3/MP4 selecionado");
    t8iStatus=a.card("ARQUIVO ATUAL",last+"\n"+a.secrets.getString("t8i_last_meta",""));
    a.body.addView(t8iStatus);

    Button pick=a.btn("📷 Selecionar CR3 ou MP4");
    pick.setOnClickListener(v->{
      Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT);
      i.addCategory(Intent.CATEGORY_OPENABLE);
      i.setType("*/*");
      i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
      a.startActivityForResult(i,PICK_T8I);
    });
    a.body.addView(pick);

    Button rawFolder=a.btn("🗂 Escolher depósito dos ORIGINAIS T8i");
    rawFolder.setOnClickListener(v->pickTree(a,TREE_T8I_RAW));
    a.body.addView(rawFolder);
    Button exportFolder=a.btn("🗂 Escolher depósito das REVELAÇÕES T8i");
    exportFolder.setOnClickListener(v->pickTree(a,TREE_T8I_EXPORTS));
    a.body.addView(exportFolder);

    Button copy=a.btn("🛡 COPIAR ORIGINAL PARA DEPÓSITO");
    copy.setOnClickListener(v->copySelectedT8i(a));
    a.body.addView(copy);

    EditText pc=a.field("URL do Super Studio no PC, ex.: http://192.168.1.2:5060");
    pc.setText(a.secrets.getString("studio_url",a.secrets.getString("pc_url","")));
    EditText token=a.field("Token local do Super Studio");
    token.setText(a.secrets.getString("studio_token",a.secrets.getString("pc_key","")));
    token.setInputType(129);
    EditText brightness=a.field("Brilho RAW (padrão 1.0)");
    brightness.setText(a.secrets.getString("t8i_brightness","1.0"));
    EditText quality=a.field("Qualidade JPEG 40–100");
    quality.setText(a.secrets.getString("t8i_quality","95"));
    a.body.addView(pc);a.body.addView(token);a.body.addView(brightness);a.body.addView(quality);

    Button saveRoute=a.btn("Salvar rota T8i");
    saveRoute.setOnClickListener(v->{
      a.secrets.edit().putString("studio_url",pc.getText().toString().trim())
          .putString("studio_token",token.getText().toString().trim())
          .putString("t8i_brightness",brightness.getText().toString().trim())
          .putString("t8i_quality",quality.getText().toString().trim()).apply();
      a.toast("Rota T8i salva no cofre local.");
    });
    a.body.addView(saveRoute);

    Button check=a.btn("🔎 VERIFICAR DEPENDÊNCIAS T8i NO PC");
    check.setOnClickListener(v->{
      saveRoute.performClick();
      pcGet(a,"/api/mobile/t8i/status",res->a.ui(()->{t8iStatus.setText("SUPORTE PC\n"+res);}));
    });
    a.body.addView(check);

    Button install=a.btn("⬇ INSTALAR SUPORTE T8i NO AMBIENTE ISOLADO DO PC");
    install.setOnClickListener(v->new AlertDialog.Builder(a)
        .setTitle("Instalar dependências T8i?")
        .setMessage("Instala somente requirements-t8i.txt no .venv do Super Studio: rawpy/LibRaw, NumPy, imageio e tifffile. Não altera o CR3 original.")
        .setNegativeButton("Cancelar",null)
        .setPositiveButton("Instalar",(d,w)->{
          saveRoute.performClick();
          pcPostJson(a,"/api/mobile/t8i/deps/install",json().put("confirm","INSTALAR_T8I"),res->a.ui(()->t8iStatus.setText("INSTALAÇÃO T8i\n"+res)));
        }).show());
    a.body.addView(install);

    Button develop=a.btn("⚙ REVELAR CR3 NO PC + TRAZER JPEG PARA O CELULAR");
    develop.setOnClickListener(v->{
      saveRoute.performClick();
      sendT8iToPc(a,brightness.getText().toString().trim(),quality.getText().toString().trim());
    });
    a.body.addView(develop);

    Button deposits=a.btn("Abrir Depósitos & Backup");
    deposits.setOnClickListener(v->showDeposits(a));
    a.body.addView(deposits);

    a.body.addView(a.tv("Fluxo: selecionar → preservar original → verificar dependências → revelar no PC → copiar JPEG final para o depósito escolhido no Android. Se o PC estiver offline, o original e o registro continuam salvos.",12));
  }

  static boolean onActivityResult(MainActivity a,int request,int result,Intent data){
    if(result!=Activity.RESULT_OK || data==null) return false;
    try{
      if(request==PICK_T8I && data.getData()!=null){
        Uri uri=data.getData();
        try{a.getContentResolver().takePersistableUriPermission(uri,Intent.FLAG_GRANT_READ_URI_PERMISSION);}catch(Exception ignored){}
        FileMeta m=meta(a,uri);
        a.secrets.edit().putString("t8i_last_uri",uri.toString()).putString("t8i_last_name",m.name)
            .putString("t8i_last_meta",m.mime+" • "+m.size+" bytes").apply();
        append(a,T8I,json().put("type","selected").put("name",m.name).put("mime",m.mime).put("size",m.size).put("uri",uri.toString()));
        if(t8iStatus!=null)t8iStatus.setText("ARQUIVO ATUAL\n"+m.name+"\n"+m.mime+" • "+m.size+" bytes");
        a.toast("T8i registrado. Original não foi alterado.");
        return true;
      }
      if(request==TREE_MASTER && data.getData()!=null){
        Uri root=data.getData();
        persistTree(a,root);
        SharedPreferences.Editor ed=a.secrets.edit().putString("deposit_master_root",root.toString());
        for(String key:TREE_NAMES.keySet()) ed.putString("deposit_"+key+"_root",root.toString());
        ed.apply();
        for(String key:TREE_NAMES.keySet()) ensureFolder(a,key);
        append(a,EVENTS,json().put("type","master_deposit_set").put("root",root.toString()));
        a.toast("Estrutura AURION criada na raiz escolhida.");
        showDeposits(a);
        return true;
      }
      String key=TREE_KEYS.get(request);
      if(key!=null && data.getData()!=null){
        Uri root=data.getData();
        persistTree(a,root);
        a.secrets.edit().putString("deposit_"+key+"_root",root.toString()).apply();
        DocumentFile folder=ensureFolder(a,key);
        append(a,EVENTS,json().put("type","deposit_set").put("category",key).put("root",root.toString()).put("folder",folder==null?"":String.valueOf(folder.getUri())));
        a.toast("Depósito "+TREE_NAMES.get(key)+" configurado.");
        showDeposits(a);
        return true;
      }
    }catch(Exception e){a.toast("Falha no seletor: "+e.getMessage());return true;}
    return false;
  }

  static void logConversation(MainActivity a,String role,String provider,String text){
    if(text==null||text.trim().isEmpty())return;
    append(a,CONVERSATIONS,json().put("role",role).put("provider",provider==null?"":provider).put("text",text));
  }

  static void exportConversations(MainActivity a){
    DocumentFile folder=ensureFolder(a,"conversations");
    if(folder==null){a.toast("Escolha o depósito de conversas primeiro.");showDeposits(a);return;}
    try{
      List<JSONObject> rows=read(a,CONVERSATIONS,10000);
      StringBuilder txt=new StringBuilder("AURION ONE · CONVERSAS\nExportado: "+now()+"\n\n");
      for(JSONObject o:rows){
        txt.append(o.optString("ts")).append(" · ").append(o.optString("role")).append(" · ").append(o.optString("provider")).append("\n");
        txt.append(o.optString("text")).append("\n\n");
      }
      writeText(a,folder,"AURION_CONVERSAS_"+stamp()+".txt","text/plain",txt.toString());
      writeText(a,folder,"AURION_CONVERSAS_"+stamp()+".jsonl","application/json",rawFile(a,CONVERSATIONS));
      a.toast("Conversas exportadas sem apagar a cópia interna.");
    }catch(Exception e){a.toast("Falha ao exportar conversas: "+e.getMessage());}
  }

  static void exportBackup(MainActivity a){
    DocumentFile folder=ensureFolder(a,"backups");
    if(folder==null){a.toast("Escolha o depósito de backups primeiro.");return;}
    new Thread(()->{
      try{
        DocumentFile out=folder.createFile("application/zip","AURION_BACKUP_"+stamp()+".zip");
        if(out==null)throw new IOException("Não foi possível criar ZIP");
        try(OutputStream os=a.getContentResolver().openOutputStream(out.getUri()); ZipOutputStream zip=new ZipOutputStream(os)){
          for(String name:new String[]{CONVERSATIONS,STUDIES,CLIENTS,T8I,EVENTS}){
            File src=file(a,name); if(!src.isFile())continue;
            zip.putNextEntry(new ZipEntry(name));
            try(InputStream in=new FileInputStream(src)){copy(in,zip);}
            zip.closeEntry();
          }
          JSONObject settings=json().put("exported_at",now()).put("version","3.0.0");
          JSONObject deposits=json();
          for(String key:TREE_NAMES.keySet()) deposits.put(key,a.secrets.getString("deposit_"+key+"_root",""));
          settings.put("deposits",deposits);
          zip.putNextEntry(new ZipEntry("settings_public.json"));
          zip.write(settings.toString(2).getBytes(StandardCharsets.UTF_8));
          zip.closeEntry();
        }
        append(a,EVENTS,json().put("type","backup_exported").put("uri",out.getUri().toString()));
        a.ui(()->a.toast("Backup completo salvo."));
      }catch(Exception e){a.ui(()->a.toast("Falha no backup: "+e.getMessage()));}
    }).start();
  }

  static void exportJsonl(MainActivity a,String category,String source,String label){
    DocumentFile folder=ensureFolder(a,category);
    if(folder==null){a.toast("Escolha o depósito de "+label+" primeiro.");return;}
    try{
      writeText(a,folder,"AURION_"+label.toUpperCase(Locale.ROOT)+"_"+stamp()+".jsonl","application/json",rawFile(a,source));
      a.toast("Histórico de "+label+" exportado.");
    }catch(Exception e){a.toast("Falha ao exportar: "+e.getMessage());}
  }

  private static void renderStudyHistory(MainActivity a){
    long sec=totalSeconds(a,STUDIES,"study_finish");
    List<JSONObject> rows=read(a,STUDIES,2000);
    int finished=0,notes=0;Map<String,Long> bySubject=new LinkedHashMap<>();
    for(JSONObject o:rows){
      String type=o.optString("type");
      if("study_finish".equals(type)){
        finished++;long s=o.optLong("seconds");
        String sub=o.optString("subject","Sem assunto"); if(sub.isEmpty())sub="Sem assunto";
        bySubject.put(sub,bySubject.getOrDefault(sub,0L)+s);
      }else if("study_note".equals(type))notes++;
    }
    a.body.addView(a.card("RESUMO",finished+" sessões • "+formatSeconds(sec)+" • "+notes+" registros sem cronômetro"));
    StringBuilder totals=new StringBuilder();
    for(Map.Entry<String,Long> e:bySubject.entrySet())totals.append(e.getKey()).append(" · ").append(formatSeconds(e.getValue())).append("\n");
    if(totals.length()>0)a.body.addView(a.card("TEMPO POR ASSUNTO",totals.toString().trim()));

    int shown=0;
    for(int i=rows.size()-1;i>=0 && shown<12;i--){
      JSONObject o=rows.get(i); if(!o.optString("type").startsWith("study_"))continue;
      String line=o.optString("title","Estudo")+" · "+o.optString("subject","")+" · "+o.optString("topic","");
      if(o.has("seconds"))line+="\n"+formatSeconds(o.optLong("seconds"));
      if(o.has("progress"))line+=" · "+o.optInt("progress")+"%";
      if(o.optBoolean("completed",false))line+=" · CONCLUÍDO";
      if(!o.optString("notes").isEmpty())line+="\n"+o.optString("notes");
      a.body.addView(a.card("HISTÓRICO",line)); shown++;
    }
  }

  private static void startTimer(MainActivity a,String kind,EditText title,EditText teacher,EditText subject,EditText topic,EditText url,EditText total,EditText progress,EditText notes,CheckBox completed){
    if(a.secrets.getLong(kind+"_active_started",0)>0){a.toast("Já existe uma sessão ativa. Finalize antes de iniciar outra.");return;}
    long started=System.currentTimeMillis();
    String id=kind+"-"+started;
    SharedPreferences.Editor e=a.secrets.edit().putLong(kind+"_active_started",started).putString(kind+"_active_id",id)
        .putString(kind+"_active_title",text(title)).putString(kind+"_active_teacher",text(teacher))
        .putString(kind+"_active_subject",text(subject)).putString(kind+"_active_topic",text(topic))
        .putString(kind+"_active_url",text(url)).putString(kind+"_active_total",text(total))
        .putString(kind+"_active_progress",text(progress)).putString(kind+"_active_notes",text(notes))
        .putBoolean(kind+"_active_completed",completed.isChecked());
    e.apply();
    append(a,STUDIES,json().put("type","study_start").put("id",id).put("title",text(title)).put("teacher",text(teacher)).put("subject",text(subject)).put("topic",text(topic)).put("started_ms",started));
    a.toast("Cronômetro iniciado e persistido.");
  }

  private static void finishStudy(MainActivity a,EditText title,EditText teacher,EditText subject,EditText topic,EditText url,EditText total,EditText progress,EditText notes,CheckBox completed){
    long started=a.secrets.getLong("study_active_started",0);
    if(started<=0){a.toast("Nenhuma sessão de estudo ativa.");return;}
    long finished=System.currentTimeMillis();
    String t=text(title).isEmpty()?a.secrets.getString("study_active_title","Estudo"):text(title);
    JSONObject o=json().put("type","study_finish").put("id",a.secrets.getString("study_active_id","study-"+started))
        .put("title",t).put("teacher",fallback(text(teacher),a.secrets.getString("study_active_teacher","")))
        .put("subject",fallback(text(subject),a.secrets.getString("study_active_subject","")))
        .put("topic",fallback(text(topic),a.secrets.getString("study_active_topic","")))
        .put("url",fallback(text(url),a.secrets.getString("study_active_url","")))
        .put("notes",text(notes)).put("progress",boundedInt(text(progress),0,100,-1))
        .put("total_hours_declared",safeDouble(text(total),-1)).put("completed",completed.isChecked())
        .put("started_ms",started).put("finished_ms",finished).put("seconds",Math.max(0,(finished-started)/1000));
    append(a,STUDIES,o);
    clearActive(a,"study");
    a.toast("Sessão salva: "+formatSeconds(o.optLong("seconds")));
  }

  private static void saveStudyNote(MainActivity a,EditText title,EditText teacher,EditText subject,EditText topic,EditText url,EditText total,EditText progress,EditText notes,CheckBox completed){
    if(text(title).isEmpty()){a.toast("Informe o estudo.");return;}
    append(a,STUDIES,json().put("type","study_note").put("title",text(title)).put("teacher",text(teacher))
        .put("subject",text(subject)).put("topic",text(topic)).put("url",text(url)).put("notes",text(notes))
        .put("progress",boundedInt(text(progress),0,100,-1)).put("total_hours_declared",safeDouble(text(total),-1))
        .put("completed",completed.isChecked()));
    a.toast("Progresso salvo.");
  }

  private static void prefillActive(MainActivity a,String kind,EditText title,EditText teacher,EditText subject,EditText topic,EditText url,EditText total,EditText progress,EditText notes,CheckBox completed){
    if(a.secrets.getLong(kind+"_active_started",0)<=0)return;
    title.setText(a.secrets.getString(kind+"_active_title",""));teacher.setText(a.secrets.getString(kind+"_active_teacher",""));
    subject.setText(a.secrets.getString(kind+"_active_subject",""));topic.setText(a.secrets.getString(kind+"_active_topic",""));
    url.setText(a.secrets.getString(kind+"_active_url",""));total.setText(a.secrets.getString(kind+"_active_total",""));
    progress.setText(a.secrets.getString(kind+"_active_progress",""));notes.setText(a.secrets.getString(kind+"_active_notes",""));
    completed.setChecked(a.secrets.getBoolean(kind+"_active_completed",false));
  }

  private static void startStudyTicker(MainActivity a){
    if(studyTicker!=null)TIMER_HANDLER.removeCallbacks(studyTicker);
    studyTicker=new Runnable(){public void run(){if(studyClock!=null)studyClock.setText(activeTimerText(a,"study"));TIMER_HANDLER.postDelayed(this,1000);}};
    TIMER_HANDLER.post(studyTicker);
  }

  private static void saveClientNote(MainActivity a,EditText client,EditText project,EditText service,EditText status,EditText deadline,EditText notes){
    if(text(client).isEmpty()&&text(project).isEmpty()){a.toast("Informe cliente ou projeto.");return;}
    append(a,CLIENTS,json().put("type","client_note").put("client",text(client)).put("project",text(project)).put("service",text(service))
        .put("status",text(status)).put("deadline",text(deadline)).put("notes",text(notes)));
    a.toast("Cliente/projeto salvo.");
  }

  private static void startClientTimer(MainActivity a,EditText client,EditText project,EditText service,EditText status,EditText deadline,EditText notes){
    if(a.secrets.getLong("client_active_started",0)>0){a.toast("Já existe trabalho de cliente em andamento.");return;}
    if(text(client).isEmpty()&&text(project).isEmpty()){a.toast("Informe cliente ou projeto.");return;}
    long st=System.currentTimeMillis();
    a.secrets.edit().putLong("client_active_started",st).putString("client_active_id","client-"+st)
        .putString("client_active_client",text(client)).putString("client_active_project",text(project))
        .putString("client_active_service",text(service)).putString("client_active_status",text(status))
        .putString("client_active_deadline",text(deadline)).putString("client_active_notes",text(notes)).apply();
    append(a,CLIENTS,json().put("type","client_start").put("client",text(client)).put("project",text(project)).put("service",text(service)).put("started_ms",st));
    a.toast("Cronômetro de cliente iniciado.");
  }

  private static void finishClient(MainActivity a,EditText client,EditText project,EditText service,EditText status,EditText deadline,EditText notes){
    long st=a.secrets.getLong("client_active_started",0);
    if(st<=0){a.toast("Nenhum cronômetro de cliente ativo.");return;}
    long end=System.currentTimeMillis();
    JSONObject o=json().put("type","client_finish").put("id",a.secrets.getString("client_active_id","client-"+st))
        .put("client",fallback(text(client),a.secrets.getString("client_active_client","")))
        .put("project",fallback(text(project),a.secrets.getString("client_active_project","")))
        .put("service",fallback(text(service),a.secrets.getString("client_active_service","")))
        .put("status",fallback(text(status),a.secrets.getString("client_active_status","")))
        .put("deadline",fallback(text(deadline),a.secrets.getString("client_active_deadline","")))
        .put("notes",text(notes)).put("started_ms",st).put("finished_ms",end).put("seconds",Math.max(0,(end-st)/1000));
    append(a,CLIENTS,o);clearActive(a,"client");a.toast("Trabalho salvo: "+formatSeconds(o.optLong("seconds")));
  }

  private static void prefillClientActive(MainActivity a,EditText client,EditText project,EditText service,EditText status,EditText deadline,EditText notes){
    if(a.secrets.getLong("client_active_started",0)<=0)return;
    client.setText(a.secrets.getString("client_active_client",""));project.setText(a.secrets.getString("client_active_project",""));
    service.setText(a.secrets.getString("client_active_service",""));status.setText(a.secrets.getString("client_active_status",""));
    deadline.setText(a.secrets.getString("client_active_deadline",""));notes.setText(a.secrets.getString("client_active_notes",""));
  }

  private static void renderClientHistory(MainActivity a){
    long sec=totalSeconds(a,CLIENTS,"client_finish");List<JSONObject> rows=read(a,CLIENTS,2000);
    int records=0;Map<String,Long> byClient=new LinkedHashMap<>();
    for(JSONObject o:rows){if(o.optString("type").startsWith("client_"))records++;if("client_finish".equals(o.optString("type"))){String c=o.optString("client","Sem cliente");if(c.isEmpty())c="Sem cliente";byClient.put(c,byClient.getOrDefault(c,0L)+o.optLong("seconds"));}}
    a.body.addView(a.card("RESUMO",records+" registros • "+formatSeconds(sec)));
    StringBuilder sb=new StringBuilder();for(Map.Entry<String,Long> e:byClient.entrySet())sb.append(e.getKey()).append(" · ").append(formatSeconds(e.getValue())).append("\n");
    if(sb.length()>0)a.body.addView(a.card("HORAS POR CLIENTE",sb.toString().trim()));
    int shown=0;for(int i=rows.size()-1;i>=0&&shown<12;i--){JSONObject o=rows.get(i);if(!o.optString("type").startsWith("client_"))continue;String x=o.optString("client")+" · "+o.optString("project")+"\n"+o.optString("service")+" · "+o.optString("status");if(o.has("seconds"))x+="\n"+formatSeconds(o.optLong("seconds"));if(!o.optString("notes").isEmpty())x+="\n"+o.optString("notes");a.body.addView(a.card("HISTÓRICO",x));shown++;}
  }

  private static void startClientTicker(MainActivity a){
    if(clientTicker!=null)TIMER_HANDLER.removeCallbacks(clientTicker);
    clientTicker=new Runnable(){public void run(){if(clientClock!=null)clientClock.setText(activeTimerText(a,"client"));TIMER_HANDLER.postDelayed(this,1000);}};
    TIMER_HANDLER.post(clientTicker);
  }

  private static String activeTimerText(MainActivity a,String kind){
    long st=a.secrets.getLong(kind+"_active_started",0);
    if(st<=0)return "00:00:00 · nenhum cronômetro ativo";
    String name=a.secrets.getString(kind+"_active_title",a.secrets.getString(kind+"_active_project",""));
    return formatSeconds((System.currentTimeMillis()-st)/1000)+" · "+name;
  }

  private static void clearActive(MainActivity a,String kind){
    SharedPreferences.Editor e=a.secrets.edit();
    for(String suffix:new String[]{"started","id","title","teacher","subject","topic","url","total","progress","notes","client","project","service","status","deadline"})e.remove(kind+"_active_"+suffix);
    e.remove(kind+"_active_completed").apply();
  }

  private static void copySelectedT8i(MainActivity a){
    String s=a.secrets.getString("t8i_last_uri","");
    if(s.isEmpty()){a.toast("Selecione um CR3/MP4 primeiro.");return;}
    DocumentFile folder=ensureFolder(a,"t8i_raw");if(folder==null){a.toast("Escolha o depósito T8i RAW primeiro.");return;}
    new Thread(()->{
      try{
        Uri uri=Uri.parse(s);FileMeta m=meta(a,uri);
        DocumentFile out=folder.createFile(m.mime==null||m.mime.isEmpty()?"application/octet-stream":m.mime,m.name);
        if(out==null)throw new IOException("Não foi possível criar o arquivo");
        try(InputStream in=a.getContentResolver().openInputStream(uri);OutputStream os=a.getContentResolver().openOutputStream(out.getUri())){copy(in,os);}
        append(a,T8I,json().put("type","original_copied").put("name",m.name).put("size",m.size).put("destination",out.getUri().toString()));
        a.ui(()->a.toast("Original copiado. Fonte permaneceu intacta."));
      }catch(Exception e){a.ui(()->a.toast("Falha ao copiar original: "+e.getMessage()));}
    }).start();
  }

  private static void sendT8iToPc(MainActivity a,String brightness,String quality){
    String uriText=a.secrets.getString("t8i_last_uri","");
    String name=a.secrets.getString("t8i_last_name","");
    if(uriText.isEmpty()){a.toast("Selecione um CR3.");return;}
    if(!name.toLowerCase(Locale.ROOT).endsWith(".cr3")){a.toast("Revelação RAW aceita somente .CR3. MP4 usa o fluxo de vídeo.");return;}
    String base=a.secrets.getString("studio_url","").replaceAll("/+$","");
    String token=a.secrets.getString("studio_token","");
    if(base.isEmpty()||token.isEmpty()){a.toast("Configure URL e token do Super Studio.");return;}
    if(t8iStatus!=null)t8iStatus.setText("T8i\nEnviando CR3 ao PC...");
    new Thread(()->{
      try{
        Uri uri=Uri.parse(uriText);FileMeta m=meta(a,uri);
        String boundary="----Aurion"+System.currentTimeMillis();
        HttpURLConnection c=(HttpURLConnection)new URL(base+"/api/t8i/develop").openConnection();
        c.setConnectTimeout(15000);c.setReadTimeout(240000);c.setRequestMethod("POST");c.setDoOutput(true);
        c.setRequestProperty("X-Aurion-Token",token);c.setRequestProperty("Content-Type","multipart/form-data; boundary="+boundary);
        try(DataOutputStream out=new DataOutputStream(c.getOutputStream())){
          writePart(out,boundary,"params",json().put("brightness",safeDouble(brightness,1.0)).put("quality",boundedInt(quality,40,100,95)).toString());
          out.writeBytes("--"+boundary+"\r\n");
          out.writeBytes("Content-Disposition: form-data; name=\"file\"; filename=\""+m.name.replace("\"","_")+"\"\r\n");
          out.writeBytes("Content-Type: application/octet-stream\r\n\r\n");
          try(InputStream in=a.getContentResolver().openInputStream(uri)){byte[] buf=new byte[1024*256];int n;while((n=in.read(buf))>0)out.write(buf,0,n);}
          out.writeBytes("\r\n--"+boundary+"--\r\n");out.flush();
        }
        int code=c.getResponseCode();String res=readResponse(c);
        append(a,T8I,json().put("type","develop_response").put("name",m.name).put("status",code).put("response",res));
        if(code>=200&&code<300){
          String download="";
          try{JSONObject j=new JSONObject(res);download=j.optString("download_name");if(download.isEmpty()&&j.has("result"))download=new File(j.getJSONObject("result").optString("output")).getName();}catch(Exception ignored){}
          final String dname=download;
          a.ui(()->{if(t8iStatus!=null)t8iStatus.setText("T8i\nRevelação concluída no PC.\n"+res);a.toast("CR3 revelado no PC.");});
          if(!dname.isEmpty())downloadT8iResult(a,base,token,dname);
        }else a.ui(()->{if(t8iStatus!=null)t8iStatus.setText("T8i\nFalha "+code+"\n"+res);});
      }catch(Exception e){append(a,T8I,json().put("type","develop_error").put("error",String.valueOf(e)));a.ui(()->{if(t8iStatus!=null)t8iStatus.setText("T8i\nFalha: "+e.getMessage());a.toast("Falha T8i: "+e.getMessage());});}
    }).start();
  }

  private static void downloadT8iResult(MainActivity a,String base,String token,String name){
    DocumentFile folder=ensureFolder(a,"t8i_exports");
    if(folder==null){a.ui(()->a.toast("Revelação ficou no PC. Escolha o depósito T8i EXPORTS para baixar ao celular."));return;}
    try{
      String enc=URLEncoder.encode(name,"UTF-8").replace("+","%20");
      HttpURLConnection c=(HttpURLConnection)new URL(base+"/api/mobile/t8i/export/"+enc).openConnection();
      c.setConnectTimeout(10000);c.setReadTimeout(120000);c.setRequestProperty("X-Aurion-Token",token);
      int code=c.getResponseCode();if(code<200||code>=300)throw new IOException("download HTTP "+code+" "+readResponse(c));
      DocumentFile out=folder.createFile("image/jpeg",name);
      if(out==null)throw new IOException("não criou JPEG no depósito");
      try(InputStream in=c.getInputStream();OutputStream os=a.getContentResolver().openOutputStream(out.getUri())){copy(in,os);}
      append(a,T8I,json().put("type","develop_downloaded").put("name",name).put("destination",out.getUri().toString()));
      a.ui(()->a.toast("JPEG revelado salvo no depósito T8i."));
    }catch(Exception e){a.ui(()->a.toast("Revelou no PC, mas não baixou ao celular: "+e.getMessage()));}
  }

  private static void pcGet(MainActivity a,String path,java.util.function.Consumer<String> done){
    String base=a.secrets.getString("studio_url","").replaceAll("/+$",""),token=a.secrets.getString("studio_token","");
    if(base.isEmpty()||token.isEmpty()){a.toast("Configure URL e token do Super Studio.");return;}
    new Thread(()->{try{HttpURLConnection c=(HttpURLConnection)new URL(base+path).openConnection();c.setConnectTimeout(8000);c.setReadTimeout(30000);c.setRequestProperty("X-Aurion-Token",token);done.accept(readResponse(c));}catch(Exception e){done.accept("Falha: "+e.getMessage());}}).start();
  }

  private static void pcPostJson(MainActivity a,String path,JSONObject payload,java.util.function.Consumer<String> done){
    String base=a.secrets.getString("studio_url","").replaceAll("/+$",""),token=a.secrets.getString("studio_token","");
    if(base.isEmpty()||token.isEmpty()){a.toast("Configure URL e token do Super Studio.");return;}
    new Thread(()->{try{HttpURLConnection c=(HttpURLConnection)new URL(base+path).openConnection();c.setConnectTimeout(10000);c.setReadTimeout(900000);c.setRequestMethod("POST");c.setDoOutput(true);c.setRequestProperty("X-Aurion-Token",token);c.setRequestProperty("Content-Type","application/json; charset=utf-8");try(OutputStream o=c.getOutputStream()){o.write(payload.toString().getBytes(StandardCharsets.UTF_8));}done.accept(readResponse(c));}catch(Exception e){done.accept("Falha: "+e.getMessage());}}).start();
  }

  private static String readResponse(HttpURLConnection c)throws Exception{
    InputStream in=c.getResponseCode()>=400?c.getErrorStream():c.getInputStream();if(in==null)return "";
    ByteArrayOutputStream b=new ByteArrayOutputStream();copy(in,b);return b.toString("UTF-8");
  }

  private static void writePart(DataOutputStream out,String boundary,String name,String value)throws IOException{
    out.writeBytes("--"+boundary+"\r\n");out.writeBytes("Content-Disposition: form-data; name=\""+name+"\"\r\n\r\n");out.write(value.getBytes(StandardCharsets.UTF_8));out.writeBytes("\r\n");
  }

  private static void pickTree(MainActivity a,int request){
    Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);
    i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_WRITE_URI_PERMISSION|Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION|Intent.FLAG_GRANT_PREFIX_URI_PERMISSION);
    a.startActivityForResult(i,request);
  }

  private static void persistTree(MainActivity a,Uri root){
    try{a.getContentResolver().takePersistableUriPermission(root,Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_WRITE_URI_PERMISSION);}catch(Exception ignored){}
  }

  private static int requestForKey(String key){
    for(Map.Entry<Integer,String> e:TREE_KEYS.entrySet())if(e.getValue().equals(key))return e.getKey();
    return TREE_MASTER;
  }

  private static DocumentFile ensureFolder(MainActivity a,String key){
    String root=a.secrets.getString("deposit_"+key+"_root",a.secrets.getString("deposit_master_root",""));
    if(root.isEmpty())return null;
    try{
      DocumentFile r=DocumentFile.fromTreeUri(a,Uri.parse(root));if(r==null||!r.canWrite())return null;
      String name=TREE_NAMES.get(key);DocumentFile f=r.findFile(name);if(f==null)f=r.createDirectory(name);return f;
    }catch(Exception e){return null;}
  }

  private static String folderState(MainActivity a,String key){
    DocumentFile f=ensureFolder(a,key);return f==null?"NÃO CONFIGURADO":"ATIVO · "+String.valueOf(f.getName());
  }

  private static void writeText(MainActivity a,DocumentFile folder,String name,String mime,String data)throws Exception{
    DocumentFile f=folder.createFile(mime,name);if(f==null)throw new IOException("Não foi possível criar "+name);
    try(OutputStream o=a.getContentResolver().openOutputStream(f.getUri())){o.write(data.getBytes(StandardCharsets.UTF_8));}
  }

  private static File dir(MainActivity a){File d=new File(a.getFilesDir(),DATA_DIR);if(!d.exists())d.mkdirs();return d;}
  private static File file(MainActivity a,String name){return new File(dir(a),name);}

  private static synchronized void append(MainActivity a,String name,JSONObject o){
    try{
      if(!o.has("ts"))o.put("ts",now());
      try(FileOutputStream fos=new FileOutputStream(file(a,name),true);OutputStreamWriter w=new OutputStreamWriter(fos,StandardCharsets.UTF_8)){
        w.write(o.toString());w.write("\n");w.flush();fos.getFD().sync();
      }
    }catch(Exception e){a.ui(()->a.toast("Registro local falhou: "+e.getMessage()));}
  }

  private static List<JSONObject> read(MainActivity a,String name,int limit){
    ArrayList<JSONObject> out=new ArrayList<>();File f=file(a,name);if(!f.isFile())return out;
    try(BufferedReader b=new BufferedReader(new InputStreamReader(new FileInputStream(f),StandardCharsets.UTF_8))){
      String line;while((line=b.readLine())!=null){if(line.trim().isEmpty())continue;try{out.add(new JSONObject(line));}catch(JSONException ignored){}if(out.size()>limit)out.remove(0);}
    }catch(Exception ignored){}
    return out;
  }

  private static String rawFile(MainActivity a,String name)throws Exception{
    File f=file(a,name);if(!f.isFile())return "";
    ByteArrayOutputStream b=new ByteArrayOutputStream();try(InputStream in=new FileInputStream(f)){copy(in,b);}return b.toString("UTF-8");
  }

  private static long totalSeconds(MainActivity a,String name,String type){
    long n=0;for(JSONObject o:read(a,name,10000))if(type.equals(o.optString("type")))n+=Math.max(0,o.optLong("seconds"));return n;
  }

  private static JSONObject json(){return new JSONObject();}
  private static String text(EditText e){return e.getText().toString().trim();}
  private static String fallback(String a,String b){return a==null||a.trim().isEmpty()?b:a;}
  private static int boundedInt(String s,int min,int max,int def){try{return Math.max(min,Math.min(max,Integer.parseInt(s.trim())));}catch(Exception e){return def;}}
  private static double safeDouble(String s,double def){try{return Double.parseDouble(s.trim().replace(",","."));}catch(Exception e){return def;}}
  private static String now(){return new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSSZ",Locale.US).format(new Date());}
  private static String stamp(){return new SimpleDateFormat("yyyyMMdd_HHmmss",Locale.US).format(new Date());}
  private static String formatSeconds(long sec){sec=Math.max(0,sec);return String.format(Locale.US,"%02d:%02d:%02d",sec/3600,(sec/60)%60,sec%60);}

  private static void copy(InputStream in,OutputStream out)throws IOException{
    if(in==null||out==null)throw new IOException("stream indisponível");byte[] buf=new byte[1024*256];int n;while((n=in.read(buf))>0)out.write(buf,0,n);out.flush();
  }

  private static FileMeta meta(MainActivity a,Uri uri){
    String name="arquivo_"+System.currentTimeMillis(),mime=a.getContentResolver().getType(uri);long size=-1;
    try(Cursor c=a.getContentResolver().query(uri,new String[]{OpenableColumns.DISPLAY_NAME,OpenableColumns.SIZE},null,null,null)){
      if(c!=null&&c.moveToFirst()){int ni=c.getColumnIndex(OpenableColumns.DISPLAY_NAME),si=c.getColumnIndex(OpenableColumns.SIZE);if(ni>=0)name=c.getString(ni);if(si>=0&&!c.isNull(si))size=c.getLong(si);}
    }catch(Exception ignored){}
    if(mime==null)mime="application/octet-stream";return new FileMeta(name,mime,size);
  }

  static void shutdown(){
    if(studyTicker!=null)TIMER_HANDLER.removeCallbacks(studyTicker);
    if(clientTicker!=null)TIMER_HANDLER.removeCallbacks(clientTicker);
    studyTicker=null;clientTicker=null;studyClock=null;clientClock=null;t8iStatus=null;
  }

  static final class FileMeta{
    final String name,mime;final long size;
    FileMeta(String n,String m,long s){name=n==null?"arquivo":n;mime=m==null?"application/octet-stream":m;size=s;}
  }
}
