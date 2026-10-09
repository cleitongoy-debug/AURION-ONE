package one.aurion.app;

import android.content.Context;
import android.content.SharedPreferences;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.ByteArrayOutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.Locale;
import java.util.Set;

/** PC ↔ POCO por loopback via ADB reverse. Nao e sync de Google/IA/contas. */
public final class AurionPcMemorySync {
    private static final String PREF = "aurion_pc_sync_v1";
    private static final int LIMIT = 3_000_000;
    private static final int MAX_RECORDS = 4000;
    private static final Set<String> TYPES = new HashSet<>();
    static {
        for (String v:new String[]{"memory","reference","conversation","project",
              "preset","evidence","experiment"}) TYPES.add(v);
    }
    private AurionPcMemorySync() { }

    private static SharedPreferences state(Context c){
        return c.getSharedPreferences(PREF,Context.MODE_PRIVATE);
    }
    public static JSONObject status(Context c){
        JSONObject x=new JSONObject();
        try{
            SharedPreferences p=state(c);
            x.put("enabled",p.getBoolean("enabled",false))
             .put("lastSuccessAt",p.getLong("lastSuccessAt",0))
             .put("lastAttemptAt",p.getLong("lastAttemptAt",0))
             .put("lastReport",new JSONObject(p.getString("lastReport","{}")))
             .put("transport","USB_ADB_REVERSE_LOOPBACK_5060_5069")
             .put("configuredEndpoint",configuredEndpoint(c))
             .put("pcReachableNow","NAO_TESTADO")
             .put("googleDriveSynced",false);
        }catch(Exception ignored){}
        return x;
    }
    private static String configuredEndpoint(Context c){
        String url=c.getSharedPreferences("aurion_nodes",Context.MODE_PRIVATE)
             .getString("pcStudio","").replaceAll("/+$","");
        return url.matches("http://(127\\.0\\.0\\.1|localhost):506[0-9]")
             ? url : "";
    }
    public static void setEnabled(Context c,boolean enabled){
        state(c).edit().putBoolean("enabled",enabled).apply();
    }
    private static boolean sensitive(String text){
        if(text==null)return false;
        String t=text.toLowerCase(Locale.ROOT);
        return t.contains("local#server")||t.contains(".webui_secret_key")||
           t.contains("sk-proj-")||t.contains("ghp_")||t.contains("gsk_")||
           t.contains("nvapi-")||t.matches("(?s).*hf_[a-z0-9]{20,}.*")||
           t.matches("(?s).*(api[_ -]?key|access[_ -]?token|password|senha|secret)\\s*[:=].*");
    }

    /* Fail closed on nested metadata keys; a quoted JSON "api_key" must not
       pass merely because the raw-string filter expected ":" immediately. */
    private static boolean sensitiveMeta(String raw){
        if(sensitive(raw))return true;
        try{
            Object root=new org.json.JSONTokener(raw).nextValue();
            return sensitiveNode(root,0);
        }catch(Exception ignored){return false;}
    }
    private static boolean sensitiveNode(Object node,int depth)throws org.json.JSONException {
        if(depth>20)return true;
        if(node instanceof JSONObject){
            JSONObject obj=(JSONObject)node;
            java.util.Iterator<String> it=obj.keys();
            while(it.hasNext()){
                String key=it.next();
                String flat=key.toLowerCase(Locale.ROOT).replaceAll("[ _-]","");
                if(flat.equals("apikey")||flat.equals("token")||flat.equals("accesstoken")
                   ||flat.equals("refreshtoken")||flat.equals("password")||flat.equals("passwd")
                   ||flat.equals("senha")||flat.equals("secret")||flat.equals("clientsecret")
                   ||flat.equals("privatekey")||flat.equals("authorization")||flat.equals("cookie")
                   ||flat.equals("credential")||flat.equals("credentials"))return true;
                if(sensitiveNode(obj.opt(key),depth+1))return true;
            }
        }else if(node instanceof JSONArray){
            JSONArray list=(JSONArray)node;
            for(int i=0;i<list.length();i++)if(sensitiveNode(list.opt(i),depth+1))return true;
        }else if(node instanceof String){
            return sensitive((String)node);
        }
        return false;
    }

