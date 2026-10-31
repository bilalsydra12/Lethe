# Measures an image the way art/levels/roanoke/croatoan-gate-spec.md does: brightness bands (sRGB luminance) and the
# average colour of each named region (boxes as frame fractions x0,x1,y0,y1). Usage: measure_frame.ps1 <image> [<image> ...]
param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Images)
Add-Type -AssemblyName System.Drawing
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @"
using System; using System.Drawing; using System.Drawing.Imaging; using System.Runtime.InteropServices;
public static class Meas {
    public static int[] Px; public static int W, H;
    public static void Load(string p) { using (var b0 = new Bitmap(p)) { var b = new Bitmap(b0.Width, b0.Height, PixelFormat.Format32bppArgb);
        using (var g = Graphics.FromImage(b)) g.DrawImage(b0, 0, 0, b0.Width, b0.Height);
        W = b.Width; H = b.Height; var d = b.LockBits(new Rectangle(0, 0, W, H), ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb);
        Px = new int[W * H]; Marshal.Copy(d.Scan0, Px, 0, Px.Length); b.UnlockBits(d); b.Dispose(); } }
    static double L(int c) { return (0.2126 * ((c >> 16) & 255) + 0.7152 * ((c >> 8) & 255) + 0.0722 * (c & 255)) / 255.0; }
    public static double[] Bands() { var n = new double[5]; double r = 0, g = 0, bl = 0;
        foreach (var c in Px) { int k = Math.Min(4, (int)(L(c) * 5)); n[k]++; r += (c >> 16) & 255; g += (c >> 8) & 255; bl += c & 255; }
        var o = new double[8]; for (int i = 0; i < 5; i++) o[i] = 100.0 * n[i] / Px.Length; o[5] = r / Px.Length; o[6] = g / Px.Length; o[7] = bl / Px.Length; return o; }
    public static double[] Region(double x0, double x1, double y0, double y1) { int a = (int)(x0 * W), b = Math.Max(a + 1, (int)(x1 * W)), c = (int)(y0 * H), d = Math.Max(c + 1, (int)(y1 * H));
        double r = 0, g = 0, bl = 0, mx = 0; int n = 0;
        for (int y = c; y < d && y < H; y++) for (int x = a; x < b && x < W; x++) { int p = Px[y * W + x]; r += (p >> 16) & 255; g += (p >> 8) & 255; bl += p & 255; mx = Math.Max(mx, L(p)); n++; }
        return new double[] { r / n, g / n, bl / n, mx * 100 }; }
}
"@
$regions = [ordered]@{
  'Sky, top left'        = 0.00, 0.04, 0.00, 0.20;  'Sky, top centre'     = 0.47, 0.57, 0.00, 0.12;  'Sky, top right'      = 0.80, 1.00, 0.00, 0.04
  'Ground mist, left'    = 0.00, 0.20, 0.55, 0.72;  'Through the gate gap'= 0.44, 0.50, 0.30, 0.48;  'Watchtower roof'     = 0.10, 0.22, 0.00, 0.08
  'Tower lantern'        = 0.18, 0.20, 0.13, 0.15;  'Left palisade stakes'= 0.05, 0.35, 0.35, 0.60;  'Gate lantern core'   = 0.530, 0.545, 0.37, 0.39
  'Gate lantern halo'    = 0.51, 0.57, 0.33, 0.43;  'Gate crossbeams'     = 0.44, 0.56, 0.17, 0.26;  'Dark second post'    = 0.59, 0.635, 0.10, 0.90
  'Post bark'            = 0.77, 0.80, 0.10, 0.90;  'Post left edge (UV)' = 0.645, 0.655, 0.35, 0.55; 'Stripped panel, upper' = 0.66, 0.75, 0.10, 0.30
  'Stripped panel, lower'= 0.66, 0.75, 0.60, 0.90;  'Panel inside UV pool'= 0.66, 0.75, 0.46, 0.54;  'Letters band'        = 0.655, 0.75, 0.40, 0.445
  'Foreground mud'       = 0.00, 0.30, 0.85, 1.00;  'Middle mud'          = 0.00, 0.40, 0.75, 0.82;  'Puddle reflection'   = 0.30, 0.50, 0.80, 0.95
  'House wall, right'    = 0.82, 0.98, 0.08, 0.16;  'House window'        = 0.84, 0.86, 0.19, 0.21;  'Right palisade stakes'= 0.82, 1.00, 0.35, 0.70
}
$res = @{}
foreach ($img in $Images) { [Meas]::Load((Resolve-Path $img).Path); $b = [Meas]::Bands()
  $o = [ordered]@{ '0-20%' = $b[0]; '20-40%' = $b[1]; '40-60%' = $b[2]; '60-80%' = $b[3]; '80-100%' = $b[4]; 'Average' = ('#{0:X2}{1:X2}{2:X2}' -f [int]$b[5], [int]$b[6], [int]$b[7]) }
  foreach ($k in $regions.Keys) { $v = $regions[$k]; $r = [Meas]::Region($v[0], $v[1], $v[2], $v[3]); $o[$k] = ('#{0:X2}{1:X2}{2:X2} (max {3:N0}%)' -f [int]$r[0], [int]$r[1], [int]$r[2], $r[3]) }
  $res[$img] = $o }
$keys = @($res[$Images[0]].Keys)
foreach ($k in $keys) { $line = "{0,-24}" -f $k; foreach ($img in $Images) { $v = $res[$img][$k]; if ($v -is [double]) { $v = '{0:N1}%' -f $v }; $line += " | {0,-20}" -f $v }; $line }
