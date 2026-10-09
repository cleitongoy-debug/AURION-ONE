package one.aurion.app;

import android.app.*;
import android.content.*;
import android.content.pm.PackageInfo;
import android.os.Build;
import androidx.annotation.NonNull;
import androidx.core.app.*;
import androidx.work.*;
import org.json.*;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Locale;

public class AurionHourlyWorker extends Worker {
  private static final String CHANNEL="aurion_updates";
  private static final String UPDATE="https://raw.githubusercontent.com/cleitongoy-debug/AURION-ONE/main/android/updates/latest.json";
  private static final String HEAD="https://api.github.com/repos/cleitongoy-debug/AURION-ONE/commits?sha=main&per_page=1";
  public AurionHourlyWorker(@NonNull Context c,@NonNull WorkerParameters p){super(c,p);}
  @NonNull public Result doWork(){Context c=getApplicationContext();AurionStore store=new AurionStore(c);SharedPreferences n=c.getSharedPreferences("aurion_nodes",0),s=c.getSharedPreferences("aurion_auto_sync",0);JSONObject r=new JSONObject();boolean ok=false;
    try{JSONObject x=get(UPDATE,"");if(x.optBoolean("ok")){ok=true;JSONObject m=new JSONObject(x.optString("body","{}"));long cur=ver(c),next=m.optLong("versionCode");r.put("apk",new JSONObject().put("current",cur).put("available",next).put("versionName",m.optString("versionName")));if(next>cur)note(c,1001,"AURION "+m.optString("versionName")+" pendente",m.optString("notes","Atualização disponível."));}}catch(Exception e){put(r,"apkError",e.getMessage());}
    try{JSONObject x=get(HEAD,"");if(x.optBoolean("ok")){ok=true;JSONArray a=new JSONArray(x.optString("body","[]"));String sha=a.length()>0?a.getJSONObject(0).optString("sha"):"",old=s.getString("repoSha","");r.put("gitHead",sha);if(!sha.isEmpty()){s.edit().putString("repoSha",sha).apply();if(!old.isEmpty()&&!old.equals(sha))note(c,1002,"AURION · Git mudou","Código novo detectado; o APK só será oferecido quando o canal assinado mudar.");}}}catch(Exception e){put(r,"gitError",e.getMessage());}
    // Drive: so metadados se credencial autorizada e valida, uma pagina por rodada.
    // Nenhum documento nem segredo e lido, copiado ou exportado ao Git.
    String drive=store.getSecret("googleDrive");
    if(!drive.isEmpty())try{
      String cursor=s.getString("driveCursor","");
      String q="https://www.googleapis.com/drive/v3/files?pageSize=100&orderBy=modifiedTime%20desc"
           +"&fields=nextPageToken,files(id,name,mimeType,modifiedTime,webViewLink,size)";
      if(!cursor.isEmpty())q+="&pageToken="+URLEncoder.encode(cursor,"UTF-8");
      JSONObject x=get(q,"Bearer "+drive);
      if(x.optBoolean("ok")){
        ok=true;
        JSONObject page=new JSONObject(x.optString("body","{}"));
        JSONArray files=page.optJSONArray("files");
        int indexed=0,modified=0,seen=0,blocked=0;
        SharedPreferences.Editor edits=s.edit();
        if(files!=null)for(int i=0;i<files.length();i++){
          JSONObject file=files.optJSONObject(i);
          if(file==null)continue;
          String id=file.optString("id",""),name=file.optString("name","");
          String low=name.toLowerCase(Locale.ROOT);
          if(!id.matches("[A-Za-z0-9_-]{8,200}")||low.startsWith(".") ||
             low.contains("local#server")||low.contains("secret")||low.contains("token")
             ||low.contains("senha")||low.contains("credential")||low.endsWith(".env")){
             blocked++;continue;
          }
          String fingerprint=sha(id+"\n"+file.optString("modifiedTime","")+"\n"
                +file.optString("size","")+"\n"+file.optString("mimeType",""));
          String key="driveItem_"+id,previous=s.getString(key,"");
          if(previous.equals(fingerprint)){seen++;continue;}
          String url=file.optString("webViewLink","");
          JSONObject meta=new JSONObject().put("source","DRIVE_METADATA_ONLY")
             .put("id",id).put("name",name).put("mime",file.optString("mimeType",""))
             .put("modifiedAt",file.optString("modifiedTime",""))
             .put("evidence","METADADOS_PROVEDOR").put("contentRead",false)
             .put("permissionState","NAO_VERIFICADA_POR_ESTA_CONSULTA");
          store.upsertReference("DRIVE "+id,name+(url.isEmpty()?"":"\n"+url),meta.toString());
          edits.putString(key,fingerprint);indexed++;
          if(!previous.isEmpty())modified++;
        }
        edits.putString("driveCursor",page.optString("nextPageToken","")).apply();
        r.put("drive","ok").put("drivePageIndexed",indexed).put("drivePageRepeated",seen)
         .put("drivePageExcluded",blocked).put("driveChangedKnown",modified)
         .put("driveComplete",page.optString("nextPageToken","").isEmpty());
        if(modified>0)note(c,1003,"AURION · Drive mudou","Metadados de arquivos ja catalogados mudaram.");
      }else r.put("drive","HTTP "+x.optInt("http"));
    }catch(Exception e){put(r,"driveError",e.getClass().getSimpleName());}
    String hf=store.getSecret("huggingface");if(!hf.isEmpty())try{JSONObject x=get("https://huggingface.co/api/whoami-v2","Bearer "+hf);if(x.optBoolean("ok")){ok=true;JSONObject me=new JSONObject(x.optString("body","{}"));String u=me.optString("name","");r.put("huggingface",u.isEmpty()?"conectado":u);if(!u.isEmpty()){JSONObject m=get("https://huggingface.co/api/models?author="+URLEncoder.encode(u,"UTF-8")+"&sort=lastModified&direction=-1&limit=10","Bearer "+hf);if(m.optBoolean("ok")){String fp=sha(m.optString("body","")),old=s.getString("hfFp","");s.edit().putString("hfFp",fp).apply();if(!old.isEmpty()&&!old.equals(fp))note(c,1004,"AURION · Hugging Face mudou","Modelos/repos do perfil conectado mudaram.");}}}}catch(Exception e){put(r,"hfError",e.getMessage());}
    String pc=n.getString("pcStudio",""),tok=store.getSecret("dedicationPc");if(!pc.isEmpty())try{JSONObject x=get(pc.replaceAll("/+$","")+"/api/mobile/snapshot",tok.isEmpty()?"":"X-Aurion-Token "+tok);if(x.optBoolean("ok")){ok=true;String fp=sha(x.optString("body","")),old=s.getString("pcFp","");s.edit().putString("pcFp",fp).apply();r.put("pc","online");if(!old.isEmpty()&&!old.equals(fp))note(c,1005,"AURION · PC mudou","Estado/arquivos do PC mudaram. Veja Portfólio / Sync.");}else r.put("pc","HTTP "+x.optInt("http"));}catch(Exception e){put(r,"pcError",e.getMessage());}
    try{r.put("checkedAt",System.currentTimeMillis());store.add("sync_event","Auto Sync · "+(ok?"ciclo concluído":"ciclo parcial"),r.toString(),new JSONObject().put("source","WorkManager").toString());}catch(Exception ignored){}AurionBootstrapIndex.scanWorkspace(c,store,false);
    if(c.getSharedPreferences("aurion_pc_sync_v1",0).getBoolean("enabled",false)) {
      JSONObject pcSync=AurionPcMemorySync.run(c,store,false);
      put(r,"pcMemorySync",pcSync.optBoolean("ok")?"RECIBO_LOCAL":"BLOQUEADO");
    }
    AurionBandChannel.sendCheckSummary(c,r);
    return ok?Result.success():Result.retry();}
  private static long ver(Context c)throws Exception{PackageInfo p=c.getPackageManager().getPackageInfo(c.getPackageName(),0);return Build.VERSION.SDK_INT>=28?p.getLongVersionCode():p.versionCode;}
  private static JSONObject get(String raw,String auth){JSONObject o=new JSONObject();HttpURLConnection h=null;try{h=(HttpURLConnection)new URL(raw).openConnection();h.setConnectTimeout(9000);h.setReadTimeout(18000);h.setRequestProperty("Accept","application/json");h.setRequestProperty("User-Agent","AURION-ONE-Poco/6.7");if(auth.startsWith("Bearer "))h.setRequestProperty("Authorization",auth);else if(auth.startsWith("X-Aurion-Token "))h.setRequestProperty("X-Aurion-Token",auth.substring(15));int code=h.getResponseCode();InputStream in=code>=400?h.getErrorStream():h.getInputStream();StringBuilder b=new StringBuilder();if(in!=null)try(BufferedReader br=new BufferedReader(new InputStreamReader(in,StandardCharsets.UTF_8))){String line;while((line=br.readLine())!=null&&b.length()<1500000)b.append(line).append('\n');}o.put("ok",code>=200&&code<300).put("http",code).put("body",b.toString().trim());}catch(Exception e){put(o,"error",e.getClass().getSimpleName()+": "+e.getMessage());}finally{if(h!=null)h.disconnect();}return o;}
  private static String sha(String t)throws Exception{MessageDigest d=MessageDigest.getInstance("SHA-256");byte[] h=d.digest(t.getBytes(StandardCharsets.UTF_8));StringBuilder s=new StringBuilder();for(byte b:h)s.append(String.format(Locale.ROOT,"%02x",b&255));return s.toString();}
  private static void put(JSONObject o,String k,Object v){try{o.put(k,v);}catch(Exception ignored){}}
  // Eventos de fonte detectada no verificador; canal voluntario do pulso.
  // Sem opt-in nao ha notificacao automatica. Regras de conteudo ficam em AurionBandChannel.
  private static void note(Context c,int id,String title,String text){
    AurionBandChannel.sendVerifiedEvent(c,id);
  }

}