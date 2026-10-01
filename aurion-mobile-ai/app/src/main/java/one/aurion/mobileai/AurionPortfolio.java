package one.aurion.mobileai;

import android.content.*;
import android.graphics.Color;
import android.view.*;
import android.widget.*;

import org.json.*;

import java.io.*;
import java.nio.charset.StandardCharsets;

/**
 * Portfólio e matriz profissional derivados do dossiê AURION.
 *
 * Regras:
 * - somente dados estruturados do asset portfolio_dossie.json;
 * - não transforma percentuais em horas;
 * - não soma blocos de horas diferentes;
 * - não publica cadastro/valores de clientes;
 * - itens pendentes continuam marcados como pendentes.
 */
public final class AurionPortfolio {
  private AurionPortfolio(){}

  private static JSONObject load(MainActivity a){
    try(InputStream in=a.getAssets().open("portfolio_dossie.json")){
      ByteArrayOutputStream out=new ByteArrayOutputStream();
      byte[] buf=new byte[8192];
      int n;
      while((n=in.read(buf))>0)out.write(buf,0,n);
      return new JSONObject(out.toString(StandardCharsets.UTF_8.name()));
    }catch(Exception e){
      return new JSONObject();
    }
  }

  static void addDashboardCard(MainActivity a){
    JSONObject d=load(a);
    JSONArray caps=d.optJSONArray("capabilities");
    JSONArray projects=d.optJSONArray("projects");
    a.body.addView(a.card(
        "PORTFÓLIO & CAPACIDADES",
        (caps==null?0:caps.length())+" serviços mapeados • "+
        (projects==null?0:projects.length())+" projetos catalogados • dossiê 28/09/2026"
    ));
  }

  static void show(MainActivity a){
    JSONObject d=load(a);
    a.clear("Portfólio · capacidades · provas");
    a.body.addView(a.tv(
        "Baseado no dossiê formal de 28/09/2026. Esta tela separa fatos registrados de pendências e não publica valores de clientes.",
        14
    ));

    JSONObject profile=d.optJSONObject("profile");
    if(profile!=null){
      a.body.addView(a.card(
          profile.optString("alias","ANARK")+" · "+profile.optString("entity","ONG DigitalPen"),
          profile.optString("name","")+"
"+profile.optString("base","")
      ));
    }

    JSONObject m=d.optJSONObject("audit_metrics");
    if(m!=null){
      a.body.addView(a.card(
          "AUDITORIA · BLOCOS INDEPENDENTES",
          "Sistema: "+m.optString("system_hours_window","—")+
          "
Operador ativo: "+m.optDouble("operator_active_hours",0)+" h"+
          "
Ciclos: "+m.optInt("operational_cycles",0)+
          " · Q-Level: "+m.optDouble("q_level",0)+
          "
Formação declarada: R$ "+String.format(java.util.Locale.US,"%,.0f",m.optDouble("training_investment_brl_declared",0)).replace(",",".")+
          "
"+m.optString("rule","")
      ));
    }

    section(a,"CURSOS · PROGRESSO AUDITADO");
    JSONArray courses=d.optJSONArray("courses");
    if(courses!=null)for(int i=0;i<courses.length();i++){
      JSONObject c=courses.optJSONObject(i);
      if(c==null)continue;
      String hours=c.isNull("total_hours")?"horas totais pendentes":c.optString("total_hours")+" h";
      a.body.addView(a.card(
          c.optString("name","Curso"),
          c.optInt("progress_percent",0)+"% concluído · "+hours+"
"+c.optString("status","")
      ));
    }

    section(a,"MATRIZ DE CAPACIDADES");
    JSONArray caps=d.optJSONArray("capabilities");
    if(caps!=null)for(int i=0;i<caps.length();i++){
      JSONObject c=caps.optJSONObject(i);
      if(c!=null)a.body.addView(a.card(c.optString("name","Capacidade"),c.optString("description","")));
    }

    section(a,"PROJETOS CATALOGADOS");
    JSONArray projects=d.optJSONArray("projects");
    if(projects!=null)for(int i=0;i<projects.length();i++){
      JSONObject p=projects.optJSONObject(i);
      if(p!=null)a.body.addView(a.card(
          p.optString("name","Projeto"),
          p.optString("status","")+"
"+p.optString("evidence_summary","")
      ));
    }

    section(a,"PROVAS PENDENTES");
    JSONArray pending=d.optJSONArray("pending_proofs");
    if(pending!=null)for(int i=0;i<pending.length();i++){
      a.body.addView(a.card("PENDENTE "+(i+1),pending.optString(i)));
    }

    Button studies=a.btn("📚 ABRIR ESTUDOS E CRONÔMETRO");
    studies.setOnClickListener(v->a.screen("Estudos"));
    a.body.addView(studies);

    Button clients=a.btn("🧰 ABRIR CLIENTES E HORAS");
    clients.setOnClickListener(v->a.screen("Clientes"));
    a.body.addView(clients);

    Button copy=a.btn("📋 COPIAR RESUMO PROFISSIONAL");
    copy.setOnClickListener(v->copySummary(a,d));
    a.body.addView(copy);

    a.body.addView(a.tv(
        "Regra do dossiê: nenhum percentual vira horas por cálculo e nenhuma prova pendente é promovida automaticamente.",
        12
    ));
  }

  private static void section(MainActivity a,String title){
    TextView t=a.tv(title,16);
    t.setTextColor(Color.rgb(255,170,55));
    a.body.addView(t);
  }

  private static void copySummary(MainActivity a,JSONObject d){
    JSONObject m=d.optJSONObject("audit_metrics");
    JSONArray caps=d.optJSONArray("capabilities");
    JSONArray projects=d.optJSONArray("projects");
    String text="AURION · ANARK · ONG DigitalPen\n"+
        "Capacidades mapeadas: "+(caps==null?0:caps.length())+"\n"+
        "Projetos catalogados: "+(projects==null?0:projects.length())+"\n"+
        "Operação ativa registrada: "+(m==null?"—":m.optDouble("operator_active_hours",0)+" h")+"\n"+
        "Ciclos: "+(m==null?"—":m.optInt("operational_cycles",0))+"\n"+
        "Cursos auditados: 3D Start 58%, Compositor HighEnd 50%, Combo Dose Diária 52%.\n"+
        "Horas totais desses cursos permanecem pendentes até prova documental.";
    ClipboardManager cm=(ClipboardManager)a.getSystemService(Context.CLIPBOARD_SERVICE);
    cm.setPrimaryClip(ClipData.newPlainText("AURION Portfólio",text));
    a.toast("Resumo profissional copiado.");
  }
}
