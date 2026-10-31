# Compares a render with the painting by eye: writes a 50% overlay, an edge comparison and a side-by-side, all 1536x864.
# Edge comparison: painting edges in red, render edges in cyan, where both agree shows white.
# Usage: compare_frame.ps1 <painting> <render> <out-prefix>   (writes <out-prefix>_overlay.png, _edges.png, _side.png)
param([string]$Painting, [string]$Render, [string]$Out)
Add-Type -AssemblyName System.Drawing
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @"
using System; using System.Drawing; using System.Drawing.Imaging; using System.Drawing.Drawing2D; using System.Runtime.InteropServices;
public static class Cmp {
    public const int W = 1536, H = 864;
    public static int[] Load(string p) { using (var b0 = new Bitmap(p)) using (var b = new Bitmap(W, H, PixelFormat.Format32bppArgb)) {
        using (var g = Graphics.FromImage(b)) { g.InterpolationMode = InterpolationMode.HighQualityBicubic; g.DrawImage(b0, 0, 0, W, H); }
        var d = b.LockBits(new Rectangle(0, 0, W, H), ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb);
        var px = new int[W * H]; Marshal.Copy(d.Scan0, px, 0, px.Length); b.UnlockBits(d); return px; } }
    static void Save(int[] px, int w, int h, string p) { using (var b = new Bitmap(w, h, PixelFormat.Format32bppArgb)) {
        var d = b.LockBits(new Rectangle(0, 0, w, h), ImageLockMode.WriteOnly, PixelFormat.Format32bppArgb);
        Marshal.Copy(px, 0, d.Scan0, px.Length); b.UnlockBits(d); b.Save(p, ImageFormat.Png); } }
    static float L(int c) { return (0.2126f * ((c >> 16) & 255) + 0.7152f * ((c >> 8) & 255) + 0.0722f * (c & 255)) / 255f; }
    // Edges of the shapes, not the texture: blur, Sobel, then keep the strongest ~12% (contrast-normalised per image).
    static float[] Edges(int[] px) {
        var l = new float[W * H]; for (int i = 0; i < l.Length; i++) l[i] = (float)Math.Sqrt(L(px[i]));
        var t = new float[W * H]; var b = new float[W * H]; int r = 2;
        for (int y = 0; y < H; y++) for (int x = 0; x < W; x++) { float s = 0; int n = 0; for (int k = -r; k <= r; k++) { int xx = x + k; if (xx < 0 || xx >= W) continue; s += l[y * W + xx]; n++; } t[y * W + x] = s / n; }
        for (int y = 0; y < H; y++) for (int x = 0; x < W; x++) { float s = 0; int n = 0; for (int k = -r; k <= r; k++) { int yy = y + k; if (yy < 0 || yy >= H) continue; s += t[yy * W + x]; n++; } b[y * W + x] = s / n; }
        var e = new float[W * H]; var hist = new int[1001];
        for (int y = 1; y < H - 1; y++) for (int x = 1; x < W - 1; x++) {
            float gx = b[(y - 1) * W + x + 1] + 2 * b[y * W + x + 1] + b[(y + 1) * W + x + 1] - b[(y - 1) * W + x - 1] - 2 * b[y * W + x - 1] - b[(y + 1) * W + x - 1];
            float gy = b[(y + 1) * W + x - 1] + 2 * b[(y + 1) * W + x] + b[(y + 1) * W + x + 1] - b[(y - 1) * W + x - 1] - 2 * b[(y - 1) * W + x] - b[(y - 1) * W + x + 1];
            float m = (float)Math.Sqrt(gx * gx + gy * gy); e[y * W + x] = m; hist[Math.Min(1000, (int)(m * 500))]++; }
        int want = (int)(0.12 * W * H), acc = 0, cut = 1000; while (cut > 0 && acc < want) { acc += hist[cut]; cut--; }
        float thr = cut / 500f; for (int i = 0; i < e.Length; i++) e[i] = e[i] > thr ? 1f : 0f; return e; }
    public static double Run(string a, string b, string outp) {
        var pa = Load(a); var pb = Load(b); var o = new int[W * H];
        for (int i = 0; i < o.Length; i++) { int r = (((pa[i] >> 16) & 255) + ((pb[i] >> 16) & 255)) / 2, g = (((pa[i] >> 8) & 255) + ((pb[i] >> 8) & 255)) / 2, bl = ((pa[i] & 255) + (pb[i] & 255)) / 2;
            o[i] = unchecked((int)0xFF000000) | (r << 16) | (g << 8) | bl; }
        Save(o, W, H, outp + "_overlay.png");
        var ea = Edges(pa); var eb = Edges(pb); int both = 0, any = 0;
        // agreement within 4 px: dilate each edge map, count render edges that land on painting edges and vice versa
        var da = Dilate(ea, 4); var db = Dilate(eb, 4);
        for (int i = 0; i < o.Length; i++) {
            float la = 0.25f * (float)Math.Sqrt(L(pa[i])) * 255;
            int r = (int)la, g = (int)la, bl = (int)la;
            if (ea[i] > 0 && db[i] > 0 || eb[i] > 0 && da[i] > 0) { r = g = bl = 255; }
            else if (ea[i] > 0) { r = 235; g = 40; bl = 40; } else if (eb[i] > 0) { r = 30; g = 220; bl = 235; }
            if (ea[i] > 0 || eb[i] > 0) { any++; if (ea[i] > 0 && db[i] > 0 || eb[i] > 0 && da[i] > 0) both++; }
            o[i] = unchecked((int)0xFF000000) | (r << 16) | (g << 8) | bl; }
        Save(o, W, H, outp + "_edges.png");
        var s = new int[W * H * 2 / 4]; int hw = W / 2, hh = H / 2;   // side by side at half size: painting | render
        for (int y = 0; y < hh; y++) for (int x = 0; x < hw; x++) { s[y * W + x] = pa[(2 * y) * W + 2 * x]; s[y * W + hw + x] = pb[(2 * y) * W + 2 * x]; }
        Save(s, W, hh, outp + "_side.png");
        return any > 0 ? 100.0 * both / any : 0; }
    static float[] Dilate(float[] e, int r) { var o = new float[W * H];
        for (int y = 0; y < H; y++) for (int x = 0; x < W; x++) { if (e[y * W + x] <= 0) continue;
            for (int dy = -r; dy <= r; dy++) for (int dx = -r; dx <= r; dx++) { int xx = x + dx, yy = y + dy; if (xx >= 0 && yy >= 0 && xx < W && yy < H) o[yy * W + xx] = 1; } }
        return o; }
}
"@
$score = [Cmp]::Run((Resolve-Path $Painting).Path, (Resolve-Path $Render).Path, $Out)
"edge agreement (edges within 4 px of an edge in the other image): {0:N1}%" -f $score
