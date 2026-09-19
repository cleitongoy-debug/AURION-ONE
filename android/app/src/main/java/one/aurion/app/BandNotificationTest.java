package one.aurion.app;

import android.Manifest;
import android.app.Activity;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.content.Context;
import android.content.pm.PackageManager;
import android.os.Build;
import android.widget.Toast;

/** Sends an ordinary Android notification. Mi Fitness decides whether to mirror it. */
public final class BandNotificationTest {
    public static final int REQUEST_NOTIFICATIONS = 109;
    private static final String CHANNEL = "aurion_band_test";

    private BandNotificationTest() { }

    public static void requestOrSend(Activity activity) {
        if (Build.VERSION.SDK_INT >= 33 && activity.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            activity.requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, REQUEST_NOTIFICATIONS);
            return;
        }
        send(activity);
    }

    public static void onPermissionResult(Activity activity, int requestCode, int[] results) {
        if (requestCode != REQUEST_NOTIFICATIONS) return;
        if (results.length > 0 && results[0] == PackageManager.PERMISSION_GRANTED) send(activity);
        else Toast.makeText(activity, "Notificações não autorizadas no Android", Toast.LENGTH_LONG).show();
    }

    private static void send(Activity activity) {
        NotificationManager manager = (NotificationManager) activity.getSystemService(Context.NOTIFICATION_SERVICE);
        if (manager == null) {
            Toast.makeText(activity, "Serviço de notificações indisponível", Toast.LENGTH_LONG).show();
            return;
        }
        NotificationChannel channel = new NotificationChannel(CHANNEL, "AURION · Teste Mi Band", NotificationManager.IMPORTANCE_DEFAULT);
        channel.setDescription("Notificação de teste iniciada manualmente pelo operador");
        manager.createNotificationChannel(channel);
        if (!manager.areNotificationsEnabled()) {
            Toast.makeText(activity, "Habilite as notificações do AURION nas configurações do Android", Toast.LENGTH_LONG).show();
            return;
        }
        Notification notification = new Notification.Builder(activity, CHANNEL)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle("AURION ONE · teste")
            .setContentText("Se esta mensagem aparecer na Mi Band, confirme no painel.")
            .setAutoCancel(true)
            .build();
        manager.notify(109, notification);
        Toast.makeText(activity, "Notificação enviada ao Android; confirme o recebimento na Mi Band", Toast.LENGTH_LONG).show();
    }
}
