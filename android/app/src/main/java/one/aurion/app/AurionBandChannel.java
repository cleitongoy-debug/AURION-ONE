package one.aurion.app;

import android.Manifest;
import android.app.Activity;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.os.Build;

import androidx.core.app.NotificationCompat;

import org.json.JSONObject;

/**
 * AURION -> notificacao LOCAL Android -> espelhamento OPCIONAL pelo Mi Fitness.
 * Nao realiza BLE direto, login no Mi Fitness, nem comprova entrega no pulso.
 * Eventos automaticos exigem opt-in do proprio operador.
 */
public final class AurionBandChannel {
    public static final int REQUEST_PERMISSION = 426;
    private static final String CHANNEL = "aurion_one_pulso_v1";
    private static final String PREF = "aurion_band_channel_v1";
    private static final String ENABLED = "enabled";
    private static final int MANUAL_TEST = 3901;
    private AurionBandChannel() { }

    private static SharedPreferences prefs(Context c) {
        return c.getSharedPreferences(PREF, Context.MODE_PRIVATE);
    }

    public static boolean hasPermission(Context c) {
        return Build.VERSION.SDK_INT < 33 || c.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED;
    }

    private static NotificationManager manager(Context c) {
        return (NotificationManager) c.getSystemService(Context.NOTIFICATION_SERVICE);
    }

    private static void ensureChannel(Context c) {
        NotificationManager nm = manager(c);
        if (nm == null) return;
        NotificationChannel ch = new NotificationChannel(CHANNEL, "AURION ONE · Pulso", NotificationManager.IMPORTANCE_DEFAULT);
        ch.setDescription("Alertas reais do AURION no POCO. O Mi Fitness controla o espelhamento no relogio.");
        ch.enableVibration(true);
        nm.createNotificationChannel(ch);
    }

    public static JSONObject status(Context c) {
        JSONObject j = new JSONObject();
        SharedPreferences p = prefs(c);
        NotificationManager nm = manager(c);
        try {
            boolean permission = hasPermission(c);
            boolean androidEnabled = nm != null && nm.areNotificationsEnabled();
            boolean channelEnabled = true;
            if (nm != null) {
                NotificationChannel ch = nm.getNotificationChannel(CHANNEL);
                channelEnabled = ch == null || ch.getImportance() != NotificationManager.IMPORTANCE_NONE;
            }
            j.put("optIn", p.getBoolean(ENABLED, false));
            j.put("androidPermission", permission);
            j.put("androidEnabled", androidEnabled);
            j.put("channelEnabled", channelEnabled);
            j.put("phoneChannelReady", permission && androidEnabled && channelEnabled);
            j.put("lastPostedAt", p.getLong("lastPostedAt", 0));
            j.put("lastTestPostedAt", p.getLong("lastTestPostedAt", 0));
            j.put("lastEventId", p.getInt("lastEventId", 0));
            j.put("operatorBandReceiptAt", p.getLong("operatorBandReceiptAt", 0));
            j.put("lastError", p.getString("lastError", ""));
            j.put("wristDeliveryVerifiedAutomatically", false);
            j.put("mirroring", "DEPENDENTE_DO_MI_FITNESS_E_DA_PERMISSAO_DO_USUARIO");
        } catch (Exception e) {
            try { j.put("error", "diagnostico_indisponivel"); } catch (Exception ignored) { }
        }
        return j;
    }

    public static JSONObject setEnabled(Context c, boolean enabled) {
        if (enabled && (!hasPermission(c) || manager(c) == null || !manager(c).areNotificationsEnabled())) {
            JSONObject result = status(c);
            try { result.put("ok", false).put("reason", "permissao_de_notificacao_ausente"); }
            catch (Exception ignored) { }
            return result;
        }
        if (enabled) ensureChannel(c);
        prefs(c).edit().putBoolean(ENABLED, enabled).apply();
        JSONObject result = status(c);
        try { result.put("ok", true); } catch (Exception ignored) { }
        return result;
    }

