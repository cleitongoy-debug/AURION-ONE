package one.aurion.app;

import android.content.Context;
import android.content.SharedPreferences;
import android.net.Uri;
import android.os.SystemClock;
import androidx.documentfile.provider.DocumentFile;
import org.json.JSONArray;
import org.json.JSONObject;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.ArrayDeque;
import java.util.HashSet;
import java.util.Locale;
import java.util.Set;

/** Indice local incremental, SEM varredura de credenciais, fotos ou Drive sem autorizacao.
 * Scan de metadados de uma arvore SAF escolhida pelo operador; nao le bytes dos documentos.
 */
public final class AurionBootstrapIndex {
    private static final String PREF = "aurion_bootstrap_v1";
    private static final String WORKSPACE = "aurion_workspace";
    private static final int MAX_FILES = 120;
    private static final long MIN_INTERVAL_MS = 30L * 60L * 1000L;
    private AurionBootstrapIndex() { }

    private static SharedPreferences pref(Context c) {
        return c.getSharedPreferences(PREF, Context.MODE_PRIVATE);
    }
    private static boolean excluded(String name) {
        String n = name == null ? "" : name.toLowerCase(Locale.ROOT);
        return n.startsWith(".") || n.contains("local#server") || n.contains("secret")
                || n.contains("token") || n.contains("password") || n.contains("senha")
                || n.contains("credential") || n.contains("chave") || n.endsWith(".env")
                || n.endsWith(".exe") || n.endsWith(".bat") || n.endsWith(".apk")
                || n.endsWith(".p12") || n.endsWith(".key") || n.endsWith(".pem");
    }
    private static String digest(String v) {
        try {
            byte[] b=MessageDigest.getInstance("SHA-256").digest(v.getBytes(StandardCharsets.UTF_8));
            StringBuilder s=new StringBuilder();
            for(byte n:b)s.append(String.format(Locale.ROOT,"%02x",n&255));
            return s.toString();
        } catch(Exception e){return "INDETERMINADO";}
    }
    private static JSONObject result(String status, String reason, int processed, int changed, int skipped, int pending) {
        JSONObject j=new JSONObject();
        try{
            j.put("status", status).put("reason",reason)
                .put("processed",processed).put("changed",changed)
                .put("skipped",skipped).put("pendingEstimate",pending)
                .put("contentRead",false)
                .put("contentPrivacy","metadados SAF autorizados; sem extracao de arquivos ou chaves")
                .put("measuredAt",System.currentTimeMillis());
        }catch(Exception ignored){}
        return j;
    }
    public static void seedPublicReferences(Context c, AurionStore store) {
        SharedPreferences p=pref(c);
        if(p.getBoolean("seeded_public",false))return;
        // Somente links PUBLICOS do projeto; URLs privadas entram por consentimento explicito.
        String[][] refs={
            {"AURION ONE — GitHub","https://github.com/cleitongoy-debug/AURION-ONE"},
            {"AURION ONE — Protocolo P0","https://github.com/cleitongoy-debug/AURION-ONE/issues/39"},
            {"AURION ONE — Revisao da memoria / Band","https://github.com/cleitongoy-debug/AURION-ONE/pull/41"},
            {"AURION ONE — Linhagem C4D","https://github.com/cleitongoy-debug/AURION-ONE/blob/main/docs/AURION_CHINA_PANEL_COMPLETO_C4D_LINHAGEM_EVIDENCIAS_2026-10-09.md"}
        };
        try {
            for(String[] row:refs){
                JSONObject meta=new JSONObject().put("origin","GITHUB_PUBLICO")
                    .put("source","catalogo_versionado")
                    .put("evidence","REFERENCIA")
                    .put("visibility","public")
                    .put("verifiedRuntime",false);
                store.upsertReference(row[0],row[1],meta.toString());
            }
            p.edit().putBoolean("seeded_public",true).apply();
        }catch(Exception ignored){/* Retentar na proxima abertura */ }
    }
    public static JSONObject status(Context c) {
        SharedPreferences p=pref(c);
        JSONObject j=new JSONObject();
        try{
            j.put("publicCatalogReady",p.getBoolean("seeded_public",false))
                .put("workspaceChosen",!c.getSharedPreferences(WORKSPACE,Context.MODE_PRIVATE)
                    .getString("tree","").isEmpty())
                .put("lastWorkspaceScanAt",p.getLong("last_scan_at",0))
                .put("lastWorkspaceScan",p.getString("last_scan_result","{}"))
                .put("driveOAuthValidated",false)
                .put("pcHeartbeatValidated",false)
                .put("scanMeaning","INDICE_DE_METADADOS_NAO_ESTUDO_IA")
                .put("hasRemoteAgentConnection",false);
        }catch(Exception ignored){}
        return j;
    }
    /** Importacao LOCAL por escolha explicita: indexa somente referencias de links.
     * NUNCA faz download dos documentos nem importa chaves.
     */
    public static JSONObject importPrivateCatalog(Context c, AurionStore store, String raw){
        JSONObject result=new JSONObject(); int accepted=0, blocked=0;
        try{
            if(raw==null||raw.length()>70000)throw new IllegalArgumentException("manifesto_maior_que_70KB");
            JSONObject doc=new JSONObject(raw);
            if(!"aurion-reference-catalog-v1".equals(doc.optString("format")))
                throw new IllegalArgumentException("formato_de_catalogo_desconhecido");
            JSONArray list=doc.optJSONArray("sources");
            if(list==null||list.length()>80)throw new IllegalArgumentException("maximo_80_links_por_manifesto");
            for(int i=0;i<list.length();i++){
                JSONObject item=list.optJSONObject(i);
                if(item==null){blocked++;continue;}
                String title=item.optString("title","").trim(),url=item.optString("url","").trim();
                if(title.isEmpty()||title.length()>160||url.length()>500||!url.startsWith("https://")){
                    blocked++;continue;
                }
                Uri u=Uri.parse(url); String host=u.getHost();
                if(host==null||!(host.equals("drive.google.com")
                    ||host.equals("docs.google.com")||host.equals("github.com"))
                    ||u.getUserInfo()!=null||u.getQuery()!=null||u.getFragment()!=null
                    ||excluded(title)||excluded(url)) {blocked++;continue;}
                JSONObject meta=new JSONObject()
                    .put("origin","MANIFESTO_IMPORTADO_PELO_OPERADOR")
                    .put("url",url).put("evidence","REFERENCIA_NAO_LIDA")
                    .put("visibility","privada_ou_desconhecida")
                    .put("contentRead",false);
                store.upsertReference("CAT "+digest(url).substring(0,18)+" · "+title,
                    url,meta.toString());
                accepted++;
            }
            result.put("ok",true).put("indexedLinks",accepted).put("blocked",blocked)
                  .put("contentRead",false).put("connectedDrive",false);
        }catch(Exception e){
            try{result.put("ok",false).put("error",e.getMessage());}
            catch(Exception ignored){}
        }
        return result;
    }

