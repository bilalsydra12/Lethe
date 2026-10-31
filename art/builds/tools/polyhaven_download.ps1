# Downloads the approved Poly Haven (CC0) assets for the CROATOAN gate scene into C:\LETHE\SourceArt\PolyHaven\<asset>\
# Textures 2k (diffuse, normal DX, roughness, ARM, displacement), models FBX 2k with their textures, HDRIs 4k EXR.
$ErrorActionPreference = 'Stop'
$h = @{ 'User-Agent' = 'LETHE-asset-fetch' }
$root = 'C:\LETHE\SourceArt\PolyHaven'
$tex = 'knotted_pine_bark','bark_brown_02','medieval_wood','brown_mud_leaves_01','brown_mud_02','forest_ground_04'
$mod = 'fir_tree_01','dead_tree_trunk','dead_tree_trunk_02','tree_stump_01','rock_moss_set_01','Lantern_01','wooden_lantern_01'
$hdr = 'rogland_moonlit_night','qwantani_night_puresky'
function Get-File($url, $dest) {
    if (Test-Path $dest) { return }
    New-Item -ItemType Directory -Force (Split-Path $dest) | Out-Null
    Invoke-WebRequest $url -OutFile $dest -Headers $h -UseBasicParsing
}
foreach ($a in $tex) { $f = Invoke-RestMethod "https://api.polyhaven.com/files/$a" -Headers $h
    foreach ($m in 'Diffuse','nor_dx','Rough','arm','Displacement') { $node = $f.$m.'2k'; if (-not $node) { continue }
        $j = $node.jpg; if (-not $j) { $j = $node.png }; if (-not $j) { continue }
        Get-File $j.url ("$root\$a\" + [IO.Path]::GetFileName($j.url)) }
    "texture $a done" }
foreach ($a in $mod) { $f = Invoke-RestMethod "https://api.polyhaven.com/files/$a" -Headers $h
    $node = $f.fbx.'2k'.fbx
    Get-File $node.url ("$root\$a\" + [IO.Path]::GetFileName($node.url))
    foreach ($inc in $node.include.PSObject.Properties) { Get-File $inc.Value.url ("$root\$a\" + ($inc.Name -replace '/', '\')) }
    "model $a done" }
foreach ($a in $hdr) { $f = Invoke-RestMethod "https://api.polyhaven.com/files/$a" -Headers $h
    $u = $f.hdri.'4k'.exr.url; Get-File $u ("$root\$a\" + [IO.Path]::GetFileName($u)); "hdri $a done" }
$sz = (Get-ChildItem $root -Recurse -File | Measure-Object Length -Sum).Sum
"ALL DONE: {0:N0} MB in {1}" -f ($sz / 1MB), $root
