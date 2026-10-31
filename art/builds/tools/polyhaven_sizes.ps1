# Lists download sizes for chosen Poly Haven (CC0) assets: textures 2k (diff, nor_dx, rough, arm, disp as PNG/JPG),
# models as FBX 2k, the HDRI as 4k EXR. Read-only: it queries api.polyhaven.com, it downloads nothing.
$h = @{ 'User-Agent' = 'LETHE-asset-survey' }
$tex = 'knotted_pine_bark','bark_brown_02','medieval_wood','brown_mud_leaves_01','brown_mud_02','forest_ground_04'
$mod = 'fir_tree_01','pine_tree_01','dead_tree_trunk','dead_tree_trunk_02','tree_stump_01','rock_moss_set_01','Lantern_01','wooden_lantern_01','pine_roots'
$hdr = 'rogland_moonlit_night','qwantani_night_puresky'
$total = 0
function Sum($node) { $s = 0; if ($node -eq $null) { return 0 }
    foreach ($p in $node.PSObject.Properties) { if ($p.Name -eq 'size' -and $p.Value -is [ValueType]) { $s += $p.Value } elseif ($p.Value -is [PSCustomObject]) { $s += Sum $p.Value } }
    return $s }
foreach ($a in $tex) { $f = Invoke-RestMethod "https://api.polyhaven.com/files/$a" -Headers $h
    $s = 0; foreach ($m in 'Diffuse','nor_dx','Rough','arm','Displacement') { $node = $f.$m.'2k'; if ($node) { $j = $node.jpg; if (-not $j) { $j = $node.png }; if ($j) { $s += $j.size } } }
    $total += $s; "{0,-24} texture 2k  {1,6:N1} MB" -f $a, ($s / 1MB) }
foreach ($a in $mod) { $f = Invoke-RestMethod "https://api.polyhaven.com/files/$a" -Headers $h
    $node = $f.fbx.'2k'; $s = 0; if ($node) { $s = $node.fbx.size; foreach ($inc in $node.fbx.include.PSObject.Properties) { $s += $inc.Value.size } }
    $total += $s; "{0,-24} model fbx 2k {1,6:N1} MB" -f $a, ($s / 1MB) }
foreach ($a in $hdr) { $f = Invoke-RestMethod "https://api.polyhaven.com/files/$a" -Headers $h
    $s = $f.hdri.'4k'.exr.size; $total += $s; "{0,-24} hdri exr 4k  {1,6:N1} MB" -f $a, ($s / 1MB) }
"TOTAL {0:N0} MB" -f ($total / 1MB)
