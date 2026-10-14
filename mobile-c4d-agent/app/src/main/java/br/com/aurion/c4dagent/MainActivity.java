package br.com.aurion.c4dagent;

import android.app.Activity;
import android.os.Bundle;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.JavascriptInterface;
import android.content.SharedPreferences;
import org.json.JSONObject;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.ByteArrayOutputStream;
import java.net.HttpURLConnection;
import java.net.URI;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends Activity {
  private WebView web;
  private SharedPreferences preferences;
  private final ExecutorService pool=Executors.newSingleThreadExecutor();

  @Override public void onCreate(Bundle state) {
    super.onCreate(state);
    getWindow().setStatusBarColor(0xff080916);
    getWindow().setNavigationBarColor(0xff080916);
    preferences=getSharedPreferences("aurion_c4d_private",MODE_PRIVATE);
    web=new WebView(this);
    WebSettings settings=web.getSettings();
    settings.setJavaScriptEnabled(true);
    settings.setDomStorageEnabled(true);
    settings.setAllowFileAccessFromFileURLs(false);
    settings.setAllowUniversalAccessFromFileURLs(false);
    settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
    web.addJavascriptInterface(new Bridge(),"Aurion");
    web.setWebViewClient(new WebViewClient(){
      @Override public boolean shouldOverrideUrlLoading(WebView w,WebResourceRequest r){
        return !r.getUrl().toString().equals("file:///android_asset/index.html");
      }
    });
    setContentView(web);
    web.loadUrl("file:///android_asset/index.html");
  }

  private static boolean privateUrl(String raw) {
    try {
      URI u=new URI(raw);
      String scheme=u.getScheme();
      if(!"http".equals(scheme)&&!"https".equals(scheme))return false;
      if(u.getUserInfo()!=null||u.getFragment()!=null||u.getQuery()!=null)return false;
      if(u.getPath()!=null&&!u.getPath().isEmpty())return false;
      if(u.getPort()<1||u.getPort()>65535)return false;
      String host=u.getHost();
      if(host==null||!host.matches("[0-9.]+"))return false;
      String[] parts=host.split("\\.");
      if(parts.length!=4)return false;
      int[] a=new int[4];
      for(int i=0;i<4;i++){a[i]=Integer.parseInt(parts[i]);if(a[i]<0||a[i]>255)return false;}
      return a[0]==10 || a[0]==127 || a[0]==192&&a[1]==168 || a[0]==172&&a[1]>=16&&a[1]<=31;
    }catch(Exception e){return false;}
  }

  private void answer(String id,String body){
    runOnUiThread(()->{
      if(web!=null)web.evaluateJavascript("window.NativeReply("+JSONObject.quote(id)+","+JSONObject.quote(body)+");",null);
    });
  }

  private String err(String message){
    JSONObject obj=new JSONObject();
    try{obj.put("error",message);}catch(Exception ignored){}
    return obj.toString();
  }

  public final class Bridge {
    @JavascriptInterface public String get(String key) {
      if(!key.matches("(aurion|c4d)_(url|token)"))return "";
      return preferences.getString(key,"");
    }
    @JavascriptInterface public boolean put(String key,String value){
      if(!key.matches("(aurion|c4d)_(url|token)")||value==null||value.length()>400)return false;
      if(key.endsWith("_url")&&!privateUrl(value.trim()))return false;
      if(key.endsWith("_token")&&value.trim().length()<12)return false;
      preferences.edit().putString(key,value.trim()).apply();
      return true;
    }
    @JavascriptInterface public void request(String profile,String path,String method,String body,String id){
      if(!profile.matches("aurion|c4d")
        || !(("aurion".equals(profile)&&path.matches("/api/(prompt|status|inventory)"))
            ||("c4d".equals(profile)&&path.matches("/(health|api/(status|scripts))")))
        ||!method.matches("GET|POST")||id.length()>60
        ||body==null||body.length()>100000){
        answer(id,err("Operação bloqueada"));return;
      }
      String host=preferences.getString(profile+"_url","");
      String token=preferences.getString(profile+"_token","");
      if(!privateUrl(host)||token.isEmpty()){answer(id,err("Configure IP e chave do PC"));return;}
      pool.execute(()->{
        HttpURLConnection c=null;
        try{
          c=(HttpURLConnection)new URL(host+path).openConnection();
          c.setInstanceFollowRedirects(false);
          c.setConnectTimeout(7000);
          c.setReadTimeout(125000);
          c.setRequestMethod(method);
          c.setRequestProperty("Authorization","Bearer "+token);
          c.setRequestProperty("Accept","application/json");
          if("POST".equals(method)){
            c.setDoOutput(true);
            c.setRequestProperty("Content-Type","application/json; charset=utf-8");
            try(OutputStream out=c.getOutputStream()){out.write(body.getBytes(StandardCharsets.UTF_8));}
          }
          int status=c.getResponseCode();
          InputStream stream=status<400?c.getInputStream():c.getErrorStream();
          String payload="{}";
          if(stream!=null){
            try(InputStream in=stream;ByteArrayOutputStream o=new ByteArrayOutputStream()){
              byte[] bytes=new byte[4096];
              int n;
              while((n=in.read(bytes))!=-1){
                if(o.size()+n>250000)throw new java.io.IOException("Resposta acima de 250KB");
                o.write(bytes,0,n);
              }
              payload=o.toString("UTF-8");
            }
          }
          if(status>=400)answer(id,err("HTTP "+status+": "+payload));
          else answer(id,payload);
        }catch(Exception e){answer(id,err(e.getClass().getSimpleName()+": "+e.getMessage()));}
        finally{if(c!=null)c.disconnect();}
      });
    }
    @JavascriptInterface public String save(String name,String code){
      try{
        if(code==null||code.length()>100000)return "Script maior que 100KB";
        String title=name.replaceAll("[^A-Za-z0-9_-]","_");
        if(title.isEmpty())title="script";
        File dir=getExternalFilesDir("scripts");
        if(dir==null)return "Armazenamento externo não disponível";
        if(!dir.isDirectory()&&!dir.mkdirs())return "Pasta indisponível";
        File file=new File(dir,title+".py");
        try(FileOutputStream out=new FileOutputStream(file)){out.write(code.getBytes(StandardCharsets.UTF_8));}
        return file.getAbsolutePath();
      }catch(Exception e){return e.getMessage();}
    }
  }
  @Override public void onDestroy(){
    pool.shutdownNow();
    if(web!=null){web.removeJavascriptInterface("Aurion");web.destroy();}
    super.onDestroy();
  }
}
