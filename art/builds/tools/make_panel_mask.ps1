# Draws the CROATOAN post mask: C:\LETHE\SourceArt\Carving\T_CroatoanPanel_Mask.png  (2048 x 8192)
#   Red   = depth of the knife cut (CROATOAN, Roman capitals made of straight V-cuts, curves as facets)
#   Green = the stripped-bark panel (pale weathered wood), with ragged, peeled edges
#   Blue  = the torn bark rim round the panel (bark section, ~2.5 cm), for the edge's depth
# The decal it feeds covers 100 cm x 400 cm of the post (20.48 px per cm), its top edge at z = 410 cm.
# Per John White, 18 Aug 1590: CROATOAN "in fayre Capitall letters", about 5 ft up, no cross.
Add-Type -AssemblyName System.Drawing
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @"
using System; using System.Collections.Generic; using System.Drawing; using System.Drawing.Drawing2D;
using System.Drawing.Imaging; using System.Runtime.InteropServices;
public static class Panel {
    const int W = 2048, H = 8192; const float PXCM = 20.48f, TOP = 410f;
    static float Y(float zcm) { return (TOP - zcm) * PXCM; }
    static float X(float xcm) { return W / 2f + xcm * PXCM; }

    // smooth 1D value noise
    static float N1(float[] g, float t) { int i = (int)Math.Floor(t); float f = t - i; f = f * f * (3 - 2 * f);
        int n = g.Length; return g[((i % n) + n) % n] * (1 - f) + g[(((i + 1) % n) + n) % n] * f; }
    static float[] Grid(Random r, int n) { var g = new float[n]; for (int i = 0; i < n; i++) g[i] = (float)r.NextDouble() * 2 - 1; return g; }

    static float[] Blur(float[] v, int radius) {
        var t = new float[W * H]; var o = new float[W * H];
        for (int y = 0; y < H; y++) { float s = 0; for (int x = -radius; x <= radius; x++) s += v[y * W + Math.Max(0, Math.Min(W - 1, x))];
            for (int x = 0; x < W; x++) { t[y * W + x] = s / (2 * radius + 1); s += v[y * W + Math.Min(W - 1, x + radius + 1)] - v[y * W + Math.Max(0, x - radius)]; } }
        for (int x = 0; x < W; x++) { float s = 0; for (int y = -radius; y <= radius; y++) s += t[Math.Max(0, Math.Min(H - 1, y)) * W + x];
            for (int y = 0; y < H; y++) { o[y * W + x] = s / (2 * radius + 1); s += t[Math.Min(H - 1, y + radius + 1) * W + x] - t[Math.Max(0, y - radius) * W + x]; } }
        return o;
    }

    static float[] Read(Bitmap b) {
        var d = b.LockBits(new Rectangle(0, 0, W, H), ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb);
        var px = new int[W * H]; Marshal.Copy(d.Scan0, px, 0, px.Length); b.UnlockBits(d);
        var v = new float[W * H]; for (int i = 0; i < v.Length; i++) v[i] = (px[i] & 0xFF) / 255f; return v;
    }

    // One knife cut: a lens (two angled cuts meeting in a V), pointed where the blade went in and came out.
    static void Cut(Graphics g, PointF a, PointF b, float sw, Random r) {
        float dx = b.X - a.X, dy = b.Y - a.Y, L = (float)Math.Sqrt(dx * dx + dy * dy); if (L < 1) return;
        float ux = dx / L, uy = dy / L, nx = -uy, ny = ux;
        float ext = sw * (0.35f + 0.3f * (float)r.NextDouble());          // overrun past the stroke end
        float w0 = sw * (0.30f + 0.12f * (float)r.NextDouble()), w1 = sw * (0.30f + 0.12f * (float)r.NextDouble());
        float wm = sw * (0.48f + 0.06f * (float)r.NextDouble());
        float mt = 0.4f + 0.2f * (float)r.NextDouble();
        PointF m = new PointF(a.X + dx * mt, a.Y + dy * mt);
        var p = new PointF[] {
            new PointF(a.X - ux * ext, a.Y - uy * ext),
            new PointF(a.X + nx * w0, a.Y + ny * w0), new PointF(m.X + nx * wm, m.Y + ny * wm), new PointF(b.X + nx * w1, b.Y + ny * w1),
            new PointF(b.X + ux * ext, b.Y + uy * ext),
            new PointF(b.X - nx * w1, b.Y - ny * w1), new PointF(m.X - nx * wm, m.Y - ny * wm), new PointF(a.X - nx * w0, a.Y - ny * w0) };
        g.FillPolygon(Brushes.White, p);
    }

