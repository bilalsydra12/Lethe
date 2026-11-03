# Draws a tileable (left-right) texture of long dark curly hair strands with alpha, for Nysa's hair cards.
# Out: SourceArt/Nysa/gltf/textures/M_curls_BaseColor.png (1024 x 1024, RGBA). Top = scalp, bottom = ragged ends.
param([string]$Out = 'C:\LETHE\SourceArt\Nysa\gltf\textures\M_curls_BaseColor.png')
Add-Type -AssemblyName System.Drawing
$S = 1024
$bmp = New-Object System.Drawing.Bitmap $S, $S, ([System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$g.Clear([System.Drawing.Color]::FromArgb(0, 30, 20, 15))
$rng = New-Object System.Random 7
function Strand($x0, $len, $amp, $wl, $ph, $w, $col) {
    $pts = New-Object System.Collections.Generic.List[System.Drawing.PointF]
    for ($y = 0; $y -le $len; $y += 3) {
        $t = $y / $wl * 2 * [Math]::PI + $ph
        # a helix seen side-on: sideways sine plus a little vertical loop
        $a = $amp * (0.6 + 0.4 * $y / $len)
        $pts.Add((New-Object System.Drawing.PointF ([float]($x0 + $a * [Math]::Sin($t))), ([float]($y + 0.35 * $a * [Math]::Cos($t)))))
    }
    $pen = New-Object System.Drawing.Pen $col, $w
    $pen.StartCap = 'Round'; $pen.EndCap = 'Round'; $pen.LineJoin = 'Round'
    foreach ($dx in (-$S, 0, $S)) {
        $p2 = $pts | ForEach-Object { New-Object System.Drawing.PointF ([float]($_.X + $dx)), $_.Y }
        $g.DrawCurve($pen, [System.Drawing.PointF[]]$p2, 0.5)
    }
    $pen.Dispose()
}
# ringlets: strands in a clump share one curl (phase, wavelength), so they read as locks; clump lengths vary
for ($c = 0; $c -lt 30; $c++) {
    $cx = $rng.NextDouble() * $S
    $clen = $S * (0.45 + 0.55 * [Math]::Pow($rng.NextDouble(), 0.6))
    $wl = 85 + $rng.NextDouble() * 40; $ph = $rng.NextDouble() * 6.28; $amp = 26 + $rng.NextDouble() * 20
    for ($k = 0; $k -lt 22; $k++) {
        $hi = $k -ge 14
        $v = if ($hi) { 55 + $rng.Next(55) } else { 14 + $rng.Next(16) }
        $col = [System.Drawing.Color]::FromArgb(255, [int]($v * 1.35), $v, [int]($v * 0.8))
        Strand ($cx + ($rng.NextDouble() - 0.5) * 44) ($clen * (0.85 + 0.15 * $rng.NextDouble())) ($amp * (0.85 + 0.3 * $rng.NextDouble())) $wl ($ph + ($rng.NextDouble() - 0.5) * 0.8) ($(if ($hi) { 2.5 } else { 6 + $rng.NextDouble() * 6 })) $col
    }
}
$g.Dispose()
$bmp.Save($Out, [System.Drawing.Imaging.ImageFormat]::Png)
"wrote $Out"