    private static JSONObject failure(String error){
        JSONObject x=new JSONObject();
        try{x.put("ok",false).put("error",error);}catch(Exception ignored){}
        return x;
    }
    private static JSONObject http(String url,String token,String method,String body)throws Exception{
        HttpURLConnection con=null;
        try{
            con=(HttpURLConnection)new URL(url).openConnection();
            con.setRequestMethod(method);
            con.setConnectTimeout(5000);con.setReadTimeout(20000);
            con.setRequestProperty("X-Aurion-Token",token);
            con.setRequestProperty("Accept","application/json");
            con.setUseCaches(false);
            if(body!=null){
                byte[] data=body.getBytes(StandardCharsets.UTF_8);
                if(data.length>LIMIT)throw new IllegalStateException("backup_excede_3MB_sem_truncamento");
                con.setDoOutput(true);
                con.setRequestProperty("Content-Type","application/json; charset=utf-8");
                con.setFixedLengthStreamingMode(data.length);
                try(OutputStream out=con.getOutputStream()){out.write(data);}
            }
            int status=con.getResponseCode();
            InputStream in=status>=400?con.getErrorStream():con.getInputStream();
            ByteArrayOutputStream response=new ByteArrayOutputStream();
            if(in!=null)try(InputStream stream=in){
                byte[] buf=new byte[8192];int n;
                while((n=stream.read(buf))>=0){
                    if(response.size()+n>LIMIT)throw new IllegalStateException("resposta_PC_excede_3MB");
                    response.write(buf,0,n);
                }
            }
            JSONObject x=new JSONObject(response.toString("UTF-8"));
            if(status<200||status>=300||!x.optBoolean("ok"))
                throw new IllegalStateException("PC_HTTP_"+status+"_"+x.optString("error",""));
            return x;
        }finally{if(con!=null)con.disconnect();}
    }

