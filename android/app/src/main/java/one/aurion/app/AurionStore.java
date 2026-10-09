package one.aurion.app;

import android.content.ContentValues;
import android.content.Context;
import android.content.SharedPreferences;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.Base64;

import org.json.JSONArray;
import org.json.JSONObject;

import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

final class AurionStore extends SQLiteOpenHelper {
    private static final String DB = "aurion_memory_v4.db";
    private static final String KEY_ALIAS = "aurion_v4_vault";
    private final SharedPreferences vault;

    AurionStore(Context context) {
        super(context, DB, null, 2);
        vault = context.getSharedPreferences("aurion_secure_vault", Context.MODE_PRIVATE);
    }

    @Override public void onCreate(SQLiteDatabase db) {
        db.execSQL("CREATE TABLE records(id INTEGER PRIMARY KEY AUTOINCREMENT,type TEXT NOT NULL,title TEXT NOT NULL,body TEXT NOT NULL,meta TEXT NOT NULL DEFAULT '{}',created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL,profile_id TEXT NOT NULL DEFAULT 'anark')");
        db.execSQL("CREATE INDEX records_type_time ON records(type,updated_at DESC)");
    }
    @Override public void onUpgrade(SQLiteDatabase db, int oldVersion, int newVersion) {
        if (oldVersion < 2) db.execSQL("ALTER TABLE records ADD COLUMN profile_id TEXT NOT NULL DEFAULT 'anark'");
    }

    private volatile String profileId = "anark";
    synchronized void setProfile(String id) { profileId = id; }
    synchronized void claimLegacy(String id) {
        getWritableDatabase().execSQL("UPDATE records SET profile_id=? WHERE profile_id='anark' AND type NOT IN ('factory','reference','sync_event')", new Object[]{id});
    }

    synchronized long add(String type, String title, String body, String meta) {
        long now = System.currentTimeMillis();
        ContentValues v = new ContentValues();
        v.put("type", clean(type, "memory")); v.put("title", clean(title, "Sem título"));
        v.put("body", body == null ? "" : body); v.put("meta", meta == null ? "{}" : meta);
        v.put("created_at", now); v.put("updated_at", now);
        v.put("profile_id", profileId);
        return getWritableDatabase().insertOrThrow("records", null, v);
    }

    synchronized boolean remove(long id) { return getWritableDatabase().delete("records", "id=? AND profile_id=?", new String[]{String.valueOf(id), profileId}) > 0; }

    synchronized long upsertReference(String title, String body, String meta) {
        long now = System.currentTimeMillis();
        ContentValues v = new ContentValues(); v.put("body", body); v.put("meta", meta); v.put("updated_at", now);
        int updated = getWritableDatabase().update("records", v, "profile_id=? AND type=? AND title=?", new String[]{profileId, "reference", title});
        return updated > 0 ? updated : add("reference", title, body, meta);
    }



    synchronized JSONArray list(String type, String query, int limit) {
        JSONArray out = new JSONArray();
        String selection = "profile_id=?"; java.util.ArrayList<String> args = new java.util.ArrayList<>(); args.add(profileId);
        if (type != null && !type.trim().isEmpty() && !"all".equals(type)) { selection += " AND type=?"; args.add(type.trim()); }
        if (query != null && !query.trim().isEmpty()) {
            selection += " AND (title LIKE ? OR body LIKE ?)";
            String q = "%" + query.trim() + "%"; args.add(q); args.add(q);
        }
        try (Cursor c = getReadableDatabase().query("records", null, selection, args.toArray(new String[0]), null, null, "updated_at DESC", String.valueOf(Math.max(1, Math.min(500, limit))))) {
            while (c.moveToNext()) {
                JSONObject x = new JSONObject();
                x.put("id", c.getLong(c.getColumnIndexOrThrow("id")));
                x.put("type", c.getString(c.getColumnIndexOrThrow("type")));
                x.put("title", c.getString(c.getColumnIndexOrThrow("title")));
                x.put("body", c.getString(c.getColumnIndexOrThrow("body")));
                x.put("meta", c.getString(c.getColumnIndexOrThrow("meta")));
                x.put("createdAt", c.getLong(c.getColumnIndexOrThrow("created_at")));
                x.put("updatedAt", c.getLong(c.getColumnIndexOrThrow("updated_at")));
                out.put(x);
            }
        } catch (Exception ignored) { }
        return out;
    }

