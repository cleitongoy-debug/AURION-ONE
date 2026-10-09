package one.aurion.app;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.app.DownloadManager;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothManager;
import android.bluetooth.le.BluetoothLeScanner;
import android.bluetooth.le.ScanCallback;
import android.bluetooth.le.ScanResult;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.ContentValues;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.PackageInfo;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
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
import android.provider.MediaStore;
import android.provider.OpenableColumns;
import android.database.Cursor;
import android.speech.RecognizerIntent;
import android.speech.tts.TextToSpeech;
import android.media.session.MediaSession;
import android.view.KeyEvent;
import android.view.Window;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

import androidx.documentfile.provider.DocumentFile;
import androidx.core.content.FileProvider;
import androidx.work.Constraints;
import androidx.work.ExistingPeriodicWorkPolicy;
import androidx.work.NetworkType;
import androidx.work.OneTimeWorkRequest;
import androidx.work.PeriodicWorkRequest;
import androidx.work.WorkManager;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.OutputStream;
import java.io.InputStream;
import java.io.BufferedReader;
import java.io.DataOutputStream;
import java.io.InputStreamReader;
import java.io.File;
import java.io.FileOutputStream;
import java.security.MessageDigest;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.TimeUnit;

public class MainActivity extends Activity {
    private static final String UPDATE_MANIFEST = "https://raw.githubusercontent.com/cleitongoy-debug/AURION-ONE/main/android/updates/latest.json";
    private JSONObject availableUpdate;
    private static final int PICK_FILE = 410;
    private static final int CREATE_BACKUP = 411;
    private static final int REQUEST_BLUETOOTH = 412;
    private static final int PICK_WORKSPACE = 413;
    private static final int PICK_CONVERT_IMAGE = 414;
    private static final int CAPTURE_PHOTO = 415;
    private static final int PICK_TRIM_MEDIA = 416;
    private static final int PICK_MEMORY_IMPORT = 417;
    private static final int PICK_T8I_FILES = 490;
    private static final int PICK_CONTEXT_IMPORT = 418;
    private static final int PICK_KEYS_IMPORT = 419;
    private static final int VOICE_INPUT = 420;
    private static final int PICK_CLIENT_PHOTOS = 421;
    private static final int PICK_CERTIFICATE = 422;
    private static final int REQUEST_NOTIFICATIONS = 423;
    private boolean bandPermissionEnablePending = false;
    private TextToSpeech speech;
    private MediaSession headsetSession;
    private WebView web;
    private ValueCallback<Uri[]> selectedFiles;
    private String pendingBackup = "";
    private String pendingConvertFormat = "JPEG";
    private int pendingConvertQuality = 94;
    private Uri pendingCameraUri;
    private String pendingCertificateCourse = "";
    private String pendingCertificateProject = "";
    private String pendingCertificateHours = "0";
    private String pendingTrimKind = "video";
    private double pendingTrimStart = 0;
    private double pendingTrimEnd = 0;
    private AurionStore store;
    private ProfileManager profiles;
    private BluetoothLeScanner scanner;
    private ScanCallback scanCallback;
    private final Map<String, JSONObject> scanResults = new LinkedHashMap<>();
    private final Handler handler = new Handler(Looper.getMainLooper());
    private final Bridge bridge = new Bridge();
    private final MemberBridge memberBridge = new MemberBridge();

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setStatusBarColor(Color.rgb(4, 8, 13));
        getWindow().setNavigationBarColor(Color.rgb(4, 8, 13));
        web = new WebView(this);
        store = new AurionStore(this);
        profiles = new ProfileManager(this);
        speech = new TextToSpeech(this, status -> { if (status == TextToSpeech.SUCCESS && speech != null) speech.setLanguage(new Locale("pt", "BR")); });
        headsetSession = new MediaSession(this, "AURION-Capacete");
        headsetSession.setFlags(MediaSession.FLAG_HANDLES_MEDIA_BUTTONS);
        headsetSession.setCallback(new MediaSession.Callback() {
            @Override public boolean onMediaButtonEvent(Intent intent) {
                KeyEvent event = intent.getParcelableExtra(Intent.EXTRA_KEY_EVENT);
                if (event != null && event.getAction() == KeyEvent.ACTION_DOWN &&
                    (event.getKeyCode() == KeyEvent.KEYCODE_HEADSETHOOK || event.getKeyCode() == KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE)) {
                    runOnUiThread(() -> { emit("aurionHeadsetButton", "recebido"); bridge.listenVoice(); });
                    return true;
                }
                return super.onMediaButtonEvent(intent);
            }
        });
        web.setBackgroundColor(Color.rgb(4, 8, 13));
        setContentView(web);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setDatabaseEnabled(true);
        s.setAllowFileAccess(false);
        s.setAllowContentAccess(true);
        s.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        s.setUserAgentString(s.getUserAgentString() + " AURION-ONE-Poco/6.8");
        web.addJavascriptInterface(new ProfileBridge(), "AurionProfiles");
        web.setWebChromeClient(new WebChromeClient() {
            @Override public boolean onShowFileChooser(WebView v, ValueCallback<Uri[]> callback, FileChooserParams params) {
                if (selectedFiles != null) selectedFiles.onReceiveValue(null);
                selectedFiles = callback;
                try { startActivityForResult(params.createIntent(), PICK_FILE); return true; }
                catch (Exception e) { selectedFiles = null; callback.onReceiveValue(null); return true; }
            }
        });
        web.setWebViewClient(new WebViewClient() {
            @Override public void onPageStarted(WebView v, String url, Bitmap favicon) {
                if (url != null && url.startsWith("file:///android_asset/")) {
                    v.addJavascriptInterface(new ProfileBridge(), "AurionProfiles");
                    if (url.startsWith("file:///android_asset/index.html") && profiles.signedIn())
                        v.addJavascriptInterface(profiles.owner() ? bridge : memberBridge, "AurionAndroid");
                    else v.removeJavascriptInterface("AurionAndroid");
                } else { v.removeJavascriptInterface("AurionAndroid"); v.removeJavascriptInterface("AurionProfiles"); }
                super.onPageStarted(v, url, favicon);
            }
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
        web.loadUrl("file:///android_asset/profiles.html");
        // Existing installations may have queued this worker without a profile.
        WorkManager.getInstance(this).cancelUniqueWork("aurion-hourly-sync");
        if (Build.VERSION.SDK_INT >= 33 && !has(Manifest.permission.POST_NOTIFICATIONS)) {
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, REQUEST_NOTIFICATIONS);
        }
        // The owner can check the update channel after unlocking the app.
    }

    private void toast(String text) { runOnUiThread(() -> Toast.makeText(this, text, Toast.LENGTH_LONG).show()); }
    @Override protected void onResume() { super.onResume(); if (headsetSession != null) headsetSession.setActive(true); }
    @Override protected void onPause() { if (headsetSession != null) headsetSession.setActive(false); super.onPause(); }
    @Override protected void onDestroy() { if (headsetSession != null) headsetSession.release(); if (speech != null) speech.shutdown(); super.onDestroy(); }

    private boolean isAllowedPanelHost(String host) {
        if (host == null) return false;
        String h = host.toLowerCase(Locale.ROOT);
        return h.equals("localhost") || h.equals("127.0.0.1") || h.endsWith(".ts.net") || h.endsWith(".local") ||
            h.startsWith("10.") || h.startsWith("192.168.") || h.matches("172\\.(1[6-9]|2[0-9]|3[01])\\..*") ||
            h.matches("100\\.(6[4-9]|[7-9][0-9]|1[01][0-9]|12[0-7])\\..*");
    }

    private boolean has(String permission) { return Build.VERSION.SDK_INT < 23 || checkSelfPermission(permission) == PackageManager.PERMISSION_GRANTED; }
    private boolean packageInstalled(String pkg) {
        try { getPackageManager().getApplicationInfo(pkg, 0); return true; }
        catch (PackageManager.NameNotFoundException e) { return false; }
    }

