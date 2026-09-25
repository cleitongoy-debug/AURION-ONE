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

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.OutputStream;
import java.io.InputStream;
import java.io.BufferedReader;
import java.io.InputStreamReader;
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
    private static final int PICK_WORKSPACE = 413;
    private static final int PICK_CONVERT_IMAGE = 414;
    private static final int CAPTURE_PHOTO = 415;
    private static final int PICK_TRIM_MEDIA = 416;
    private static final int PICK_MEMORY_IMPORT = 417;
    private WebView web;
    private ValueCallback<Uri[]> selectedFiles;
    private String pendingBackup = "";
    private String pendingConvertFormat = "JPEG";
    private int pendingConvertQuality = 94;
    private Uri pendingCameraUri;
    private String pendingTrimKind = "video";
    private double pendingTrimStart = 0;
    private double pendingTrimEnd = 0;
    private AurionStore store;
    private BluetoothLeScanner scanner;
    private ScanCallback scanCallback;
    private final Map<String, JSONObject> scanResults = new LinkedHashMap<>();
    private final Handler handler = new Handler(Looper.getMainLooper());
    private final Bridge bridge = new Bridge();

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setStatusBarColor(Color.rgb(4, 8, 13));
        getWindow().setNavigationBarColor(Color.rgb(4, 8, 13));
        web = new WebView(this);
        store = new AurionStore(this);
        web.setBackgroundColor(Color.rgb(4, 8, 13));
        setContentView(web);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setDatabaseEnabled(true);
        s.setAllowFileAccess(false);
        s.setAllowContentAccess(true);
        s.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        s.setUserAgentString(s.getUserAgentString() + " AURION-ONE-SuperStudio/5.5");
        web.addJavascriptInterface(bridge, "AurionAndroid");
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
                if (url != null && url.startsWith("file:///android_asset/")) v.addJavascriptInterface(bridge, "AurionAndroid");
                else v.removeJavascriptInterface("AurionAndroid");
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
            j.put("appVersion", "5.5.0");
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
            j.put("accounts", store.accountStatus());
            j.put("memoryRecords", store.list("all", "", 5000).length());
            j.put("memoryStats", store.memoryStats());
            j.put("audioInputPermission", has(Manifest.permission.RECORD_AUDIO));
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
            h.equals("api.openai.com") || h.equals("api.groq.com") || h.equals("api.deepseek.com") || h.equals("gen.pollinations.ai") || h.equals("api.siliconflow.cn") || h.equals("api.x.ai") || h.equals("generativelanguage.googleapis.com") || h.equals("www.googleapis.com") ||
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
            else if ("deepseek".equals(service)) result = cloudJson("GET", "https://api.deepseek.com/models", "Bearer " + key, "", null);
            else if ("pollinations".equals(service)) result = cloudJson("GET", "https://gen.pollinations.ai/v1/models", "Bearer " + key, "", null);
            else if ("siliconflow".equals(service)) result = cloudJson("GET", "https://api.siliconflow.cn/v1/models", "Bearer " + key, "", null);
            else if ("xai".equals(service)) result = cloudJson("GET", "https://api.x.ai/v1/models", "Bearer " + key, "", null);
            else if ("gemini".equals(service)) result = cloudJson("GET", "https://generativelanguage.googleapis.com/v1beta/models?pageSize=1", "", key, null);
            else if ("googleDrive".equals(service)) result = cloudJson("GET", "https://www.googleapis.com/drive/v3/about?fields=user,storageQuota", "Bearer " + key, "", null);
            else { result = new JSONObject(); try { result.put("ok", false); result.put("error", "Serviço desconhecido"); } catch (Exception ignored) { } }
            emit("aurionAccountResult", new JSONObjectResult(service, result).toString());
        }).start();
    }

    private void runCloudAi(String provider, String model, String prompt, String memory) {
        new Thread(() -> {
            JSONObject result = new JSONObject();
            try {
                String key = store.getSecret(provider); if (key.isEmpty()) throw new IllegalStateException("Credencial ausente para " + provider);
                String input = (memory == null || memory.trim().isEmpty() ? "" : "MEMÓRIA AUTORIZADA:\n" + memory.trim() + "\n\n") + prompt;
                if ("openai".equals(provider)) {
                    JSONObject body = new JSONObject().put("model", model.isEmpty() ? "gpt-5-mini" : model).put("input", input);
                    result = cloudJson("POST", "https://api.openai.com/v1/responses", "Bearer " + key, "", body.toString());
                } else if ("gemini".equals(provider)) {
                    JSONArray parts = new JSONArray().put(new JSONObject().put("text", input)); JSONArray contents = new JSONArray().put(new JSONObject().put("role", "user").put("parts", parts));
                    JSONObject body = new JSONObject().put("contents", contents); String selected = model.isEmpty() ? "gemini-2.5-flash" : model;
                    result = cloudJson("POST", "https://generativelanguage.googleapis.com/v1beta/models/" + selected + ":generateContent", "", key, body.toString());
                } else if ("huggingface".equals(provider)) {
                    JSONArray messages = new JSONArray().put(new JSONObject().put("role", "user").put("content", input)); JSONObject body = new JSONObject().put("model", model).put("messages", messages).put("max_tokens", 2400);
                    result = cloudJson("POST", "https://router.huggingface.co/v1/chat/completions", "Bearer " + key, "", body.toString());
                } else if ("groq".equals(provider) || "deepseek".equals(provider) || "pollinations".equals(provider) || "siliconflow".equals(provider) || "xai".equals(provider)) {
                    String endpoint = "groq".equals(provider) ? "https://api.groq.com/openai/v1/chat/completions" : "deepseek".equals(provider) ? "https://api.deepseek.com/chat/completions" : "pollinations".equals(provider) ? "https://gen.pollinations.ai/v1/chat/completions" : "siliconflow".equals(provider) ? "https://api.siliconflow.cn/v1/chat/completions" : "https://api.x.ai/v1/chat/completions";
                    String selected = model == null || model.isEmpty() ? ("groq".equals(provider) ? "groq/compound" : "deepseek".equals(provider) ? "deepseek-v4-flash" : "pollinations".equals(provider) ? "openai" : "siliconflow".equals(provider) ? "Qwen/Qwen3-8B" : "grok-4") : model;
                    JSONArray messages = new JSONArray().put(new JSONObject().put("role","system").put("content","Você é o motor conectado do AURION ONE. Use memória e referências fornecidas, não invente estado de ferramentas.")).put(new JSONObject().put("role","user").put("content",input));
                    JSONObject body = new JSONObject().put("model",selected).put("messages",messages).put("max_tokens",2400);
                    result = cloudJson("POST", endpoint, "Bearer " + key, "", body.toString());
                } else throw new IllegalArgumentException("Provedor não suportado");
            } catch (Exception e) { try { result.put("ok", false); result.put("error", e.getMessage()); } catch (Exception ignored) { } }
            emit("aurionAiResult", new JSONObjectResult(provider, result).toString());
        }).start();
    }

    private void listModels(String provider) {
        new Thread(() -> {
            JSONObject result = new JSONObject();
            try {
                String key=store.getSecret(provider); if(key.isEmpty()) throw new IllegalStateException("Credencial ausente");
                String url = "groq".equals(provider)?"https://api.groq.com/openai/v1/models":"deepseek".equals(provider)?"https://api.deepseek.com/models":"pollinations".equals(provider)?"https://gen.pollinations.ai/v1/models":"siliconflow".equals(provider)?"https://api.siliconflow.cn/v1/models":"xai".equals(provider)?"https://api.x.ai/v1/models":"openai".equals(provider)?"https://api.openai.com/v1/models":null;
                if(url==null) throw new IllegalArgumentException("Catálogo automático não disponível para "+provider);
                result=cloudJson("GET",url,"Bearer "+key,"",null);
            } catch(Exception e){try{result.put("ok",false).put("error",e.getMessage());}catch(Exception ignored){}}
            emit("aurionModelsResult",new JSONObjectResult(provider,result).toString());
        }).start();
    }

    private void generateCloudImage(String prompt, String model, int width, int height) {
        new Thread(() -> {
            JSONObject result=new JSONObject();
            try {
                String key=store.getSecret("pollinations"); if(key.isEmpty()) throw new IllegalStateException("Configure Pollinations em Contas");
                JSONObject body=new JSONObject().put("model",model==null||model.isEmpty()?"flux":model).put("prompt",prompt).put("n",1).put("size",Math.max(256,width)+"x"+Math.max(256,height)).put("response_format","b64_json");
                result=cloudJson("POST","https://gen.pollinations.ai/v1/images/generations","Bearer "+key,"",body.toString());
            }catch(Exception e){try{result.put("ok",false).put("error",e.getMessage());}catch(Exception ignored){}}
            emit("aurionImageResult",result.toString());
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

    public final class Bridge {
        @JavascriptInterface public String getDiagnostics() { return diagnostics().toString(); }
        @JavascriptInterface public void refreshDiagnostics() { emit("aurionDiagnostics", diagnostics().toString()); }
        @JavascriptInterface public void openPanel(String raw) { runOnUiThread(() -> { try { Uri u = Uri.parse(raw); if (!isAllowedPanelHost(u.getHost())) throw new IllegalArgumentException(); web.loadUrl(raw); } catch (Exception e) { toast("Use IP local ou endereço Tailscale do PC"); } }); }
        @JavascriptInterface public void testPanel(String raw) { MainActivity.this.testPanel(raw); }
        @JavascriptInterface public void testService(String label, String raw) { new Thread(() -> emit("aurionServiceResult", new JSONObjectResult(label, httpJson("GET", raw, "", null)).toString())).start(); }
        @JavascriptInterface public void sendAgent(String base, String token, String text) { new Thread(() -> {
            try { JSONObject body = new JSONObject(); body.put("text", text); body.put("device_id", "poco-aurion-final"); body.put("moving", false); emit("aurionAgentResult", httpJson("POST", new URL(new URL(base), "/api/prompt").toString(), token, body.toString()).toString()); }
            catch (Exception e) { emit("aurionAgentResult", "{\"ok\":false,\"error\":\"Endereço inválido\"}"); }
        }).start(); }
        @JavascriptInterface public void queueComfy(String base, String workflow) { new Thread(() -> {
            try { JSONObject parsed = new JSONObject(workflow); JSONObject body = parsed.has("prompt") ? parsed : new JSONObject().put("prompt", parsed); emit("aurionComfyResult", httpJson("POST", new URL(new URL(base), "/prompt").toString(), "", body.toString()).toString()); }
            catch (Exception e) { emit("aurionComfyResult", "{\"ok\":false,\"error\":\"Workflow JSON inválido\"}"); }
        }).start(); }
        @JavascriptInterface public void chooseWorkspace() { runOnUiThread(MainActivity.this::chooseWorkspace); }
        @JavascriptInterface public void capturePhoto() { runOnUiThread(MainActivity.this::capturePhoto); }
        @JavascriptInterface public void convertImage(String format, int quality) { runOnUiThread(() -> chooseImageForConversion(format, quality)); }
        @JavascriptInterface public void saveEditedImage(String format, int quality, String dataUrl) { new Thread(() -> emit("aurionEditorResult", MediaTools.saveDataImage(MainActivity.this, format, quality, dataUrl).toString())).start(); }
        @JavascriptInterface public void saveBase64File(String filename, String mime, String base64) { new Thread(() -> emit("aurionFileResult", MediaTools.saveBase64File(MainActivity.this, filename, mime, base64).toString())).start(); }
        @JavascriptInterface public void trimMedia(String kind, double start, double end) { runOnUiThread(() -> chooseTrimMedia(kind, start, end)); }
        @JavascriptInterface public long memoryAdd(String type, String title, String body, String meta) { try { return store.add(type, title, body, meta); } catch (Exception e) { return -1; } }
        @JavascriptInterface public String memoryList(String type, String query, int limit) { return store.list(type, query, limit).toString(); }
        @JavascriptInterface public String memoryContext(String query, int limit) { return store.contextPack(query, limit).toString(); }
        @JavascriptInterface public String memoryStats() { return store.memoryStats().toString(); }
        @JavascriptInterface public boolean memoryDelete(long id) { return store.remove(id); }
        @JavascriptInterface public String memoryExport() { return store.exportAll().toString(); }
        @JavascriptInterface public void memorySync() { syncMemoryToWorkspace(); }
        @JavascriptInterface public void memoryImport() { runOnUiThread(() -> startActivityForResult(new Intent(Intent.ACTION_OPEN_DOCUMENT).setType("application/json").addCategory(Intent.CATEGORY_OPENABLE), PICK_MEMORY_IMPORT)); }
        @JavascriptInterface public void setSecret(String service, String value) { try { store.setSecret(service, value == null ? "" : value.trim()); emit("aurionVaultResult", new JSONObject().put("ok", true).put("service", service).toString()); } catch (Exception e) { try { emit("aurionVaultResult", new JSONObject().put("ok", false).put("service", service).put("error", e.getMessage()).toString()); } catch (Exception ignored) { } } }
        @JavascriptInterface public String accountStatus() { return store.accountStatus().toString(); }
        @JavascriptInterface public void testAccount(String service) { MainActivity.this.testAccount(service); }
        @JavascriptInterface public void runCloudAi(String provider, String model, String prompt, String memory) { MainActivity.this.runCloudAi(provider, model, prompt, memory); }
        @JavascriptInterface public void listModels(String provider) { MainActivity.this.listModels(provider); }
        @JavascriptInterface public void generateCloudImage(String prompt, String model, int width, int height) { MainActivity.this.generateCloudImage(prompt, model, width, height); }
        @JavascriptInterface public void downloadResource(String url, String filename, String sha256) { runOnUiThread(() -> MainActivity.this.downloadResource(url, filename, sha256)); }
        @JavascriptInterface public void shareProject(String title, String text) { shareText(title, text); }
        @JavascriptInterface public void openExternal(String raw) { runOnUiThread(() -> { try { Uri u = Uri.parse(raw); String s = u.getScheme(); if (!("http".equals(s) || "https".equals(s))) throw new IllegalArgumentException(); startActivity(new Intent(Intent.ACTION_VIEW, u)); } catch (Exception e) { toast("Endereço externo inválido"); } }); }
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
        @JavascriptInterface public void copyText(String label, String text) { ClipboardManager cm = (ClipboardManager) getSystemService(CLIPBOARD_SERVICE); cm.setPrimaryClip(ClipData.newPlainText(label == null ? "AURION" : label, text == null ? "" : text)); toast("Copiado. Revise antes de executar."); }
        @JavascriptInterface public void exportBackup(String json) {
            pendingBackup = json;
            runOnUiThread(() -> {
                Intent i = new Intent(Intent.ACTION_CREATE_DOCUMENT).setType("application/json").putExtra(Intent.EXTRA_TITLE, "aurion-mobile-backup.json");
                startActivityForResult(i, CREATE_BACKUP);
            });
        }
        @JavascriptInterface public void appInfo() { runOnUiThread(() -> new AlertDialog.Builder(MainActivity.this).setTitle("AURION ONE Super Studio").setMessage("Versão 5.5.0\nLaboratórios de foto, vídeo, áudio, cor, efeitos, motion, IA e memória permanente.").setPositiveButton("OK", null).show()); }
    }

    private static final class JSONObjectResult {
        private final JSONObject value = new JSONObject();
        JSONObjectResult(String label, JSONObject result) { try { value.put("label", label); value.put("result", result); } catch (Exception ignored) {} }
        @Override public String toString() { return value.toString(); }
    }

    @Override protected void onActivityResult(int request, int result, Intent data) {
        super.onActivityResult(request, result, data);
        if (request == PICK_FILE && selectedFiles != null) { selectedFiles.onReceiveValue(WebChromeClient.FileChooserParams.parseResult(result, data)); selectedFiles = null; }
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
        if (code == REQUEST_BLUETOOTH) { boolean ok = true; for (int r : results) ok &= r == PackageManager.PERMISSION_GRANTED; if (ok) startBleScan(); else emit("aurionBandResult", "{\"status\":\"blocked\",\"message\":\"Permissão Bluetooth negada\"}"); }
    }
    @Override public void onBackPressed() {
        if (web != null && web.getUrl() != null && !web.getUrl().startsWith("file:///android_asset/")) web.loadUrl("file:///android_asset/index.html");
        else if (web != null && web.canGoBack()) web.goBack(); else super.onBackPressed();
    }
}