    synchronized JSONArray inspectProfile(String id) {
        if (!(id.equals("ds") || id.equals("davi") || id.equals("spectra"))) return new JSONArray();
        String previous = profileId;
        try { profileId = id; return list("all", "", 200); }
        finally { profileId = previous; }
    }

    // Backup completo DO PERFIL ATUAL. A listagem de tela ainda tem limite de 500,
    // mas exportacao nunca pode usar esse limite (risco de perda silenciosa).
    synchronized JSONObject exportAll() {
        JSONObject out = new JSONObject();
        try {
            JSONArray records = new JSONArray();
            SQLiteDatabase db = getReadableDatabase();
            try (Cursor c = db.query("records", null, "profile_id=?",
                    new String[]{profileId}, null, null, "id ASC")) {
                while (c.moveToNext()) {
                    JSONObject row = new JSONObject();
                    row.put("id", c.getLong(c.getColumnIndexOrThrow("id")));
                    row.put("type", c.getString(c.getColumnIndexOrThrow("type")));
                    row.put("title", c.getString(c.getColumnIndexOrThrow("title")));
                    row.put("body", c.getString(c.getColumnIndexOrThrow("body")));
                    row.put("meta", c.getString(c.getColumnIndexOrThrow("meta")));
                    row.put("createdAt", c.getLong(c.getColumnIndexOrThrow("created_at")));
                    row.put("updatedAt", c.getLong(c.getColumnIndexOrThrow("updated_at")));
                    records.put(row);
                }
            }
            out.put("ok", true);
            out.put("format", "aurion-memory-v4");
            out.put("exportedAt", System.currentTimeMillis());
            out.put("recordCount", records.length());
            out.put("profile", profileId);
            out.put("records", records);
            // Somente booleanos de configuracao; NUNCA exportar credenciais.
            out.put("accounts", accountStatus());
        } catch (Exception e) {
            // Falha explicita: proibido entregar JSON vazio parecendo backup valido.
            return errorJson("backup_falhou: " + e.getClass().getSimpleName());
        }
        return out;
    }

    private static JSONObject errorJson(String error) {
        JSONObject result = new JSONObject();
        try { result.put("ok", false); result.put("error", error); }
        catch (Exception ignored) { }
        return result;
    }

    // Restaura atomicamente sem apagar anteriores e sem duplicar ao repetir o mesmo backup.
    // Backup de outro perfil precisa ser restaurado no perfil correto, nao misturado.
    synchronized JSONObject importAll(String raw) {
        JSONArray records;
        try {
            JSONObject root = new JSONObject(raw);
            records = root.optJSONArray("records");
            if (records == null && root.optJSONObject("memory") != null)
                records = root.optJSONObject("memory").optJSONArray("records");
            if (records == null) return errorJson("backup_sem_registros");
            String sourceProfile = root.optString("profile", "");
            if (!sourceProfile.isEmpty() && !sourceProfile.equals(profileId))
                return errorJson("perfil_de_backup_diferente");
        } catch (Exception e) {
            return errorJson("backup_json_invalido");
        }
        SQLiteDatabase db = getWritableDatabase();
        int imported = 0, skipped = 0;
        try {
            java.util.HashSet<String> known = new java.util.HashSet<>();
            try (Cursor c = db.query("records", new String[]{"type", "title", "body", "meta"},
                    "profile_id=?", new String[]{profileId}, null, null, null)) {
                while (c.moveToNext())
                    known.add(recordFingerprint(c.getString(0), c.getString(1), c.getString(2), c.getString(3)));
            }
            db.beginTransaction();
            try {
                for (int i = 0; i < records.length(); i++) {
                    JSONObject x = records.optJSONObject(i);
                    if (x == null) throw new IllegalArgumentException("registro_nao_objeto");
                    String type = clean(x.optString("type", "memory"), "memory");
                    String title = clean(x.optString("title", "Importado"), "Importado");
                    String body = x.optString("body", "");
                    String meta = x.optString("meta", "{}");
                    String fingerprint = recordFingerprint(type, title, body, meta);
                    if (!known.add(fingerprint)) { skipped++; continue; }
                    ContentValues v = new ContentValues();
                    v.put("type", type);
                    v.put("title", title);
                    v.put("body", body);
                    v.put("meta", meta);
                    v.put("profile_id", profileId);
                    long now = System.currentTimeMillis();
                    v.put("created_at", x.optLong("createdAt", now));
                    v.put("updated_at", x.optLong("updatedAt", now));
                    db.insertOrThrow("records", null, v);
                    imported++;
                }
                db.setTransactionSuccessful();
            } finally {
                db.endTransaction();
            }
        } catch (Exception e) {
            return errorJson("restauracao_revertida: " + e.getClass().getSimpleName());
        }
        JSONObject result = new JSONObject();
        try {
            result.put("ok", true);
            result.put("imported", imported);
            result.put("skippedDuplicates", skipped);
            result.put("received", records.length());
        } catch (Exception ignored) { }
        return result;
    }