    // Letter strokes in cap-height units (x right, y up, 0..1), curves already broken into facets.
    static List<float[][]> Strokes(char c, out float w) {
        var s = new List<float[][]>();
        Func<float, float, float, float, float, float, int, float[][]> arc = (cx, cy, rx, ry, a0, a1, n) => {
            var pts = new float[n + 1][]; for (int i = 0; i <= n; i++) { double t = (a0 + (a1 - a0) * i / n) * Math.PI / 180; pts[i] = new float[] { cx + rx * (float)Math.Cos(t), cy + ry * (float)Math.Sin(t) }; } return pts; };
        switch (c) {
            case 'C': w = 0.56f; s.Add(arc(0.31f, 0.5f, 0.30f, 0.5f, 48, 312, 8)); break;
            case 'R': w = 0.52f; s.Add(new[] { new[] { 0.04f, 0f }, new[] { 0.04f, 1f } });
                      var bowl = new List<float[]> { new[] { 0.04f, 1f }, new[] { 0.28f, 1f } }; bowl.AddRange(arc(0.28f, 0.75f, 0.2f, 0.25f, 90, -90, 4)); bowl.Add(new[] { 0.04f, 0.5f });
                      s.Add(bowl.ToArray()); s.Add(new[] { new[] { 0.24f, 0.5f }, new[] { 0.52f, 0f } }); break;
            case 'O': w = 0.62f; s.Add(arc(0.31f, 0.5f, 0.30f, 0.5f, 0, 360, 10)); break;
            case 'A': w = 0.60f; s.Add(new[] { new[] { 0f, 0f }, new[] { 0.30f, 1f }, new[] { 0.60f, 0f } }); s.Add(new[] { new[] { 0.13f, 0.36f }, new[] { 0.47f, 0.36f } }); break;
            case 'T': w = 0.56f; s.Add(new[] { new[] { 0f, 1f }, new[] { 0.56f, 1f } }); s.Add(new[] { new[] { 0.28f, 1f }, new[] { 0.28f, 0f } }); break;
            default:  w = 0.56f; s.Add(new[] { new[] { 0.03f, 0f }, new[] { 0.03f, 1f }, new[] { 0.53f, 0f }, new[] { 0.53f, 1f } }); break; // N
        }
        return s;
    }

