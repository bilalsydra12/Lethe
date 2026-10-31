# Draws distant pine silhouettes for the fog: C:\LETHE\SourceArt\Pines\T_Pine_<n>.png (1024 x 2048, alpha = tree)
# Seen at 30-60 m through night fog these read only as dark shapes, so each is a trunk, uneven drooping branch tiers
# with ragged needle tufts, a lean, and a few gaps where branches have broken off.
Add-Type -AssemblyName System.Drawing
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @"
using System; using System.Drawing; using System.Drawing.Drawing2D; using System.Drawing.Imaging;
public static class Pines {
    public static void Make(string path, int seed) {
        var r = new Random(seed);
        int W = 1024, H = 2048;
        var b = new Bitmap(W, H, PixelFormat.Format32bppArgb);
        var g = Graphics.FromImage(b); g.SmoothingMode = SmoothingMode.AntiAlias; g.Clear(Color.Transparent);
        var br = new SolidBrush(Color.FromArgb(255, 18, 20, 22));
        float lean = (float)(r.NextDouble() - 0.5) * 60f;
        float baseY = H - 10, topY = 60 + (float)r.NextDouble() * 120;
        Func<float, float> cx = y => W / 2f + lean * (1f - (y - topY) / (baseY - topY));
        // trunk
        var trunk = new PointF[] { new PointF(cx(baseY) - 22, baseY), new PointF(cx(topY) - 3, topY), new PointF(cx(topY) + 3, topY), new PointF(cx(baseY) + 22, baseY) };
        g.FillPolygon(br, trunk);
        // branch tiers from the top down; the crown widens, lower tiers sparser, some missing
        float crownBase = baseY - 320 - (float)r.NextDouble() * 300;
        for (float y = topY + 20; y < crownBase; y += 12 + (float)r.NextDouble() * 16) {
            float t = (y - topY) / (crownBase - topY);
            if (t > 0.55 && r.NextDouble() < 0.18) continue;           // broken-off tier
            float reach = 30 + t * (W * 0.42f) * (0.75f + 0.45f * (float)r.NextDouble());
            for (int side = -1; side <= 1; side += 2) {
                if (t > 0.7 && r.NextDouble() < 0.25) continue;
                float rr = reach * (0.7f + 0.5f * (float)r.NextDouble());
                float droop = 0.25f + 0.35f * t + 0.15f * (float)r.NextDouble();
                float x0 = cx(y), ex = x0 + side * rr, ey = y + rr * droop;
                // the branch limb
                g.FillPolygon(br, new PointF[] { new PointF(x0, y - 3), new PointF(ex, ey - 1), new PointF(ex, ey + 2), new PointF(x0, y + 6) });
                // ragged needle tufts hanging along it
                int tufts = (int)(rr / 4.5f);
                for (int k = 0; k < tufts; k++) {
                    float f = (k + (float)r.NextDouble()) / tufts;
                    float px = x0 + (ex - x0) * f, py = y + (ey - y) * f;
                    float tw = 12 + 30 * (1 - f) * (float)r.NextDouble() + 8, th = 16 + 46 * (float)r.NextDouble() * (0.4f + t);
                    g.FillEllipse(br, px - tw / 2, py - th * 0.35f, tw, th);
                }
            }
        }
        g.Dispose();
        b.Save(path, ImageFormat.Png); b.Dispose();
    }
}
"@
$dir = 'C:\LETHE\SourceArt\Pines'; New-Item -ItemType Directory -Force $dir | Out-Null
for ($i = 0; $i -lt 6; $i++) { [Pines]::Make("$dir\T_Pine_$i.png", 1587 + $i * 31) }
"6 pine silhouettes written to $dir"