    private static String recordFingerprint(String type, String title, String body, String meta) throws Exception {
        java.security.MessageDigest digest = java.security.MessageDigest.getInstance("SHA-256");
        for (String value : new String[]{type, title, body, meta}) {
            byte[] bytes = (value == null ? "" : value).getBytes(StandardCharsets.UTF_8);
            // Comprimento prefixado evita ambiguidades da concatenacao.
            digest.update(new byte[]{(byte)(bytes.length >>> 24), (byte)(bytes.length >>> 16),
                    (byte)(bytes.length >>> 8), (byte)bytes.length});
            digest.update(bytes);
        }
        byte[] out = digest.digest();
        StringBuilder hex = new StringBuilder();
        for (byte b : out) hex.append(String.format(java.util.Locale.ROOT, "%02x", b & 0xff));
        return hex.toString();
    }

    synchronized void setSecret(String name, String value) throws Exception {
        name = scopedSecret(name);
        if (value == null || value.isEmpty()) { vault.edit().remove(name).apply(); return; }
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding"); cipher.init(Cipher.ENCRYPT_MODE, key());
        byte[] encrypted = cipher.doFinal(value.getBytes(StandardCharsets.UTF_8));
        byte[] packed = new byte[cipher.getIV().length + encrypted.length];
        System.arraycopy(cipher.getIV(), 0, packed, 0, cipher.getIV().length); System.arraycopy(encrypted, 0, packed, cipher.getIV().length, encrypted.length);
        vault.edit().putString(name, Base64.encodeToString(packed, Base64.NO_WRAP)).apply();
    }

    synchronized String getSecret(String name) {
        try {
            name = scopedSecret(name);
            byte[] packed = Base64.decode(vault.getString(name, ""), Base64.NO_WRAP); if (packed.length < 13) return "";
            byte[] iv = new byte[12]; byte[] encrypted = new byte[packed.length - 12];
            System.arraycopy(packed, 0, iv, 0, 12); System.arraycopy(packed, 12, encrypted, 0, encrypted.length);
            Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding"); cipher.init(Cipher.DECRYPT_MODE, key(), new GCMParameterSpec(128, iv));
            return new String(cipher.doFinal(encrypted), StandardCharsets.UTF_8);
        } catch (Exception e) { return ""; }
    }

    private String scopedSecret(String name) { return "anark".equals(profileId) ? name : "profile_" + profileId + "_" + name; }

    synchronized JSONObject accountStatus() {
        JSONObject j = new JSONObject();
        for (String key : new String[]{"github","huggingface","openai","groq","nvidia","gemini","googleDrive"}) try { j.put(key, !getSecret(key).isEmpty()); } catch (Exception ignored) { }
        return j;
    }

    private SecretKey key() throws Exception {
        KeyStore ks = KeyStore.getInstance("AndroidKeyStore"); ks.load(null);
        if (ks.containsAlias(KEY_ALIAS)) return ((KeyStore.SecretKeyEntry) ks.getEntry(KEY_ALIAS, null)).getSecretKey();
        KeyGenerator g = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore");
        g.init(new KeyGenParameterSpec.Builder(KEY_ALIAS, KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT).setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).build());
        return g.generateKey();
    }

    private static String clean(String text, String fallback) { return text == null || text.trim().isEmpty() ? fallback : text.trim(); }
}
