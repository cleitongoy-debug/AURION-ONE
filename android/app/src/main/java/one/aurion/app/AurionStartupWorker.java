package one.aurion.app;

import android.content.Context;
import androidx.annotation.NonNull;
import androidx.work.Worker;
import androidx.work.WorkerParameters;
import androidx.work.WorkManager;
import androidx.work.OneTimeWorkRequest;
import androidx.work.Constraints;
import androidx.work.NetworkType;
import androidx.work.ExistingWorkPolicy;

/** Apenas apos login do perfil titular, nunca invocado por perfis de convidados. */
public class AurionStartupWorker extends Worker {
    public AurionStartupWorker(@NonNull Context c,@NonNull WorkerParameters p){super(c,p);}
    @NonNull @Override public Result doWork(){
        Context c=getApplicationContext();
        AurionStore store=new AurionStore(c);
        store.setProfile("anark");
        AurionBootstrapIndex.seedPublicReferences(c,store);
        AurionBootstrapIndex.scanWorkspace(c,store,false);
        long now=System.currentTimeMillis();
        android.content.SharedPreferences state=c.getSharedPreferences("aurion_startup_v1",Context.MODE_PRIVATE);
        if(now-state.getLong("last_network_job",0)>3600000L){
            Constraints online=new Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build();
            OneTimeWorkRequest check=new OneTimeWorkRequest.Builder(AurionHourlyWorker.class)
                .setConstraints(online).build();
            WorkManager.getInstance(c).enqueueUniqueWork("aurion-start-online",
                    ExistingWorkPolicy.KEEP,check);
            state.edit().putLong("last_network_job",now).apply();
        }
        return Result.success();
    }
}
