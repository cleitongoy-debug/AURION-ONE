package one.aurion.app;

import android.content.ContentResolver;
import android.content.ContentValues;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.pdf.PdfDocument;
import android.media.MediaCodec;
import android.media.MediaExtractor;
import android.media.MediaFormat;
import android.media.MediaMuxer;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.provider.MediaStore;
import android.util.Base64;

import org.json.JSONObject;

import java.io.FileDescriptor;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.ByteBuffer;
import java.util.Locale;

final class MediaTools {
    private MediaTools() { }

    static JSONObject saveDataImage(Context context, String format, int quality, String dataUrl) {
        JSONObject result = new JSONObject();
        try {
            String f = format == null ? "JPEG" : format.toUpperCase(Locale.ROOT);
            String ext = f.equals("PNG") ? "png" : f.equals("WEBP") ? "webp" : f.equals("PDF") ? "pdf" : "jpg";
            int comma = dataUrl.indexOf(','); byte[] bytes = Base64.decode(comma >= 0 ? dataUrl.substring(comma + 1) : dataUrl, Base64.DEFAULT);
            if (f.equals("PDF")) return imageBytesToPdf(context, bytes);
            String mime = ext.equals("png") ? "image/png" : ext.equals("webp") ? "image/webp" : "image/jpeg";
            Uri target = imageTarget(context, "AURION_EDIT_" + System.currentTimeMillis() + "." + ext, mime);
            try (OutputStream out = context.getContentResolver().openOutputStream(target)) { if (out == null) throw new IllegalStateException("Destino indisponível"); out.write(bytes); }
            result.put("ok", true); result.put("format", f); result.put("uri", target.toString()); result.put("message", "Salvo em Pictures/AURION/EXPORTS");
        } catch (Exception e) { putError(result, e); }
        return result;
    }

