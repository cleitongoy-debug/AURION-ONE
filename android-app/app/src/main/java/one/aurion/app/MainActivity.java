package one.aurion.app;
import android.app.Activity;
import android.os.Bundle;
import android.content.Intent;
import android.net.Uri;
import android.webkit.*;

public class MainActivity extends Activity {
 private WebView view;
 private ValueCallback<Uri[]> pendingFiles;
 private static final int PICK_FILES = 41;
 @Override public void onCreate(Bundle saved) {
  super.onCreate(saved);
  view = new WebView(this);
  setContentView(view);
  view.getSettings().setJavaScriptEnabled(true);
  view.getSettings().setDomStorageEnabled(true);
  view.setWebChromeClient(new WebChromeClient() {
   @Override public boolean onShowFileChooser(WebView w, ValueCallback<Uri[]> callback, FileChooserParams params) {
    if (pendingFiles != null) pendingFiles.onReceiveValue(null);
    pendingFiles = callback;
    try { startActivityForResult(params.createIntent(), PICK_FILES); return true; }
    catch (Exception error) { pendingFiles = null; return false; }
   }
  });
  view.setWebViewClient(new WebViewClient() {
   @Override public boolean shouldOverrideUrlLoading(WebView w, WebResourceRequest request) {
    Uri uri = request.getUrl();
    if ("https".equals(uri.getScheme())) {
     startActivity(new Intent(Intent.ACTION_VIEW, uri));
     return true;
    }
    return !"file".equals(uri.getScheme());
   }
  });
  view.loadUrl("file:///android_asset/index.html");
 }
 @Override protected void onActivityResult(int request, int result, Intent data) {
  super.onActivityResult(request, result, data);
  if (request == PICK_FILES && pendingFiles != null) {
   pendingFiles.onReceiveValue(WebChromeClient.FileChooserParams.parseResult(result, data));
   pendingFiles = null;
  }
 }
 @Override public void onBackPressed() { if (view.canGoBack()) view.goBack(); else super.onBackPressed(); }
}