    /** Canonical binary record digest: same 4 UTF-8 length-prefixed fields as the PC. */
    private static String shaHex(byte[] input)throws Exception{
        java.security.MessageDigest sha=java.security.MessageDigest.getInstance("SHA-256");
        byte[] digest=sha.digest(input);
        StringBuilder hex=new StringBuilder(digest.length*2);
        for(byte b:digest)hex.append(String.format(Locale.ROOT,"%02x",b&255));
        return hex.toString();
    }
    private static String recordFingerprint(JSONObject item)throws Exception{
        java.security.MessageDigest sha=java.security.MessageDigest.getInstance("SHA-256");
        for(String field:new String[]{"type","title","body","meta"}){
            if(!item.has(field)||item.isNull(field))throw new IllegalArgumentException("campo_ausente");
            Object raw=item.get(field);
            if(!(raw instanceof String))throw new IllegalArgumentException("campo_nao_textual");
            byte[] bytes=((String)raw).getBytes(StandardCharsets.UTF_8);
            int n=bytes.length;
            sha.update(new byte[]{(byte)(n>>>24),(byte)(n>>>16),(byte)(n>>>8),(byte)n});
            sha.update(bytes);
        }
        byte[] digest=sha.digest();
        StringBuilder out=new StringBuilder(digest.length*2);
        for(byte b:digest)out.append(String.format(Locale.ROOT,"%02x",b&255));
        return out.toString();
    }
    private static String recordSetDigest(JSONArray rows)throws Exception{
        java.util.ArrayList<String> all=new java.util.ArrayList<>();
        for(int i=0;i<rows.length();i++)all.add(recordFingerprint(rows.getJSONObject(i)));
        java.util.Collections.sort(all);
        StringBuilder joined=new StringBuilder();
        for(String fp:all){
            if(joined.length()>0)joined.append('\n');
            joined.append(fp);
        }
        return shaHex(joined.toString().getBytes(StandardCharsets.UTF_8));
    }
    public static synchronized JSONObject run(Context c,AurionStore store,boolean manual){
        long started=System.currentTimeMillis();
        SharedPreferences p=state(c);
        if(!manual&&!p.getBoolean("enabled",false))return failure("auto_sync_desativado");
        p.edit().putLong("lastAttemptAt",started).apply();
        try{
            String root=c.getSharedPreferences("aurion_nodes",Context.MODE_PRIVATE)
                  .getString("pcStudio","").replaceAll("/+$","");
            String token=store.getSecret("dedicationPc");
            // Nunca enviar memoria para hosts da LAN, internet, ou portas desconhecidas.
            if(!root.matches("http://(127\\.0\\.0\\.1|localhost):506[0-9]"))
                throw new IllegalStateException("use_HTTP_localhost_5060_via_cabo_ADB");
            if(token.isEmpty())throw new IllegalStateException("token_local_PC_nao_configurado");
            JSONObject upstream=store.exportAll();
            if(!upstream.optBoolean("ok"))throw new IllegalStateException("backup_SQLite_falhou");
            JSONArray records=upstream.getJSONArray("records");
            JSONArray safe=new JSONArray();
            int excluded=0;
            for(int i=0;i<records.length();i++){
                JSONObject row=records.getJSONObject(i);
                String type=row.optString("type",""), title=row.optString("title","");
                String body=row.optString("body",""), meta=row.optString("meta","");
                if(!TYPES.contains(type)||title.isEmpty()||title.length()>200||
                    body.length()>15000||meta.length()>5000||
                    sensitive(title)||sensitive(body)||sensitiveMeta(meta)){
                    excluded++;continue;
                }
                safe.put(row);
                if(safe.length()>MAX_RECORDS)throw new IllegalStateException("mais_de_4000_registros_seguro_pausado");
            }
            JSONObject payload=new JSONObject();
            payload.put("format","aurion-memory-v4").put("profile","anark")
                   .put("recordCount",safe.length()).put("records",safe);
            String endpoint=root+"/api/mobile/memory-sync";
            JSONObject response=http(endpoint,token,"POST",payload.toString());
            if(!"aurion-pc-poco-v1".equals(response.optString("format"))||
                response.optInt("received",-1)!=safe.length())
                throw new IllegalStateException("recibo_PC_contagem_divergente");
            JSONArray remote=response.optJSONArray("records");
            if(remote==null||remote.length()!=response.optInt("recordCount",-1))
                throw new IllegalStateException("registros_PC_incompletos");
            String digest=recordSetDigest(remote);
            if(!digest.equals(response.optString("recordsFingerprintSha256","")))
                throw new IllegalStateException("PC_conteudo_divergente_nao_importado");
            JSONObject backup=new JSONObject();
            backup.put("format","aurion-memory-v4").put("profile","anark").put("records",remote);
            JSONObject imported=store.importAll(backup.toString());
            if(!imported.optBoolean("ok") ||
                imported.optInt("imported")+imported.optInt("skippedDuplicates")!=remote.length())
                throw new IllegalStateException("importacao_local_nao_confirmada_"+imported.optString("error",""));
            JSONObject readback=http(endpoint,token,"GET",null);
            if(readback.optInt("phoneMirroredRecords",-1)!=remote.length())
                throw new IllegalStateException("PC_readback_divergente");
            if(!digest.equals(readback.optString("recordsFingerprintSha256","")))
                throw new IllegalStateException("PC_readback_hash_divergente");
            JSONObject report=new JSONObject();
            report.put("ok",true).put("status","RECIBOS_PC_E_POCO_CONFIRMADOS")
                  .put("sent",safe.length()).put("excludedLocal",excluded)
                  .put("pcNew",response.optInt("pcNew"))
                  .put("received",remote.length())
                  .put("imported",imported.optInt("imported"))
                  .put("duplicates",imported.optInt("skippedDuplicates"))
                  .put("pcReadbackCount",readback.optInt("phoneMirroredRecords"))
                  .put("contentDigestVerified",true)
                  .put("completedAt",System.currentTimeMillis())
                  .put("pcReceipt",response.optString("pcReceipt"))
                  .put("receiptType","CONTAGENS_E_READBACK_LOCAL_NAO_TESTE_FISICO_DESTA_SESSAO");
            p.edit().putString("lastReport",report.toString())
              .putLong("lastSuccessAt",System.currentTimeMillis())
              .putBoolean("enabled",true).apply();
            return report;
        }catch(Exception e){
            JSONObject bad=failure(e.getClass().getSimpleName()+": "+e.getMessage());
            p.edit().putString("lastReport",bad.toString()).apply();
            return bad;
        }
    }
}