    static JSONObject saveBase64File(Context context, String filename, String mime, String base64) {
        JSONObject result = new JSONObject();
        try {
            String clean = filename == null ? "aurion_export.bin" : filename.replaceAll("[^A-Za-z0-9._-]", "_");
            byte[] bytes = Base64.decode(base64, Base64.DEFAULT); ContentValues v = new ContentValues();
            v.put(MediaStore.Downloads.DISPLAY_NAME, clean); v.put(MediaStore.Downloads.MIME_TYPE, mime == null ? "application/octet-stream" : mime);
            if (Build.VERSION.SDK_INT >= 29) v.put(MediaStore.Downloads.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS + "/AURION/EXPORTS");
            Uri uri = context.getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, v); if (uri == null) throw new IllegalStateException("Destino indisponível");
            try (OutputStream out = context.getContentResolver().openOutputStream(uri)) { if (out == null) throw new IllegalStateException("Saída indisponível"); out.write(bytes); }
            result.put("ok", true); result.put("uri", uri.toString()); result.put("message", clean + " salvo em Downloads/AURION/EXPORTS");
        } catch (Exception e) { putError(result, e); }
        return result;
    }

    private static JSONObject imageBytesToPdf(Context context, byte[] bytes) {
        JSONObject result = new JSONObject(); PdfDocument pdf = new PdfDocument();
        try {
            Bitmap bitmap = BitmapFactory.decodeByteArray(bytes, 0, bytes.length); if (bitmap == null) throw new IllegalArgumentException("Imagem inválida");
            int pageWidth = 2480; int pageHeight = Math.max(3508, Math.round(pageWidth * (bitmap.getHeight() / (float) bitmap.getWidth())));
            PdfDocument.Page page = pdf.startPage(new PdfDocument.PageInfo.Builder(pageWidth, pageHeight, 1).create());
            Canvas canvas = page.getCanvas(); float scale = Math.min(pageWidth / (float) bitmap.getWidth(), pageHeight / (float) bitmap.getHeight());
            float left = (pageWidth - bitmap.getWidth() * scale) / 2f; float top = (pageHeight - bitmap.getHeight() * scale) / 2f;
            canvas.save(); canvas.translate(left, top); canvas.scale(scale, scale); canvas.drawBitmap(bitmap, 0, 0, null); canvas.restore(); pdf.finishPage(page);
            ContentValues v = new ContentValues(); v.put(MediaStore.Downloads.DISPLAY_NAME, "AURION_EDIT_" + System.currentTimeMillis() + ".pdf"); v.put(MediaStore.Downloads.MIME_TYPE, "application/pdf");
            if (Build.VERSION.SDK_INT >= 29) v.put(MediaStore.Downloads.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS + "/AURION/EXPORTS");
            Uri uri = context.getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, v); if (uri == null) throw new IllegalStateException("Destino PDF indisponível");
            try (OutputStream out = context.getContentResolver().openOutputStream(uri)) { pdf.writeTo(out); }
            bitmap.recycle(); result.put("ok", true); result.put("format", "PDF"); result.put("uri", uri.toString()); result.put("message", "PDF salvo em Downloads/AURION/EXPORTS");
        } catch (Exception e) { putError(result, e); }
        finally { pdf.close(); }
        return result;
    }

    static JSONObject trim(Context context, Uri source, String kind, double startSeconds, double endSeconds) {
        JSONObject result = new JSONObject(); MediaExtractor extractor = new MediaExtractor(); MediaMuxer muxer = null;
        try {
            if (Build.VERSION.SDK_INT < 29) throw new UnsupportedOperationException("Recorte local requer Android 10+");
            extractor.setDataSource(context, source, null);
            boolean audioOnly = "audio".equalsIgnoreCase(kind); String ext = audioOnly ? "m4a" : "mp4"; String mime = audioOnly ? "audio/mp4" : "video/mp4";
            ContentValues values = new ContentValues(); values.put(MediaStore.MediaColumns.DISPLAY_NAME, "AURION_TRIM_" + System.currentTimeMillis() + "." + ext); values.put(MediaStore.MediaColumns.MIME_TYPE, mime);
            Uri target;
            if (audioOnly) { values.put(MediaStore.MediaColumns.RELATIVE_PATH, Environment.DIRECTORY_MUSIC + "/AURION/EXPORTS"); target = context.getContentResolver().insert(MediaStore.Audio.Media.EXTERNAL_CONTENT_URI, values); }
            else { values.put(MediaStore.MediaColumns.RELATIVE_PATH, Environment.DIRECTORY_MOVIES + "/AURION/EXPORTS"); target = context.getContentResolver().insert(MediaStore.Video.Media.EXTERNAL_CONTENT_URI, values); }
            if (target == null) throw new IllegalStateException("Destino indisponível");
            android.os.ParcelFileDescriptor pfd = context.getContentResolver().openFileDescriptor(target, "rw"); if (pfd == null) throw new IllegalStateException("Arquivo de saída indisponível");
            muxer = new MediaMuxer(pfd.getFileDescriptor(), MediaMuxer.OutputFormat.MUXER_OUTPUT_MPEG_4);
            int tracks = extractor.getTrackCount(); int[] map = new int[tracks]; java.util.Arrays.fill(map, -1); int selected = 0; int maxBuffer = 1024 * 1024;
            for (int i = 0; i < tracks; i++) {
                MediaFormat fmt = extractor.getTrackFormat(i); String trackMime = fmt.getString(MediaFormat.KEY_MIME); boolean use = trackMime != null && (audioOnly ? trackMime.startsWith("audio/") : (trackMime.startsWith("audio/") || trackMime.startsWith("video/")));
                if (use) { map[i] = muxer.addTrack(fmt); extractor.selectTrack(i); selected++; if (fmt.containsKey(MediaFormat.KEY_MAX_INPUT_SIZE)) maxBuffer = Math.max(maxBuffer, fmt.getInteger(MediaFormat.KEY_MAX_INPUT_SIZE)); }
            }
            if (selected == 0) throw new IllegalArgumentException("Nenhuma faixa compatível");
            muxer.start(); long startUs = Math.max(0, (long)(startSeconds * 1_000_000)); long endUs = endSeconds <= 0 ? Long.MAX_VALUE : (long)(endSeconds * 1_000_000);
            extractor.seekTo(startUs, MediaExtractor.SEEK_TO_PREVIOUS_SYNC); ByteBuffer buffer = ByteBuffer.allocateDirect(maxBuffer); MediaCodec.BufferInfo info = new MediaCodec.BufferInfo();
            while (true) {
                int sourceTrack = extractor.getSampleTrackIndex(); if (sourceTrack < 0) break; long sampleTime = extractor.getSampleTime(); if (sampleTime < 0 || sampleTime > endUs) break;
                int destTrack = sourceTrack < map.length ? map[sourceTrack] : -1; if (destTrack < 0) { extractor.advance(); continue; }
                buffer.clear(); int size = extractor.readSampleData(buffer, 0); if (size < 0) break;
                info.offset = 0; info.size = size; info.presentationTimeUs = Math.max(0, sampleTime - startUs); info.flags = extractor.getSampleFlags(); muxer.writeSampleData(destTrack, buffer, info); extractor.advance();
            }
            muxer.stop(); muxer.release(); muxer = null; pfd.close();
            result.put("ok", true); result.put("uri", target.toString()); result.put("message", "Recorte salvo localmente em " + (audioOnly ? "Music" : "Movies") + "/AURION/EXPORTS");
        } catch (Exception e) { putError(result, e); try { if (muxer != null) { muxer.stop(); muxer.release(); } } catch (Exception ignored) { } }
        finally { extractor.release(); }
        return result;
    }

    private static Uri imageTarget(Context context, String name, String mime) {
        ContentValues values = new ContentValues(); values.put(MediaStore.Images.Media.DISPLAY_NAME, name); values.put(MediaStore.Images.Media.MIME_TYPE, mime);
        if (Build.VERSION.SDK_INT >= 29) values.put(MediaStore.Images.Media.RELATIVE_PATH, Environment.DIRECTORY_PICTURES + "/AURION/EXPORTS");
        Uri target = context.getContentResolver().insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values); if (target == null) throw new IllegalStateException("Destino indisponível"); return target;
    }
    private static void putError(JSONObject target, Exception e) { try { target.put("ok", false); target.put("error", e.getClass().getSimpleName()); target.put("message", e.getMessage()); } catch (Exception ignored) { } }
}