    /** Chamado somente quando um evento do verificador realmente muda (ids 1001-1005). */
    public static boolean sendVerifiedEvent(Context c, int eventId) {
        if (!prefs(c).getBoolean(ENABLED, false)) return false;
        String body;
        switch (eventId) {
            case 1001: body = "Nova versao APK detectada; revisar antes de instalar."; break;
            case 1002: body = "Git alterado; revisao pendente. Nao e implantacao."; break;
            case 1003: body = "Listagem do Drive mudou; sync nao comprovado."; break;
            case 1004: body = "Indice Hugging Face alterado; revisar fonte."; break;
            case 1005: body = "Snapshot do PC respondeu com alteracao; conferir."; break;
            default: return false; // NUNCA exibir mensagem arbitraria/segredo no pulso.
        }
        return post(c, eventId, "AURION ONE · Alteracao detectada", body);
    }

    public static JSONObject sendManualTest(Context c) {
        JSONObject out = status(c);
        if (!prefs(c).getBoolean(ENABLED, false)) {
            try { out.put("ok", false).put("reason", "canal_nao_ativado"); } catch (Exception ignored) { }
            return out;
        }
        boolean sent = post(c, MANUAL_TEST, "AURION ONE · Teste do pulso",
                "Mensagem do POCO. Confirme no painel se chegou a Mi Band.");
        out = status(c);
        try { out.put("ok", sent).put("postedToAndroid", sent); } catch (Exception ignored) { }
        return out;
    }

    public static JSONObject confirmOperatorReceipt(Context c) {
        SharedPreferences p = prefs(c);
        JSONObject out = status(c);
        if (p.getLong("lastTestPostedAt", 0) == 0) {
            try { out.put("ok", false).put("reason", "nenhum_teste_Android_anterior"); } catch (Exception ignored) { }
            return out;
        }
        p.edit().putLong("operatorBandReceiptAt", System.currentTimeMillis()).apply();
        out = status(c);
        try { out.put("ok", true).put("proof", "RELATO_DE_TESTE_FISICO_DO_OPERADOR"); } catch (Exception ignored) { }
        return out;
    }

    private static boolean post(Context c, int id, String title, String message) {
        try {
            NotificationManager nm = manager(c);
            if (!hasPermission(c) || nm == null || !nm.areNotificationsEnabled()) {
                prefs(c).edit().putString("lastError", "Android_sem_permissao").apply();
                return false;
            }
            ensureChannel(c);
            NotificationChannel ch = nm.getNotificationChannel(CHANNEL);
            if (ch != null && ch.getImportance() == NotificationManager.IMPORTANCE_NONE) {
                prefs(c).edit().putString("lastError", "canal_bloqueado").apply();
                return false;
            }
            Intent intent = new Intent(c, MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP);
            PendingIntent pi = PendingIntent.getActivity(c, id, intent,
                    PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
            Notification n = new NotificationCompat.Builder(c, CHANNEL)
                    .setSmallIcon(android.R.drawable.ic_dialog_info)
                    .setContentTitle(title)
                    .setContentText(message)
                    .setStyle(new NotificationCompat.BigTextStyle().bigText(message))
                    .setContentIntent(pi)
                    .setVisibility(NotificationCompat.VISIBILITY_PRIVATE)
                    .setAutoCancel(true)
                    .build();
            nm.notify(id, n);
            SharedPreferences.Editor edit = prefs(c).edit()
                    .putLong("lastPostedAt", System.currentTimeMillis())
                    .putInt("lastEventId", id)
                    .remove("lastError");
            if (id == MANUAL_TEST) edit.putLong("lastTestPostedAt", System.currentTimeMillis())
                    .remove("operatorBandReceiptAt");
            edit.apply();
            return true;
        } catch (SecurityException e) {
            prefs(c).edit().putString("lastError", "sem_autorizacao_Android").apply();
        } catch (Exception e) {
            prefs(c).edit().putString("lastError", "falha_local_notificacao").apply();
        }
        return false;
    }
}
