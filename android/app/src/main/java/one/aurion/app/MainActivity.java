package one.aurion.app;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothManager;
import android.bluetooth.le.BluetoothLeScanner;
import android.bluetooth.le.ScanCallback;
import android.bluetooth.le.ScanResult;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;
import android.net.Uri;
import android.os.BatteryManager;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.os.Handler;
import android.os.Looper;
import android.os.PowerManager;
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

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

public class MainActivity extends Activity {
    private static final int PICK_FILE = 410;
    private static final int CREATE_BACKUP = 411;
    private static final int REQUEST_BLUETOOTH = 412;
    private WebView web;
    private ValueCallback<Uri[]> selectedFiles;
    private String pendingBackup = "";
    private BluetoothLeScanner scanner;
    private ScanCallback scanCallback;
    private final Map<String, JSONObject> scanResults = new LinkedHashMap<>();
    private final Handler handler = new Handler(Looper.getMainLooper());

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setStatusBarColor(Color.rgb(4, 8, 13));
        getWindow().setNavigationBarColor(Color.rgb(4, 8, 13));
        web = new WebView(this);
        web.setBackgroundColor(Color.rgb(4, 8, 13));
        setContentView(web);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setDatabaseEnabled(true);
        s.setAllowFileAccess(false);
        s.setAllowContentAccess(true);
        s.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        s.setUserAgentString(s.getUserAgentString() + " AURION-ONE-Mobile-Fixo/2.0");
        web.addJavascriptInterface(new Bridge(), "AurionAndroid");
        web.setWebChromeClient(new WebChromeClient() {
            @Override public boolean onShowFileChooser(WebView v, ValueCallback<Uri[]> callback, FileChooserParams params) {
                if (selectedFiles != null) selectedFiles.onReceiveValue(null);
                selectedFiles = callback;
                try { startActivityForResult(params.createIntent(), PICK_FILE); return true; }
                catch (Exception e) { selectedFiles = null; callback.onReceiveValue(null); return true; }
            }
        });
        web.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest request) {
                Uri uri = request.getUrl();
                String scheme = uri.getScheme() == null ? "" : uri.getScheme();
                if ((scheme.equals("http") || scheme.equals("https")) && isAllowedPanelHost(uri.getHost())) return false;
                if (scheme.equals("file")) return false;
                try { startActivity(new Intent(Intent.ACTION_VIEW, uri)); }
                catch (Exception ignored) { toast("Não foi possível abrir o endereço"); }
                return true;
            }
        });
        web.loadUrl("file:///android_asset/index.html");
    }

    private void toast(String text) { runOnUiThread(() -> Toast.makeText(this, text, Toast.LENGTH_LONG).show()); }

    private boolean isAllowedPanelHost(String host) {
        if (host == null) return false;
        String h = host.toLowerCase(Locale.ROOT);
        return h.equals("localhost") || h.equals("127.0.0.1") || h.endsWith(".ts.net") || h.endsWith(".local") ||
            h.startsWith("10.") || h.startsWith("192.168.") || h.matches("172\\.(1[6-9]|2[0-9]|3[01])\\..*");
    }

    private boolean has(String permission) { return Build.VERSION.SDK_INT < 23 || checkSelfPermission(permission) == PackageManager.PERMISSION_GRANTED; }
    private boolean packageInstalled(String pkg) {
        try { getPackageManager().getApplicationInfo(pkg, 0); return true; }
        catch (PackageManager.NameNotFoundException e) { return false; }
    }

    private JSONObject diagnostics() {
        JSONObject j = new JSONObject();
        try {
            j.put("appVersion", BuildConfig.VERSION_NAME);
            j.put("manufacturer", Build.MANUFACTURER);
            j.put("model", Build.MODEL);
            j.put("android", Build.VERSION.RELEASE);
            j.put("api", Build.VERSION.SDK_INT);
            j.put("developerMode", Settings.Global.getInt(getContentResolver(), Settings.Global.DEVELOPMENT_SETTINGS_ENABLED, 0) == 1);
            j.put("usbDebug", Settings.Global.getInt(getContentResolver(), Settings.Global.ADB_ENABLED, 0) == 1);
            BatteryManager battery = (BatteryManager) getSystemService(BATTERY_SERVICE);
            j.put("battery", battery == null ? -1 : battery.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY));
            long free = Environment.getDataDirectory().getFreeSpace();
            long total = Environment.getDataDirectory().getTotalSpace();
            j.put("storageFreeGb", Math.round(free / 107374182.4) / 10.0);
            j.put("storageTotalGb", Math.round(total / 107374182.4) / 10.0);
            ConnectivityManager cm = (ConnectivityManager) getSystemService(CONNECTIVITY_SERVICE);
            Network active = cm == null ? null : cm.getActiveNetwork();
            NetworkCapabilities nc = cm == null || active == null ? null : cm.getNetworkCapabilities(active);
            String network = "offline";
            if (nc != null && nc.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)) network = "wifi";
            else if (nc != null && nc.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR)) network = "mobile";
            else if (nc != null && nc.hasTransport(NetworkCapabilities.TRANSPORT_VPN)) network = "vpn";
            else if (nc != null) network = "other";
            j.put("network", network);
            BluetoothManager bm = (BluetoothManager) getSystemService(BLUETOOTH_SERVICE);
            BluetoothAdapter ba = bm == null ? null : bm.getAdapter();
            j.put("bluetoothSupported", ba != null);
            j.put("bluetoothEnabled", ba != null && ba.isEnabled());
            j.put("bleSupported", getPackageManager().hasSystemFeature(PackageManager.FEATURE_BLUETOOTH_LE));
            j.put("bluetoothPermission", Build.VERSION.SDK_INT < 31 || (has(Manifest.permission.BLUETOOTH_SCAN) && has(Manifest.permission.BLUETOOTH_CONNECT)));
            android.app.NotificationManager nm = (android.app.NotificationManager) getSystemService(NOTIFICATION_SERVICE);
            j.put("notifications", nm != null && nm.areNotificationsEnabled());
            PowerManager pm = (PowerManager) getSystemService(POWER_SERVICE);
            j.put("batteryUnrestricted", pm != null && pm.isIgnoringBatteryOptimizations(getPackageName()));
            j.put("miFitness", packageInstalled("com.xiaomi.wearable"));
            j.put("termux", packageInstalled("com.termux"));
            j.put("tailscale", packageInstalled("com.tailscale.ipn"));
            j.put("healthConnect", packageInstalled("com.google.android.apps.healthdata") || Build.VERSION.SDK_INT >= 34);
            j.put("bandBonded", bondedDevices());
        } catch (Exception e) { try { j.put("error", e.getClass().getSimpleName()); } catch (Exception ignored) {} }
        return j;
    }

    private JSONArray bondedDevices() {
        JSONArray arr = new JSONArray();
        if (Build.VERSION.SDK_INT >= 31 && !has(Manifest.permission.BLUETOOTH_CONNECT)) return arr;
        try {
            BluetoothManager bm = (BluetoothManager) getSystemService(BLUETOOTH_SERVICE);
            BluetoothAdapter ba = bm == null ? null : bm.getAdapter();
            Set<BluetoothDevice> devices = ba == null ? null : ba.getBondedDevices();
            if (devices != null) for (BluetoothDevice d : devices) {
                JSONObject x = new JSONObject(); x.put("name", d.getName() == null ? "Dispositivo sem nome" : d.getName()); x.put("type", d.getType()); arr.put(x);
            }
        } catch (Exception ignored) { }
        return arr;
    }

    private void emit(String function, Object payload) {
        final String js = "window." + function + "(" + JSONObject.quote(String.valueOf(payload)) + ")";
        runOnUiThread(() -> web.evaluateJavascript(js, null));
    }

    private void requestBluetoothOrScan() {
        if (Build.VERSION.SDK_INT >= 31 && (!has(Manifest.permission.BLUETOOTH_SCAN) || !has(Manifest.permission.BLUETOOTH_CONNECT))) {
            requestPermissions(new String[]{Manifest.permission.BLUETOOTH_SCAN, Manifest.permission.BLUETOOTH_CONNECT}, REQUEST_BLUETOOTH);
            return;
        }
        startBleScan();
    }

    private void startBleScan() {
        try {
            BluetoothManager bm = (BluetoothManager) getSystemService(BLUETOOTH_SERVICE);
            BluetoothAdapter ba = bm == null ? null : bm.getAdapter();
            if (ba == null) { emit("aurionBandResult", "{\"status\":\"blocked\",\"message\":\"Bluetooth não suportado\"}"); return; }
            if (!ba.isEnabled()) { emit("aurionBandResult", "{\"status\":\"blocked\",\"message\":\"Ative o Bluetooth\"}"); return; }
            scanner = ba.getBluetoothLeScanner();
            if (scanner == null) { emit("aurionBandResult", "{\"status\":\"blocked\",\"message\":\"Scanner BLE indisponível\"}"); return; }
            scanResults.clear();
            scanCallback = new ScanCallback() {
                @Override public void onScanResult(int callbackType, ScanResult result) {
                    try {
                        BluetoothDevice d = result.getDevice();
                        String name = (Build.VERSION.SDK_INT < 31 || has(Manifest.permission.BLUETOOTH_CONNECT)) ? d.getName() : null;
                        String key = name == null ? "BLE sem nome " + (scanResults.size() + 1) : name;
                        JSONObject x = new JSONObject(); x.put("name", key); x.put("rssi", result.getRssi());
                        scanResults.put(key, x);
                    } catch (Exception ignored) { }
                }
                @Override public void onScanFailed(int errorCode) { emit("aurionBandResult", "{\"status\":\"error\",\"message\":\"Falha BLE " + errorCode + "\"}"); }
            };
            scanner.startScan(scanCallback);
            emit("aurionBandResult", "{\"status\":\"running\",\"message\":\"Buscando BLE por 8 segundos...\"}");
            handler.postDelayed(this::stopBleScan, 8000);
        } catch (SecurityException e) { emit("aurionBandResult", "{\"status\":\"blocked\",\"message\":\"Permissão Bluetooth ausente\"}"); }
    }

    private void stopBleScan() {
        try { if (scanner != null && scanCallback != null) scanner.stopScan(scanCallback); } catch (Exception ignored) { }
        JSONArray found = new JSONArray(); for (JSONObject x : scanResults.values()) found.put(x);
        JSONObject out = new JSONObject(); try { out.put("status", "completed"); out.put("devices", found); out.put("message", found.length() + " dispositivo(s) BLE observado(s). Isso não confirma integração com a Band."); } catch (Exception ignored) {}
        emit("aurionBandResult", out.toString());
    }

    private void testPanel(String raw) {
        new Thread(() -> {
            JSONObject out = new JSONObject(); JSONArray probes = new JSONArray(); boolean reached = false; String classif = "offline";
            try {
                URL supplied = new URL(raw); if (!isAllowedPanelHost(supplied.getHost())) throw new IllegalArgumentException("host");
                URL root = new URL(supplied.getProtocol(), supplied.getHost(), supplied.getPort(), "/");
                String[] paths = {"health", "api/one/health", "api/status", "api/one/state", "one"};
                for (String path : paths) {
                    HttpURLConnection c = null; JSONObject p = new JSONObject();
                    try {
                        URL u = new URL(root, path); c = (HttpURLConnection) u.openConnection(); c.setConnectTimeout(2600); c.setReadTimeout(2600); c.setUseCaches(false);
                        int code = c.getResponseCode(); p.put("path", "/" + path); p.put("http", code);
                        if (code > 0) reached = true;
                        if (path.equals("health") && code >= 200 && code < 300) classif = "home-node";
                        else if ((path.equals("api/one/health") || path.equals("api/one/state") || path.equals("one")) && code >= 200 && code < 500 && classif.equals("offline")) classif = "painel-pc";
                        else if ((code == 401 || code == 403) && classif.equals("offline")) classif = "online-auth";
                    } catch (Exception e) { p.put("path", "/" + path); p.put("error", e.getClass().getSimpleName()); }
                    finally { if (c != null) c.disconnect(); }
                    probes.put(p);
                }
                out.put("reached", reached); out.put("classification", reached ? classif : "offline"); out.put("probes", probes);
            } catch (Exception e) { try { out.put("reached", false); out.put("classification", "invalid"); out.put("error", e.getClass().getSimpleName()); } catch (Exception ignored) {} }
            emit("aurionConnectionResult", out.toString());
        }).start();
    }

    private void openPackage(String pkg, String fallback) {
        runOnUiThread(() -> {
            try {
                Intent i = getPackageManager().getLaunchIntentForPackage(pkg);
                if (i != null) startActivity(i); else startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(fallback)));
            } catch (Exception e) { toast("Aplicativo não encontrado"); }
        });
    }

    private void openSetting(String key) {
        runOnUiThread(() -> {
            Intent i;
            switch (key) {
                case "bluetooth": i = new Intent(Settings.ACTION_BLUETOOTH_SETTINGS); break;
                case "notifications": i = new Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS).putExtra(Settings.EXTRA_APP_PACKAGE, getPackageName()); break;
                case "battery": i = new Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS); break;
                case "developer": i = new Intent(Settings.ACTION_APPLICATION_DEVELOPMENT_SETTINGS); break;
                case "update": i = new Intent(Settings.ACTION_SYSTEM_UPDATE_SETTINGS); break;
                case "app": i = new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.parse("package:" + getPackageName())); break;
                case "health": i = new Intent("android.health.connect.action.HEALTH_HOME_SETTINGS"); break;
                default: i = new Intent(Settings.ACTION_SETTINGS);
            }
            try { startActivity(i); } catch (Exception e) { startActivity(new Intent(Settings.ACTION_SETTINGS)); }
        });
    }

    public final class Bridge {
        @JavascriptInterface public String getDiagnostics() { return diagnostics().toString(); }
        @JavascriptInterface public void refreshDiagnostics() { emit("aurionDiagnostics", diagnostics().toString()); }
        @JavascriptInterface public void openPanel(String raw) { runOnUiThread(() -> { try { Uri u = Uri.parse(raw); if (!isAllowedPanelHost(u.getHost())) throw new IllegalArgumentException(); web.loadUrl(raw); } catch (Exception e) { toast("Use IP local ou endereço Tailscale do PC"); } }); }
        @JavascriptInterface public void testPanel(String raw) { MainActivity.this.testPanel(raw); }
        @JavascriptInterface public void scanBand() { runOnUiThread(MainActivity.this::requestBluetoothOrScan); }
        @JavascriptInterface public void notifyBand() { runOnUiThread(() -> BandNotificationTest.requestOrSend(MainActivity.this)); }
        @JavascriptInterface public void openMiFitness() { openPackage("com.xiaomi.wearable", "https://play.google.com/store/apps/details?id=com.xiaomi.wearable"); }
        @JavascriptInterface public void openTermux() { openPackage("com.termux", "https://github.com/termux/termux-app"); }
        @JavascriptInterface public void openTailscale() { openPackage("com.tailscale.ipn", "https://play.google.com/store/apps/details?id=com.tailscale.ipn"); }
        @JavascriptInterface public void openSetting(String key) { MainActivity.this.openSetting(key); }
        @JavascriptInterface public void copyTermuxBootstrap() {
            String script = "pkg update && pkg install -y python git curl openssh && mkdir -p \\\"$HOME/aurion-mobile\\\"/{logs,backups,media} && python --version && git --version";
            ClipboardManager cm = (ClipboardManager) getSystemService(CLIPBOARD_SERVICE); cm.setPrimaryClip(ClipData.newPlainText("AURION Termux", script)); toast("Comando copiado. Revise e execute manualmente no Termux.");
        }
        @JavascriptInterface public void exportBackup(String json) {
            pendingBackup = json;
            runOnUiThread(() -> {
                Intent i = new Intent(Intent.ACTION_CREATE_DOCUMENT).setType("application/json").putExtra(Intent.EXTRA_TITLE, "aurion-mobile-backup.json");
                startActivityForResult(i, CREATE_BACKUP);
            });
        }
        @JavascriptInterface public void appInfo() { runOnUiThread(() -> new AlertDialog.Builder(MainActivity.this).setTitle("AURION ONE Mobile Fixo").setMessage("Versão " + BuildConfig.VERSION_NAME + "\nCliente móvel local. Diagnóstico não altera o sistema sem sua ação.").setPositiveButton("OK", null).show()); }
    }

    @Override protected void onActivityResult(int request, int result, Intent data) {
        super.onActivityResult(request, result, data);
        if (request == PICK_FILE && selectedFiles != null) { selectedFiles.onReceiveValue(WebChromeClient.FileChooserParams.parseResult(result, data)); selectedFiles = null; }
        if (request == CREATE_BACKUP && result == RESULT_OK && data != null && data.getData() != null) {
            try (OutputStream out = getContentResolver().openOutputStream(data.getData())) { if (out != null) out.write(pendingBackup.getBytes(StandardCharsets.UTF_8)); toast("Backup salvo no local escolhido"); }
            catch (Exception e) { toast("Falha ao salvar backup: " + e.getClass().getSimpleName()); }
            pendingBackup = "";
        }
    }
    @Override public void onRequestPermissionsResult(int code, String[] permissions, int[] results) {
        super.onRequestPermissionsResult(code, permissions, results);
        BandNotificationTest.onPermissionResult(this, code, results);
        if (code == REQUEST_BLUETOOTH) { boolean ok = true; for (int r : results) ok &= r == PackageManager.PERMISSION_GRANTED; if (ok) startBleScan(); else emit("aurionBandResult", "{\"status\":\"blocked\",\"message\":\"Permissão Bluetooth negada\"}"); }
    }
    @Override public void onBackPressed() {
        if (web != null && web.getUrl() != null && !web.getUrl().startsWith("file:///android_asset/")) web.loadUrl("file:///android_asset/index.html");
        else if (web != null && web.canGoBack()) web.goBack(); else super.onBackPressed();
    }
}
