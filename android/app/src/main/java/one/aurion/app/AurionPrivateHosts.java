package one.aurion.app;

import java.util.Locale;

/**
 * Syntax-only private host allowlist. Does NOT replace authentication, TLS or
 * proof that a remote service belongs to the operator.
 */
public final class AurionPrivateHosts {
    private AurionPrivateHosts() { }

    public static boolean isAllowed(String host) {
        if (host == null || host.length() > 253) return false;
        String h = host.trim().toLowerCase(Locale.ROOT);
        if (h.equals("localhost") || h.equals("127.0.0.1")) return true;
        if (h.endsWith(".ts.net") && h.length() > ".ts.net".length()
                && !h.startsWith(".") && !h.contains("..")) return true;
        if (h.endsWith(".local") && h.length() > ".local".length()
                && !h.startsWith(".") && !h.contains("..")) return true;
        String[] chunks = h.split("\\.", -1);
        if (chunks.length != 4) return false;
        int[] octets = new int[4];
        for (int i = 0; i < chunks.length; i++) {
            String c = chunks[i];
            if (c.isEmpty() || c.length() > 3 || (c.length() > 1 && c.charAt(0) == '0')) return false;
            int value = 0;
            for (int j = 0; j < c.length(); j++) {
                char digit = c.charAt(j);
                if (digit < '0' || digit > '9') return false;
                value = value * 10 + digit - '0';
            }
            if (value > 255) return false;
            octets[i] = value;
        }
        return (octets[0] == 10)
            || (octets[0] == 192 && octets[1] == 168)
            || (octets[0] == 172 && octets[1] >= 16 && octets[1] <= 31)
            || (octets[0] == 100 && octets[1] >= 64 && octets[1] <= 127);
    }
}
