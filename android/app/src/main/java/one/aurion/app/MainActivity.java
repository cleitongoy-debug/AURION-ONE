package one.aurion.app;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.provider.Settings;
import android.view.Window;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;
import java.net.HttpURLConnection;
import java.net.InetAddress;
import java.net.URL;

public class MainActivity extends Activity {
    private static final int PICK_FILE = 410;
    private WebView web;
    private ValueCallback<Uri[]> selectedFiles;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setStatusBarColor(Color.rgb(5, 8, 13));
        getWindow().setNavigationBarColor(Color.rgb(5, 8, 13));

        web = new WebView(this);
        web.setBackgroundColor(Color.rgb(5, 8, 13));
        setContentView(web);

        WebSettings settings = web.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(true);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        settings.setUserAgentString(settings.getUserAgentString() + " AURION-ONE-Mobile/1.0");
        web.addJavascriptInterface(new Bridge(), "AurionAndroid");
        web.setWebChromeClient(new WebChromeClient() {
            @Override public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback, FileChooserParams params) {
                if (selectedFiles != null) selectedFiles.onReceiveValue(null);
                selectedFiles = callback;
                try { startActivityForResult(params.createIntent(), PICK_FILE); return true; }
                catch (Exception error) { selectedFiles = null; callback.onReceiveValue(null); return true; }
            }
        });
        web.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                String scheme = uri.getScheme() == null ? "" : uri.getScheme();
                if ((scheme.equals("http") || scheme.equals("https")) && isPanelHost(uri.getHost())) return false;
                if (scheme.equals("file")) return false;
                try { startActivity(new Intent(Intent.ACTION_VIEW, uri)); }
                catch (Exception ignored) { Toast.makeText(MainActivity.this, "Não foi possível abrir o endereço", Toast.LENGTH_LONG).show(); }
                return true;
            }
            @Override public void onReceivedError(WebView view, android.webkit.WebResourceRequest req, android.webkit.WebResourceError err) {
                if (req.isForMainFrame()) Toast.makeText(MainActivity.this, "Painel do PC indisponível. Voltando ao painel móvel.", Toast.LENGTH_LONG).show();
            }
        });
        web.loadUrl("file:///android_asset/index.html");
    }

    private boolean isPanelHost(String host) {
        if (host == null) return false;
        String h = host.toLowerCase();
        return h.equals("localhost") || h.equals("127.0.0.1") || h.endsWith(".ts.net") || h.endsWith(".local") ||
            h.startsWith("10.") || h.startsWith("192.168.") || h.matches("172\\.(1[6-9]|2[0-9]|3[01])\\..*");
    }

    public final class Bridge {
        @JavascriptInterface public void openPanel(String raw) {
            runOnUiThread(() -> {
                try {
                    Uri uri = Uri.parse(raw);
                    if (!("http".equals(uri.getScheme()) || "https".equals(uri.getScheme())) || !isPanelHost(uri.getHost()))
                        throw new IllegalArgumentException();
                    web.loadUrl(raw);
                } catch (Exception error) { Toast.makeText(MainActivity.this, "Use o IP local ou endereço Tailscale do seu PC", Toast.LENGTH_LONG).show(); }
            });
        }
        @JavascriptInterface public void testPanel(String raw) {
            new Thread(() -> {
                String message; HttpURLConnection connection = null;
                try {
                    URL base = new URL(raw); String health = new URL(base, "/api/one/health").toString();
                    connection = (HttpURLConnection) new URL(health).openConnection();
                    connection.setConnectTimeout(3500); connection.setReadTimeout(3500); connection.setUseCaches(false);
                    int code = connection.getResponseCode(); message = code >= 200 && code < 500 ? "PC respondeu HTTP " + code : "PC respondeu HTTP " + code;
                } catch (Exception error) { message = "Sem resposta do PC: " + error.getClass().getSimpleName(); }
                finally { if (connection != null) connection.disconnect(); }
                final String safe = message.replace("\\", "\\\\").replace("'", "\\'");
                runOnUiThread(() -> web.evaluateJavascript("window.aurionConnectionResult('" + safe + "')", null));
            }).start();
        }
        @JavascriptInterface public void notifyBand() { runOnUiThread(() -> BandNotificationTest.requestOrSend(MainActivity.this)); }
        @JavascriptInterface public void appInfo() { runOnUiThread(() -> new AlertDialog.Builder(MainActivity.this)
            .setTitle("AURION ONE Mobile")
            .setMessage("Versão 1.0.0 · interface móvel local · painel PC carregado somente pelo endereço escolhido por você.")
            .setPositiveButton("OK", null).show()); }
        @JavascriptInterface public void notificationSettings() { runOnUiThread(() -> {
            Intent intent = new Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS).putExtra(Settings.EXTRA_APP_PACKAGE, getPackageName());
            startActivity(intent);
        }); }
    }

    @Override protected void onActivityResult(int request, int result, Intent data) {
        super.onActivityResult(request, result, data);
        if (request == PICK_FILE && selectedFiles != null) {
            selectedFiles.onReceiveValue(WebChromeClient.FileChooserParams.parseResult(result, data)); selectedFiles = null;
        }
    }
    @Override public void onRequestPermissionsResult(int code, String[] permissions, int[] results) {
        super.onRequestPermissionsResult(code, permissions, results); BandNotificationTest.onPermissionResult(this, code, results);
    }
    @Override public void onBackPressed() {
        if (web != null && !web.getUrl().startsWith("file:///android_asset/")) web.loadUrl("file:///android_asset/index.html");
        else if (web != null && web.canGoBack()) web.goBack(); else super.onBackPressed();
    }
}
