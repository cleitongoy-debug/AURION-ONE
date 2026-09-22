package one.aurion.app;

import android.app.Activity;
import android.content.Intent;
import android.content.Context;
import android.content.ContentResolver;
import android.content.SharedPreferences;
import android.net.Uri;
import android.os.Handler;
import android.os.Looper;
import android.provider.DocumentsContract;
import android.util.Base64;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;

import org.json.JSONObject;

import java.io.OutputStream;

/** User-picked SAF destination. Only the bundled T8i page may call storage methods. */
public final class T8iBridge {
    private static final int PICK_TREE = 462;
    private static final String PREFS = "aurion_t8i_storage";
    private static final String KEY_TREE = "tree_uri";
    private final Activity activity;
    private final WebView web;
    private final Handler main = new Handler(Looper.getMainLooper());
    private volatile boolean editorActive = false;

    public T8iBridge(Activity activity, WebView web) {
        this.activity = activity;
        this.web = web;
    }

    /** Main-thread navigation callback: turn off native storage access on any other page. */
    public void setEditorActive(boolean active) { editorActive = active; }

    private void result(String event, boolean ok, String message) {
        try {
            JSONObject j = new JSONObject();
            j.put("event", event);
            j.put("ok", ok);
            j.put("message", message);
            String call = "window.t8iNativeResult && window.t8iNativeResult(" + JSONObject.quote(j.toString()) + ")";
            main.post(() -> web.evaluateJavascript(call, null));
        } catch (Exception ignored) { }
    }

    @JavascriptInterface public void chooseFolder() {
        if (!editorActive) return;
        main.post(() -> {
            if (!editorActive) return;
            Intent i = new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);
            i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION |
                    Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
            try { activity.startActivityForResult(i, PICK_TREE); }
            catch (Exception e) { result("folder", false, "O Android não disponibilizou o seletor de pastas: " + e.getClass().getSimpleName()); }
        });
    }

    /** Called on the WebView bridge thread. Saves only inside the user-granted tree. */
    @JavascriptInterface public void saveBase64(String mime, String filename, String payload) {
        if (!editorActive) return;
        if (!("image/png".equals(mime) || "image/jpeg".equals(mime) || "application/json".equals(mime))) {
            result("save", false, "Formato não autorizado."); return;
        }
        if (payload == null || payload.length() > 38_000_000) {
            result("save", false, "Arquivo excede o limite de transferência móvel."); return;
        }
        String safe = filename == null ? "aurion-export" : filename.replaceAll("[^A-Za-z0-9_.-]", "_");
        if (safe.isEmpty() || safe.startsWith(".")) safe = "aurion-export";
        if (safe.length() > 100) safe = safe.substring(0, 100);
        SharedPreferences prefs = activity.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        String stored = prefs.getString(KEY_TREE, "");
        if (stored.isEmpty()) { result("save", false, "Escolha a pasta de destino primeiro."); return; }
        try {
            byte[] bytes = Base64.decode(payload, Base64.DEFAULT);
            if (!editorActive) return;
            Uri tree = Uri.parse(stored);
            Uri parent = DocumentsContract.buildDocumentUriUsingTree(tree, DocumentsContract.getTreeDocumentId(tree));
            ContentResolver resolver = activity.getContentResolver();
            Uri destination = DocumentsContract.createDocument(resolver, parent, mime, safe);
            if (destination == null) throw new IllegalStateException("Provedor não criou o documento");
            try (OutputStream out = resolver.openOutputStream(destination, "w")) {
                if (out == null) throw new IllegalStateException("Provedor recusou gravação");
                out.write(bytes);
                out.flush();
            }
            result("save", true, "Salvo: " + safe + " · " + bytes.length + " bytes. Confira a pasta escolhida.");
        } catch (Exception e) {
            result("save", false, "Falha ao salvar: " + e.getClass().getSimpleName() + ". Confira permissões/espaço do provedor.");
        }
    }

    /** Invoked by MainActivity; document tree access remains private to this APK. */
    public boolean onActivityResult(int request, int code, Intent data) {
        if (request != PICK_TREE) return false;
        if (code != Activity.RESULT_OK || data == null || data.getData() == null) {
            result("folder", false, "Seleção cancelada; pasta anterior preservada."); return true;
        }
        try {
            Uri uri = data.getData();
            int flags = data.getFlags() & (Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
            if ((flags & Intent.FLAG_GRANT_WRITE_URI_PERMISSION) == 0) throw new SecurityException("Sem gravação");
            activity.getContentResolver().takePersistableUriPermission(uri, flags);
            activity.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().putString(KEY_TREE, uri.toString()).apply();
            result("folder", true, "Pasta autorizada. Fotos e receitas serão criadas ali, sem sobrescrever originais.");
        } catch (Exception e) {
            result("folder", false, "Acesso à pasta negado: " + e.getClass().getSimpleName());
        }
        return true;
    }
}
