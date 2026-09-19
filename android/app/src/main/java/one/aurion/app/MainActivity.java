package one.aurion.app;

import android.app.Activity;
import android.app.AlertDialog;
import android.os.Bundle;
import android.content.Intent;
import android.net.Uri;
import android.graphics.Color;
import android.view.View;
import android.view.WindowInsets;
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
    private Button refreshButton, resetButton;
    private boolean refreshing = false;
    private int requestVersion = 0;
    private ValueCallback<Uri[]> selectedFiles;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().getDecorView().setSystemUiVisibility(0);
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setBackgroundColor(Color.rgb(12, 24, 40));
        layout.setOnApplyWindowInsetsListener((v, insets) -> {
            android.graphics.Insets bars = insets.getInsets(WindowInsets.Type.systemBars() | WindowInsets.Type.displayCutout());
            v.setPadding(bars.left, bars.top, bars.right, bars.bottom);
            return insets;
        });
        LinearLayout controls = new LinearLayout(this);
        controls.setOrientation(LinearLayout.HORIZONTAL);
        refreshButton = new Button(this);
        refreshButton.setText("Atualizar");
        refreshButton.setContentDescription("Buscar painel mais recente");
        controls.addView(refreshButton, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        resetButton = new Button(this);
        resetButton.setText("Socorro");
        resetButton.setContentDescription("Recuperar painel sem apagar configurações");
        controls.addView(resetButton, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        Button bandButton = new Button(this);
        bandButton.setText("Testar Band");
        bandButton.setContentDescription("Enviar notificação Android de teste para verificar espelhamento no Mi Fitness");
        controls.addView(bandButton, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
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
        bandButton.setOnClickListener(v -> BandNotificationTest.requestOrSend(this));
        resetButton.setOnClickListener(v -> new AlertDialog.Builder(this)
            .setTitle("Recuperar AURION")
            .setMessage("Restaurar o painel básico? A cópia baixada será removida, mas suas configurações serão mantidas.")
            .setNegativeButton("Cancelar", null)
            .setPositiveButton("Restaurar", (dialog, which) -> resetPanel())
            .show());
        loadPanel();
    }

    @Override public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        BandNotificationTest.onPermissionResult(this, requestCode, grantResults);
    }

    private void resetPanel() {
        requestVersion++;
        refreshing = false;
        refreshButton.setEnabled(true);
        refreshButton.setText("Atualizar");
        new File(getFilesDir(), "panel-cache.html").delete();
        view.stopLoading();
        view.loadUrl("file:///android_asset/index.html");
        Toast.makeText(this, "Painel básico restaurado", Toast.LENGTH_LONG).show();
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
