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
        super(context, DB, null, 1);
        vault = context.getSharedPreferences("aurion_secure_vault", Context.MODE_PRIVATE);
    }

    @Override public void onCreate(SQLiteDatabase db) {
        db.execSQL("CREATE TABLE records(id INTEGER PRIMARY KEY AUTOINCREMENT,type TEXT NOT NULL,title TEXT NOT NULL,body TEXT NOT NULL,meta TEXT NOT NULL DEFAULT '{}',created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL)");
        db.execSQL("CREATE INDEX records_type_time ON records(type,updated_at DESC)");
    }
    @Override public void onUpgrade(SQLiteDatabase db, int oldVersion, int newVersion) { }

    synchronized long add(String type, String title, String body, String meta) {
        long now = System.currentTimeMillis();
        ContentValues v = new ContentValues();
        v.put("type", clean(type, "memory")); v.put("title", clean(title, "Sem título"));
        v.put("body", body == null ? "" : body); v.put("meta", meta == null ? "{}" : meta);
        v.put("created_at", now); v.put("updated_at", now);
        return getWritableDatabase().insertOrThrow("records", null, v);
    }

    synchronized boolean remove(long id) { return getWritableDatabase().delete("records", "id=?", new String[]{String.valueOf(id)}) > 0; }

    synchronized JSONArray list(String type, String query, int limit) {
        JSONArray out = new JSONArray();
        String selection = null; java.util.ArrayList<String> args = new java.util.ArrayList<>();
        if (type != null && !type.trim().isEmpty() && !"all".equals(type)) { selection = "type=?"; args.add(type.trim()); }
        if (query != null && !query.trim().isEmpty()) {
            selection = selection == null ? "(title LIKE ? OR body LIKE ?)" : selection + " AND (title LIKE ? OR body LIKE ?)";
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

    synchronized JSONArray contextPack(String query, int limit) {
        JSONArray all = list("all", "", 500);
        java.util.ArrayList<JSONObject> ranked = new java.util.ArrayList<>();
        final String q = query == null ? "" : query.toLowerCase(java.util.Locale.ROOT);
        final java.util.HashSet<String> terms = new java.util.HashSet<>();
        for (String t : q.split("[^\\p{L}\\p{N}_-]+")) if (t.length() >= 3) terms.add(t);
        for (int i=0;i<all.length();i++) {
            JSONObject x=all.optJSONObject(i); if(x==null) continue;
            String hay=(x.optString("title")+" "+x.optString("body")+" "+x.optString("type")).toLowerCase(java.util.Locale.ROOT);
            int score=0; for(String t:terms) if(hay.contains(t)) score+=3;
            String type=x.optString("type");
            if("project".equals(type)||"memory".equals(type)||"evidence".equals(type)||"preset".equals(type)) score+=2;
            if("conversation".equals(type)) score+=1;
            try{x.put("_score",score);}catch(Exception ignored){}
            ranked.add(x);
        }
        java.util.Collections.sort(ranked,(a,b)->{
            int d=Integer.compare(b.optInt("_score"),a.optInt("_score"));
            return d!=0?d:Long.compare(b.optLong("updatedAt"),a.optLong("updatedAt"));
        });
        JSONArray out=new JSONArray(); java.util.HashSet<String> seen=new java.util.HashSet<>();
        for(JSONObject x:ranked){
            String sig=(x.optString("type")+"|"+x.optString("title")+"|"+x.optString("body")).toLowerCase(java.util.Locale.ROOT);
            if(seen.add(sig)){x.remove("_score");out.put(x);}
            if(out.length()>=Math.max(1,Math.min(24,limit))) break;
        }
        return out;
    }

    synchronized JSONObject memoryStats() {
        JSONObject o=new JSONObject(); JSONArray all=list("all","",500);
        try{o.put("records",all.length()); JSONObject types=new JSONObject();
            for(int i=0;i<all.length();i++){JSONObject x=all.optJSONObject(i);if(x==null)continue;String t=x.optString("type","memory");types.put(t,types.optInt(t)+1);}
            o.put("types",types);
        }catch(Exception ignored){}
        return o;
    }

    synchronized JSONObject exportAll() {
        JSONObject out = new JSONObject();
        try { out.put("format", "aurion-memory-v4"); out.put("exportedAt", System.currentTimeMillis()); out.put("records", list("all", "", 5000)); out.put("accounts", accountStatus()); }
        catch (Exception ignored) { }
        return out;
    }

    synchronized JSONObject importAll(String raw) {
        JSONObject result = new JSONObject(); int imported = 0;
        try {
            JSONObject root = new JSONObject(raw); JSONArray records = root.optJSONArray("records");
            if (records == null && root.optJSONObject("memory") != null) records = root.optJSONObject("memory").optJSONArray("records");
            if (records == null) throw new IllegalArgumentException("Backup sem registros");
            for (int i = 0; i < records.length(); i++) {
                JSONObject x = records.optJSONObject(i); if (x == null) continue;
                add(x.optString("type", "memory"), x.optString("title", "Importado"), x.optString("body", ""), x.optString("meta", "{}")); imported++;
            }
            result.put("ok", true); result.put("imported", imported);
        } catch (Exception e) { try { result.put("ok", false); result.put("error", e.getMessage()); } catch (Exception ignored) { } }
        return result;
    }

    synchronized void setSecret(String name, String value) throws Exception {
        if (value == null || value.isEmpty()) { vault.edit().remove(name).apply(); return; }
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding"); cipher.init(Cipher.ENCRYPT_MODE, key());
        byte[] encrypted = cipher.doFinal(value.getBytes(StandardCharsets.UTF_8));
        byte[] packed = new byte[cipher.getIV().length + encrypted.length];
        System.arraycopy(cipher.getIV(), 0, packed, 0, cipher.getIV().length); System.arraycopy(encrypted, 0, packed, cipher.getIV().length, encrypted.length);
        vault.edit().putString(name, Base64.encodeToString(packed, Base64.NO_WRAP)).apply();
    }

    synchronized String getSecret(String name) {
        try {
            byte[] packed = Base64.decode(vault.getString(name, ""), Base64.NO_WRAP); if (packed.length < 13) return "";
            byte[] iv = new byte[12]; byte[] encrypted = new byte[packed.length - 12];
            System.arraycopy(packed, 0, iv, 0, 12); System.arraycopy(packed, 12, encrypted, 0, encrypted.length);
            Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding"); cipher.init(Cipher.DECRYPT_MODE, key(), new GCMParameterSpec(128, iv));
            return new String(cipher.doFinal(encrypted), StandardCharsets.UTF_8);
        } catch (Exception e) { return ""; }
    }

    synchronized JSONObject accountStatus() {
        JSONObject j = new JSONObject();
        for (String key : new String[]{"github","huggingface","openai","gemini","googleDrive","groq","deepseek","pollinations","siliconflow","xai","neurotron","custom"}) try { j.put(key, !getSecret(key).isEmpty()); } catch (Exception ignored) { }
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
