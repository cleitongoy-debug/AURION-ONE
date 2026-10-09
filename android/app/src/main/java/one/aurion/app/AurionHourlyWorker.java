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
  private static final String UPDATE="https://raw.githubusercontent.com/cleitongoy-debug/AURION-ONE/feat/poco-autonomo-v6-20260928/android/updates/latest.json";
  private static final String HEAD="https://api.github.com/repos/cleitongoy-debug/AURION-ONE/commits?sha=feat%2Fdedicacao-certificados-20260928&per_page=1";
  public AurionHourlyWorker(@NonNull Context c,@NonNull WorkerParameters p){super(c,p);}
  @NonNull public Result doWork(){Context c=getApplicationContext();AurionStore store=new AurionStore(c);SharedPreferences n=c.getSharedPreferences("aurion_nodes",0),s=c.getSharedPreferences("aurion_auto_sync",0);JSONObject r=new JSONObject();boolean ok=false;
    try{JSONObject x=get(UPDATE,"");if(x.optBoolean("ok")){ok=true;JSONObject m=new JSONObject(x.optString("body","{}"));long cur=ver(c),next=m.optLong("versionCode");r.put("apk",new JSONObject().put("current",cur).put("available",next).put("versionName",m.optString("versionName")));if(next>cur)note(c,1001,"AURION "+m.optString("versionName")+" pendente",m.optString("notes","Atualização disponível."));}}catch(Exception e){put(r,"apkError",e.getMessage());}
    try{JSONObject x=get(HEAD,"");if(x.optBoolean("ok")){ok=true;JSONArray a=new JSONArray(x.optString("body","[]"));String sha=a.length()>0?a.getJSONObject(0).optString("sha"):"",old=s.getString("repoSha","");r.put("gitHead",sha);if(!sha.isEmpty()){s.edit().putString("repoSha",sha).apply();if(!old.isEmpty()&&!old.equals(sha))note(c,1002,"AURION · Git mudou","Código novo detectado; o APK só será oferecido quando o canal assinado mudar.");}}}catch(Exception e){put(r,"gitError",e.getMessage());}
    String drive=store.getSecret("googleDrive");if(!drive.isEmpty())try{JSONObject x=get("https://www.googleapis.com/drive/v3/files?pageSize=20&orderBy=modifiedTime%20desc&fields=files(id,name,mimeType,modifiedTime,webViewLink)","Bearer "+drive);if(x.optBoolean("ok")){ok=true;String fp=sha(x.optString("body","")),old=s.getString("driveFp","");s.edit().putString("driveFp",fp).apply();r.put("drive","ok");if(!old.isEmpty()&&!old.equals(fp))note(c,1003,"AURION · Drive mudou","Arquivos recentes mudaram. Revise as provas e cases.");}else r.put("drive","HTTP "+x.optInt("http"));}catch(Exception e){put(r,"driveError",e.getMessage());}
    String hf=store.getSecret("huggingface");if(!hf.isEmpty())try{JSONObject x=get("https://huggingface.co/api/whoami-v2","Bearer "+hf);if(x.optBoolean("ok")){ok=true;JSONObject me=new JSONObject(x.optString("body","{}"));String u=me.optString("name","");r.put("huggingface",u.isEmpty()?"conectado":u);if(!u.isEmpty()){JSONObject m=get("https://huggingface.co/api/models?author="+URLEncoder.encode(u,"UTF-8")+"&sort=lastModified&direction=-1&limit=10","Bearer "+hf);if(m.optBoolean("ok")){String fp=sha(m.optString("body","")),old=s.getString("hfFp","");s.edit().putString("hfFp",fp).apply();if(!old.isEmpty()&&!old.equals(fp))note(c,1004,"AURION · Hugging Face mudou","Modelos/repos do perfil conectado mudaram.");}}}}catch(Exception e){put(r,"hfError",e.getMessage());}
    String pc=n.getString("pcStudio",""),tok=store.getSecret("dedicationPc");if(!pc.isEmpty())try{JSONObject x=get(pc.replaceAll("/+$","")+"/api/mobile/snapshot",tok.isEmpty()?"":"X-Aurion-Token "+tok);if(x.optBoolean("ok")){ok=true;String fp=sha(x.optString("body","")),old=s.getString("pcFp","");s.edit().putString("pcFp",fp).apply();r.put("pc","online");if(!old.isEmpty()&&!old.equals(fp))note(c,1005,"AURION · PC mudou","Estado/arquivos do PC mudaram. Veja Portfólio / Sync.");}else r.put("pc","HTTP "+x.optInt("http"));}catch(Exception e){put(r,"pcError",e.getMessage());}
    try{r.put("checkedAt",System.currentTimeMillis());store.add("sync_event","Auto Sync · "+(ok?"ciclo concluído":"ciclo parcial"),r.toString(),new JSONObject().put("source","WorkManager").toString());}catch(Exception ignored){}return ok?Result.success():Result.retry();}
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