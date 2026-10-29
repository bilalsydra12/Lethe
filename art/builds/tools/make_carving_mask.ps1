# Draws the CROATOAN carving mask (C:\LETHE\SourceArt\Carving\T_CroatoanCarving_Mask.png).
# CROATOAN: hand-cut Roman capitals, each letter with its own size, tilt and baseline, uneven spacing,
# V-cut grooves (deepest in the middle of each stroke) with chipped, rough edges.
# Around it, fainter knife-scratched names of 1587 colonists. Grey value = depth of the cut.
Add-Type -AssemblyName System.Drawing
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @"
using System; using System.Drawing; using System.Drawing.Imaging; using System.Runtime.InteropServices;
public static class Carve {
    // Box-blur a greyscale image (V profile), then erode edges with value noise (chips).
    public static void Finish(Bitmap b, int radius, int seed, double chip) {
        int w = b.Width, h = b.Height;
        var r = new Rectangle(0, 0, w, h);
        var d = b.LockBits(r, ImageLockMode.ReadWrite, PixelFormat.Format32bppArgb);
        int n = w * h; var px = new int[n]; Marshal.Copy(d.Scan0, px, 0, n);
        var v = new float[n]; for (int i = 0; i < n; i++) v[i] = (px[i] & 0xFF) / 255f;
        var t = new float[n];
        for (int y = 0; y < h; y++) { float s = 0; for (int x = -radius; x <= radius; x++) s += v[y * w + Math.Max(0, Math.Min(w - 1, x))];
            for (int x = 0; x < w; x++) { t[y * w + x] = s / (2 * radius + 1); int a = Math.Min(w - 1, x + radius + 1), c = Math.Max(0, x - radius); s += v[y * w + a] - v[y * w + c]; } }
        for (int x = 0; x < w; x++) { float s = 0; for (int y = -radius; y <= radius; y++) s += t[Math.Max(0, Math.Min(h - 1, y)) * w + x];
            for (int y = 0; y < h; y++) { v[y * w + x] = s / (2 * radius + 1); int a = Math.Min(h - 1, y + radius + 1), c = Math.Max(0, y - radius); s += t[a * w + x] - t[c * w + x]; } }
        var rnd = new Random(seed); int g = 24; int gw = w / g + 2, gh = h / g + 2; var grid = new float[gw * gh];
        for (int i = 0; i < grid.Length; i++) grid[i] = (float)rnd.NextDouble();
        for (int y = 0; y < h; y++) for (int x = 0; x < w; x++) {
            int i = y * w + x; float val = v[i]; if (val <= 0.001f) { px[i] = unchecked((int)0xFF000000); continue; }
            float fx = (float)x / g, fy = (float)y / g; int ix = (int)fx, iy = (int)fy; float ax = fx - ix, ay = fy - iy;
            float nz = grid[iy * gw + ix] * (1 - ax) * (1 - ay) + grid[iy * gw + ix + 1] * ax * (1 - ay) + grid[(iy + 1) * gw + ix] * (1 - ax) * ay + grid[(iy + 1) * gw + ix + 1] * ax * ay;
            float fine = (float)rnd.NextDouble();
            float edge = val < 0.5f ? (float)(1 - chip * (0.6 * nz + 0.4 * fine)) : 1f;   // chips only at the groove edge
            float o = Math.Max(0, Math.Min(1, val * edge * (0.9f + 0.1f * fine)));
            int g8 = (int)(o * 255); px[i] = unchecked((int)0xFF000000) | (g8 << 16) | (g8 << 8) | g8; }
        Marshal.Copy(px, 0, d.Scan0, n); b.UnlockBits(d);
    }
}
"@

$out = 'C:\LETHE\SourceArt\Carving'; $W = 2048; $H = 4096
$b = New-Object System.Drawing.Bitmap $W, $H; $g = [System.Drawing.Graphics]::FromImage($b)
$g.SmoothingMode = 'AntiAlias'; $g.TextRenderingHint = 'AntiAliasGridFit'; $g.Clear([System.Drawing.Color]::Black)
$rnd = New-Object System.Random 1590

# Later names: knife scratches, shallow, irregular
$names = @('ELEANOR DARE','ANANIAS DARE','MARGERY HARVIE','ROGER BAYLYE','THOMAS WARNER','ELIZABETH VICCARS','AGNES WOOD','JOHN SAMPSON','A.D. 1587','IOHN','WILLIAM','EMME','TOMAS','JANE','HENRY')
$scratch = New-Object System.Drawing.Font('Ink Free', 80)
$y = 260
foreach ($n in $names) {
  if ($y -gt 1600 -and $y -lt 2400) { $y = 2400 }
  $a = 60 + $rnd.Next(60); $brush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, $a, $a, $a))
  $st = $g.Save(); $g.TranslateTransform(380 + $rnd.Next(300), $y); $g.RotateTransform(-4 + $rnd.NextDouble() * 8)
  $g.DrawString($n, $scratch, $brush, 0, 0); $g.Restore($st); $y += 230 + $rnd.Next(60)
}

# CROATOAN: letter by letter, hand-cut
$letters = 'CROATOAN'.ToCharArray()
$base = 228.0; $sx = 0.48
$widths = foreach ($c in $letters) { $f = New-Object System.Drawing.Font('Times New Roman', $base, [System.Drawing.FontStyle]::Bold); ($g.MeasureString([string]$c, $f).Width - 40) * $sx }
$total = ($widths | Measure-Object -Sum).Sum
$x = $W / 2 - $total * 0.88 / 2
for ($i = 0; $i -lt $letters.Count; $i++) {
  $size = $base * (0.93 + $rnd.NextDouble() * 0.12)           # uneven heights
  $f = New-Object System.Drawing.Font('Times New Roman', $size, [System.Drawing.FontStyle]::Bold)
  $st = $g.Save()
  $g.TranslateTransform($x + $widths[$i] / 2 + ($rnd.NextDouble() - 0.5) * 18, 2030 + ($rnd.NextDouble() - 0.5) * 26)   # uneven baseline/spacing
  $g.RotateTransform(-3.5 + $rnd.NextDouble() * 7)              # each letter its own tilt
  $g.ScaleTransform($sx * (0.95 + $rnd.NextDouble() * 0.1), 1.0)
  $fmt = New-Object System.Drawing.StringFormat; $fmt.Alignment = 'Center'; $fmt.LineAlignment = 'Center'
  $g.DrawString([string]$letters[$i], $f, [System.Drawing.Brushes]::White, 0, 0, $fmt)
  $g.Restore($st)
  $x += $widths[$i] * (0.84 + $rnd.NextDouble() * 0.08)
}
$g.Dispose()
[Carve]::Finish($b, 5, 1590, 0.85)       # V-groove profile + chipped edges
$b.Save("$out\T_CroatoanCarving_Mask.png", [System.Drawing.Imaging.ImageFormat]::Png); $b.Dispose()
"carving written"


