package one.aurion.app;

import android.app.Activity;
import android.os.Bundle;
import android.content.Intent;
import android.net.Uri;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.ValueCallback;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

public class MainActivity extends Activity {
    private static final String PANEL_URL = "https://raw.githubusercontent.com/cleitongoy-debug/AURION-ONE/main/mobile/aurion-one-live.html";
    private static final int PICK_FILE = 41;
    private WebView view;
    private ValueCallback<Uri[]> selectedFiles;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        view = new WebView(this);
        setContentView(view);
        view.getSettings().setJavaScriptEnabled(true);
        view.getSettings().setDomStorageEnabled(true);
        view.getSettings().setAllowFileAccess(false);
        view.getSettings().setAllowContentAccess(true);
        view.setWebChromeClient(new WebChromeClient() {
            @Override public boolean onShowFileChooser(WebView webView, ValueCallback<Uri[]> callback, FileChooserParams params) {
                if (selectedFiles != null) selectedFiles.onReceiveValue(null);
                selectedFiles = callback;
                try { startActivityForResult(params.createIntent(), PICK_FILE); return true; }
                catch (Exception error) { selectedFiles = null; return false; }
            }
        });
        view.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView webView, WebResourceRequest request) {
                Uri uri = request.getUrl();
                if ("https".equals(uri.getScheme())) {
                    try { startActivity(new Intent(Intent.ACTION_VIEW, uri)); } catch (Exception ignored) { }
                    return true;
                }
                return !"file".equals(uri.getScheme());
            }
        });
        loadPanel();
    }

    private void loadPanel() {
        new Thread(() -> {
            byte[] html = null;
            HttpURLConnection connection = null;
            try {
                connection = (HttpURLConnection) new URL(PANEL_URL).openConnection();
                connection.setConnectTimeout(7000);
                connection.setReadTimeout(7000);
                connection.setUseCaches(false);
                connection.setRequestProperty("Accept", "text/html");
                if (connection.getResponseCode() == 200) {
                    try (InputStream input = connection.getInputStream(); ByteArrayOutputStream output = new ByteArrayOutputStream()) {
                        byte[] buffer = new byte[4096]; int count;
                        while ((count = input.read(buffer)) != -1) {
                            if (output.size() + count > 512000) throw new Exception("Panel exceeds size limit");
                            output.write(buffer, 0, count);
                        }
                        html = output.toByteArray();
                    }
                    String text = new String(html, StandardCharsets.UTF_8);
                    if (!text.contains("AURION_ONE_LIVE_V1")) html = null;
                    else try (FileOutputStream output = new FileOutputStream(new File(getFilesDir(), "panel-cache.html"))) { output.write(html); }
                }
            } catch (Exception ignored) { }
            finally { if (connection != null) connection.disconnect(); }
            if (html == null) {
                try (FileInputStream input = new FileInputStream(new File(getFilesDir(), "panel-cache.html")); ByteArrayOutputStream output = new ByteArrayOutputStream()) {
                    byte[] buffer = new byte[4096]; int count;
                    while ((count = input.read(buffer)) != -1) output.write(buffer, 0, count);
                    html = output.toByteArray();
                } catch (Exception ignored) { }
            }
            final byte[] result = html;
            runOnUiThread(() -> {
                if (isFinishing() || isDestroyed()) return;
                if (result != null) view.loadDataWithBaseURL("https://raw.githubusercontent.com/", new String(result, StandardCharsets.UTF_8), "text/html", "UTF-8", null);
                else view.loadUrl("file:///android_asset/index.html");
            });
        }).start();
    }

    @Override protected void onActivityResult(int request, int result, Intent data) {
        super.onActivityResult(request, result, data);
        if (request == PICK_FILE && selectedFiles != null) {
            selectedFiles.onReceiveValue(WebChromeClient.FileChooserParams.parseResult(result, data));
            selectedFiles = null;
        }
    }

    @Override public void onBackPressed() {
        if (view != null && view.canGoBack()) view.goBack(); else super.onBackPressed();
    }
}
