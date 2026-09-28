package com.digitalpen.auriont8i;

import android.app.*;import android.os.*;import android.content.*;import android.graphics.*;import android.graphics.drawable.*;import android.net.Uri;import android.provider.OpenableColumns;import android.view.*;import android.widget.*;import java.io.*;import java.util.*;

public class MainActivity extends Activity{
 final int BG=Color.rgb(3,3,8),SURF=Color.rgb(13,13,21),LINE=Color.rgb(40,40,55),MUTED=Color.rgb(155,155,172);
 LinearLayout root,stage,panel,tools; ImageView photo; TextView title,meta,hist,histCount; Bitmap source,current; Uri uri; ArrayList<HashMap<String,Integer>> history=new ArrayList<>(); int hp=-1;
 HashMap<String,Integer> v=new HashMap<>(); String active="LUZ";
 String[] keys={"exposure","contrast","highlights","shadows","whites","blacks","temp","tint","vibrance","sat","sharp","vignette"};
 public void onCreate(Bundle b){super.onCreate(b);for(String k:keys)v.put(k,0);build();}
 int dp(int x){return (int)(x*getResources().getDisplayMetrics().density+.5f);}
 TextView txt(String s,int z,int c){TextView t=new TextView(this);t.setText(s);t.setTextSize(z);t.setTextColor(c);t.setGravity(Gravity.CENTER_VERTICAL);t.setPadding(dp(10),0,dp(10),0);return t;}
 GradientDrawable box(int stroke){GradientDrawable g=new GradientDrawable();g.setColor(SURF);g.setCornerRadius(dp(14));if(stroke>0)g.setStroke(dp(stroke),Color.rgb(111,45,220));return g;}
 GradientDrawable quantum(){GradientDrawable g=new GradientDrawable(GradientDrawable.Orientation.LEFT_RIGHT,new int[]{Color.rgb(108,43,255),Color.rgb(255,36,184),Color.rgb(53,92,255),Color.rgb(0,210,255)});g.setCornerRadius(dp(18));return g;}
 Button button(String s){Button b=new Button(this);b.setText(s);b.setTextSize(11);b.setTextColor(Color.WHITE);b.setAllCaps(false);b.setBackground(box(1));b.setPadding(dp(8),0,dp(8),0);return b;}
 public void build(){
  root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setBackgroundColor(BG);root.setPadding(dp(12),dp(8),dp(12),dp(8));setContentView(root);
  LinearLayout head=new LinearLayout(this);head.setGravity(Gravity.CENTER_VERTICAL);TextView brand=txt("AURION T8i",20,Color.WHITE);brand.setTypeface(null,1);head.addView(brand,new LinearLayout.LayoutParams(0,dp(48),1));
  TextView ha=txt("⌕   ◌   ⚙",18,Color.WHITE);head.addView(ha,new LinearLayout.LayoutParams(-2,dp(48)));root.addView(head);
  View q=new View(this);q.setBackground(quantum());root.addView(q,new LinearLayout.LayoutParams(-1,dp(3)));
  LinearLayout quick=new LinearLayout(this);quick.setGravity(Gravity.CENTER_VERTICAL);title=txt("EDIÇÃO",12,MUTED);quick.addView(title,new LinearLayout.LayoutParams(0,dp(46),1));
  Button u=button("↶");u.setOnClickListener(x->undo());quick.addView(u,new LinearLayout.LayoutParams(dp(56),dp(38)));
  Button r=button("↷");r.setOnClickListener(x->redo());quick.addView(r,new LinearLayout.LayoutParams(dp(56),dp(38)));
  histCount=txt("HIST 0",11,Color.WHITE);histCount.setGravity(Gravity.CENTER);quick.addView(histCount,new LinearLayout.LayoutParams(dp(76),dp(42)));root.addView(quick);
  stage=new LinearLayout(this);stage.setOrientation(LinearLayout.VERTICAL);stage.setBackgroundColor(Color.BLACK);
  photo=new ImageView(this);photo.setScaleType(ImageView.ScaleType.FIT_CENTER);photo.setBackgroundColor(Color.BLACK);photo.setOnClickListener(x->{if(source==null)pick();});
  photo.setOnTouchListener((x,e)->{if(source==null)return false;if(e.getAction()==MotionEvent.ACTION_DOWN){photo.setImageBitmap(source);return true;}if(e.getAction()==MotionEvent.ACTION_UP||e.getAction()==MotionEvent.ACTION_CANCEL){render();return true;}return true;});
  stage.addView(photo,new LinearLayout.LayoutParams(-1,0,1));
  LinearLayout info=new LinearLayout(this);info.setGravity(Gravity.CENTER_VERTICAL);meta=txt("TOQUE NA ÁREA DA FOTO PARA IMPORTAR",10,MUTED);info.addView(meta,new LinearLayout.LayoutParams(0,dp(34),1));TextView before=txt("SEGURE · ANTES",9,MUTED);info.addView(before);stage.addView(info);
  hist=txt("RGB  HISTOGRAMA",10,Color.WHITE);hist.setBackgroundColor(Color.rgb(8,8,13));stage.addView(hist,new LinearLayout.LayoutParams(-1,dp(54)));
  root.addView(stage,new LinearLayout.LayoutParams(-1,0,1));
  HorizontalScrollView rail=new HorizontalScrollView(this);rail.setHorizontalScrollBarEnabled(false);tools=new LinearLayout(this);tools.setPadding(0,dp(7),0,dp(7));
  String[] names={"☼\nLuz","◉\nCor","HSL\nMix","⌁\nCurvas","◒\nRoda","◌\nMáscara","△\nDetalhe","✦\nEfeitos","⌗\nCrop","▦\nPresets","A\nAuto","⇧\nExportar"};
  for(String n:names){Button b=button(n);b.setGravity(Gravity.CENTER);b.setOnClickListener(x->open(((Button)x).getText().toString()));tools.addView(b,new LinearLayout.LayoutParams(dp(78),dp(58)));}
  rail.addView(tools);root.addView(rail,new LinearLayout.LayoutParams(-1,dp(72)));
  panel=new LinearLayout(this);panel.setOrientation(LinearLayout.VERTICAL);panel.setBackgroundColor(SURF);root.addView(panel,new LinearLayout.LayoutParams(-1,dp(170)));open("Luz");
  LinearLayout bottom=new LinearLayout(this);String[] bn={"▣\nBiblioteca","◆\nEditar","⇄\nConverter","▤\nProjetos","•••\nMais"};for(String n:bn){Button b=button(n);if(n.contains("Editar"))b.setBackground(quantum());if(n.contains("Biblioteca"))b.setOnClickListener(x->pick());bottom.addView(b,new LinearLayout.LayoutParams(0,dp(58),1));}root.addView(bottom);
 }
 void open(String raw){active=raw.replace("\n"," ").toUpperCase();panel.removeAllViews();TextView h=txt(active,13,Color.WHITE);h.setTypeface(null,1);panel.addView(h,new LinearLayout.LayoutParams(-1,dp(34)));
  if(active.contains("LUZ")){slider("Exposição","exposure",-100,100);slider("Contraste","contrast",-100,100);slider("Realces","highlights",-100,100);slider("Sombras","shadows",-100,100);}
  else if(active.contains("COR")){slider("Temperatura","temp",-100,100);slider("Matiz","tint",-100,100);slider("Vibração","vibrance",-100,100);slider("Saturação","sat",-100,100);}
  else if(active.contains("HSL")){hsl();}
  else if(active.contains("CURVAS"))curve();
  else if(active.contains("RODA"))wheel();
  else if(active.contains("MÁSCARA"))notice("Máscara local: engine será habilitado somente quando o processamento local estiver ligado.");
  else if(active.contains("DETALHE"))slider("Nitidez","sharp",0,100);
  else if(active.contains("EFEITOS"))slider("Vinheta","vignette",-100,100);
  else if(active.contains("AUTO"))auto();
  else if(active.contains("EXPORTAR"))exportPanel();
  else notice("Módulo reservado no blueprint. Não habilitado como função até existir processamento real.");
 }
 void slider(String label,String key,int lo,int hi){LinearLayout row=new LinearLayout(this);row.setGravity(Gravity.CENTER_VERTICAL);TextView l=txt(label,11,Color.LTGRAY);row.addView(l,new LinearLayout.LayoutParams(dp(105),dp(38)));SeekBar s=new SeekBar(this);s.setMax(hi-lo);s.setProgress(v.getOrDefault(key,0)-lo);TextView val=txt(""+v.getOrDefault(key,0),10,Color.WHITE);val.setGravity(Gravity.CENTER);s.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){public void onProgressChanged(SeekBar b,int p,boolean f){int z=p+lo;v.put(key,z);val.setText((z>0?"+":"")+z);render();}public void onStartTrackingTouch(SeekBar b){}public void onStopTrackingTouch(SeekBar b){snap();}});row.addView(s,new LinearLayout.LayoutParams(0,dp(38),1));row.addView(val,new LinearLayout.LayoutParams(dp(48),dp(38)));panel.addView(row);}
 void hsl(){LinearLayout dots=new LinearLayout(this);String[] c={"● R","● L","● A","● V","● C","● B","● R","● M"};for(String x:c){TextView t=txt(x,9,Color.WHITE);t.setGravity(Gravity.CENTER);dots.addView(t,new LinearLayout.LayoutParams(0,dp(34),1));}panel.addView(dots);notice("MIX DE CORES · Matiz / Saturação / Luminância por faixa entra no próximo engine; não é mostrado como controle falso.");}
 void curve(){notice("CURVAS RGB");View cv=new View(this){protected void onDraw(Canvas c){super.onDraw(c);Paint p=new Paint(1);p.setColor(Color.DKGRAY);for(int i=1;i<4;i++){c.drawLine(getWidth()*i/4f,0,getWidth()*i/4f,getHeight(),p);c.drawLine(0,getHeight()*i/4f,getWidth(),getHeight()*i/4f,p);}p.setColor(Color.rgb(200,120,255));p.setStrokeWidth(4);c.drawLine(0,getHeight(),getWidth(),0,p);}};panel.addView(cv,new LinearLayout.LayoutParams(-1,dp(100)));}
 void wheel(){notice("COLOR GRADING · SOMBRAS   MÉDIOS   REALCES");View w=new View(this){protected void onDraw(Canvas c){float cx=getWidth()/2f,cy=getHeight()/2f,r=Math.min(getWidth(),getHeight())*.42f;Paint p=new Paint(1);for(int i=0;i<360;i+=3){p.setColor(Color.HSVToColor(new float[]{i,1,1}));double a=Math.toRadians(i);c.drawCircle(cx+(float)Math.cos(a)*r*.72f,cy+(float)Math.sin(a)*r*.72f,6,p);}}};panel.addView(w,new LinearLayout.LayoutParams(-1,dp(100)));}
 void notice(String s){TextView t=txt(s,11,MUTED);t.setBackground(box(0));panel.addView(t,new LinearLayout.LayoutParams(-1,dp(60)));}
 void pick(){Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT);i.setType("image/*");i.addCategory(Intent.CATEGORY_OPENABLE);startActivityForResult(i,7);}
 protected void onActivityResult(int r,int c,Intent d){super.onActivityResult(r,c,d);if(r==7&&c==RESULT_OK&&d!=null){uri=d.getData();try{getContentResolver().takePersistableUriPermission(uri,Intent.FLAG_GRANT_READ_URI_PERMISSION);}catch(Exception e){}load();}}
 void load(){try(InputStream in=getContentResolver().openInputStream(uri)){source=BitmapFactory.decodeStream(in);if(source==null)throw new Exception();meta.setText("IMAGEM · "+source.getWidth()+"×"+source.getHeight()+" · edição não destrutiva");snap();render();}catch(Exception e){meta.setText("Não foi possível abrir esta imagem.");}}
 void render(){if(source==null)return;float ex=(float)Math.pow(2,v.get("exposure")/100f);float ct=1+v.get("contrast")/100f;float st=1+v.get("sat")/100f;float tr=v.get("temp")/300f,ti=v.get("tint")/400f;ColorMatrix cm=new ColorMatrix();cm.setSaturation(Math.max(0,st));ColorMatrix x=new ColorMatrix(new float[]{ex*ct*(1+tr),0,0,0,128*(1-ct),0,ex*ct*(1+ti),0,0,128*(1-ct),0,0,ex*ct*(1-tr),0,128*(1-ct),0,0,0,1,0});cm.postConcat(x);Bitmap out=Bitmap.createBitmap(source.getWidth(),source.getHeight(),Bitmap.Config.ARGB_8888);Canvas c=new Canvas(out);Paint p=new Paint(3);p.setColorFilter(new ColorMatrixColorFilter(cm));c.drawBitmap(source,0,0,p);current=out;photo.setImageBitmap(out);hist.setText(histText(out));}
 String histText(Bitmap b){int n=24;long sr=0,sg=0,sb=0;int step=Math.max(1,(b.getWidth()*b.getHeight())/8000);int[] px=new int[b.getWidth()*b.getHeight()];b.getPixels(px,0,b.getWidth(),0,0,b.getWidth(),b.getHeight());for(int i=0;i<px.length;i+=step){sr+=Color.red(px[i]);sg+=Color.green(px[i]);sb+=Color.blue(px[i]);n++;}return "RGB  HISTOGRAMA     R "+sr/n+"   G "+sg/n+"   B "+sb/n;}
 void snap(){while(history.size()>hp+1)history.remove(history.size()-1);history.add(new HashMap<>(v));hp=history.size()-1;histCount.setText("HIST "+history.size());}
 void undo(){if(hp>0){hp--;v.clear();v.putAll(history.get(hp));render();open(active);}}
 void redo(){if(hp+1<history.size()){hp++;v.clear();v.putAll(history.get(hp));render();open(active);}}
 void auto(){v.put("exposure",8);v.put("contrast",10);v.put("sat",5);snap();render();open("LUZ");}
 void exportPanel(){Button b=button("EXPORTAR JPG");b.setBackground(quantum());b.setOnClickListener(x->save());panel.addView(b,new LinearLayout.LayoutParams(-1,dp(54)));}
 void save(){if(current==null){meta.setText("Importe uma foto primeiro.");return;}try{String name="AURION_"+System.currentTimeMillis()+".jpg";android.content.ContentValues cv=new android.content.ContentValues();cv.put(android.provider.MediaStore.Images.Media.DISPLAY_NAME,name);cv.put(android.provider.MediaStore.Images.Media.MIME_TYPE,"image/jpeg");Uri u=getContentResolver().insert(android.provider.MediaStore.Images.Media.EXTERNAL_CONTENT_URI,cv);OutputStream o=getContentResolver().openOutputStream(u);current.compress(Bitmap.CompressFormat.JPEG,95,o);o.close();meta.setText("EXPORTADO · "+name);}catch(Exception e){meta.setText("Falha ao exportar.");}}
}