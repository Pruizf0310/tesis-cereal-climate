$ErrorActionPreference = 'Stop'
$workspaceRoot = [IO.Path]::GetFullPath((Split-Path $PSScriptRoot -Parent))
$sourceRoot = Join-Path $workspaceRoot 'outputs'
$thesisRoot = 'C:\Users\paola\Tesis'
$targetRoot = [IO.Path]::GetFullPath((Join-Path $thesisRoot '03_Resultados\Agroclima\vigente\correlaciones\maize_ONI_frecuencias'))
if (-not $targetRoot.StartsWith(($thesisRoot+'\'),[StringComparison]::OrdinalIgnoreCase)) { throw 'Destino fuera de tesis' }
$names = @('matriz_frecuencias_ONI_20261019_152551','matriz_frecuencias_ONI_corregida_20261019_165114','contrastes_frecuencias_ONI_20261019_211055','sensibilidad_ONI_20261019_211459','mapas_ONI_20261020_091318','revision_58_pixeles_20261019','revision_limpieza_20261019')
$plan = foreach ($name in $names) {
    $sourcePath = [IO.Path]::GetFullPath((Join-Path $sourceRoot $name))
    $targetPath = [IO.Path]::GetFullPath((Join-Path $targetRoot $name))
    if (-not $sourcePath.StartsWith(($sourceRoot+'\'),[StringComparison]::OrdinalIgnoreCase)) { throw 'Origen fuera de outputs' }
    if (-not $targetPath.StartsWith(($targetRoot+'\'),[StringComparison]::OrdinalIgnoreCase)) { throw 'Destino fuera del objetivo' }
    if (-not (Test-Path -LiteralPath $sourcePath)) { throw "Origen ausente: $sourcePath" }
    $item = Get-Item -LiteralPath $sourcePath
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Origen ya es un enlace: $sourcePath" }
    if (Test-Path -LiteralPath $targetPath) { throw "Destino ya existe: $targetPath" }
    [pscustomobject]@{name=$name;source=$sourcePath;target=$targetPath}
}
New-Item -ItemType Directory -Path $targetRoot -Force | Out-Null
$report = foreach ($entry in $plan) {
    $hashes = @(Get-ChildItem -LiteralPath $entry.source -File -Recurse | ForEach-Object {
        [pscustomobject]@{relative=$_.FullName.Substring($entry.source.Length+1);bytes=$_.Length;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash}
    })
    Move-Item -LiteralPath $entry.source -Destination $entry.target
    # Preserve historical absolute references without duplicating the result files.
    New-Item -ItemType Junction -Path $entry.source -Target $entry.target | Out-Null
    foreach ($record in $hashes) {
        $newFile = Join-Path $entry.target $record.relative
        if ((Get-FileHash -LiteralPath $newFile -Algorithm SHA256).Hash -ne $record.sha256) { throw "Hash diferente: $newFile" }
    }
    Write-Host "Reubicado y verificado: $($entry.name) ($($hashes.Count) archivos)"
    [pscustomobject]@{origen=$entry.source;destino=$entry.target;enlace_compatibilidad=$true;archivos=$hashes}
}
$json = $report | ConvertTo-Json -Depth 7
$json | Set-Content -LiteralPath (Join-Path $targetRoot 'registro_reubicacion_20261020.json') -Encoding utf8
$json | Set-Content -LiteralPath (Join-Path $sourceRoot 'registro_reubicacion_ONI_20261020.json') -Encoding utf8
@'
# Resultados ONI y frecuencias: ubicación oficial

Esta carpeta contiene las matrices, los contrastes, la sensibilidad sin tendencia, los mapas y sus diagnósticos.

La carpeta vigente de mapas es mapas_ONI_20261020_091318.
La matriz vigente es matriz_frecuencias_ONI_corregida_20261019_165114.

Los archivos se trasladaron sin recalcular ni alterar resultados y se verificaron con SHA256. Las rutas antiguas en Documents/ChatGPT/Tesis/outputs son enlaces de compatibilidad hacia estas carpetas, para conservar referencias históricas sin duplicar los datos.

Los scripts permanecen en Documents/ChatGPT/Tesis/pipeline_amenazas, pero las nuevas salidas predeterminadas apuntan a esta carpeta de la tesis. Se puede seguir indicando --output / -Output para una salida explícita distinta.
'@ | Set-Content -LiteralPath (Join-Path $targetRoot 'LEEME_UBICACION.md') -Encoding utf8
Write-Host "COMPLETO: $targetRoot"