    /** Idempotente por assinatura de metadados + caminho, com orcamento por rodada. */
    public static synchronized JSONObject scanWorkspace(Context c, AurionStore store, boolean force){
        SharedPreferences p=pref(c);long now=System.currentTimeMillis();
        if(!force && now-p.getLong("last_scan_at",0)<MIN_INTERVAL_MS)
            return result("INTERVALO","Proxima rodada sem revarrer antes do intervalo",0,0,0,0);
        String raw=c.getSharedPreferences(WORKSPACE,Context.MODE_PRIVATE).getString("tree","");
        if(raw.isEmpty())return result("BLOQUEADO","Operador ainda nao escolheu pasta pelo Android",0,0,0,0);
        boolean authorized=false;
        for(android.content.UriPermission grant:c.getContentResolver().getPersistedUriPermissions()) {
            if(grant.isReadPermission() && grant.getUri().toString().equals(raw)){authorized=true;break;}
        }
        if(!authorized)return result("BLOQUEADO","Permissao SAF nao persistida; reautorizar pasta",0,0,0,0);
        int processed=0,changed=0,skipped=0,remaining=0;
        try{
            DocumentFile root=DocumentFile.fromTreeUri(c,Uri.parse(raw));
            if(root==null || !root.canRead())return result("BLOQUEADO","Pasta nao permite leitura",0,0,0,0);
            ArrayDeque<DocumentFile> todo=new ArrayDeque<>();
            ArrayDeque<String> paths=new ArrayDeque<>();
            todo.add(root);paths.add("");
            Set<String> seen=new HashSet<>();
            int visitedFolders=0,enumerated=0;
            int startOffset=p.getInt("scan_cursor",0);
            while(!todo.isEmpty()&&processed<MAX_FILES&&visitedFolders<250) {
                DocumentFile dir=todo.removeFirst();String prefix=paths.removeFirst();
                visitedFolders++;
                DocumentFile[] children=dir.listFiles();
                java.util.Arrays.sort(children,(left,right) -> String.valueOf(left.getName()).compareToIgnoreCase(String.valueOf(right.getName())));
                for(DocumentFile file:children) {
                    if(processed>=MAX_FILES){remaining++;continue;}
                    String filename=file.getName();
                    if(filename==null||excluded(filename)){skipped++;continue;}
                    String part=prefix+"/"+filename;
                    if(file.isDirectory()){
                        if(part.split("/").length<=5){
                            todo.add(file);paths.add(part);
                        } else skipped++;
                        continue;
                    }
                    enumerated++;
                    if(enumerated<=startOffset)continue;
                    processed++;
                    String mime=file.getType()==null?"indeterminado":file.getType();
                    long bytes=file.length(), modified=file.lastModified();
                    String fp=digest(part+"\n"+bytes+"\n"+modified+"\n"+mime);
                    if(!seen.add(fp)){skipped++;continue;}
                    String id="item_"+digest(raw+"\n"+part).substring(0,20);
                    String former=p.getString(id,"");
                    if(fp.equals(former))continue;
                    JSONObject meta=new JSONObject().put("origin","SAF_PASTA_AUTORIZADA")
                        .put("path",part).put("mime",mime)
                        .put("bytes",bytes).put("modifiedAt",modified)
                        .put("fingerprintMetadataSha256",fp)
                        .put("contentRead",false).put("evidence","METADADOS_ANDROID");
                    // Nao guardar conteudo nem arquivo, apenas dados declarados pelo provider.
                    store.upsertReference("SAF "+id,part,meta.toString());
                    p.edit().putString(id,fp).apply();
                    changed++;
                }
            }
            boolean partial=remaining>0||!todo.isEmpty()||visitedFolders>=250;
            JSONObject result=result(partial?"AMOSTRA_LIMITADA":"CONCLUIDO",
                "Metadados; scan incremental por caminho, nao leitura do documento",processed,changed,skipped,remaining+todo.size());
            p.edit().putLong("last_scan_at",now)
                .putInt("scan_cursor",partial?startOffset+processed:0)
                .putString("last_scan_result",result.toString()).apply();
            if(changed>0)store.add("sync_event","Catalogo local: "+changed+" alteracoes",
                result.toString(),new JSONObject().put("source","SAF").put("scope","METADADOS").toString());
            return result;
        }catch(SecurityException e){return result("BLOQUEADO","Permissao SAF revogada",processed,changed,skipped,remaining);}
        catch(Exception e){return result("ERRO","Falha em leitura de metadados: "+e.getClass().getSimpleName(),processed,changed,skipped,remaining);}
    }
}
