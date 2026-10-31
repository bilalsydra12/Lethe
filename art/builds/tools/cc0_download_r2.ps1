# Round 2 CC0 downloads (approved): Poly Haven textures/models and ambientCG materials into C:\LETHE\SourceArt\PolyHaven and \AmbientCG
$ErrorActionPreference = 'Stop'
$h = @{ 'User-Agent' = 'LETHE-asset-fetch' }
$ph = 'C:\LETHE\SourceArt\PolyHaven'; $acg = 'C:\LETHE\SourceArt\AmbientCG'
function Get-File($url, $dest) { if (Test-Path $dest) { return }; New-Item -ItemType Directory -Force (Split-Path $dest) | Out-Null; Invoke-WebRequest $url -OutFile $dest -Headers $h -UseBasicParsing }
foreach ($a in 'rough_wood','fine_grained_wood','thatch_roof_angled','wood_trunk_wall') { $f = Invoke-RestMethod "https://api.polyhaven.com/files/$a" -Headers $h
    foreach ($m in 'Diffuse','nor_dx','Rough','arm','Displacement') { $n = $f.$m.'2k'; if (-not $n) { continue }; $j = $n.jpg; if (-not $j) { $j = $n.png }; if ($j) { Get-File $j.url ("$ph\$a\" + [IO.Path]::GetFileName($j.url)) } }
    "texture $a done" }
foreach ($a in 'grass_medium_01','weed_plant_02') { $f = Invoke-RestMethod "https://api.polyhaven.com/files/$a" -Headers $h
    $n = $f.fbx.'2k'.fbx; Get-File $n.url ("$ph\$a\" + [IO.Path]::GetFileName($n.url))
    foreach ($i in $n.include.PSObject.Properties) { Get-File $i.Value.url ("$ph\$a\" + ($i.Name -replace '/', '\')) }
    "model $a done" }
foreach ($a in 'Rope001','Plaster001') {
    $r = Invoke-RestMethod "https://ambientcg.com/api/v2/full_json?id=$a&include=downloadData" -Headers $h
    $d = $r.foundAssets[0].downloadFolders.default.downloadFiletypeCategories.zip.downloads | ? { $_.attribute -eq '2K-JPG' } | Select-Object -First 1
    $zip = "$acg\$a.zip"; Get-File $d.downloadLink $zip
    $dir = "$acg\$a"; if (-not (Test-Path $dir)) { Expand-Archive $zip -DestinationPath $dir }
    "ambientcg $a done" }
"ALL DONE"
