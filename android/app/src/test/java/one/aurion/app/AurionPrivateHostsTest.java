package one.aurion.app;

/** Runs as plain Java from CI; no Android/POCO and no real network calls. */
public final class AurionPrivateHostsTest {
    private static int checks=0;
    private static void test(String host, boolean expected) {
        boolean actual=AurionPrivateHosts.isAllowed(host);
        if (actual!=expected) throw new AssertionError(
            "Host policy mismatch: " + host + " expected=" + expected + " actual=" + actual);
        checks++;
    }
    public static void main(String[] args) {
        test(null, false);
        test("", false);
        test("localhost", true);
        test("127.0.0.1", true);
        test("127.0.0.2", false);
        test("10.1.2.3", true);
        test("10.evil.com", false);
        test("10.1.2.999", false);
        test("10.001.2.3", false);
        test("10.0.0.0", true);
        test("192.168.1.2", true);
        test("192.168.evil.com", false);
        test("192.168.1.2.evil.com", false);
        test("172.16.0.3", true);
        test("172.31.255.254", true);
        test("172.32.0.1", false);
        test("100.70.12.34", true);
        test("100.127.200.99", true);
        test("100.128.0.1", false);
        test("100.64.evil.com", false);
        test("mycomputer.mytailnet.ts.net", true);
        test("mycomputer.local", true);
        test(".ts.net", false);
        test("bad..ts.net", false);
        test("localhost.example.com", false);
        test("200.1.2.3", false);
        test("10.1.2.-1", false);
        test("10.1.2.256", false);
        System.out.println("PASS "+checks+"/"+checks+" private-host regression cases (no network).");
    }
}
