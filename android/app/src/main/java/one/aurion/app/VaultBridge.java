package one.aurion.app;

import android.app.Activity;
import android.content.Intent;
import android.content.SharedPreferences;
import android.database.Cursor;
import android.net.Uri;
import android.provider.DocumentsContract;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;
import java.util.UUID;
import java.util.function.BooleanSupplier;

/** Armazena cópias em diretório explicitamente escolhido via seletor Android. */
public final class VaultBridge {
    public static final int PICK_TREE = 6811;
    private static final String PREFS = "aurion_vault_v1";
    private static final String KEY = "tree";
    private final Activity activity;
    private final WebView web;
    private final BooleanSupplier trusted;

    public VaultBridge(Activity activity, WebView web, BooleanSupplier trusted) {
        this.activity = activity; this.web = web; this.trusted = trusted;
    }
    private void guard() { if (!trusted.getAsBoolean()) throw new SecurityException("Somente interface local do AURION"); }
    private JSONObject result(boolean ok, String message) throws Exception {
        JSONObject j = new JSONObject(); j.put("ok", ok); j.put("message", message); return j;
    }
    private String failure(Exception e) {
        try { return result(false, e.getClass().getSimpleName() + ": " + String.valueOf(e.getMessage())).toString(); }
        catch (Exception ignored) { return "{\"ok\":false}"; }
    }
    private Uri tree() {
        String raw = activity.getSharedPreferences(PREFS, Activity.MODE_PRIVATE).getString(KEY, "");
        return raw.isEmpty() ? null : Uri.parse(raw);
    }
    private String clean(String value) {
        if (value == null) value = "";
        String text = value.replaceAll("[\\p{Cntrl}/\\\\:*?\"<>|]", "_").trim();
        if (text.equals(".") || text.equals("..") || text.isEmpty()) text = "Sem_titulo";
        return text.length() > 58 ? text.substring(0, 58) : text;
    }
    @JavascriptInterface public void chooseFolder() {
        guard();
        activity.runOnUiThread(() -> {
            Intent i = new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);
            i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION |
                    Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION | Intent.FLAG_GRANT_PREFIX_URI_PERMISSION);
            try { activity.startActivityForResult(i, PICK_TREE); }
            catch (Exception e) { emit(failure(e)); }
        });
    }
    public void onFolderChosen(int resultCode, Intent data) {
        if (resultCode != Activity.RESULT_OK || data == null || data.getData() == null) { emit("{\"ok\":false,\"message\":\"Seleção cancelada\"}"); return; }
        try {
            Uri selected = data.getData();
            int flags = data.getFlags() & (Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
            activity.getContentResolver().takePersistableUriPermission(selected, flags);
            activity.getSharedPreferences(PREFS, Activity.MODE_PRIVATE).edit().putString(KEY, selected.toString()).apply();
            emit(status());
        } catch (Exception e) { emit(failure(e)); }
    }
    private void emit(String json) {
        web.post(() -> web.evaluateJavascript("window.aurionVaultSelected && window.aurionVaultSelected(" + JSONObject.quote(json) + ")", null));
    }
    @JavascriptInterface public String status() {
        guard();
        try {
            Uri t = tree(); JSONObject j = result(t != null, t == null ? "Escolha uma pasta" : "Pasta selecionada");
            j.put("selected", t != null);
            if (t != null) j.put("folder", DocumentsContract.getTreeDocumentId(t));
            return j.toString();
        } catch (Exception e) { return failure(e); }
    }
    private Uri rootDocument(Uri t) { return DocumentsContract.buildDocumentUriUsingTree(t, DocumentsContract.getTreeDocumentId(t)); }
    private Uri child(Uri t, Uri parent, String name, String mime, boolean create) throws Exception {
        String parentId = DocumentsContract.getDocumentId(parent);
        Uri children = DocumentsContract.buildChildDocumentsUriUsingTree(t, parentId);
        try (Cursor c = activity.getContentResolver().query(children,
                new String[]{DocumentsContract.Document.COLUMN_DOCUMENT_ID, DocumentsContract.Document.COLUMN_DISPLAY_NAME,
                    DocumentsContract.Document.COLUMN_MIME_TYPE}, null, null, null)) {
            if (c != null) while (c.moveToNext()) {
                if (name.equals(c.getString(1)) && mime.equals(c.getString(2)))
                    return DocumentsContract.buildDocumentUriUsingTree(t, c.getString(0));
            }
        }
        return create ? DocumentsContract.createDocument(activity.getContentResolver(), parent, mime, name) : null;
    }
    private Uri project(Uri t, String name, boolean create) throws Exception {
        Uri root = child(t, rootDocument(t), "AURION_ONE", DocumentsContract.Document.MIME_TYPE_DIR, create);
        if (root == null) return null;
        return child(t, root, clean(name), DocumentsContract.Document.MIME_TYPE_DIR, create);
    }
    @JavascriptInterface public String save(String projectName, String title, String content) {
        guard();
        try {
            if (content == null || content.trim().isEmpty()) return result(false, "Não há conteúdo para salvar").toString();
            if (content.length() > 500000) return result(false, "Limite de 500 mil caracteres por arquivo").toString();
            Uri t = tree(); if (t == null) return result(false, "Escolha a pasta de destino primeiro").toString();
            Uri directory = project(t, projectName, true);
            if (directory == null) return result(false, "Falha ao criar pasta do projeto").toString();
            String stamp = new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.ROOT).format(new Date());
            String filename = stamp + "_" + clean(title) + "_" + UUID.randomUUID().toString().substring(0, 8) + ".txt";
            Uri output = DocumentsContract.createDocument(activity.getContentResolver(), directory, "text/plain", filename);
            if (output == null) return result(false, "Falha ao criar arquivo").toString();
            byte[] data = content.getBytes(StandardCharsets.UTF_8);
            try (OutputStream stream = activity.getContentResolver().openOutputStream(output, "wt")) {
                if (stream == null) throw new IllegalStateException("Destino não permite gravação");
                stream.write(data); stream.flush();
            }
            JSONObject j = result(true, "Arquivo salvo na pasta escolhida");
            j.put("project", clean(projectName)); j.put("filename", filename); j.put("bytes", data.length);
            return j.toString();
        } catch (Exception e) { return failure(e); }
    }
    @JavascriptInterface public String list(String projectName) {
        guard();
        try {
            Uri t = tree(); if (t == null) return result(false, "Escolha uma pasta primeiro").toString();
            Uri dir = project(t, projectName, false); JSONArray a = new JSONArray();
            if (dir != null) {
                Uri children = DocumentsContract.buildChildDocumentsUriUsingTree(t, DocumentsContract.getDocumentId(dir));
                try (Cursor c = activity.getContentResolver().query(children,
                    new String[]{DocumentsContract.Document.COLUMN_DOCUMENT_ID, DocumentsContract.Document.COLUMN_DISPLAY_NAME,
                        DocumentsContract.Document.COLUMN_MIME_TYPE}, null, null, null)) {
                    if (c != null) while (c.moveToNext()) if ("text/plain".equals(c.getString(2))) {
                        JSONObject row = new JSONObject(); row.put("id", c.getString(0)); row.put("name", c.getString(1)); a.put(row);
                    }
                }
            }
            JSONObject j = result(true, "Arquivos encontrados"); j.put("items", a); return j.toString();
        } catch (Exception e) { return failure(e); }
    }
    @JavascriptInterface public String read(String projectName, String documentId) {
        guard();
        try {
            JSONObject list = new JSONObject(list(projectName));
            if (!list.optBoolean("ok")) return list.toString();
            boolean known = false;
            JSONArray items = list.getJSONArray("items");
            for (int i = 0; i < items.length(); i++) if (items.getJSONObject(i).getString("id").equals(documentId)) known = true;
            if (!known) return result(false, "Arquivo fora da pasta selecionada").toString();
            Uri t = tree(); Uri file = DocumentsContract.buildDocumentUriUsingTree(t, documentId);
            ByteArrayOutputStream buffer = new ByteArrayOutputStream(); byte[] bytes = new byte[8192]; int count;
            try (InputStream in = activity.getContentResolver().openInputStream(file)) {
                if (in == null) throw new IllegalStateException("Arquivo não abre");
                while ((count = in.read(bytes)) != -1) {
                    if (buffer.size() + count > 1500000) return result(false, "Arquivo maior que 1,5 MB").toString();
                    buffer.write(bytes, 0, count);
                }
            }
            JSONObject j = result(true, "Arquivo lido"); j.put("text", new String(buffer.toByteArray(), StandardCharsets.UTF_8)); return j.toString();
        } catch (Exception e) { return failure(e); }
    }
}
