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
        float cap = 10f * PXCM, sw = 0.12f * cap, gap = 0.10f;
        string word = "CROATOAN"; float total = 0; var ws = new float[word.Length];
        for (int i = 0; i < word.Length; i++) { float w; Strokes(word[i], out w); ws[i] = w; total += w + (i > 0 ? gap : 0); }
        float xs = 0.62f; for (int i = 0; i < ws.Length; i++) ws[i] *= xs; total *= xs;   // narrower Roman capitals
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
            float cx = -21f + 42f * (float)r.NextDouble(), z0 = 96f + 90f * (float)r.NextDouble(), len = 10f + 30f * (float)r.NextDouble();
            if (z0 < 170f && z0 + len > 130f) { if (z0 < 150f) { len = Math.Max(4f, 128f - z0); if (z0 > 124f) z0 = 120f; } else z0 = 172f; }   // keep the word clear
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
        for (int k = 0; k <= strips; k++) { tops[k] = 200f + (float)r.NextDouble() * 16f; bots[k] = 86f + (float)r.NextDouble() * 10f; }
        for (int y = 0; y < H; y++) {
            float z = TOP - y / PXCM;
            float xl = -27f + 2.5f * N1(gl, z / 22f) + 0.8f * N1(gf, z / 2.5f);
            float xr =  27f + 2.5f * N1(gr, z / 22f) + 0.8f * N1(gf, z / 2.5f + 40);
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
            float cx = (r.NextDouble() < 0.5 ? -1 : 1) * (26f + (float)r.NextDouble() * 2f), cz = 96f + (float)r.NextDouble() * 106f;
            if (cz > 130f && cz < 170f) cz = (cz < 150f) ? 118f : 184f;                         // keep the word clear
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
        if (MeshPath != null) Mesh(MeshPath, cut, pan, seed);
    }

    // ================================================================== the post as geometry
    // Dark furrowed bark all round; the stripped panel sunk 2.5 cm below the bark (the torn edge shows its thickness);
    // CROATOAN and the cracks cut as V-grooves up to ~1.1 cm deep. Three material groups: Bark, Panel, Cut (raw wood).
    // Local frame (UE, cm): +X = out of the panel's face, +Z up, base at z = -60. Mask x (to the reader's right) -> -Y.
    public static string MeshPath = null;
    public static string Conv = "x,z,-y";     // OBJ axes from UE local axes (set from the importer probe)
    public static bool Flip = false;          // reverse winding after making it outward in OBJ space
    const float RAD = 33f;

    static float Samp(float[] a, float xcm, float zcm) {
        float fx = X(xcm), fy = Y(zcm); if (fx < 0 || fy < 0 || fx >= W - 1 || fy >= H - 1) return 0f;
        int x0 = (int)fx, y0 = (int)fy; float tx = fx - x0, ty = fy - y0;
        return (a[y0 * W + x0] * (1 - tx) + a[y0 * W + x0 + 1] * tx) * (1 - ty) + (a[(y0 + 1) * W + x0] * (1 - tx) + a[(y0 + 1) * W + x0 + 1] * tx) * ty;
    }
    static float Hash(int x, int y, int s) { unchecked { uint h = (uint)(x * 374761393 + y * 668265263 + s * 1442695041); h = (h ^ (h >> 13)) * 1274126177u; h ^= h >> 16; return (h & 0xFFFFFF) / 16777215f; } }
    static float VN(float x, float y, int s) {
        int x0 = (int)Math.Floor(x), y0 = (int)Math.Floor(y); float tx = x - x0, ty = y - y0;
        tx = tx * tx * (3 - 2 * tx); ty = ty * ty * (3 - 2 * ty);
        float a = Hash(x0, y0, s), b = Hash(x0 + 1, y0, s), c = Hash(x0, y0 + 1, s), d = Hash(x0 + 1, y0 + 1, s);
        return (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty;
    }
    // bark: long vertical plates split by deep furrows, a finer texture on the plates
    static float Bark(float s, float z) {
        float warp = 2.5f * (VN(s / 9f, z / 40f, 7) - 0.5f);
        float n = VN((s + warp) / 3.2f, z / 28f, 3);
        float plate = 1f - Math.Abs(2f * n - 1f);
        float fine = VN(s / 0.9f, z / 5f, 11);
        return 2.4f * (float)Math.Pow(plate, 1.6) - 0.9f + 0.45f * fine;
    }

    static int[] ax = new int[3]; static double[] sg = new double[3];
    static void ParseConv() { var p = Conv.Split(','); for (int i = 0; i < 3; i++) { string t = p[i].Trim(); sg[i] = t.StartsWith("-") ? -1 : 1; ax[i] = "xyz".IndexOf(t.TrimStart('-')); } }
    static double[] ToObj(double[] u) { return new double[] { sg[0] * u[ax[0]], sg[1] * u[ax[1]], sg[2] * u[ax[2]] }; }

    static void Mesh(string path, float[] cut, float[] pan, int seed) {
        ParseConv();
        var inv = System.Globalization.CultureInfo.InvariantCulture;
        double half = Math.PI * RAD;
        var cols = new List<float>(); for (double s = -half; s < half - 0.01; ) { cols.Add((float)s); s += Math.Abs(s) < 30 ? 0.25 : 1.5; }
        var rows = new List<float>(); for (double z = -60; z <= 700.01; ) { rows.Add((float)z); z += (z >= 138 && z < 163) ? 0.25 : (z >= 85 && z < 215) ? 0.8 : 2.5; }
        int nc = cols.Count, nr = rows.Count, cap = nc * nr;   // cap = index of the top centre vertex
        var P = new double[cap + 1][]; var G = new float[cap]; var C = new float[cap];
        for (int j = 0; j < nr; j++) for (int i = 0; i < nc; i++) {
            float s = cols[i], z = rows[j];
            float g = Samp(pan, s, z), c = Samp(cut, s, z) * g;
            float r = RAD + (1 - g) * Bark(s, z) - 2.5f * g - 1.1f * c;
            double th = -s / RAD;
            P[j * nc + i] = new double[] { r * Math.Cos(th), r * Math.Sin(th), z }; G[j * nc + i] = g; C[j * nc + i] = c;
        }
        P[cap] = new double[] { 0, 0, 700 };
        var sb = new System.Text.StringBuilder(1 << 26);
        sb.Append("# LETHE CROATOAN post: bark, stripped panel, cut letters (Scripts/make_panel_mask.ps1)\n");
        foreach (var p in P) { var o = ToObj(p); sb.AppendFormat(inv, "v {0:F3} {1:F3} {2:F3}\n", o[0], o[1], o[2]); }
        // Texture coords: panel and cuts map the long grain strip of the log scan once over the panel; bark repeats that
        // strip every 50 cm round and 150 cm up, per face, so the repeat seams stay clean.
        var vt = new Dictionary<long, int>(); var vts = new System.Text.StringBuilder(1 << 24); int nvt = 0;
        Func<int, int, int, int, int> VT = (vi, mode, s0, z0) => {
            long key = (long)vi * 1048576L + (long)mode * 262144L + (long)(s0 + 8) * 1024L + (long)(z0 + 4);
            int id; if (vt.TryGetValue(key, out id)) return id;
            double u, v;
            if (vi == cap) { u = 0.2; v = 0.5; }
            else { float s = cols[vi % nc], z = rows[vi / nc];
                if (mode == 0) { u = 0.06 + 0.32 * ((s + 30) / 60.0); v = 0.04 + 0.92 * ((215 - z) / 130.0); }
                else { u = 0.06 + 0.32 * ((s - s0 * 50.0) / 50.0); v = 0.04 + 0.92 * ((z - 75 - z0 * 150.0) / 150.0); } }
            vts.AppendFormat(inv, "vt {0:F5} {1:F5}\n", u, v);
            vt[key] = ++nvt; return nvt;
        };
        var groups = new Dictionary<string, System.Text.StringBuilder> { { "Bark", new System.Text.StringBuilder() }, { "Panel", new System.Text.StringBuilder() }, { "Cut", new System.Text.StringBuilder() } };
        Action<string, int, int, int, int> Tri = (mat, a, b, c, mode) => {
            // face it outward (away from the post's axis) in OBJ space, then flip if the importer wants that
            double[] pa = ToObj(P[a]), pb = ToObj(P[b]), pc = ToObj(P[c]);
            double e1x = pb[0] - pa[0], e1y = pb[1] - pa[1], e1z = pb[2] - pa[2], e2x = pc[0] - pa[0], e2y = pc[1] - pa[1], e2z = pc[2] - pa[2];
            double nx = e1y * e2z - e1z * e2y, ny = e1z * e2x - e1x * e2z, nz = e1x * e2y - e1y * e2x;
            double[] o;
            if (a == cap || b == cap || c == cap) o = ToObj(new double[] { 0, 0, 1 });
            else { var m = ToObj(new double[] { (P[a][0] + P[b][0] + P[c][0]) / 3, (P[a][1] + P[b][1] + P[c][1]) / 3, 0 }); o = m; }
            bool outward = nx * o[0] + ny * o[1] + nz * o[2] > 0;
            if (outward == Flip) { int t = b; b = c; c = t; }
            int s0 = 0, z0 = 0;
            if (mode == 1 && a != cap) { s0 = (int)Math.Floor(cols[a % nc] / 50.0); z0 = (int)Math.Floor((rows[a / nc] - 75) / 150.0); }
            groups[mat].AppendFormat("f {0}/{1} {2}/{3} {4}/{5}\n", a + 1, VT(a, mode, s0, z0), b + 1, VT(b, mode, s0, z0), c + 1, VT(c, mode, s0, z0));
        };
        for (int j = 0; j + 1 < nr; j++) for (int i = 0; i < nc; i++) {
            int i1 = (i + 1) % nc;
            int a = j * nc + i, b = j * nc + i1, c = (j + 1) * nc + i1, d = (j + 1) * nc + i;
            float g = (G[a] + G[b] + G[c] + G[d]) / 4, cm = Math.Max(Math.Max(C[a], C[b]), Math.Max(C[c], C[d]));
            string mat = g < 0.5f ? "Bark" : (cm > 0.2f ? "Cut" : "Panel");
            int mode = mat == "Bark" ? 1 : 0;
            Tri(mat, a, b, c, mode); Tri(mat, a, c, d, mode);
        }
        for (int i = 0; i < nc; i++) Tri("Bark", (nr - 1) * nc + i, (nr - 1) * nc + (i + 1) % nc, cap, 1);
        sb.Append(vts);
        foreach (var kv in groups) { sb.Append("usemtl ").Append(kv.Key).Append("\n"); sb.Append(kv.Value); }
        System.IO.File.WriteAllText(path, sb.ToString());
        Console.WriteLine("post mesh: " + nc + " x " + nr + " vertices, " + nvt + " uvs -> " + path);
    }
}
"@
$out = 'C:\LETHE\SourceArt\Carving\T_CroatoanPanel_Mask.png'
[Panel]::MeshPath = 'C:\LETHE\SourceArt\Carving\CroatoanPost.obj'
[Panel]::Conv = $env:LETHE_OBJ_CONV; if (-not [Panel]::Conv) { [Panel]::Conv = 'x,z,-y' }
[Panel]::Flip = ($env:LETHE_OBJ_FLIP -eq '1')
[Panel]::Make($out, 1590)
"panel mask written: $out"
