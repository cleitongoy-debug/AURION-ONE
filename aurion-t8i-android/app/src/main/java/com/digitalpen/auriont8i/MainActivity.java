package com.digitalpen.auriont8i;

import android.app.*; import android.os.*; import android.content.*; import android.graphics.*; import android.graphics.drawable.*; import android.net.Uri; import android.provider.OpenableColumns; import android.database.Cursor; import android.view.*; import android.widget.*; import java.io.*; import java.util.*;

public class MainActivity extends Activity {
 LinearLayout root, body, controls; ImageView preview; TextView title,status,fileInfo; SeekBar exposure,contrast,saturation; Uri currentUri; Bitmap source, working;
 int cyan=Color.rgb(0,183,217), violet=Color.rgb(142,108,245), coral=Color.rgb(255,107,95), bg=Color.rgb(8,10,16), panel=Color.rgb(17,19,23);
 @Override public void onCreate(Bundle b){super.onCreate(b); build();}
 TextView txt(String s,int sp){ TextView v=new TextView(this); v.setText(s);v.setTextColor(Color.WHITE);v.setTextSize(sp);v.setPadding(16,12,16,12);return v;}
 Button btn(String s){Button b=new Button(this);b.setText(s);b.setTextColor(Color.WHITE);GradientDrawable g=new GradientDrawable();g.setColor(panel);g.setStroke(2,cyan);g.setCornerRadius(22);b.setBackground(g);return b;}
 void build(){
  root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setBackgroundColor(bg);setContentView(root);
  title=txt("AURION T8i · QUANTUM PHOTO STUDIO",18);title.setTextColor(cyan);root.addView(title);
  status=txt("LOCAL FIRST · Natural Premium · v0.1",12);status.setTextColor(violet);root.addView(status);
  HorizontalScrollView nav=new HorizontalScrollView(this);LinearLayout row=new LinearLayout(this);row.setOrientation(LinearLayout.HORIZONTAL);
  String[] tabs={"BIBLIOTECA","REVELAÇÃO","AUTO","COR/LUT","CONVERSOR","ENTREGA","AGENTE","LAB"};
  for(String t:tabs){Button x=btn(t);x.setOnClickListener(v->status.setText(((Button)v).getText()+" · pronto para fluxo mobile"));row.addView(x);}
  nav.addView(row);root.addView(nav,new LinearLayout.LayoutParams(-1,-2));
  body=new LinearLayout(this);body.setOrientation(LinearLayout.VERTICAL);body.setPadding(12,8,12,8);root.addView(body,new LinearLayout.LayoutParams(-1,0,1));
  preview=new ImageView(this);preview.setBackgroundColor(Color.BLACK);preview.setScaleType(ImageView.ScaleType.FIT_CENTER);body.addView(preview,new LinearLayout.LayoutParams(-1,0,1));
  fileInfo=txt("Nenhuma imagem carregada. Toque IMPORTAR.",12);body.addView(fileInfo);
  controls=new LinearLayout(this);controls.setOrientation(LinearLayout.VERTICAL);body.addView(controls);
  addSlider("EXPOSIÇÃO", exposure=new SeekBar(this),50); addSlider("CONTRASTE",contrast=new SeekBar(this),50); addSlider("SATURAÇÃO",saturation=new SeekBar(this),50);
  SeekBar.OnSeekBarChangeListener l=new SeekBar.OnSeekBarChangeListener(){public void onProgressChanged(SeekBar s,int p,boolean f){render();}public void onStartTrackingTouch(SeekBar s){}public void onStopTrackingTouch(SeekBar s){}}; exposure.setOnSeekBarChangeListener(l);contrast.setOnSeekBarChangeListener(l);saturation.setOnSeekBarChangeListener(l);
  LinearLayout actions=new LinearLayout(this);actions.setOrientation(LinearLayout.HORIZONTAL);
  Button imp=btn("IMPORTAR");imp.setOnClickListener(v->pick());actions.addView(imp,new LinearLayout.LayoutParams(0,-2,1));
  Button auto=btn("AUTO");auto.setOnClickListener(v->{exposure.setProgress(52);contrast.setProgress(56);saturation.setProgress(53);render();status.setText("AUTO conservador aplicado · não destrutivo");});actions.addView(auto,new LinearLayout.LayoutParams(0,-2,1));
  Button exp=btn("ENTREGA");exp.setOnClickListener(v->saveDialog());actions.addView(exp,new LinearLayout.LayoutParams(0,-2,1));
  root.addView(actions);
 }
 void addSlider(String n,SeekBar s,int p){LinearLayout r=new LinearLayout(this);r.setGravity(Gravity.CENTER_VERTICAL);TextView t=txt(n,11);t.setTextColor(Color.LTGRAY);r.addView(t,new LinearLayout.LayoutParams(0,-2,.32f));s.setMax(100);s.setProgress(p);r.addView(s,new LinearLayout.LayoutParams(0,-2,.68f));controls.addView(r);}
 void pick(){Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT);i.addCategory(Intent.CATEGORY_OPENABLE);i.setType("image/*");i.putExtra(Intent.EXTRA_MIME_TYPES,new String[]{"image/*","application/octet-stream"});startActivityForResult(i,42);}
 @Override protected void onActivityResult(int r,int c,Intent d){super.onActivityResult(r,c,d);if(r==42&&c==RESULT_OK&&d!=null){currentUri=d.getData();try{getContentResolver().takePersistableUriPermission(currentUri,Intent.FLAG_GRANT_READ_URI_PERMISSION);}catch(Exception e){} load();}}
 void load(){try(InputStream in=getContentResolver().openInputStream(currentUri)){source=BitmapFactory.decodeStream(in);if(source==null){fileInfo.setText(name(currentUri)+" · formato detectado, preview nativo indisponível nesta build");status.setText("Arquivo preservado · RAW/codec avançado entra no próximo núcleo");return;} fileInfo.setText(name(currentUri)+" · "+source.getWidth()+"×"+source.getHeight());render();}catch(Exception e){status.setText("Falha ao abrir: "+e.getMessage());}}
 String name(Uri u){try(Cursor c=getContentResolver().query(u,null,null,null,null)){if(c!=null&&c.moveToFirst()){int i=c.getColumnIndex(OpenableColumns.DISPLAY_NAME);if(i>=0)return c.getString(i);}}catch(Exception e){}return "imagem";}
 void render(){if(source==null)return;float ev=(exposure.getProgress()-50)/50f;float con=(contrast.getProgress()-50)/50f;float sat=saturation.getProgress()/50f;float scale=(float)Math.pow(2,ev);float c=con+1f;float t=128f*(1f-c);ColorMatrix m=new ColorMatrix(new float[]{scale*c,0,0,0,t,0,scale*c,0,0,t,0,0,scale*c,0,t,0,0,0,1,0});ColorMatrix sm=new ColorMatrix();sm.setSaturation(sat);m.postConcat(sm);preview.setImageBitmap(source);preview.setColorFilter(new android.graphics.ColorMatrixColorFilter(m));}
 void saveDialog(){if(source==null){status.setText("Importe uma imagem primeiro.");return;} final String[] o={"JPEG · qualidade máxima","PNG · sem perdas","WEBP · qualidade máxima"};new AlertDialog.Builder(this).setTitle("ENTREGA MASTER").setItems(o,(d,w)->create(w)).show();}
 void create(int type){String mime=type==1?"image/png":type==2?"image/webp":"image/jpeg";String ext=type==1?".png":type==2?".webp":".jpg";Intent i=new Intent(Intent.ACTION_CREATE_DOCUMENT);i.addCategory(Intent.CATEGORY_OPENABLE);i.setType(mime);i.putExtra(Intent.EXTRA_TITLE,"AURION_T8i_MASTER"+ext);pendingType=type;startActivityForResult(i,77);}
 int pendingType=0;
 void exportTo(Uri u){try(OutputStream out=getContentResolver().openOutputStream(u)){Bitmap.CompressFormat f=pendingType==1?Bitmap.CompressFormat.PNG:pendingType==2?Bitmap.CompressFormat.WEBP_LOSSLESS:Bitmap.CompressFormat.JPEG;source.compress(f,100,out);status.setText("ENTREGA concluída · arquivo master criado");}catch(Exception e){status.setText("Erro na entrega: "+e.getMessage());}}
 @Override protected void onActivityResult(int r,int c,Intent d,android.os.Bundle x){super.onActivityResult(r,c,d,x);}
}
