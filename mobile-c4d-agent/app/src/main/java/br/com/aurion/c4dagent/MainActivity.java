package br.com.aurion.c4dagent;
import android.app.Activity;
import android.os.Bundle;
import android.webkit.*;
import android.content.*;
import org.json.*;
import java.net.*;
import java.io.*;
import java.nio.charset.StandardCharsets;

public class MainActivity extends Activity {
  WebView web;
  @Override public void onCreate(Bundle b) {
    super.onCreate(b);
    getWindow().setStatusBarColor(0xff080916);
    getWindow().setNavigationBarColor(0xff080916);
    web=new WebView(this);
    WebSettings s=web.getSettings();
    s.setJavaScriptEnabled(true); s.setDomStorageEnabled(true);
    s.setAllowFileAccessFromFileURLs(false);
    s.setAllowUniversalAccessFromFileURLs(false);
    web.addJavascriptInterface(new Bridge(),"Aurion");
    web.setWebViewClient(new WebViewClient(){
      @Override public boolean shouldOverrideUrlLoading(WebView w,WebResourceRequest r){
        return !r.getUrl().toString().equals("file:///android_asset/index.html");
      }
    });
    setContentView(web); web.loadUrl("file:///android_asset/index.html");
  }
  public class Bridge {
    @JavascriptInterface public String get(String k){
      return getPreferences(0).getString(k,"");
    }
    @JavascriptInterface public boolean put(String k,String v){
      if(!k.matches("(aurion|c4d)_(url|token)"))return false;
      if(k.endsWith("_url")&&!v.matches("https?://(10|127|192|172)\\.[0-9.]+:[0-9]{2,5}"))return false;
      getPreferences(0).edit().putString(k,v.trim()).apply();return true;
    }
    @JavascriptInterface public String call(String profile,String path,String method,String body){
      if(!profile.matches("aurion|c4d")||!path.matches("/(health|api/(prompt|status|inventory|scripts))")||!method.matches("GET|POST")) return "{\\"error\\":\\"Rota bloqueada\\"}";
      String host=get(profile+"_url");
      String token=get(profile+"_token");
      if(host.isEmpty()||token.isEmpty())return "{\\"error\\":\\"Configure PC e chave\\"}";
      HttpURLConnection c=null;
      try{
        c=(HttpURLConnection)new URL(host+path).openConnection();
        c.setConnectTimeout(6000);c.setReadTimeout(120000);c.setRequestMethod(method);
        c.setInstanceFollowRedirects(false);c.setRequestProperty("Authorization","Bearer "+token);
        if(method.equals("POST")){
          c.setDoOutput(true);c.setRequestProperty("Content-Type","application/json");
          try(OutputStream o=c.getOutputStream()){o.write(body.getBytes(StandardCharsets.UTF_8));}
        }
        InputStream in=c.getResponseCode()<400?c.getInputStream():c.getErrorStream();
        if(in==null)return "{}";
        try(InputStream i=in;ByteArrayOutputStream a=new ByteArrayOutputStream()){
          byte[] buf=new byte[4096];int n;
          while((n=i.read(buf))>=0&&a.size()<200000)a.write(buf,0,n);
          return a.toString("UTF-8");
        }
      }catch(Exception e){return "{\\"error\\":"+JSONObject.quote(e.getClass().getSimpleName()+": "+e.getMessage())+"}";}
      finally{if(c!=null)c.disconnect();}
    }
    @JavascriptInterface public String save(String name,String source){
      try{
        if(source.length()>100000)return "Limite de 100KB";
        String clean=name.replaceAll("[^a-zA-Z0-9_-]","_");
        if(clean.isEmpty())clean="script";
        File d=getExternalFilesDir("scripts");if(d==null)return "Sem armazenamento";
        d.mkdirs(); File f=new File(d,clean+".py");
        try(FileOutputStream o=new FileOutputStream(f)){o.write(source.getBytes(StandardCharsets.UTF_8));}
        return f.getAbsolutePath();
      }catch(Exception e){return e.getMessage();}
    }
  }
}