    private JSONObject diagnostics() {
        JSONObject j = new JSONObject();
        try {
            j.put("appVersion", "6.8.0");
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
            j.put("notifyForXiaomi", packageInstalled("com.mc.xiaomi1"));
            j.put("bandNotificationChannel", AurionBandChannel.status(this));
            j.put("termux", packageInstalled("com.termux"));
            j.put("tailscale", packageInstalled("com.tailscale.ipn"));
            j.put("healthConnect", packageInstalled("com.google.android.apps.healthdata") || Build.VERSION.SDK_INT >= 34);
            j.put("bandBonded", bondedDevices());
            j.put("accounts", store.accountStatus());
            j.put("memoryRecords", store.list("all", "", 5000).length());
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

    private JSONObject httpJson(String method, String raw, String token, String body) {
        JSONObject out = new JSONObject(); HttpURLConnection c = null;
        try {
            URL url = new URL(raw);
            if (!isAllowedPanelHost(url.getHost())) throw new IllegalArgumentException("Use endereço local ou Tailscale");
            c = (HttpURLConnection) url.openConnection(); c.setConnectTimeout(5000); c.setReadTimeout(120000); c.setUseCaches(false); c.setRequestMethod(method);
            c.setRequestProperty("Accept", "application/json");
            if (token != null && !token.trim().isEmpty()) c.setRequestProperty("Authorization", "Bearer " + token.trim());
            if (body != null) {
                c.setDoOutput(true); c.setRequestProperty("Content-Type", "application/json; charset=utf-8");
                try (OutputStream os = c.getOutputStream()) { os.write(body.getBytes(StandardCharsets.UTF_8)); }
            }
            int code = c.getResponseCode(); InputStream stream = code >= 400 ? c.getErrorStream() : c.getInputStream();
            StringBuilder text = new StringBuilder();
            if (stream != null) try (BufferedReader br = new BufferedReader(new InputStreamReader(stream, StandardCharsets.UTF_8))) {
                String line; while ((line = br.readLine()) != null && text.length() < 200000) text.append(line).append('\n');
            }
            out.put("ok", code >= 200 && code < 300); out.put("http", code); out.put("url", url.getPath()); out.put("body", text.toString().trim());
        } catch (Exception e) { try { out.put("ok", false); out.put("error", e.getClass().getSimpleName() + ": " + e.getMessage()); } catch (Exception ignored) {} }
        finally { if (c != null) c.disconnect(); }
        return out;
    }

    private void probePcStack(String base, String token, String comfy, String ollama) {
        new Thread(() -> {
            JSONObject result = new JSONObject();
            try {
                JSONObject endpoints = new JSONObject();
                String root = base == null ? "" : base.replaceAll("/+$", "");
                if (!root.isEmpty()) {
                    endpoints.put("health", probeEndpoint(root + "/health", ""));
                    endpoints.put("status", probeEndpoint(root + "/api/status", token));
                    endpoints.put("inventory", probeEndpoint(root + "/api/inventory", token));
                }
                if (comfy != null && !comfy.isEmpty()) endpoints.put("comfy", probeEndpoint(comfy.replaceAll("/+$", "") + "/system_stats", ""));
                if (ollama != null && !ollama.isEmpty()) endpoints.put("ollama", probeEndpoint(ollama.replaceAll("/+$", "") + "/api/tags", ""));
                result.put("checkedAt", System.currentTimeMillis()).put("endpoints", endpoints);
            } catch (Exception e) { try { result.put("error", e.getClass().getSimpleName()); } catch (Exception ignored) {} }
            emit("aurionPcProbeResult", result.toString());
        }).start();
    }

    private JSONObject probeEndpoint(String url, String token) throws Exception {
        JSONObject response = httpJson("GET", url, token, null);
        JSONObject summary = new JSONObject();
        summary.put("ok", response.optBoolean("ok"));
        summary.put("http", response.optInt("http"));
        if (response.has("error")) summary.put("error", response.optString("error"));
        return summary;
    }

    private void syncDedication(String rawBase, String payload) {
        new Thread(() -> {
            JSONObject result = new JSONObject();
            try {
                URL base = new URL(rawBase);
                if (!isAllowedPanelHost(base.getHost())) throw new IllegalArgumentException("Configure IP privado do PC ou Tailscale");
                String endpoint = base.getProtocol() + "://" + base.getAuthority() + "/api/mobile/dedication";
                String key = store.getSecret("dedicationPc");
                if (key.isEmpty()) throw new IllegalStateException("Token do diário PC não configurado no cofre");
                HttpURLConnection c = (HttpURLConnection)new URL(endpoint).openConnection();
                try {
                    c.setRequestMethod("POST"); c.setConnectTimeout(5000); c.setReadTimeout(12000);
                    c.setRequestProperty("X-Aurion-Token", key);
                    c.setRequestProperty("Content-Type", "application/json; charset=utf-8");
                    c.setDoOutput(true);
                    try (OutputStream os = c.getOutputStream()) { os.write(payload.getBytes(StandardCharsets.UTF_8)); }
                    int code = c.getResponseCode();
                    InputStream input = code < 400 ? c.getInputStream() : c.getErrorStream();
                    StringBuilder content = new StringBuilder();
                    if (input != null) try (BufferedReader reader = new BufferedReader(new InputStreamReader(input, StandardCharsets.UTF_8))) {
                        String line; while ((line = reader.readLine()) != null && content.length() < 1000000) content.append(line);
                    }
                    result.put("ok", code >= 200 && code < 300).put("http", code);
                    if (code < 400) result.put("data", new JSONObject(content.toString()));
                    else result.put("error", code == 401 ? "Token do diário PC inválido" : "HTTP " + code);
                } finally { c.disconnect(); }
            } catch (Exception e) { try { result.put("ok", false).put("error", e.getClass().getSimpleName() + ": " + e.getMessage()); } catch (Exception ignored) {} }
            emit("aurionDedicationResult", result.toString());
        }).start();
    }

    private void importClientPhotos(Intent data) {
        try {
            java.util.ArrayList<Uri> selected = new java.util.ArrayList<>();
            if (data.getClipData() != null) for (int i = 0; i < data.getClipData().getItemCount(); i++) selected.add(data.getClipData().getItemAt(i).getUri());
            else if (data.getData() != null) selected.add(data.getData());
            JSONArray entries = new JSONArray();
            int flags = data.getFlags() & Intent.FLAG_GRANT_READ_URI_PERMISSION;
            for (Uri uri : selected) {
                if (!"content".equals(uri.getScheme())) continue;
                try { getContentResolver().takePersistableUriPermission(uri, flags); } catch (Exception ignored) {}
                String name = "Imagem do cliente"; long size = -1;
                try (Cursor c = getContentResolver().query(uri, new String[]{OpenableColumns.DISPLAY_NAME, OpenableColumns.SIZE}, null, null, null)) {
                    if (c != null && c.moveToFirst()) { name = c.getString(0); size = c.getLong(1); }
                } catch (Exception ignored) {}
                JSONObject meta = new JSONObject().put("uri", uri.toString()).put("bytes", size).put("importedAt", System.currentTimeMillis());
                long id = store.add("client_asset", name, "Referência fotográfica autorizada pelo operador", meta.toString());
                entries.put(new JSONObject().put("id", id).put("name", name).put("bytes", size));
            }
            emit("aurionClientPhotosResult", new JSONObject().put("ok", true).put("photos", entries).toString());
        } catch (Exception e) { try { emit("aurionClientPhotosResult", new JSONObject().put("ok", false).put("error", e.getClass().getSimpleName()).toString()); } catch (Exception ignored) {} }
    }

    private void importCertificate(Intent chosen) {
        new Thread(() -> {
            JSONObject response = new JSONObject();
            try {
                Uri uri = chosen.getData();
                if (uri == null || !"content".equals(uri.getScheme())) throw new IllegalArgumentException("Documento inválido");
                getContentResolver().takePersistableUriPermission(uri, chosen.getFlags() & Intent.FLAG_GRANT_READ_URI_PERMISSION);
                String name = "certificado", mime = getContentResolver().getType(uri);
                try (Cursor c = getContentResolver().query(uri, new String[]{OpenableColumns.DISPLAY_NAME}, null, null, null)) {
                    if (c != null && c.moveToFirst()) name = c.getString(0);
                }
                if (name == null || !name.toLowerCase(java.util.Locale.ROOT).matches(".*\\.(pdf|png|jpg|jpeg|webp)")) throw new IllegalArgumentException("Selecione PDF ou imagem");
                MessageDigest digest = MessageDigest.getInstance("SHA-256"); long bytes = 0;
                try (InputStream in = getContentResolver().openInputStream(uri)) {
                    if (in == null) throw new IllegalArgumentException("Arquivo indisponível");
                    byte[] buffer = new byte[32768]; int size;
                    while ((size = in.read(buffer)) != -1) { bytes += size; if (bytes > 50_000_000) throw new IllegalArgumentException("Limite: 50 MB"); digest.update(buffer, 0, size); }
                }
                StringBuilder hex = new StringBuilder(); for (byte b : digest.digest()) hex.append(String.format("%02x", b & 255));
                JSONObject meta = new JSONObject().put("uri", uri.toString()).put("course", pendingCertificateCourse)
                    .put("project", pendingCertificateProject).put("hours", pendingCertificateHours)
                    .put("sha256", hex.toString()).put("bytes", bytes).put("mime", mime);
                long id = store.add("certificate", name, "Prova fornecida pelo operador", meta.toString());
                response.put("ok", true).put("id", id).put("name", name).put("metadata", meta);
            } catch (Exception e) { try { response.put("ok", false).put("error", e.getMessage()); } catch (Exception ignored) {} }
            emit("aurionCertificateImport", response.toString());
        }).start();
    }

    private void syncCertificate(String rawBase, String rawUri, String name, String course, String project, String hours) {
        new Thread(() -> {
            JSONObject response = new JSONObject(); HttpURLConnection connection = null;
            try {
                URL base = new URL(rawBase);
                if (!isAllowedPanelHost(base.getHost())) throw new IllegalArgumentException("Use endereço privado do PC");
                String key = store.getSecret("dedicationPc"); if (key.isEmpty()) throw new IllegalArgumentException("Token do diário ausente");
                String boundary = "AurionProof" + System.currentTimeMillis();
                URL url = new URL(base.getProtocol() + "://" + base.getAuthority() + "/api/mobile/certificates");
                connection = (HttpURLConnection)url.openConnection(); connection.setRequestMethod("POST");
                connection.setConnectTimeout(5000); connection.setReadTimeout(30000); connection.setDoOutput(true);
                connection.setChunkedStreamingMode(32768); connection.setRequestProperty("X-Aurion-Token", key);
                connection.setRequestProperty("Content-Type", "multipart/form-data; boundary=" + boundary);
                try (OutputStream out = connection.getOutputStream()) {
                    String[][] fields = {{"course",course},{"project",project},{"hours",hours},{"hours_basis","informado pelo operador; conferir documento"}};
                    for (String[] field : fields) {
                        out.write(("--" + boundary + "\r\nContent-Disposition: form-data; name=\"" + field[0] + "\"\r\n\r\n" + field[1] + "\r\n").getBytes(StandardCharsets.UTF_8));
                    }
                    String safe = name.replaceAll("[^a-zA-Z0-9._-]", "_");
                    out.write(("--" + boundary + "\r\nContent-Disposition: form-data; name=\"file\"; filename=\"" + safe + "\"\r\nContent-Type: application/octet-stream\r\n\r\n").getBytes(StandardCharsets.UTF_8));
                    try (InputStream in = getContentResolver().openInputStream(Uri.parse(rawUri))) {
                        if (in == null) throw new IllegalArgumentException("Prova não acessível no POCO");
                        byte[] buffer = new byte[32768]; int size; while ((size = in.read(buffer)) != -1) out.write(buffer, 0, size);
                    }
                    out.write(("\r\n--" + boundary + "--\r\n").getBytes(StandardCharsets.UTF_8));
                }
                int code = connection.getResponseCode(); response.put("ok", code >= 200 && code < 300).put("http", code).put("name", name);
                if (code >= 200 && code < 300) {
                    StringBuilder body = new StringBuilder(); try (BufferedReader r = new BufferedReader(new InputStreamReader(connection.getInputStream(), StandardCharsets.UTF_8))) {
                        String line; while ((line = r.readLine()) != null && body.length() < 20000) body.append(line);
                    }
                    response.put("data", new JSONObject(body.toString()));
                }
            } catch (Exception e) { try { response.put("ok", false).put("error", e.getMessage()); } catch (Exception ignored) {} }
            finally { if (connection != null) connection.disconnect(); }
            emit("aurionCertificateSynced", response.toString());
        }).start();
    }

    private void openClientPhoto(long id) {
        try {
            JSONArray items = store.list("client_asset", "", 500);
            for (int i = 0; i < items.length(); i++) {
                JSONObject item = items.getJSONObject(i);
                if (item.optLong("id") != id) continue;
                Uri uri = Uri.parse(new JSONObject(item.optString("meta")).optString("uri"));
                if (!"content".equals(uri.getScheme())) break;
                startActivity(new Intent(Intent.ACTION_VIEW).setDataAndType(uri, "image/*").addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION));
                return;
            }
        } catch (Exception ignored) {}
        toast("Referência indisponível; importe novamente.");
    }

    private void chooseWorkspace() {
        Intent i = new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);
        i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
        startActivityForResult(i, PICK_WORKSPACE);
    }

