package one.aurion.app;

import android.app.Activity;
import android.app.AlertDialog;
import android.os.Bundle;
import android.content.Intent;
import android.net.Uri;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.ValueCallback;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.Toast;
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
    private Button refreshButton;
    private Button resetButton;
    private boolean refreshing = false;
    private int requestVersion = 0;
    private ValueCallback<Uri[]> selectedFiles;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        LinearLayout controls = new LinearLayout(this);
        controls.setOrientation(LinearLayout.HORIZONTAL);
        refreshButton = new Button(this);
        refreshButton.setText("Atualizar");
        refreshButton.setContentDescription("Buscar e aplicar painel mais recente");
        controls.addView(refreshButton, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        resetButton = new Button(this);
        resetButton.setText("Reset / socorro");
        resetButton.setContentDescription("Recuperar painel travado sem apagar configurações");
        controls.addView(resetButton, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        layout.addView(controls);
        view = new WebView(this);
        layout.addView(view, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, 0, 1));
        setContentView(layout);
        view.getSettings().setJavaScriptEnabled(true);
        view.getSettings().setDomStorageEnabled(true);
        view.getSettings().setAllowFileAccess(false);
        view.getSettings().setAllowContentAccess(true);
        view.setWebChromeClient(new WebChromeClient() {
            @Override public boolean onShowFileChooser(WebView webView, ValueCallback<Uri[]> callback, FileChooserParams params) {
                if (selectedFiles != null) selectedFiles.onReceiveValue(null);
                selectedFiles = callback;
                try { startActivityForResult(params.createIntent(), PICK_FILE); return true; }
                catch (Exception error) { selectedFiles = null; callback.onReceiveValue(null); return true; }
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
        refreshButton.setOnClickListener(v -> loadPanel());
        resetButton.setOnClickListener(v -> new AlertDialog.Builder(this)
            .setTitle("Recuperar AURION")
            .setMessage("Voltar ao painel básico incluído no aplicativo? Isso remove somente o painel baixado e mantém as configurações locais. Depois, use Atualizar para tentar novamente.")
            .setNegativeButton("Cancelar", null)
            .setPositiveButton("Resetar painel", (dialog, which) -> resetPanel())
            .show());
        loadPanel();
    }

    private void resetPanel() {
        requestVersion++;
        refreshing = false;
        refreshButton.setEnabled(true);
        refreshButton.setText("Atualizar");
        new File(getFilesDir(), "panel-cache.html").delete();
        view.stopLoading();
        view.loadUrl("file:///android_asset/index.html");
        Toast.makeText(this, "Painel básico restaurado. Configurações preservadas.", Toast.LENGTH_LONG).show();
    }

    private void loadPanel() {
        if (refreshing) return;
        refreshing = true;
        final int currentRequest = ++requestVersion;
        refreshButton.setEnabled(false);
        refreshButton.setText("Buscando...");
        new Thread(() -> {
            byte[] html = null;
            boolean downloaded = false;
            HttpURLConnection connection = null;
            try {
                connection = (HttpURLConnection) new URL(PANEL_URL).openConnection();
                connection.setConnectTimeout(5000);
                connection.setReadTimeout(5000);
                connection.setUseCaches(false);
                connection.setRequestProperty("Cache-Control", "no-cache");
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
                    if (!text.contains("AURION ONE") || !text.toLowerCase().contains("<html")) html = null;
                    else {
                        try (FileOutputStream output = new FileOutputStream(new File(getFilesDir(), "panel-cache.html"))) { output.write(html); }
                        downloaded = true;
                    }
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
            final boolean updated = downloaded;
            runOnUiThread(() -> {
                if (isFinishing() || isDestroyed() || currentRequest != requestVersion) return;
                if (result != null) view.loadDataWithBaseURL("https://raw.githubusercontent.com/", new String(result, StandardCharsets.UTF_8), "text/html", "UTF-8", null);
                else view.loadUrl("file:///android_asset/index.html");
                refreshButton.setText("Atualizar");
                refreshButton.setEnabled(true);
                refreshing = false;
                Toast.makeText(this, updated ? "Painel recebido e aplicado" : "Sem atualização; exibindo versão disponível", Toast.LENGTH_LONG).show();
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
