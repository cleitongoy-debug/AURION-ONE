package one.aurion.app;

import android.app.*;
import android.os.*;
import android.content.*;
import android.content.pm.PackageManager;
import android.graphics.*;
import android.graphics.drawable.*;
import android.net.*;
import android.provider.MediaStore;
import android.view.Window;
import android.webkit.*;
import android.widget.Toast;
import android.database.sqlite.*;
import android.database.Cursor;
import android.content.ContentValues;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.Base64;

import org.json.*;

import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import java.text.SimpleDateFormat;
import java.util.*;
import javax.crypto.*;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.SecretKey;

public class MainActivityV2 extends Activity {
    private static final int PICK_WORKSPACE=701, PICK_IMAGE=702, PICK_RAW=703;
    private WebView web;
    private String convertFormat="JPEG";
    private int convertQuality=92;
    private float brightness=0f, contrast=1f, saturation=1f, temperature=0f, tint=0f;
    private Uri workspaceUri;
    private final Bridge bridge=new Bridge();
    private MemoryDb memory;
    private SecureStore secrets;

    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setStatusBarColor(Color.rgb(5,11,18));
        getWindow().setNavigationBarColor(Color.rgb(5,11,18));
        memory=new MemoryDb(this);
        secrets=new SecureStore(this);
        workspaceUri=loadWorkspace();
        web=new WebView(this);
        setContentView(web);
        WebSettings s=web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setDatabaseEnabled(true);
        s.setAllowFileAccess(false);
        s.setAllowContentAccess(true);
        s.setMixedContentMode(WebSettings.MIXED_CONTENT_COMPATIBILITY_MODE);
        s.setUserAgentString(s.getUserAgentString()+" AURION-ONE-V2/6.0");
        web.addJavascriptInterface(bridge,"AurionV2");
        web.setWebChromeClient(new WebChromeClient());
        web.setWebViewClient(new WebViewClient(){
            @Override public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest r){
                Uri u=r.getUrl();
                String scheme=u.getScheme()==null?"":u.getScheme();
                if("file".equals(scheme)) return false;
                try{startActivity(new Intent(Intent.ACTION_VIEW,u));}catch(Exception ignored){}
                return true;
            }
        });
        web.loadUrl("file:///android_asset/v2/index.html");
    }

    private void toast(String s){runOnUiThread(()->Toast.makeText(this,s,Toast.LENGTH_LONG).show());}
    private void emit(String fn, JSONObject payload){
        String js="window."+fn+"("+JSONObject.quote(payload.toString())+")";
        runOnUiThread(()->web.evaluateJavascript(js,null));
    }
    private Uri loadWorkspace(){
        String s=getSharedPreferences("aurion",MODE_PRIVATE).getString("workspace","");
        try{return s.isEmpty()?null:Uri.parse(s);}catch(Exception e){return null;}
    }
    private void saveWorkspace(Uri u){
        workspaceUri=u;
        getSharedPreferences("aurion",MODE_PRIVATE).edit().putString("workspace",u==null?"":u.toString()).apply();
    }
    private String now(){return new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ssZ",Locale.US).format(new Date());}

    private JSONObject diagnostics(){
        JSONObject j=new JSONObject();
        try{
            j.put("app","AURION ONE V2 SUPER STUDIO");
            j.put("version","6.0.0");
            j.put("android",Build.VERSION.RELEASE);
            j.put("api",Build.VERSION.SDK_INT);
            j.put("manufacturer",Build.MANUFACTURER);
            j.put("model",Build.MODEL);
            j.put("workspace",workspaceUri==null?JSONObject.NULL:workspaceUri.toString());
            j.put("memoryRecords",memory.count());
            JSONObject acc=new JSONObject();
            acc.put("github",secrets.has("github_token"));
            acc.put("huggingface",secrets.has("hf_token"));
            acc.put("pc",secrets.has("pc_token"));
            j.put("accounts",acc);
            ConnectivityManager cm=(ConnectivityManager)getSystemService(CONNECTIVITY_SERVICE);
            Network n=cm==null?null:cm.getActiveNetwork();
            NetworkCapabilities nc=cm==null||n==null?null:cm.getNetworkCapabilities(n);
            j.put("network",nc==null?"offline":nc.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)?"wifi":nc.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR)?"mobile":nc.hasTransport(NetworkCapabilities.TRANSPORT_VPN)?"vpn":"other");
        }catch(Exception ignored){}
        return j;
    }

    private Bitmap process(Bitmap src){
        Bitmap out=Bitmap.createBitmap(src.getWidth(),src.getHeight(),Bitmap.Config.ARGB_8888);
        Canvas c=new Canvas(out);
        ColorMatrix m=new ColorMatrix();
        ColorMatrix sat=new ColorMatrix(); sat.setSaturation(Math.max(0f,saturation)); m.postConcat(sat);
        float con=Math.max(0.1f,contrast), trans=(1f-con)*128f + brightness*255f;
        ColorMatrix cmat=new ColorMatrix(new float[]{
            con*(1f+0.22f*temperature),0,0,0,trans,
            0,con*(1f+0.12f*tint),0,0,trans,
            0,0,con*(1f-0.22f*temperature),0,trans,
            0,0,0,1,0
        });
        m.postConcat(cmat);
        Paint p=new Paint(Paint.ANTI_ALIAS_FLAG); p.setColorFilter(new android.graphics.ColorMatrixColorFilter(m));
        c.drawBitmap(src,0,0,p);
        return out;
    }

    private void convertPickedImage(Uri uri){
        try(InputStream in=getContentResolver().openInputStream(uri)){
            Bitmap src=BitmapFactory.decodeStream(in);
            if(src==null) throw new IOException("Imagem não decodificada");
            Bitmap outBmp=process(src);
            String fmt=convertFormat.toUpperCase(Locale.ROOT);
            String ext=fmt.equals("PNG")?"png":fmt.equals("WEBP")?"webp":"jpg";
            String mime=fmt.equals("PNG")?"image/png":fmt.equals("WEBP")?"image/webp":"image/jpeg";
            ContentValues cv=new ContentValues();
            cv.put(MediaStore.Images.Media.DISPLAY_NAME,"AURION_V2_"+System.currentTimeMillis()+"."+ext);
            cv.put(MediaStore.Images.Media.MIME_TYPE,mime);
            if(Build.VERSION.SDK_INT>=29)cv.put(MediaStore.Images.Media.RELATIVE_PATH,"Pictures/AURION");
            Uri dst=getContentResolver().insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI,cv);
            if(dst==null) throw new IOException("Sem destino");
            try(OutputStream os=getContentResolver().openOutputStream(dst)){
                Bitmap.CompressFormat cf=fmt.equals("PNG")?Bitmap.CompressFormat.PNG:
                    (Build.VERSION.SDK_INT>=30&&fmt.equals("WEBP")?Bitmap.CompressFormat.WEBP_LOSSY:Bitmap.CompressFormat.JPEG);
                outBmp.compress(cf,convertQuality,os);
            }
            JSONObject j=new JSONObject(); j.put("ok",true); j.put("uri",dst.toString()); j.put("format",fmt); emit("aurionConvertResult",j);
        }catch(Exception e){
            try{JSONObject j=new JSONObject(); j.put("ok",false); j.put("error",e.getClass().getSimpleName()+": "+e.getMessage()); emit("aurionConvertResult",j);}catch(Exception ignored){}
        }
    }

    private void backupMemoryToWorkspace(){
        if(workspaceUri==null){toast("Escolha a pasta de trabalho primeiro.");return;}
        try{
            androidx.documentfile.provider.DocumentFile root=androidx.documentfile.provider.DocumentFile.fromTreeUri(this,workspaceUri);
            if(root==null)throw new IOException("Pasta inválida");
            androidx.documentfile.provider.DocumentFile f=root.createFile("application/json","aurion_memory_"+System.currentTimeMillis()+".json");
            if(f==null)throw new IOException("Não foi possível criar backup");
            try(OutputStream os=getContentResolver().openOutputStream(f.getUri())){
                os.write(memory.exportJson().toString(2).getBytes(StandardCharsets.UTF_8));
            }
            toast("Backup salvo na pasta escolhida.");
        }catch(Exception e){toast("Falha no backup: "+e.getMessage());}
    }

    private void testPc(String base,String token){
        new Thread(()->{
            JSONObject result=new JSONObject(); JSONArray probes=new JSONArray();
            try{
                String b=base==null?"":base.trim();
                if(!b.startsWith("http://")&&!b.startsWith("https://"))throw new IllegalArgumentException("URL inválida");
                String[] paths={"/api/status","/api/one/boot","/health"};
                for(String path:paths){
                    JSONObject p=new JSONObject(); HttpURLConnection c=null;
                    try{
                        URL u=new URL(b.replaceAll("/+$","")+path); c=(HttpURLConnection)u.openConnection();
                        c.setConnectTimeout(3000); c.setReadTimeout(5000); c.setRequestProperty("Accept","application/json");
                        if(token!=null&&!token.trim().isEmpty())c.setRequestProperty("Authorization","Bearer "+token.trim());
                        int code=c.getResponseCode(); p.put("path",path); p.put("http",code);
                    }catch(Exception e){p.put("path",path);p.put("error",e.getClass().getSimpleName());}
                    finally{if(c!=null)c.disconnect();}
                    probes.put(p);
                }
                result.put("ok",true);result.put("probes",probes);
            }catch(Exception e){try{result.put("ok",false);result.put("error",e.getMessage());}catch(Exception ignored){}}
            emit("aurionPcResult",result);
        }).start();
    }

    public class Bridge{
        @JavascriptInterface public String diagnostics(){return diagnostics().toString();}
        @JavascriptInterface public void chooseWorkspace(){
            Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);
            i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_WRITE_URI_PERMISSION|Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
            startActivityForResult(i,PICK_WORKSPACE);
        }
        @JavascriptInterface public String workspace(){return workspaceUri==null?"":workspaceUri.toString();}
        @JavascriptInterface public long saveMemory(String title,String body,String tags){return memory.add(title,body,tags);}
        @JavascriptInterface public String searchMemory(String q){return memory.search(q,200).toString();}
        @JavascriptInterface public void backupMemory(){backupMemoryToWorkspace();}
        @JavascriptInterface public void saveSecret(String name,String value){
            if(!Arrays.asList("github_token","hf_token","pc_token").contains(name))return;
            try{secrets.put(name,value==null?"":value);toast("Credencial salva no cofre local.");}catch(Exception e){toast("Falha no cofre: "+e.getMessage());}
        }
        @JavascriptInterface public boolean hasSecret(String name){return secrets.has(name);}
        @JavascriptInterface public void convertImage(String format,int quality,float bright,float con,float sat,float temp,float ti){
            convertFormat=format;convertQuality=Math.max(1,Math.min(100,quality));brightness=bright;contrast=con;saturation=sat;temperature=temp;tint=ti;
            Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT).setType("image/*").addCategory(Intent.CATEGORY_OPENABLE);
            startActivityForResult(i,PICK_IMAGE);
        }
        @JavascriptInterface public void pickRaw(){
            Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT).setType("*/*").addCategory(Intent.CATEGORY_OPENABLE);
            startActivityForResult(i,PICK_RAW);
        }
        @JavascriptInterface public void testPc(String base,String token){MainActivityV2.this.testPc(base,token);}
    }

    @Override protected void onActivityResult(int req,int res,Intent data){
        super.onActivityResult(req,res,data);
        if(res!=RESULT_OK||data==null)return;
        Uri u=data.getData(); if(u==null)return;
        if(req==PICK_WORKSPACE){
            try{getContentResolver().takePersistableUriPermission(u,Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_WRITE_URI_PERMISSION);}catch(Exception ignored){}
            saveWorkspace(u); toast("Pasta AURION conectada.");
            try{JSONObject j=new JSONObject();j.put("ok",true);j.put("workspace",u.toString());emit("aurionWorkspaceResult",j);}catch(Exception ignored){}
        } else if(req==PICK_IMAGE){
            convertPickedImage(u);
        } else if(req==PICK_RAW){
            try{
                JSONObject j=new JSONObject();j.put("ok",true);j.put("uri",u.toString());j.put("message","Arquivo RAW selecionado. Desenvolvimento CR3 completo usa o módulo T8i do PC quando conectado.");emit("aurionRawResult",j);
            }catch(Exception ignored){}
        }
    }

    private static class MemoryDb extends SQLiteOpenHelper{
        MemoryDb(Context c){super(c,"aurion_memory_v2.db",null,1);}
        @Override public void onCreate(SQLiteDatabase db){db.execSQL("CREATE TABLE memory(id INTEGER PRIMARY KEY AUTOINCREMENT,ts TEXT,title TEXT,body TEXT,tags TEXT)");}
        @Override public void onUpgrade(SQLiteDatabase db,int o,int n){}
        long add(String title,String body,String tags){ContentValues v=new ContentValues();v.put("ts",new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ssZ",Locale.US).format(new Date()));v.put("title",title);v.put("body",body);v.put("tags",tags);return getWritableDatabase().insert("memory",null,v);}
        int count(){Cursor c=getReadableDatabase().rawQuery("SELECT COUNT(*) FROM memory",null);try{return c.moveToFirst()?c.getInt(0):0;}finally{c.close();}}
        JSONArray search(String q,int limit){
            JSONArray a=new JSONArray();String like="%"+(q==null?"":q)+"%";
            Cursor c=getReadableDatabase().rawQuery("SELECT id,ts,title,body,tags FROM memory WHERE title LIKE ? OR body LIKE ? OR tags LIKE ? ORDER BY id DESC LIMIT "+Math.max(1,Math.min(500,limit)),new String[]{like,like,like});
            try{while(c.moveToNext()){JSONObject j=new JSONObject();try{j.put("id",c.getLong(0));j.put("ts",c.getString(1));j.put("title",c.getString(2));j.put("body",c.getString(3));j.put("tags",c.getString(4));a.put(j);}catch(Exception ignored){}}}finally{c.close();}return a;
        }
        JSONArray exportJson(){return search("",500);}
    }

    private static class SecureStore{
        private final Context ctx; private static final String ALIAS="aurion_v2_key";
        SecureStore(Context c){ctx=c;}
        SecretKey key() throws Exception{
            KeyStore ks=KeyStore.getInstance("AndroidKeyStore");ks.load(null);
            if(ks.containsAlias(ALIAS))return ((KeyStore.SecretKeyEntry)ks.getEntry(ALIAS,null)).getSecretKey();
            KeyGenerator g=KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES,"AndroidKeyStore");
            g.init(new KeyGenParameterSpec.Builder(ALIAS,KeyProperties.PURPOSE_ENCRYPT|KeyProperties.PURPOSE_DECRYPT).setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).build());
            return g.generateKey();
        }
        void put(String name,String value) throws Exception{
            Cipher c=Cipher.getInstance("AES/GCM/NoPadding");c.init(Cipher.ENCRYPT_MODE,key());
            byte[] enc=c.doFinal(value.getBytes(StandardCharsets.UTF_8));
            String packed=Base64.encodeToString(c.getIV(),Base64.NO_WRAP)+":"+Base64.encodeToString(enc,Base64.NO_WRAP);
            ctx.getSharedPreferences("aurion_secure",MODE_PRIVATE).edit().putString(name,packed).apply();
        }
        boolean has(String name){return !ctx.getSharedPreferences("aurion_secure",MODE_PRIVATE).getString(name,"").isEmpty();}
    }
}
