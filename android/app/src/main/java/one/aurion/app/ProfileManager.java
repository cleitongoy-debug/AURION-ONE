package one.aurion.app;

import android.content.Context;
import android.content.SharedPreferences;
import android.util.Base64;
import org.json.JSONArray;
import org.json.JSONObject;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.SecureRandom;
import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;

/** Local device identities. Server accounts must enforce the same ACL separately. */
final class ProfileManager {
    private static final String[] IDS = {"anark", "ds", "davi", "spectra"};
    private static final String ALL = "history,dedication,certificates,setup,home,project,capture,photo,colorlab,fxlab,video,timeline,motion,audio,convert,t8i,agent,memory,lab,accounts,resources,imagegen,comfy,connect,band,portfolio,delivery,diag,profiles";
    private static final String DS = "home,project,capture,photo,colorlab,fxlab,video,motion,audio,convert,agent,memory,dedication,certificates,portfolio,delivery";
    private static final String DAVI = "home,project,photo,video,agent,memory";
    private static final String SPECTRA = "home,portfolio";
    private final SharedPreferences prefs;
    private volatile String active = "";
    private int failed = 0;
    private long blockedUntil = 0;

    ProfileManager(Context context) { prefs = context.getSharedPreferences("aurion_profiles_v7", Context.MODE_PRIVATE); }
    String active() { return active; }
    boolean signedIn() { return !active.isEmpty(); }
    boolean owner() { return "anark".equals(active); }
    boolean allowed(String tab) {
        if (!signedIn()) return false;
        if (owner()) return true;
        return ("," + prefs.getString("tabs_" + active, "") + ",").contains("," + tab + ",");
    }
    synchronized JSONObject status() {
        JSONObject j = new JSONObject();
        try {
            j.put("bootstrapped", prefs.getBoolean("bootstrapped", false)); j.put("active", active);
            JSONArray people = new JSONArray();
            for (String id : IDS) people.put(new JSONObject().put("id", id).put("enabled", prefs.contains("pin_" + id))
                    .put("tabs", prefs.getString("tabs_" + id, id.equals("anark") ? ALL : "")));
            j.put("people", people);
        } catch (Exception ignored) { }
        return j;
    }
    synchronized JSONObject bootstrap(String id, String pin) {
        try {
            if (prefs.getBoolean("bootstrapped", false)) throw new IllegalStateException("Perfis já iniciados");
            checkId(id); checkPin(pin);
            if (!id.equals("anark") && !id.equals("ds")) throw new IllegalArgumentException("Primeiro aparelho: escolha ANARK ou DS");
            String salt = salt();
            // Legacy records remain ANARK unless this device explicitly belongs to DS.
            prefs.edit().putString("pin_" + id, hash(pin, salt)).putString("salt_" + id, salt)
                    .putString("tabs_" + id, id.equals("anark") ? ALL : DS)
                    .putBoolean("bootstrapped", true).putString("legacy_owner", id).commit();
            active = id;
            return ok();
        } catch (Exception e) { return error(e); }
    }
    synchronized JSONObject login(String id, String pin) {
        try {
            checkId(id);
            if (System.currentTimeMillis() < blockedUntil) throw new IllegalStateException("Aguarde antes de tentar novamente");
            String salt = prefs.getString("salt_" + id, "");
            if (salt.isEmpty() || !MessageDigest.isEqual(hash(pin, salt).getBytes(StandardCharsets.US_ASCII), prefs.getString("pin_" + id, "").getBytes(StandardCharsets.US_ASCII))) {
                if (++failed >= 5) { blockedUntil = System.currentTimeMillis() + 60000; failed = 0; }
                throw new IllegalArgumentException("Perfil ou código inválido");
            }
            failed = 0; active = id; return ok();
        } catch (Exception e) { return error(e); }
    }
    synchronized JSONObject provision(String id, String pin, String tabs) {
        try {
            if (!owner()) throw new SecurityException("Somente ANARK define perfis");
            checkId(id); if (id.equals("anark")) throw new IllegalArgumentException("Código do titular permanece neste aparelho");
            checkPin(pin);
            String salt = salt(), validated = validateTabs(tabs);
            prefs.edit().putString("pin_" + id, hash(pin, salt)).putString("salt_" + id, salt).putString("tabs_" + id, validated).commit();
            return ok();
        } catch (Exception e) { return error(e); }
    }
    synchronized JSONObject grant(String id, String tabs) {
        try {
            if (!owner()) throw new SecurityException("Somente ANARK altera abas");
            checkId(id); if (id.equals("anark") || !prefs.contains("pin_" + id)) throw new IllegalArgumentException("Perfil não configurado");
            prefs.edit().putString("tabs_" + id, validateTabs(tabs)).commit(); return ok();
        } catch (Exception e) { return error(e); }
    }
    synchronized void logout() { active = ""; }
    String legacyOwner() { return prefs.getString("legacy_owner", "anark"); }
    private static void checkId(String id) { for (String known : IDS) if (known.equals(id)) return; throw new IllegalArgumentException("Perfil desconhecido"); }
    private static void checkPin(String pin) { if (pin == null || pin.length() < 8 || pin.length() > 64) throw new IllegalArgumentException("Use um código de 8 a 64 caracteres"); }
    private static String validateTabs(String value) {
        StringBuilder valid = new StringBuilder();
        for (String item : value.split(",")) {
            item = item.trim();
            if (item.isEmpty()) continue;
            if (!( "," + ALL + ",").contains("," + item + ",") || item.equals("profiles") || item.equals("accounts") || item.equals("setup") || item.equals("diag") || item.equals("connect") || item.equals("history")) throw new IllegalArgumentException("Aba não autorizável: " + item);
            if (valid.length() > 0) valid.append(','); valid.append(item);
        }
        return valid.toString();
    }
    private static String salt() { byte[] bytes = new byte[24]; new SecureRandom().nextBytes(bytes); return Base64.encodeToString(bytes, Base64.NO_WRAP); }
    private static String hash(String pin, String salt) throws Exception {
        PBEKeySpec spec = new PBEKeySpec(pin.toCharArray(), Base64.decode(salt, Base64.NO_WRAP), 180000, 256);
        try { return Base64.encodeToString(SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256").generateSecret(spec).getEncoded(), Base64.NO_WRAP); }
        finally { spec.clearPassword(); }
    }
    private JSONObject ok() { try { return status().put("ok", true); } catch (Exception e) { return new JSONObject(); } }
    private static JSONObject error(Exception e) { try { return new JSONObject().put("ok", false).put("error", e.getMessage()); } catch (Exception ignored) { return new JSONObject(); } }
}