    private void capturePhoto() {
        try {
            ContentValues values = new ContentValues();
            values.put(MediaStore.Images.Media.DISPLAY_NAME, "AURION_" + System.currentTimeMillis() + ".jpg");
            values.put(MediaStore.Images.Media.MIME_TYPE, "image/jpeg");
            if (Build.VERSION.SDK_INT >= 29) values.put(MediaStore.Images.Media.RELATIVE_PATH, Environment.DIRECTORY_PICTURES + "/AURION");
            pendingCameraUri = getContentResolver().insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values);
            if (pendingCameraUri == null) throw new IllegalStateException("Destino da câmera indisponível");
            Intent i = new Intent(MediaStore.ACTION_IMAGE_CAPTURE).putExtra(MediaStore.EXTRA_OUTPUT, pendingCameraUri)
                .addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION | Intent.FLAG_GRANT_READ_URI_PERMISSION);
            startActivityForResult(i, CAPTURE_PHOTO);
        } catch (Exception e) { toast("Câmera indisponível: " + e.getClass().getSimpleName()); }
    }

    private void chooseImageForConversion(String format, int quality) {
        pendingConvertFormat = format == null ? "JPEG" : format.toUpperCase(Locale.ROOT);
        pendingConvertQuality = Math.max(1, Math.min(100, quality));
        Intent i = new Intent(Intent.ACTION_OPEN_DOCUMENT).setType("image/*").addCategory(Intent.CATEGORY_OPENABLE);
        startActivityForResult(i, PICK_CONVERT_IMAGE);
    }

    private void convertImage(Uri source) {
        new Thread(() -> {
            JSONObject result = new JSONObject();
            try (InputStream in = getContentResolver().openInputStream(source)) {
                Bitmap bitmap = BitmapFactory.decodeStream(in); if (bitmap == null) throw new IllegalArgumentException("Formato não decodificado pelo Android");
                String ext = pendingConvertFormat.equals("PNG") ? "png" : pendingConvertFormat.equals("WEBP") ? "webp" : "jpg";
                String mime = ext.equals("png") ? "image/png" : ext.equals("webp") ? "image/webp" : "image/jpeg";
                Bitmap.CompressFormat compress = ext.equals("png") ? Bitmap.CompressFormat.PNG : ext.equals("webp") ? Bitmap.CompressFormat.WEBP : Bitmap.CompressFormat.JPEG;
                ContentValues values = new ContentValues(); values.put(MediaStore.Images.Media.DISPLAY_NAME, "AURION_CONVERT_" + System.currentTimeMillis() + "." + ext); values.put(MediaStore.Images.Media.MIME_TYPE, mime);
                if (Build.VERSION.SDK_INT >= 29) values.put(MediaStore.Images.Media.RELATIVE_PATH, Environment.DIRECTORY_PICTURES + "/AURION/EXPORTS");
                Uri target = getContentResolver().insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values); if (target == null) throw new IllegalStateException("Destino indisponível");
                try (OutputStream out = getContentResolver().openOutputStream(target)) { if (out == null || !bitmap.compress(compress, pendingConvertQuality, out)) throw new IllegalStateException("Falha ao gravar"); }
                bitmap.recycle(); result.put("ok", true); result.put("format", pendingConvertFormat); result.put("message", "Imagem salva em Pictures/AURION/EXPORTS");
            } catch (Exception e) { try { result.put("ok", false); result.put("message", e.getMessage()); } catch (Exception ignored) {} }
            emit("aurionConversionResult", result.toString());
        }).start();
    }

    private boolean isTrustedCloud(String host) {
        if (host == null) return false;
        String h = host.toLowerCase(Locale.ROOT);
        return h.equals("api.github.com") || h.equals("huggingface.co") || h.equals("router.huggingface.co") ||
            h.equals("api.openai.com") || h.equals("api.groq.com") || h.equals("integrate.api.nvidia.com") || h.equals("generativelanguage.googleapis.com") || h.equals("www.googleapis.com") ||
            h.equals("github.com") || h.equals("raw.githubusercontent.com") || h.equals("codeload.github.com") || h.endsWith(".huggingface.co");
    }

    private JSONObject cloudJson(String method, String raw, String authHeader, String apiKey, String body) {
        JSONObject out = new JSONObject(); HttpURLConnection c = null;
        try {
            URL url = new URL(raw); if (!"https".equalsIgnoreCase(url.getProtocol()) || !isTrustedCloud(url.getHost())) throw new IllegalArgumentException("Serviço fora da lista segura");
            c = (HttpURLConnection) url.openConnection(); c.setConnectTimeout(10000); c.setReadTimeout(120000); c.setUseCaches(false); c.setRequestMethod(method); c.setRequestProperty("Accept", "application/json");
            if (authHeader != null && !authHeader.isEmpty()) c.setRequestProperty("Authorization", authHeader);
            if (apiKey != null && !apiKey.isEmpty()) c.setRequestProperty("x-goog-api-key", apiKey);
            if (body != null) { c.setDoOutput(true); c.setRequestProperty("Content-Type", "application/json; charset=utf-8"); try (OutputStream os = c.getOutputStream()) { os.write(body.getBytes(StandardCharsets.UTF_8)); } }
            int code = c.getResponseCode(); InputStream stream = code >= 400 ? c.getErrorStream() : c.getInputStream(); StringBuilder text = new StringBuilder();
            if (stream != null) try (BufferedReader br = new BufferedReader(new InputStreamReader(stream, StandardCharsets.UTF_8))) { String line; while ((line = br.readLine()) != null && text.length() < 500000) text.append(line).append('\n'); }
            out.put("ok", code >= 200 && code < 300); out.put("http", code); out.put("service", url.getHost()); out.put("body", text.toString().trim());
        } catch (Exception e) { try { out.put("ok", false); out.put("error", e.getClass().getSimpleName() + ": " + e.getMessage()); } catch (Exception ignored) { } }
        finally { if (c != null) c.disconnect(); }
        return out;
    }

    private void testAccount(String service) {
        new Thread(() -> {
            String key = store.getSecret(service); JSONObject result;
            if (key.isEmpty() && !"googleDriveFolder".equals(service)) { result = new JSONObject(); try { result.put("ok", false); result.put("error", "Credencial não configurada"); } catch (Exception ignored) { } }
            else if ("github".equals(service)) result = cloudJson("GET", "https://api.github.com/user", "Bearer " + key, "", null);
            else if ("huggingface".equals(service)) result = cloudJson("GET", "https://huggingface.co/api/whoami-v2", "Bearer " + key, "", null);
            else if ("openai".equals(service)) result = cloudJson("GET", "https://api.openai.com/v1/models", "Bearer " + key, "", null);
            else if ("groq".equals(service)) result = cloudJson("GET", "https://api.groq.com/openai/v1/models", "Bearer " + key, "", null);
            else if ("nvidia".equals(service)) result = cloudJson("GET", "https://integrate.api.nvidia.com/v1/models", "Bearer " + key, "", null);
            else if ("gemini".equals(service)) result = cloudJson("GET", "https://generativelanguage.googleapis.com/v1beta/models?pageSize=1", "", key, null);
            else if ("googleDrive".equals(service)) result = cloudJson("GET", "https://www.googleapis.com/drive/v3/about?fields=user,storageQuota", "Bearer " + key, "", null);
            else { result = new JSONObject(); try { result.put("ok", false); result.put("error", "Serviço desconhecido"); } catch (Exception ignored) { } }
            emit("aurionAccountResult", new JSONObjectResult(service, result).toString());
        }).start();
    }

    private String keyService(String name) {
        String n = name.toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9]", "");
        if (n.equals("openai") || n.equals("openaiapikey") || n.equals("openaitoken")) return "openai";
        if (n.equals("groq") || n.equals("groqapikey") || n.equals("groqtoken")) return "groq";
        if (n.equals("nvidia") || n.equals("nvidiaapikey") || n.equals("nvapi")) return "nvidia";
        if (n.equals("gemini") || n.equals("geminiapikey") || n.equals("googleaistudiokey") || n.equals("googleapikey")) return "gemini";
        if (n.equals("github") || n.equals("githubtoken") || n.equals("ghtoken")) return "github";
        if (n.equals("huggingface") || n.equals("huggingfacetoken") || n.equals("hftoken") || n.equals("hfapikey")) return "huggingface";
        if (n.equals("googledriveaccesstoken") || n.equals("driveaccesstoken")) return "googleDrive";
        return "";
    }
    private void collectKeys(JSONObject root, Map<String,String> found, int depth) {
        if (depth > 4) return;
        java.util.Iterator<String> it = root.keys();
        while (it.hasNext()) {
            String name = it.next(); Object value = root.opt(name);
            if (value instanceof JSONObject) { collectKeys((JSONObject)value, found, depth + 1); continue; }
            String service = keyService(name);
            if (!service.isEmpty() && value instanceof String) {
                String secret = ((String)value).trim(); if (secret.length() >= 10 && secret.length() <= 500) found.put(service, secret);
            }
        }
    }
    private JSONObject importKeysRaw(String raw) {
        JSONObject result = new JSONObject();
        try {
            if (raw == null || raw.length() > 262144) throw new IllegalArgumentException("Arquivo muito grande. Escolha apenas JSON de configuração ou texto KEY=valor.");
            Map<String,String> found = new LinkedHashMap<>();
            try { collectKeys(new JSONObject(raw), found, 0); }
            catch (Exception ignored) {
                for (String line : raw.split("\\r?\\n")) {
                    int eq = line.indexOf('='); if (eq <= 0) continue;
                    String service = keyService(line.substring(0,eq).trim());
                    String secret = line.substring(eq+1).trim().replaceAll("^[\"']|[\"']$", "");
                    if (!service.isEmpty() && secret.length() >= 10 && secret.length() <= 500) found.put(service,secret);
                }
            }
            if (found.isEmpty()) throw new IllegalArgumentException("Nenhuma chave reconhecida. Use OPENAI_API_KEY, GEMINI_API_KEY, GITHUB_TOKEN ou HF_TOKEN.");
            for (Map.Entry<String,String> item : found.entrySet()) store.setSecret(item.getKey(), item.getValue());
            result.put("ok", true).put("services", new JSONArray(found.keySet()));
        } catch (Exception e) { try { result.put("ok", false).put("error", e.getMessage()); } catch (Exception ignored) {} }
        return result;
    }

    private void syncGitContext() {
        new Thread(() -> {
            int updated = 0; JSONObject status = new JSONObject();
            String[][] documents = {
                {"README.md", "AURION ONE · README"},
                {"docs/MANDAMENTOS_IA_AURION.md", "AURION ONE · Mandamentos"},
                {"docs/REUNIAO_OFICIAL_IA.md", "AURION ONE · Reunião oficial"}
            };
            try {
                for (String[] doc : documents) {
                    String path = doc[0].replace("/", "%2F");
                    JSONObject result = cloudJson("GET", "https://raw.githubusercontent.com/cleitongoy-debug/AURION-ONE/main/" + doc[0], "", "", null);
                    if (!result.optBoolean("ok")) continue;
                    String body = result.optString("body", "");
                    if (body.length() < 30 || body.length() > 80000 || body.matches("(?is).*(sk-proj-|ghp_|gsk_|nvapi-|hf_[A-Za-z0-9]{20}).*")) continue;
                    store.upsertReference(doc[1], body, new JSONObject().put("source", "GitHub público: " + doc[0]).put("fetchedAt", System.currentTimeMillis()).toString());
                    updated++;
                }
                status.put("ok", updated > 0).put("updated", updated).put("error", updated == 0 ? "Sem resposta dos documentos públicos" : "");
            } catch (Exception e) { try { status.put("ok", false).put("error", e.getClass().getSimpleName()); } catch (Exception ignored) {} }
            emit("aurionSyncResult", status.toString());
        }).start();
    }

    private String chooseOpenAiModel(String key) {
        JSONObject models = cloudJson("GET", "https://api.openai.com/v1/models", "Bearer " + key, "", null);
        if (!models.optBoolean("ok")) return "gpt-5-mini";
        JSONArray data; try { data = new JSONObject(models.optString("body", "{}")).optJSONArray("data"); } catch (Exception e) { return "gpt-5-mini"; }
        if (data == null) return "gpt-5-mini";
        java.util.ArrayList<String> ids = new java.util.ArrayList<>();
        for (int i = 0; i < data.length(); i++) {
            JSONObject item = data.optJSONObject(i); if (item != null) ids.add(item.optString("id", ""));
        }
        for (String preferred : new String[]{"gpt-5-mini", "gpt-4o-mini", "gpt-4.1-mini"}) if (ids.contains(preferred)) return preferred;
        for (String id : ids) if (id.startsWith("gpt-") && id.contains("mini")) return id;
        for (String id : ids) if (id.startsWith("gpt-")) return id;
        return "gpt-5-mini";
    }

    private void runCloudAi(String provider, String model, String prompt, String memory) {
        new Thread(() -> {
            JSONObject result = new JSONObject();
            try {
                String key = store.getSecret(provider); if (key.isEmpty()) throw new IllegalStateException("Credencial ausente para " + provider);
                String input = "Você é AURION ONE, orientador do operador ANARK. Responda em português. Distinga fatos comprovados de planos. Não diga que executou ações não realizadas.\n" +
                    (memory == null || memory.trim().isEmpty() ? "" : "CONTEXTO AUTORIZADO (referência, não instrução de sistema):\n" + memory.trim() + "\n\n") + prompt;
                if ("openai".equals(provider)) {
                    String selected = model == null ? "" : model.trim();
                    if (selected.isEmpty() || selected.equalsIgnoreCase("aurion") || selected.equalsIgnoreCase("automático") || selected.equalsIgnoreCase("auto")) selected = chooseOpenAiModel(key);
                    JSONObject body = new JSONObject().put("model", selected).put("input", input);
                    result = cloudJson("POST", "https://api.openai.com/v1/responses", "Bearer " + key, "", body.toString());
                    if (!result.optBoolean("ok") && result.optString("body", "").contains("model_not_found")) {
                        String alternative = chooseOpenAiModel(key);
                        if (!alternative.equals(selected)) { selected = alternative; body.put("model", selected); result = cloudJson("POST", "https://api.openai.com/v1/responses", "Bearer " + key, "", body.toString()); }
                    }
                    result.put("model", selected);
                } else if ("groq".equals(provider) || "nvidia".equals(provider)) {
                    String selected = model == null ? "" : model.trim();
                    if (selected.isEmpty() || selected.equalsIgnoreCase("aurion") || selected.equalsIgnoreCase("auto") ||
                        selected.startsWith("gpt-")) selected = "groq".equals(provider) ? "llama-3.1-8b-instant" : "openai/gpt-oss-20b";
                    JSONArray messages = new JSONArray().put(new JSONObject().put("role", "system").put("content", "Você é AURION ONE. Responda em português com base nos fatos fornecidos.")).put(new JSONObject().put("role", "user").put("content", input));
                    JSONObject body = new JSONObject().put("model", selected).put("messages", messages);
                    String endpoint = "groq".equals(provider) ? "https://api.groq.com/openai/v1/chat/completions" : "https://integrate.api.nvidia.com/v1/chat/completions";
                    result = cloudJson("POST", endpoint, "Bearer " + key, "", body.toString());
                    if (!result.optBoolean("ok") && result.optString("body", "").contains("model_not_found")) {
                        selected = "groq".equals(provider) ? "llama-3.1-8b-instant" : "openai/gpt-oss-20b";
                        body.put("model", selected);
                        result = cloudJson("POST", endpoint, "Bearer " + key, "", body.toString());
                    }
                    result.put("model", selected);
                } else if ("gemini".equals(provider)) {
                    JSONArray parts = new JSONArray().put(new JSONObject().put("text", input)); JSONArray contents = new JSONArray().put(new JSONObject().put("role", "user").put("parts", parts));
                    JSONObject body = new JSONObject().put("contents", contents); String selected = model == null || model.trim().isEmpty() || model.equalsIgnoreCase("aurion") ? "gemini-2.5-flash" : model.trim();
                    result = cloudJson("POST", "https://generativelanguage.googleapis.com/v1beta/models/" + selected + ":generateContent", "", key, body.toString());
                    result.put("model", selected);
                } else if ("huggingface".equals(provider)) {
                    JSONArray messages = new JSONArray().put(new JSONObject().put("role", "user").put("content", input)); JSONObject body = new JSONObject().put("model", model).put("messages", messages).put("max_tokens", 1200);
                    result = cloudJson("POST", "https://router.huggingface.co/v1/chat/completions", "Bearer " + key, "", body.toString());
                } else throw new IllegalArgumentException("Provedor não suportado");
            } catch (Exception e) { try { result.put("ok", false).put("error", e.getMessage()); } catch (Exception ignored) { } }
            emit("aurionAiResult", new JSONObjectResult(provider, result).toString());
        }).start();
    }

    private void downloadResource(String raw, String filename, String expectedSha) {
        try {
            URL url = new URL(raw); if (!"https".equalsIgnoreCase(url.getProtocol()) || !isTrustedCloud(url.getHost())) throw new IllegalArgumentException("Use GitHub ou Hugging Face por HTTPS");
            String clean = filename == null ? "aurion_resource.bin" : filename.replaceAll("[^A-Za-z0-9._-]", "_"); if (clean.isEmpty()) clean = "aurion_resource.bin";
            DownloadManager.Request request = new DownloadManager.Request(Uri.parse(raw)).setTitle("AURION · " + clean).setDescription("Recurso solicitado pelo operador").setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED).setDestinationInExternalFilesDir(this, Environment.DIRECTORY_DOWNLOADS, "AURION/RECURSOS/" + clean);
            long id = ((DownloadManager)getSystemService(DOWNLOAD_SERVICE)).enqueue(request);
            JSONObject meta = new JSONObject().put("url", raw).put("filename", clean).put("sha256Expected", expectedSha == null ? "" : expectedSha).put("downloadId", id).put("status", "solicitado");
            store.add("download", clean, raw, meta.toString()); emit("aurionDownloadResult", new JSONObject().put("ok", true).put("id", id).put("message", "Download iniciado. Verifique o hash informado ao concluir.").toString());
        } catch (Exception e) { try { emit("aurionDownloadResult", new JSONObject().put("ok", false).put("error", e.getMessage()).toString()); } catch (Exception ignored) { } }
    }

    private void chooseTrimMedia(String kind, double start, double end) {
        pendingTrimKind = "audio".equals(kind) ? "audio" : "video"; pendingTrimStart = Math.max(0, start); pendingTrimEnd = Math.max(0, end);
        Intent i = new Intent(Intent.ACTION_OPEN_DOCUMENT).setType(pendingTrimKind.equals("audio") ? "audio/*" : "video/*").addCategory(Intent.CATEGORY_OPENABLE); startActivityForResult(i, PICK_TRIM_MEDIA);
    }

    private void syncMemoryToWorkspace() {
        new Thread(() -> {
            JSONObject result = new JSONObject();
            try {
                String raw = getSharedPreferences("aurion_workspace", MODE_PRIVATE).getString("tree", ""); if (raw.isEmpty()) throw new IllegalStateException("Escolha um workspace primeiro");
                DocumentFile root = DocumentFile.fromTreeUri(this, Uri.parse(raw)); if (root == null || !root.canWrite()) throw new IllegalStateException("Workspace sem permissão de escrita");
                DocumentFile folder = root.findFile("AURION_MEMORY"); if (folder == null) folder = root.createDirectory("AURION_MEMORY"); if (folder == null) throw new IllegalStateException("Não foi possível criar AURION_MEMORY");
                String name = "aurion_memory_" + System.currentTimeMillis() + ".json"; DocumentFile file = folder.createFile("application/json", name); if (file == null) throw new IllegalStateException("Não foi possível criar backup");
                try (OutputStream out = getContentResolver().openOutputStream(file.getUri())) { out.write(store.exportAll().toString(2).getBytes(StandardCharsets.UTF_8)); }
                result.put("ok", true); result.put("message", "Memória sincronizada em AURION_MEMORY/" + name);
            } catch (Exception e) { try { result.put("ok", false); result.put("error", e.getMessage()); } catch (Exception ignored) { } }
            emit("aurionMemoryResult", result.toString());
        }).start();
    }


    private DocumentFile ensureChildDirectory(DocumentFile parent, String name) throws Exception {
        DocumentFile found = parent.findFile(name);
        if (found != null && found.isDirectory()) return found;
        DocumentFile created = parent.createDirectory(name);
        if (created == null) throw new IllegalStateException("Não foi possível criar " + name);
        return created;
    }

    private DocumentFile t8iWorkspaceRoot() throws Exception {
        String raw = getSharedPreferences("aurion_workspace", MODE_PRIVATE).getString("tree", "");
        if (raw.isEmpty()) throw new IllegalStateException("Escolha uma pasta raiz primeiro");
        DocumentFile root = DocumentFile.fromTreeUri(this, Uri.parse(raw));
        if (root == null || !root.canWrite()) throw new IllegalStateException("Workspace sem permissão de escrita");
        return ensureChildDirectory(root, "AURION_T8I");
    }

    private void chooseT8iFiles() {
        Intent i = new Intent(Intent.ACTION_OPEN_DOCUMENT).setType("*/*").addCategory(Intent.CATEGORY_OPENABLE);
        i.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, true);
        i.putExtra(Intent.EXTRA_MIME_TYPES, new String[]{"image/*","video/*","image/x-canon-cr3","application/octet-stream","application/json","text/plain"});
        startActivityForResult(i, PICK_T8I_FILES);
    }

    private void importT8iFiles(Intent data) {
        new Thread(() -> {
            JSONObject response = new JSONObject(); JSONArray entries = new JSONArray();
            try {
                java.util.ArrayList<Uri> selected = new java.util.ArrayList<>();
                if (data.getClipData() != null) for (int i = 0; i < data.getClipData().getItemCount(); i++) selected.add(data.getClipData().getItemAt(i).getUri());
                else if (data.getData() != null) selected.add(data.getData());
                int flags = data.getFlags() & Intent.FLAG_GRANT_READ_URI_PERMISSION;
                for (Uri uri : selected) {
                    if (!"content".equals(uri.getScheme())) continue;
                    try { getContentResolver().takePersistableUriPermission(uri, flags); } catch (Exception ignored) {}
                    String name = "arquivo", mime = getContentResolver().getType(uri); long size = -1;
                    try (Cursor c = getContentResolver().query(uri, new String[]{OpenableColumns.DISPLAY_NAME, OpenableColumns.SIZE}, null, null, null)) {
                        if (c != null && c.moveToFirst()) { name = c.getString(0); size = c.getLong(1); }
                    } catch (Exception ignored) {}
                    String lower = name == null ? "" : name.toLowerCase(java.util.Locale.ROOT);
                    if (!lower.matches(".*\\.(cr3|jpg|jpeg|png|tif|tiff|mp4|mov|cube|xmp|json)$")) continue;
                    JSONObject meta = new JSONObject().put("uri", uri.toString()).put("bytes", size)
                        .put("mime", mime == null ? "" : mime).put("importedAt", System.currentTimeMillis())
                        .put("originalPreserved", true);
                    long id = store.add("t8i_file", name, "Original/recurso T8i autorizado pelo operador", meta.toString());
                    entries.put(new JSONObject().put("id", id).put("name", name).put("bytes", size).put("mime", mime));
                }
                response.put("ok", true).put("files", entries).put("count", entries.length());
            } catch (Exception e) { try { response.put("ok", false).put("error", e.getMessage()); } catch (Exception ignored) {} }
            emit("aurionT8iFilesResult", response.toString());
        }).start();
    }

    private void prepareT8iWorkspace() {
        new Thread(() -> {
            JSONObject result = new JSONObject(); JSONArray folders = new JSONArray();
            try {
                DocumentFile base = t8iWorkspaceRoot();
                for (String name : new String[]{"RAW","PREVIEWS","EXPORTS","PRESETS","CONVERSAS","REFERENCIAS","LUTS","LOGS","BACKUPS"}) {
                    ensureChildDirectory(base, name); folders.put(name);
                }
                JSONObject meta = new JSONObject().put("folders", folders).put("at", System.currentTimeMillis());
                store.add("t8i_evidence", "Workspace T8i preparado", "Estrutura criada/conferida sem sobrescrever originais", meta.toString());
                result.put("ok", true).put("root", base.getName()).put("folders", folders);
            } catch (Exception e) { try { result.put("ok", false).put("error", e.getMessage()); } catch (Exception ignored) {} }
            emit("aurionT8iWorkspaceResult", result.toString());
        }).start();
    }

    private void archiveT8iOriginals() {
        new Thread(() -> {
            JSONObject result = new JSONObject(); int copied = 0, skipped = 0, failed = 0;
            try {
                DocumentFile rawDir = ensureChildDirectory(t8iWorkspaceRoot(), "RAW");
                JSONArray files = store.list("t8i_file", "", 500);
                byte[] buffer = new byte[65536];
                for (int i = 0; i < files.length(); i++) {
                    try {
                        JSONObject item = files.getJSONObject(i); JSONObject meta = new JSONObject(item.optString("meta", "{}"));
                        Uri uri = Uri.parse(meta.optString("uri")); String name = item.optString("title", "arquivo");
                        if (rawDir.findFile(name) != null) { skipped++; continue; }
                        String mime = meta.optString("mime", "application/octet-stream"); if (mime.isEmpty()) mime = "application/octet-stream";
                        DocumentFile target = rawDir.createFile(mime, name); if (target == null) throw new IllegalStateException("Destino indisponível");
                        try (InputStream in = getContentResolver().openInputStream(uri); OutputStream out = getContentResolver().openOutputStream(target.getUri())) {
                            if (in == null || out == null) throw new IllegalStateException("Arquivo sem acesso");
                            int n; while ((n = in.read(buffer)) != -1) out.write(buffer, 0, n);
                        }
                        copied++;
                    } catch (Exception one) { failed++; }
                }
                JSONObject meta = new JSONObject().put("copied", copied).put("skipped", skipped).put("failed", failed).put("at", System.currentTimeMillis());
                store.add("t8i_evidence", "Arquivamento de originais T8i", "Cópia explícita para RAW; arquivos existentes não foram sobrescritos", meta.toString());
                result.put("ok", failed == 0).put("copied", copied).put("skipped", skipped).put("failed", failed);
            } catch (Exception e) { try { result.put("ok", false).put("error", e.getMessage()); } catch (Exception ignored) {} }
            emit("aurionT8iArchiveResult", result.toString());
        }).start();
    }

    private void syncT8iWorkspace() {
        new Thread(() -> {
            JSONObject result = new JSONObject();
            try {
                DocumentFile base = t8iWorkspaceRoot(); DocumentFile backups = ensureChildDirectory(base, "BACKUPS");
                JSONObject payload = new JSONObject();
                payload.put("format", "aurion-t8i-v1").put("exportedAt", System.currentTimeMillis())
                    .put("files", store.list("t8i_file", "", 500))
                    .put("presets", store.list("t8i_preset", "", 500))
                    .put("notes", store.list("t8i_note", "", 500))
                    .put("conversations", store.list("t8i_conversation", "", 500))
                    .put("errors", store.list("t8i_error", "", 500))
                    .put("references", store.list("t8i_reference", "", 500))
                    .put("evidence", store.list("t8i_evidence", "", 500));
                String name = "t8i_backup_" + System.currentTimeMillis() + ".json";
                DocumentFile file = backups.createFile("application/json", name);
                if (file == null) throw new IllegalStateException("Não foi possível criar backup");
                try (OutputStream out = getContentResolver().openOutputStream(file.getUri())) {
                    if (out == null) throw new IllegalStateException("Destino de backup indisponível");
                    out.write(payload.toString(2).getBytes(StandardCharsets.UTF_8));
                }
                store.add("t8i_evidence", "Backup T8i", name, new JSONObject().put("uri", file.getUri().toString()).put("at", System.currentTimeMillis()).toString());
                result.put("ok", true).put("name", name).put("uri", file.getUri().toString());
            } catch (Exception e) { try { result.put("ok", false).put("error", e.getMessage()); } catch (Exception ignored) {} }
            emit("aurionT8iBackupResult", result.toString());
        }).start();
    }


    private String t8iPcBase() {
        return getSharedPreferences("aurion_nodes", MODE_PRIVATE).getString("pcStudio", "").replaceAll("/+$", "");
    }

    private String t8iPcToken() {
        return store.getSecret("dedicationPc");
    }

    private JSONObject t8iPcJson(String method, String path, String body, int readTimeoutMs) {
        JSONObject result = new JSONObject(); HttpURLConnection connection = null;
        try {
            String root = t8iPcBase(), key = t8iPcToken();
            if (root.isEmpty()) throw new IllegalStateException("Configure a URL privada do Super Studio na aba T8i.");
            if (key.isEmpty()) throw new IllegalStateException("Configure o token local do Super Studio na aba T8i.");
            URL base = new URL(root);
            if (!isAllowedPanelHost(base.getHost())) throw new IllegalArgumentException("Use IP privado, .local ou Tailscale.");
            URL url = new URL(base.getProtocol() + "://" + base.getAuthority() + path);
            connection = (HttpURLConnection) url.openConnection();
            connection.setRequestMethod(method); connection.setConnectTimeout(8000); connection.setReadTimeout(readTimeoutMs);
            connection.setUseCaches(false); connection.setRequestProperty("X-Aurion-Token", key);
            connection.setRequestProperty("Accept", "application/json");
            if (body != null) {
                connection.setDoOutput(true); connection.setRequestProperty("Content-Type", "application/json; charset=utf-8");
                try (OutputStream out = connection.getOutputStream()) { out.write(body.getBytes(StandardCharsets.UTF_8)); }
            }
            int code = connection.getResponseCode();
            InputStream input = code < 400 ? connection.getInputStream() : connection.getErrorStream();
            StringBuilder content = new StringBuilder();
            if (input != null) try (BufferedReader reader = new BufferedReader(new InputStreamReader(input, StandardCharsets.UTF_8))) {
                String line; while ((line = reader.readLine()) != null && content.length() < 1000000) content.append(line);
            }
            result.put("ok", code >= 200 && code < 300).put("http", code).put("body", content.toString());
            if (!content.toString().trim().isEmpty()) {
                try { result.put("data", new JSONObject(content.toString())); } catch (Exception ignored) {}
            }
        } catch (Exception e) {
            try { result.put("ok", false).put("error", e.getClass().getSimpleName() + ": " + e.getMessage()); } catch (Exception ignored) {}
        } finally { if (connection != null) connection.disconnect(); }
        return result;
    }

    private void t8iPcStatus() {
        new Thread(() -> emit("aurionT8iPcResult", t8iPcJson("GET", "/api/mobile/t8i/status", null, 30000).toString())).start();
    }

    private void t8iPcInstall() {
        new Thread(() -> {
            JSONObject payload = new JSONObject();
            try { payload.put("confirm", "INSTALAR_T8I"); } catch (Exception ignored) {}
            JSONObject result = t8iPcJson("POST", "/api/mobile/t8i/deps/install", payload.toString(), 900000);
            try { store.add("t8i_evidence", "Dependências T8i no PC", result.toString(), new JSONObject().put("at", System.currentTimeMillis()).toString()); } catch (Exception ignored) {}
            emit("aurionT8iPcResult", result.toString());
        }).start();
    }

    private JSONObject latestT8iCr3() throws Exception {
        JSONArray files = store.list("t8i_file", "", 500);
        for (int i = 0; i < files.length(); i++) {
            JSONObject row = files.getJSONObject(i);
            if (row.optString("title", "").toLowerCase(Locale.ROOT).endsWith(".cr3")) return row;
        }
        throw new IllegalStateException("Nenhum CR3 registrado no cofre T8i.");
    }

    private DocumentFile createUniqueDocument(DocumentFile parent, String mime, String requested) {
        String clean = requested == null || requested.trim().isEmpty() ? "AURION_T8I_" + System.currentTimeMillis() + ".jpg" : requested.replaceAll("[\\\\/:*?\"<>|]", "_");
        if (parent.findFile(clean) != null) {
            int dot = clean.lastIndexOf('.');
            String stem = dot > 0 ? clean.substring(0, dot) : clean;
            String ext = dot > 0 ? clean.substring(dot) : "";
            clean = stem + "_" + System.currentTimeMillis() + ext;
        }
        return parent.createFile(mime, clean);
    }

    private void t8iPcDevelop(double brightness, int quality) {
        final double safeBrightness = Math.max(0.10, Math.min(8.0, brightness));
        final int safeQuality = Math.max(40, Math.min(100, quality));
        new Thread(() -> {
            JSONObject finalResult = new JSONObject(); HttpURLConnection connection = null;
            try {
                JSONObject row = latestT8iCr3();
                JSONObject meta = new JSONObject(row.optString("meta", "{}"));
                Uri uri = Uri.parse(meta.optString("uri", ""));
                if (!"content".equals(uri.getScheme())) throw new IllegalStateException("URI do CR3 não está mais disponível.");
                String fileName = row.optString("title", "arquivo.cr3");

                String root = t8iPcBase(), key = t8iPcToken();
                if (root.isEmpty() || key.isEmpty()) throw new IllegalStateException("Configure URL e token do Super Studio.");
                URL base = new URL(root);
                if (!isAllowedPanelHost(base.getHost())) throw new IllegalArgumentException("Use IP privado, .local ou Tailscale.");
                URL endpoint = new URL(base.getProtocol() + "://" + base.getAuthority() + "/api/t8i/develop");

                String boundary = "----AurionT8i" + System.currentTimeMillis();
                connection = (HttpURLConnection) endpoint.openConnection();
                connection.setRequestMethod("POST"); connection.setDoOutput(true);
                connection.setConnectTimeout(10000); connection.setReadTimeout(240000);
                connection.setRequestProperty("X-Aurion-Token", key);
                connection.setRequestProperty("Content-Type", "multipart/form-data; boundary=" + boundary);

                try (DataOutputStream out = new DataOutputStream(connection.getOutputStream())) {
                    JSONObject params = new JSONObject().put("brightness", safeBrightness).put("quality", safeQuality);
                    out.writeBytes("--" + boundary + "\r\n");
                    out.writeBytes("Content-Disposition: form-data; name=\"params\"\r\n\r\n");
                    out.write(params.toString().getBytes(StandardCharsets.UTF_8)); out.writeBytes("\r\n");
                    out.writeBytes("--" + boundary + "\r\n");
                    out.writeBytes("Content-Disposition: form-data; name=\"file\"; filename=\"" + fileName.replace("\"", "_") + "\"\r\n");
                    out.writeBytes("Content-Type: application/octet-stream\r\n\r\n");
                    try (InputStream in = getContentResolver().openInputStream(uri)) {
                        if (in == null) throw new IllegalStateException("Não foi possível ler o CR3.");
                        byte[] buffer = new byte[262144]; int n; long total = 0;
                        while ((n = in.read(buffer)) != -1) {
                            total += n; if (total > 2L * 1024 * 1024 * 1024) throw new IllegalStateException("CR3 excede limite de 2 GB.");
                            out.write(buffer, 0, n);
                        }
                    }
                    out.writeBytes("\r\n--" + boundary + "--\r\n"); out.flush();
                }

                int code = connection.getResponseCode();
                InputStream responseStream = code < 400 ? connection.getInputStream() : connection.getErrorStream();
                StringBuilder responseText = new StringBuilder();
                if (responseStream != null) try (BufferedReader br = new BufferedReader(new InputStreamReader(responseStream, StandardCharsets.UTF_8))) {
                    String line; while ((line = br.readLine()) != null && responseText.length() < 1000000) responseText.append(line);
                }
                if (code < 200 || code >= 300) throw new IllegalStateException("Revelação HTTP " + code + ": " + responseText);
                JSONObject response = new JSONObject(responseText.toString());
                String downloadName = response.optString("download_name", "");
                if (downloadName.isEmpty() && response.optJSONObject("result") != null) {
                    String p = response.getJSONObject("result").optString("path", "");
                    if (!p.isEmpty()) downloadName = new File(p).getName();
                }
                if (downloadName.isEmpty()) throw new IllegalStateException("PC concluiu sem nome de exportação.");

                String encoded = URLEncoder.encode(downloadName, "UTF-8").replace("+", "%20");
                HttpURLConnection dl = (HttpURLConnection)new URL(base.getProtocol() + "://" + base.getAuthority() + "/api/mobile/t8i/export/" + encoded).openConnection();
                dl.setConnectTimeout(8000); dl.setReadTimeout(120000); dl.setRequestProperty("X-Aurion-Token", key);
                int dcode = dl.getResponseCode();
                if (dcode < 200 || dcode >= 300) {
                    String err = "";
                    InputStream ein = dl.getErrorStream();
                    if (ein != null) try (BufferedReader br = new BufferedReader(new InputStreamReader(ein, StandardCharsets.UTF_8))) { err = br.readLine(); }
                    dl.disconnect();
                    throw new IllegalStateException("Download do JPEG HTTP " + dcode + (err == null ? "" : ": " + err));
                }

                DocumentFile exports = ensureChildDirectory(t8iWorkspaceRoot(), "EXPORTS");
                DocumentFile target = createUniqueDocument(exports, "image/jpeg", downloadName);
                if (target == null) { dl.disconnect(); throw new IllegalStateException("Não foi possível criar o JPEG em EXPORTS."); }
                long bytes = 0;
                try (InputStream in = dl.getInputStream(); OutputStream out = getContentResolver().openOutputStream(target.getUri())) {
                    if (out == null) throw new IllegalStateException("Destino EXPORTS sem escrita.");
                    byte[] buffer = new byte[65536]; int n;
                    while ((n = in.read(buffer)) != -1) { bytes += n; out.write(buffer, 0, n); }
                } finally { dl.disconnect(); }
                if (bytes <= 0) throw new IllegalStateException("JPEG retornou vazio.");

                JSONObject evidence = new JSONObject().put("source", fileName).put("output", target.getUri().toString())
                    .put("bytes", bytes).put("brightness", safeBrightness).put("quality", safeQuality)
                    .put("pc", base.getAuthority()).put("at", System.currentTimeMillis());
                store.add("t8i_evidence", "CR3 revelado no PC · " + fileName, response.toString(), evidence.toString());
                finalResult.put("ok", true).put("source", fileName).put("outputName", target.getName()).put("bytes", bytes)
                    .put("outputUri", target.getUri().toString()).put("pcResponse", response);
            } catch (Exception e) {
                try { finalResult.put("ok", false).put("error", e.getClass().getSimpleName() + ": " + e.getMessage()); } catch (Exception ignored) {}
                try { store.add("t8i_error", "Falha revelação T8i PC", finalResult.toString(), new JSONObject().put("at", System.currentTimeMillis()).toString()); } catch (Exception ignored) {}
            } finally { if (connection != null) connection.disconnect(); }
            emit("aurionT8iPcResult", finalResult.toString());
        }).start();
    }

    private void shareText(String title, String text) {
        runOnUiThread(() -> {
            Intent send = new Intent(Intent.ACTION_SEND).setType("text/plain").putExtra(Intent.EXTRA_SUBJECT, title).putExtra(Intent.EXTRA_TEXT, text);
            startActivity(Intent.createChooser(send, "Compartilhar com cliente"));
        });
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
                case "update": i = new Intent("android.settings.SYSTEM_UPDATE_SETTINGS"); break;
                case "app": i = new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.parse("package:" + getPackageName())); break;
                case "health": i = new Intent("android.health.connect.action.HEALTH_HOME_SETTINGS"); break;
                default: i = new Intent(Settings.ACTION_SETTINGS);
            }
            try { startActivity(i); } catch (Exception e) { startActivity(new Intent(Settings.ACTION_SETTINGS)); }
        });
    }

    private void scheduleHourlySync() {
        Constraints constraints = new Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build();
        PeriodicWorkRequest request = new PeriodicWorkRequest.Builder(AurionHourlyWorker.class, 1, TimeUnit.HOURS, 15, TimeUnit.MINUTES)
            .setConstraints(constraints).build();
        WorkManager.getInstance(this).enqueueUniquePeriodicWork("aurion-hourly-sync", ExistingPeriodicWorkPolicy.UPDATE, request);
    }

    private void runHourlySyncNow() {
        Constraints constraints = new Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build();
        OneTimeWorkRequest request = new OneTimeWorkRequest.Builder(AurionHourlyWorker.class).setConstraints(constraints).build();
        WorkManager.getInstance(this).enqueue(request);
        try { store.add("sync_event", "Auto busca solicitada", "Git/Drive/Hug/PC serão conferidos em segundo plano.", new JSONObject().put("at", System.currentTimeMillis()).toString()); }
        catch (Exception ignored) {}
        toast("Auto busca enviada. Resultado em Portfólio / Sync.");
    }

    private void saveNodeSettings(String panel, String agent, String token, String comfy, String ollama) {
        getSharedPreferences("aurion_nodes", MODE_PRIVATE).edit()
            .putString("panel", panel == null ? "" : panel)
            .putString("agent", agent == null ? "" : agent)
            .putString("comfy", comfy == null ? "" : comfy)
            .putString("ollama", ollama == null ? "" : ollama).apply();
        if (token != null && !token.trim().isEmpty()) try { store.setSecret("homeNode", token.trim()); } catch (Exception ignored) {}
    }

    private void savePcStudio(String base, String token) {
        getSharedPreferences("aurion_nodes", MODE_PRIVATE).edit().putString("pcStudio", base == null ? "" : base).apply();
        if (token != null && !token.trim().isEmpty()) try { store.setSecret("dedicationPc", token.trim()); } catch (Exception ignored) {}
    }

    private void updateEvent(String state, String message, String version) {
        try { emit("aurionUpdateStatus", new JSONObject().put("state", state).put("message", message).put("version", version).toString()); }
        catch (Exception ignored) { }
    }

    private void checkForUpdate() {
        if (getPackageName().endsWith(".preview")) {
            updateEvent("current", "Prévia separada: atualizações da instalação principal não se aplicam aqui.", "7.0.0-preview");
            return;
        }
        new Thread(() -> {
            try {
                JSONObject response = cloudJson("GET", UPDATE_MANIFEST, "", "", null);
                if (!response.optBoolean("ok")) throw new IllegalStateException("Canal indisponível");
                JSONObject m = new JSONObject(response.getString("body"));
                int current = getPackageManager().getPackageInfo(getPackageName(), 0).versionCode;
                int next = m.getInt("versionCode");
                String url = m.getString("apkUrl"), hash = m.getString("sha256");
                if (next <= current) {
                    String currentName = getPackageManager().getPackageInfo(getPackageName(), 0).versionName;
                    updateEvent("current", "Versão atual. Nenhuma instalação necessária.", currentName == null ? String.valueOf(current) : currentName);
                    return;
                }
                if (!url.startsWith("https://raw.githubusercontent.com/cleitongoy-debug/AURION-ONE/main/android/updates/")
                    || !url.endsWith(".apk") || !hash.matches("[a-fA-F0-9]{64}"))
                    throw new IllegalArgumentException("Publicação sem URL ou checksum válido");
                availableUpdate = m;
                updateEvent("available", "Versão " + m.optString("versionName") + " disponível: " + m.optString("notes", "Correções e recursos."), m.optString("versionName"));
            } catch (Exception e) { updateEvent("error", "Não foi possível conferir atualizações: " + e.getMessage(), ""); }
        }).start();
    }

    private void installAvailableUpdate() {
        JSONObject m = availableUpdate;
        if (m == null) { checkForUpdate(); return; }
        new Thread(() -> {
            File temp = new File(new File(getCacheDir(), "updates"), "aurion-update.apk");
            try {
                temp.getParentFile().mkdirs();
                URL url = new URL(m.getString("apkUrl"));
                HttpURLConnection connection = (HttpURLConnection) url.openConnection();
                connection.setConnectTimeout(15000); connection.setReadTimeout(60000);
                connection.setInstanceFollowRedirects(false);
                if (connection.getResponseCode() != 200) throw new IllegalStateException("Download HTTP " + connection.getResponseCode());
                MessageDigest sha = MessageDigest.getInstance("SHA-256");
                long count = 0;
                try (InputStream in = connection.getInputStream(); FileOutputStream out = new FileOutputStream(temp)) {
                    byte[] buffer = new byte[32768]; int n;
                    while ((n = in.read(buffer)) != -1) {
                        count += n; if (count > 100L * 1024 * 1024) throw new IllegalStateException("APK excede 100 MB");
                        out.write(buffer, 0, n); sha.update(buffer, 0, n);
                    }
                } finally { connection.disconnect(); }
                StringBuilder digest = new StringBuilder();
                for (byte b : sha.digest()) digest.append(String.format(Locale.ROOT, "%02x", b & 255));
                if (!digest.toString().equalsIgnoreCase(m.getString("sha256"))) throw new SecurityException("Checksum do APK diferente da publicação");
                PackageInfo archive = getPackageManager().getPackageArchiveInfo(temp.getAbsolutePath(), PackageManager.GET_SIGNING_CERTIFICATES);
                PackageInfo installed = getPackageManager().getPackageInfo(getPackageName(), PackageManager.GET_SIGNING_CERTIFICATES);
                if (archive == null || !getPackageName().equals(archive.packageName) || archive.versionCode != m.getInt("versionCode")
                    || archive.versionCode <= installed.versionCode || archive.signingInfo == null || installed.signingInfo == null
                    || !MessageDigest.isEqual(archive.signingInfo.getApkContentsSigners()[0].toByteArray(),
                                              installed.signingInfo.getApkContentsSigners()[0].toByteArray()))
                    throw new SecurityException("Pacote, versão ou assinatura incompatível");
                updateEvent("ready", "APK conferido. Confirme a instalação na tela do Android.", m.optString("versionName"));
                runOnUiThread(() -> {
                    if (Build.VERSION.SDK_INT >= 26 && !getPackageManager().canRequestPackageInstalls()) {
                        updateEvent("permission", "Autorize atualizações deste app e toque em INSTALAR novamente.", m.optString("versionName"));
                        startActivity(new Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES, Uri.parse("package:" + getPackageName())));
                        return;
                    }
                    Uri content = FileProvider.getUriForFile(this, getPackageName() + ".updates", temp);
                    Intent intent = new Intent(Intent.ACTION_VIEW).setDataAndType(content, "application/vnd.android.package-archive")
                        .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_ACTIVITY_NEW_TASK);
                    startActivity(intent);
                });
            } catch (Exception e) { updateEvent("error", "Atualização não instalada: " + e.getMessage(), ""); }
        }).start();
    }

    private void generateImage(String prompt, String model) {
        new Thread(() -> {
            JSONObject result = new JSONObject();
            HttpURLConnection connection = null;
            try {
                String key = store.getSecret("huggingface");
                if (key.isEmpty()) throw new IllegalStateException("Importe uma chave Hugging Face com permissão Inference Providers");
                if (prompt == null || prompt.trim().isEmpty()) throw new IllegalArgumentException("Escreva um prompt");
                String selected = model == null || model.trim().isEmpty() ? "stabilityai/stable-diffusion-3-medium-diffusers" : model.trim();
                if (!selected.matches("[A-Za-z0-9._-]+/[A-Za-z0-9._-]+")) throw new IllegalArgumentException("Modelo deve ser autor/nome");
                URL url = new URL("https://router.huggingface.co/hf-inference/models/" + selected);
                connection = (HttpURLConnection) url.openConnection();
                connection.setRequestMethod("POST"); connection.setDoOutput(true);
                connection.setConnectTimeout(15000); connection.setReadTimeout(120000);
                connection.setRequestProperty("Authorization", "Bearer " + key);
                connection.setRequestProperty("Content-Type", "application/json");
                byte[] body = new JSONObject().put("inputs", prompt.trim()).toString().getBytes(StandardCharsets.UTF_8);
                try (OutputStream out = connection.getOutputStream()) { out.write(body); }
                int code = connection.getResponseCode();
                if (code < 200 || code >= 300) {
                    StringBuilder error = new StringBuilder();
                    try (InputStream in = connection.getErrorStream()) {
                        if (in != null) { byte[] b = new byte[2048]; int n = in.read(b); if (n > 0) error.append(new String(b, 0, n, StandardCharsets.UTF_8)); }
                    }
                    throw new IllegalStateException("HTTP " + code + ": " + error.toString().replaceAll("(?i)hf_[A-Za-z0-9]+", "[chave oculta]"));
                }
                String type = connection.getContentType();
                if (type == null || !type.toLowerCase(Locale.ROOT).startsWith("image/")) throw new IllegalStateException("Provedor não retornou imagem");
                String ext = type.contains("png") ? "png" : "jpg";
                ContentValues values = new ContentValues();
                values.put(MediaStore.Images.Media.DISPLAY_NAME, "AURION-" + System.currentTimeMillis() + "." + ext);
                values.put(MediaStore.Images.Media.MIME_TYPE, ext.equals("png") ? "image/png" : "image/jpeg");
                values.put(MediaStore.Images.Media.RELATIVE_PATH, "Pictures/AURION/GERADAS");
                Uri uri = getContentResolver().insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values);
                if (uri == null) throw new IllegalStateException("Galeria indisponível");
                long count = 0;
                try (InputStream in = connection.getInputStream(); OutputStream out = getContentResolver().openOutputStream(uri)) {
                    if (out == null) throw new IllegalStateException("Não foi possível salvar");
                    byte[] b = new byte[32768]; int n;
                    while ((n = in.read(b)) != -1) { count += n; if (count > 25L * 1024 * 1024) throw new IllegalStateException("Imagem excede 25 MB"); out.write(b, 0, n); }
                }
                if (count < 1000) { getContentResolver().delete(uri, null, null); throw new IllegalStateException("Resposta de imagem vazia"); }
                result.put("ok", true).put("model", selected).put("uri", uri.toString()).put("bytes", count);
                store.add("evidence", "Imagem gerada · " + selected, prompt, new JSONObject().put("uri", uri.toString()).put("bytes", count).toString());
            } catch (Exception e) { try { result.put("ok", false).put("error", e.getMessage()); } catch (Exception ignored) { } }
            finally { if (connection != null) connection.disconnect(); }
            emit("aurionImageResult", result.toString());
        }).start();
    }

    public final class ProfileBridge {
        @JavascriptInterface public String status() { return profiles.status().toString(); }
        @JavascriptInterface public String bootstrap(String id, String pin) {
            JSONObject result = profiles.bootstrap(id, pin);
            if (result.optBoolean("ok")) {
                if (!"anark".equals(id)) store.claimLegacy(id);
                store.setProfile(id);
            }
            return result.toString();
        }
        @JavascriptInterface public String login(String id, String pin) {
            JSONObject result = profiles.login(id, pin);
            if (result.optBoolean("ok")) store.setProfile(id);
            return result.toString();
        }
        @JavascriptInterface public void enter() { if (profiles.signedIn()) runOnUiThread(() -> { if (profiles.owner()) { scheduleHourlySync(); handler.postDelayed(MainActivity.this::checkForUpdate, 1800); } web.loadUrl("file:///android_asset/index.html"); }); }
        @JavascriptInterface public void logout() {
            profiles.logout(); store.setProfile("anark");
            runOnUiThread(() -> { WorkManager.getInstance(MainActivity.this).cancelUniqueWork("aurion-hourly-sync"); web.removeJavascriptInterface("AurionAndroid"); web.loadUrl("file:///android_asset/profiles.html"); });
        }
        @JavascriptInterface public String provision(String id, String pin, String tabs) { return profiles.provision(id, pin, tabs).toString(); }
        @JavascriptInterface public String grant(String id, String tabs) { return profiles.grant(id, tabs).toString(); }
    }

    /** Explicit allowlist: member pages cannot invoke PC, vault, updater or owner's cloud routes. */
    public final class MemberBridge {
        @JavascriptInterface public long memoryAdd(String type, String title, String body, String meta) {
            return profiles.allowed("memory") || profiles.allowed("portfolio") || profiles.allowed("project") || profiles.allowed("dedication") ? store.add(type, title, body, meta) : -1;
        }
        @JavascriptInterface public String memoryList(String type, String query, int limit) { return profiles.signedIn() ? store.list(type, query, limit).toString() : "[]"; }
        @JavascriptInterface public boolean memoryDelete(long id) { return profiles.allowed("memory") && store.remove(id); }
        @JavascriptInterface public String memoryExport() { return profiles.signedIn() ? store.exportAll().toString() : "{}"; }
        @JavascriptInterface public String getDiagnostics() { return diagnostics().toString(); }
        @JavascriptInterface public String accountStatus() { return "{}"; }
        @JavascriptInterface public void shareProject(String title, String body) { if (profiles.allowed("portfolio") || profiles.allowed("delivery")) shareText(title, body); }
        @JavascriptInterface public void openExternal(String raw) { if (profiles.signedIn()) bridge.openExternal(raw); }
        @JavascriptInterface public void speakText(String text) { if (profiles.allowed("agent")) bridge.speakText(text); }
        @JavascriptInterface public void listenVoice() { if (profiles.allowed("agent")) bridge.listenVoice(); }
    }

    public final class Bridge {
        @JavascriptInterface public String profileInspect(String id) { return profiles.owner() ? store.inspectProfile(id).toString() : "[]"; }
        @JavascriptInterface public void runHourlySyncNow() { MainActivity.this.runHourlySyncNow(); }
        @JavascriptInterface public void saveNodeSettings(String panel, String agent, String token, String comfy, String ollama) { MainActivity.this.saveNodeSettings(panel, agent, token, comfy, ollama); }
        @JavascriptInterface public void savePcStudio(String base, String token) { MainActivity.this.savePcStudio(base, token); }
        @JavascriptInterface public void checkForUpdate() { MainActivity.this.checkForUpdate(); }
        @JavascriptInterface public void installAvailableUpdate() { MainActivity.this.installAvailableUpdate(); }
        @JavascriptInterface public void generateImage(String prompt, String model) { MainActivity.this.generateImage(prompt, model); }
        @JavascriptInterface public void speakText(String text) { runOnUiThread(() -> { if (speech != null) speech.speak(text == null ? "" : text.substring(0, Math.min(text.length(), 3000)), TextToSpeech.QUEUE_FLUSH, null, "aurion-response"); }); }
        @JavascriptInterface public void listenVoice() { runOnUiThread(() -> { try { Intent intent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM).putExtra(RecognizerIntent.EXTRA_LANGUAGE, "pt-BR"); startActivityForResult(intent, VOICE_INPUT); } catch (Exception e) { toast("Ditado não disponível neste aparelho"); } }); }
        @JavascriptInterface public String getDiagnostics() { return diagnostics().toString(); }
        @JavascriptInterface public void refreshDiagnostics() { emit("aurionDiagnostics", diagnostics().toString()); }
        @JavascriptInterface public void openPanel(String raw) { runOnUiThread(() -> { try { Uri u = Uri.parse(raw); if (!isAllowedPanelHost(u.getHost())) throw new IllegalArgumentException(); web.loadUrl(raw); } catch (Exception e) { toast("Use IP local ou endereço Tailscale do PC"); } }); }
        @JavascriptInterface public void testPanel(String raw) { MainActivity.this.testPanel(raw); }
        @JavascriptInterface public void probePcStack(String base, String token, String comfy, String ollama) { MainActivity.this.probePcStack(base, token, comfy, ollama); }
        @JavascriptInterface public void syncDedication(String base, String json) { MainActivity.this.syncDedication(base, json); }
        @JavascriptInterface public void chooseCertificate(String course, String project, String hours) { runOnUiThread(() -> {
            pendingCertificateCourse = course; pendingCertificateProject = project; pendingCertificateHours = hours;
            Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT).setType("*/*").addCategory(Intent.CATEGORY_OPENABLE)
                .putExtra(Intent.EXTRA_MIME_TYPES, new String[]{"application/pdf", "image/png", "image/jpeg", "image/webp"});
            startActivityForResult(intent, PICK_CERTIFICATE);
        }); }
        @JavascriptInterface public void syncCertificate(String base, String uri, String name, String course, String project, String hours) { MainActivity.this.syncCertificate(base, uri, name, course, project, hours); }
        @JavascriptInterface public void openCertificate(long id) { runOnUiThread(() -> {
            try {
                JSONArray entries = store.list("certificate", "", 500);
                for (int i = 0; i < entries.length(); i++) {
                    JSONObject row = entries.getJSONObject(i);
                    if (row.optLong("id") != id) continue;
                    JSONObject meta = new JSONObject(row.optString("meta"));
                    Uri uri = Uri.parse(meta.optString("uri"));
                    if (!"content".equals(uri.getScheme())) break;
                    String mime = meta.optString("mime", "application/octet-stream");
                    startActivity(new Intent(Intent.ACTION_VIEW).setDataAndType(uri, mime).addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION));
                    return;
                }
            } catch (Exception e) { toast("Falha ao abrir prova: " + e.getClass().getSimpleName()); return; }
            toast("Prova indisponível neste aparelho");
        }); }
        @JavascriptInterface public void chooseClientPhotos() { runOnUiThread(() -> {
            Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT).setType("image/*").addCategory(Intent.CATEGORY_OPENABLE);
            intent.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, true);
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
            startActivityForResult(intent, PICK_CLIENT_PHOTOS);
        }); }
        @JavascriptInterface public void openClientPhoto(long id) { runOnUiThread(() -> MainActivity.this.openClientPhoto(id)); }
        @JavascriptInterface public void testService(String label, String raw) { new Thread(() -> emit("aurionServiceResult", new JSONObjectResult(label, httpJson("GET", raw, "", null)).toString())).start(); }
        @JavascriptInterface public void sendAgent(String base, String token, String text) { new Thread(() -> {
            try { JSONObject body = new JSONObject(); body.put("text", text); body.put("device_id", "poco-aurion-final"); body.put("moving", false); emit("aurionAgentResult", httpJson("POST", new URL(new URL(base), "/api/prompt").toString(), token, body.toString()).toString()); }
            catch (Exception e) { emit("aurionAgentResult", "{\"ok\":false,\"error\":\"Endereço inválido\"}"); }
        }).start(); }
        @JavascriptInterface public void queueComfy(String base, String workflow) { new Thread(() -> {
            try { JSONObject parsed = new JSONObject(workflow); JSONObject body = parsed.has("prompt") ? parsed : new JSONObject().put("prompt", parsed); emit("aurionComfyResult", httpJson("POST", new URL(new URL(base), "/prompt").toString(), "", body.toString()).toString()); }
            catch (Exception e) { emit("aurionComfyResult", "{\"ok\":false,\"error\":\"Workflow JSON inválido\"}"); }
        }).start(); }
        @JavascriptInterface public void chooseT8iFiles() { runOnUiThread(MainActivity.this::chooseT8iFiles); }
        @JavascriptInterface public void t8iPcStatus() { MainActivity.this.t8iPcStatus(); }
        @JavascriptInterface public void t8iPcInstall() { MainActivity.this.t8iPcInstall(); }
        @JavascriptInterface public void t8iPcDevelop(double brightness, int quality) { MainActivity.this.t8iPcDevelop(brightness, quality); }
        @JavascriptInterface public void prepareT8iWorkspace() { MainActivity.this.prepareT8iWorkspace(); }
        @JavascriptInterface public void archiveT8iOriginals() { MainActivity.this.archiveT8iOriginals(); }
        @JavascriptInterface public void syncT8iWorkspace() { MainActivity.this.syncT8iWorkspace(); }
        @JavascriptInterface public void chooseWorkspace() { runOnUiThread(MainActivity.this::chooseWorkspace); }
        @JavascriptInterface public void capturePhoto() { runOnUiThread(MainActivity.this::capturePhoto); }
        @JavascriptInterface public void convertImage(String format, int quality) { runOnUiThread(() -> chooseImageForConversion(format, quality)); }
        @JavascriptInterface public void saveEditedImage(String format, int quality, String dataUrl) { new Thread(() -> emit("aurionEditorResult", MediaTools.saveDataImage(MainActivity.this, format, quality, dataUrl).toString())).start(); }
        @JavascriptInterface public void saveBase64File(String filename, String mime, String base64) { new Thread(() -> emit("aurionFileResult", MediaTools.saveBase64File(MainActivity.this, filename, mime, base64).toString())).start(); }
        @JavascriptInterface public void trimMedia(String kind, double start, double end) { runOnUiThread(() -> chooseTrimMedia(kind, start, end)); }
        @JavascriptInterface public long memoryAdd(String type, String title, String body, String meta) { try { return store.add(type, title, body, meta); } catch (Exception e) { return -1; } }
        @JavascriptInterface public String memoryList(String type, String query, int limit) { return store.list(type, query, limit).toString(); }
        @JavascriptInterface public boolean memoryDelete(long id) { return store.remove(id); }
        @JavascriptInterface public String memoryExport() { return store.exportAll().toString(); }
        @JavascriptInterface public void memorySync() { syncMemoryToWorkspace(); }
        @JavascriptInterface public void importKeysJson(String raw) { new Thread(() -> emit("aurionKeysResult", MainActivity.this.importKeysRaw(raw).toString())).start(); }
        @JavascriptInterface public void importKeyFile() { runOnUiThread(() -> startActivityForResult(new Intent(Intent.ACTION_OPEN_DOCUMENT).setType("*/*").addCategory(Intent.CATEGORY_OPENABLE).putExtra(Intent.EXTRA_MIME_TYPES, new String[]{"application/json", "text/plain"}), PICK_KEYS_IMPORT)); }
        @JavascriptInterface public void syncGitContext() { MainActivity.this.syncGitContext(); }
        @JavascriptInterface public void importContextFile() { runOnUiThread(() -> startActivityForResult(new Intent(Intent.ACTION_OPEN_DOCUMENT).setType("*/*").addCategory(Intent.CATEGORY_OPENABLE).putExtra(Intent.EXTRA_MIME_TYPES, new String[]{"text/plain", "text/markdown", "application/json"}), PICK_CONTEXT_IMPORT)); }
        @JavascriptInterface public void memoryImport() { runOnUiThread(() -> startActivityForResult(new Intent(Intent.ACTION_OPEN_DOCUMENT).setType("application/json").addCategory(Intent.CATEGORY_OPENABLE), PICK_MEMORY_IMPORT)); }
        @JavascriptInterface public void setSecret(String service, String value) { try { store.setSecret(service, value == null ? "" : value.trim()); emit("aurionVaultResult", new JSONObject().put("ok", true).put("service", service).toString()); } catch (Exception e) { try { emit("aurionVaultResult", new JSONObject().put("ok", false).put("service", service).put("error", e.getMessage()).toString()); } catch (Exception ignored) { } } }
        @JavascriptInterface public String accountStatus() { return store.accountStatus().toString(); }
        @JavascriptInterface public void testAccount(String service) { MainActivity.this.testAccount(service); }
        @JavascriptInterface public void runCloudAi(String provider, String model, String prompt, String memory) { MainActivity.this.runCloudAi(provider, model, prompt, memory); }
        @JavascriptInterface public void downloadResource(String url, String filename, String sha256) { runOnUiThread(() -> MainActivity.this.downloadResource(url, filename, sha256)); }
        @JavascriptInterface public void shareProject(String title, String text) { shareText(title, text); }
        @JavascriptInterface public void openExternal(String raw) { runOnUiThread(() -> { try { Uri u = Uri.parse(raw); String s = u.getScheme(); if (!("http".equals(s) || "https".equals(s) || "mailto".equals(s) || "tel".equals(s))) throw new IllegalArgumentException(); startActivity(new Intent(Intent.ACTION_VIEW, u)); } catch (Exception e) { toast("Endereço externo inválido"); } }); }
        @JavascriptInterface public void scanBand() { runOnUiThread(MainActivity.this::requestBluetoothOrScan); }
        @JavascriptInterface public void notifyBand() { runOnUiThread(() -> BandNotificationTest.requestOrSend(MainActivity.this)); }
        @JavascriptInterface public String bandChannelStatus() {
            return AurionBandChannel.status(MainActivity.this).toString();
        }
        @JavascriptInterface public void bandChannelEnable(boolean enabled) {
            runOnUiThread(() -> {
                if (enabled && !AurionBandChannel.hasPermission(MainActivity.this)
                    && Build.VERSION.SDK_INT >= 33) {
                    bandPermissionEnablePending = true;
                    requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS},
                            AurionBandChannel.REQUEST_PERMISSION);
                    return;
                }
                emit("aurionBandChannelResult", AurionBandChannel.setEnabled(MainActivity.this, enabled).toString());
            });
        }
        @JavascriptInterface public void bandChannelTest() {
            runOnUiThread(() -> emit("aurionBandChannelResult",
                    AurionBandChannel.sendManualTest(MainActivity.this).toString()));
        }
        @JavascriptInterface public String bandChannelConfirmReceipt() {
            return AurionBandChannel.confirmOperatorReceipt(MainActivity.this).toString();
        }
        @JavascriptInterface public void openMiFitness() { openPackage("com.xiaomi.wearable", "https://play.google.com/store/apps/details?id=com.xiaomi.wearable"); }
        @JavascriptInterface public void openNotifyPro() {
            runOnUiThread(() -> {
                try {
                    Intent launch = getPackageManager().getLaunchIntentForPackage("com.mc.xiaomi1");
                    if (launch != null) startActivity(launch);
                    else toast("Notify Pro não identificado no POCO. Nada será instalado automaticamente.");
                } catch (Exception e) { toast("Não foi possível abrir Notify Pro."); }
            });
        }
        @JavascriptInterface public void openTermux() { openPackage("com.termux", "https://github.com/termux/termux-app"); }
        @JavascriptInterface public void openTailscale() { openPackage("com.tailscale.ipn", "https://play.google.com/store/apps/details?id=com.tailscale.ipn"); }
        @JavascriptInterface public void openSetting(String key) { MainActivity.this.openSetting(key); }
        @JavascriptInterface public void copyTermuxBootstrap() {
            String script = "pkg update && pkg install -y python git curl openssh && mkdir -p \\\"$HOME/aurion-mobile\\\"/{logs,backups,media} && python --version && git --version";
            ClipboardManager cm = (ClipboardManager) getSystemService(CLIPBOARD_SERVICE); cm.setPrimaryClip(ClipData.newPlainText("AURION Termux", script)); toast("Comando copiado. Revise e execute manualmente no Termux.");
        }
        @JavascriptInterface public void copyText(String label, String text) { ClipboardManager cm = (ClipboardManager) getSystemService(CLIPBOARD_SERVICE); cm.setPrimaryClip(ClipData.newPlainText(label == null ? "AURION" : label, text == null ? "" : text)); toast("Copiado. Revise antes de executar."); }
        @JavascriptInterface public void exportBackup(String json) {
            pendingBackup = json;
            runOnUiThread(() -> {
                Intent i = new Intent(Intent.ACTION_CREATE_DOCUMENT).setType("application/json").putExtra(Intent.EXTRA_TITLE, "aurion-mobile-backup.json");
                startActivityForResult(i, CREATE_BACKUP);
            });
        }
        @JavascriptInterface public void appInfo() { runOnUiThread(() -> new AlertDialog.Builder(MainActivity.this).setTitle("AURION ONE Super Studio").setMessage("Versão 7.0.0\nPerfis locais, dados separados e permissões do titular.").setPositiveButton("OK", null).show()); }
    }

    private static final class JSONObjectResult {
        private final JSONObject value = new JSONObject();
        JSONObjectResult(String label, JSONObject result) { try { value.put("label", label); value.put("result", result); } catch (Exception ignored) {} }
        @Override public String toString() { return value.toString(); }
    }

    @Override protected void onActivityResult(int request, int result, Intent data) {
        super.onActivityResult(request, result, data);
        if (request == VOICE_INPUT && result == RESULT_OK && data != null) {
            java.util.ArrayList<String> heard = data.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS);
            if (heard != null && !heard.isEmpty()) emit("aurionVoiceResult", heard.get(0));
        }
        if (request == PICK_FILE && selectedFiles != null) { selectedFiles.onReceiveValue(WebChromeClient.FileChooserParams.parseResult(result, data)); selectedFiles = null; }
        if (request == PICK_CLIENT_PHOTOS && result == RESULT_OK && data != null) importClientPhotos(data);
        if (request == PICK_CERTIFICATE && result == RESULT_OK && data != null) importCertificate(data);
        if (request == CREATE_BACKUP && result == RESULT_OK && data != null && data.getData() != null) {
            try (OutputStream out = getContentResolver().openOutputStream(data.getData())) { if (out != null) out.write(pendingBackup.getBytes(StandardCharsets.UTF_8)); toast("Backup salvo no local escolhido"); }
            catch (Exception e) { toast("Falha ao salvar backup: " + e.getClass().getSimpleName()); }
            pendingBackup = "";
        }
        if (request == PICK_WORKSPACE && result == RESULT_OK && data != null && data.getData() != null) {
            Uri uri = data.getData();
            try { getContentResolver().takePersistableUriPermission(uri, data.getFlags() & (Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION)); } catch (Exception ignored) {}
            getSharedPreferences("aurion_workspace", MODE_PRIVATE).edit().putString("tree", uri.toString()).apply();
            emit("aurionWorkspaceResult", uri.toString());
        }
        if (request == PICK_CONVERT_IMAGE && result == RESULT_OK && data != null && data.getData() != null) convertImage(data.getData());
        if (request == CAPTURE_PHOTO) {
            if (result == RESULT_OK && pendingCameraUri != null) emit("aurionCaptureResult", pendingCameraUri.toString());
            else if (pendingCameraUri != null) { try { getContentResolver().delete(pendingCameraUri, null, null); } catch (Exception ignored) {} }
            pendingCameraUri = null;
        }
        if (request == PICK_TRIM_MEDIA && result == RESULT_OK && data != null && data.getData() != null) {
            Uri uri = data.getData(); new Thread(() -> emit("aurionTrimResult", MediaTools.trim(this, uri, pendingTrimKind, pendingTrimStart, pendingTrimEnd).toString())).start();
        }
        if (request == PICK_KEYS_IMPORT && result == RESULT_OK && data != null && data.getData() != null) {
            Uri chosen = data.getData(); new Thread(() -> {
                JSONObject imported;
                try (InputStream in = getContentResolver().openInputStream(chosen); BufferedReader br = new BufferedReader(new InputStreamReader(in, StandardCharsets.UTF_8))) {
                    StringBuilder raw = new StringBuilder(); String line;
                    while ((line = br.readLine()) != null) { raw.append(line).append('\n'); if (raw.length() > 262144) throw new IllegalArgumentException("Arquivo de chaves maior que 256 KB"); }
                    imported = importKeysRaw(raw.toString());
                } catch (Exception e) { imported = new JSONObject(); try { imported.put("ok", false).put("error", e.getMessage()); } catch (Exception ignored) {} }
                emit("aurionKeysResult", imported.toString());
            }).start();
        }
        if (request == PICK_CONTEXT_IMPORT && result == RESULT_OK && data != null && data.getData() != null) {
            Uri chosen = data.getData(); new Thread(() -> {
                JSONObject imported = new JSONObject();
                try (InputStream in = getContentResolver().openInputStream(chosen); BufferedReader br = new BufferedReader(new InputStreamReader(in, StandardCharsets.UTF_8))) {
                    StringBuilder raw = new StringBuilder(); String line;
                    while ((line = br.readLine()) != null) { raw.append(line).append('\n'); if (raw.length() > 200000) throw new IllegalArgumentException("Arquivo maior que 200 KB; selecione um resumo sem chaves"); }
                    String body = raw.toString();
                    if (body.matches("(?is).*(sk-proj-|ghp_|gsk_|nvapi-|hf_[A-Za-z0-9]{20}).*")) throw new IllegalArgumentException("Possíveis credenciais detectadas; importação bloqueada");
                    String title = chosen.getLastPathSegment(); if (title == null) title = "Contexto do Drive";
                    store.upsertReference("Importado · " + title, body, new JSONObject().put("source", "Arquivo selecionado no Android").toString());
                    imported.put("ok", true).put("title", title);
                } catch (Exception e) { try { imported.put("ok", false).put("error", e.getMessage()); } catch (Exception ignored) {} }
                emit("aurionContextImportResult", imported.toString());
            }).start();
        }
        if (request == PICK_T8I_FILES && result == RESULT_OK && data != null) {
            importT8iFiles(data);
        }
        if (request == PICK_MEMORY_IMPORT && result == RESULT_OK && data != null && data.getData() != null) {
            new Thread(() -> {
                JSONObject imported;
                try (InputStream in = getContentResolver().openInputStream(data.getData()); BufferedReader br = new BufferedReader(new InputStreamReader(in, StandardCharsets.UTF_8))) {
                    StringBuilder raw = new StringBuilder(); String line; while ((line = br.readLine()) != null && raw.length() < 10000000) raw.append(line).append('\n'); imported = store.importAll(raw.toString());
                } catch (Exception e) { imported = new JSONObject(); try { imported.put("ok", false).put("error", e.getMessage()); } catch (Exception ignored) { } }
                emit("aurionMemoryResult", imported.toString());
            }).start();
        }
    }
    @Override public void onRequestPermissionsResult(int code, String[] permissions, int[] results) {
        super.onRequestPermissionsResult(code, permissions, results);
        BandNotificationTest.onPermissionResult(this, code, results);
        if (code == AurionBandChannel.REQUEST_PERMISSION) {
            boolean granted = results.length > 0 && results[0] == PackageManager.PERMISSION_GRANTED;
            if (bandPermissionEnablePending) {
                bandPermissionEnablePending = false;
                emit("aurionBandChannelResult",
                     AurionBandChannel.setEnabled(this, granted).toString());
            }
        }
        if (code == REQUEST_BLUETOOTH) { boolean ok = true; for (int r : results) ok &= r == PackageManager.PERMISSION_GRANTED; if (ok) startBleScan(); else emit("aurionBandResult", "{\"status\":\"blocked\",\"message\":\"Permissão Bluetooth negada\"}"); }
    }
    @Override public void onBackPressed() {
        if (web != null && web.getUrl() != null && !web.getUrl().startsWith("file:///android_asset/")) web.loadUrl("file:///android_asset/index.html");
        else if (web != null && web.canGoBack()) web.goBack(); else super.onBackPressed();
    }
}