    public static void Make(string path, int seed) {
        var r = new Random(seed);
        // ---- red: CROATOAN, cap height 10 cm, centred 150 cm above the ground
        var bc = new Bitmap(W, H, PixelFormat.Format32bppArgb); var g = Graphics.FromImage(bc);
        g.SmoothingMode = SmoothingMode.AntiAlias; g.Clear(Color.Black);
        float cap = 10f * PXCM, sw = 0.12f * cap, gap = 0.12f;
        string word = "CROATOAN"; float total = 0; var ws = new float[word.Length];
        for (int i = 0; i < word.Length; i++) { float w; Strokes(word[i], out w); ws[i] = w; total += w + (i > 0 ? gap : 0); }
        float xs = 0.80f; for (int i = 0; i < ws.Length; i++) ws[i] *= xs; total *= xs;   // narrower Roman capitals
        float x0 = X(0) - total * cap / 2f;
        float wob = (float)r.NextDouble() * 6f;
        for (int i = 0; i < word.Length; i++) {
            float w; var st = Strokes(word[i], out w); w *= xs;
            // each letter cut on its own: height +-15%, tilt +-4 deg, its own stroke weight, a wandering baseline
            float size = cap * (0.85f + 0.30f * (float)r.NextDouble());
            float rot = (float)((r.NextDouble() - 0.5) * 8.0 * Math.PI / 180);
            float lw = sw * (0.80f + 0.45f * (float)r.NextDouble());
            float by = Y(150f) + cap / 2f + 0.07f * cap * (float)Math.Sin(wob + i * 0.9f) + (float)(r.NextDouble() - 0.5) * 0.06f * cap;   // baseline
            float ox = x0 + (float)(r.NextDouble() - 0.5) * 0.05f * cap;
            float sq = 0.92f + 0.16f * (float)r.NextDouble();                 // a little wider or narrower
            foreach (var line in st) {
                var pts = new PointF[line.Length];
                for (int k = 0; k < line.Length; k++) {
                    float lx = (line[k][0] * xs - w / 2) * size * sq + (float)(r.NextDouble() - 0.5) * 0.05f * cap;
                    float ly = (line[k][1] - 0.5f) * size + (float)(r.NextDouble() - 0.5) * 0.05f * cap;
                    float rx = lx * (float)Math.Cos(rot) - ly * (float)Math.Sin(rot), ry = lx * (float)Math.Sin(rot) + ly * (float)Math.Cos(rot);
                    pts[k] = new PointF(ox + w * cap / 2 + rx, by - cap / 2 - ry);
                }
                for (int k = 0; k + 1 < pts.Length; k++) Cut(g, pts[k], pts[k + 1], lw * (0.8f + 0.4f * (float)r.NextDouble()), r);
            }
            x0 += (w + gap * (0.6f + 0.9f * (float)r.NextDouble())) * cap;
        }
        // a few long dry cracks running with the grain, kept off the word
        for (int c = 0; c < 6; c++) {
            float cx = -24f + 48f * (float)r.NextDouble(), z0 = 40f + 280f * (float)r.NextDouble(), len = 20f + 60f * (float)r.NextDouble();
            if (z0 < 180f && z0 + len > 120f) z0 = 182f;                  // keep the word clear
            float cxp = cx, pz = z0;
            for (int s2 = 0; s2 < 8; s2++) {
                float nz = pz + len / 8f, nx2 = cxp + ((float)r.NextDouble() - 0.5f) * 1.2f;
                Cut(g, new PointF(X(cxp), Y(pz)), new PointF(X(nx2), Y(nz)), 0.35f * PXCM * (0.6f + 0.8f * (float)r.NextDouble()), r);
                cxp = nx2; pz = nz;
            }
        }
        g.Dispose();
        var cut = Blur(Read(bc), 7); bc.Dispose();
        // chipped groove edges
        var cg = Grid(r, 4096);
        for (int i = 0; i < cut.Length; i++) { float v = cut[i]; if (v <= 0.002f) { cut[i] = 0; continue; }
            float n = 0.5f + 0.5f * N1(cg, (i % W) / 9f + (i / W) * 0.37f);
            cut[i] = Math.Min(1f, v < 0.45f ? v * (1f - 0.7f * n) * 1.6f : v * 1.15f); }

        // ---- green: the stripped panel, peeled in vertical strips of uneven height
        var pan = new float[W * H];
        var gl = Grid(r, 64); var gr = Grid(r, 64); var gf = Grid(r, 512);
        int strips = 9; var tops = new float[strips + 1]; var bots = new float[strips + 1];
        for (int k = 0; k <= strips; k++) { tops[k] = 300f + (float)r.NextDouble() * 80f; bots[k] = 32f + (float)r.NextDouble() * 30f; }
        for (int y = 0; y < H; y++) {
            float z = TOP - y / PXCM;
            float xl = -30f + 2.5f * N1(gl, z / 22f) + 0.8f * N1(gf, z / 2.5f);
            float xr =  30f + 2.5f * N1(gr, z / 22f) + 0.8f * N1(gf, z / 2.5f + 40);
            for (int x = 0; x < W; x++) {
                float xc = (x - W / 2f) / PXCM; if (xc < xl - 1 || xc > xr + 1) continue;
                float u = (xc - xl) / (xr - xl) * strips; int k = Math.Max(0, Math.Min(strips - 1, (int)u)); float f = u - k;
                float top = tops[k] * (1 - f) + tops[k + 1] * f + 1.2f * N1(gf, xc / 1.7f);
                float bot = bots[k] * (1 - f) + bots[k + 1] * f + 1.5f * N1(gf, xc / 2.1f + 90);
                if (xc >= xl && xc <= xr && z <= top && z >= bot) pan[y * W + x] = 1f;
            }
        }
        // a few islands of bark left clinging near the edges
        for (int b = 0; b < 8; b++) {
            float cx = (r.NextDouble() < 0.5 ? -1 : 1) * (29f + (float)r.NextDouble() * 2f), cz = 60f + (float)r.NextDouble() * 280f;
            if (cz > 128f && cz < 172f) cz += 60f;                         // keep the word clear
            float rx = 1.5f + (float)r.NextDouble() * 2.5f, rz = 2f + (float)r.NextDouble() * 6f;
            for (int y = (int)Y(cz + rz); y < (int)Y(cz - rz); y++) for (int x = (int)X(cx - rx); x < (int)X(cx + rx); x++) {
                if (x < 0 || x >= W || y < 0 || y >= H) continue;
                float ex = ((x - X(cx)) / PXCM) / rx, ez = ((TOP - y / PXCM) - cz) / rz; if (ex * ex + ez * ez < 1) pan[y * W + x] = 0; }
        }
        // ---- blue: the torn bark rim just outside the panel, ~2.5 cm, strongest at the edge
        var wide = Blur(pan, 50);
        pan = Blur(pan, 3);
        var rim = new float[W * H];
        for (int i = 0; i < rim.Length; i++) rim[i] = Math.Min(1f, wide[i] * 2.6f) * (1f - pan[i]);

        var outb = new Bitmap(W, H, PixelFormat.Format32bppArgb);
        var od = outb.LockBits(new Rectangle(0, 0, W, H), ImageLockMode.WriteOnly, PixelFormat.Format32bppArgb);
        var px = new int[W * H];
        for (int i = 0; i < px.Length; i++) { int R = (int)(Math.Min(1f, cut[i]) * 255), G = (int)(Math.Min(1f, pan[i]) * 255),
            B = (int)(Math.Min(1f, rim[i]) * 255);
            px[i] = unchecked((int)0xFF000000) | (R << 16) | (G << 8) | B; }
        Marshal.Copy(px, 0, od.Scan0, px.Length); outb.UnlockBits(od);
        outb.Save(path, ImageFormat.Png); outb.Dispose();
    }
}
"@
$out = 'C:\LETHE\SourceArt\Carving\T_CroatoanPanel_Mask.png'
[Panel]::Make($out, 1590)
"panel mask written: $out"
