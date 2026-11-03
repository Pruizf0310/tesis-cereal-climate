$mjoFolder = 'C:\Users\paola\Documents\ChatGPT\Tesis\outputs\maize_mjo_cinco_fases_20261009_165410'
$Host.UI.RawUI.WindowTitle = 'Maíz ONI-MJO | Avance de las cinco fases'
while ($true) {
    Clear-Host
    Write-Host 'MAÍZ · COINCIDENCIA DIARIA AMENAZA / ONI / MJO' -ForegroundColor Cyan
    Write-Host ('Actualización: ' + (Get-Date -Format 'HH:mm:ss') + ' | refresco cada 10 segundos')
    Write-Host '10.923 píxeles por fase · 1981–2016 · EST ya completada'
    Write-Host ''
    foreach ($mjoPhase in @('VEG','FLO','REP','FIL','MAT')) {
        $mjoLog = Join-Path $mjoFolder ($mjoPhase + '.log')
        Write-Host $mjoPhase -ForegroundColor Yellow
        if (Test-Path -LiteralPath $mjoLog) {
            $mjoLines = Get-Content -LiteralPath $mjoLog -Tail 50 -Encoding utf8
            $mjoProgress = @($mjoLines | Where-Object { $_ -match '^Píxeles |^TERMINADO:|^RuntimeError:|^Error|^Traceback' })
            if ($mjoProgress.Count -gt 0) { $mjoProgress | Select-Object -Last 2 | ForEach-Object { Write-Host ('  ' + $_) } }
            else { $mjoLines | Select-Object -Last 1 | ForEach-Object { Write-Host ('  ' + $_) } }
        } else { Write-Host '  Esperando registro...' }
        Write-Host ''
    }
    Write-Host 'GEE tiene cuota restringida. Las estimaciones de tiempo son preliminares.'
    Write-Host 'Esta ventana solo muestra el avance. Cerrarla NO detiene el cálculo.' -ForegroundColor Green
    Start-Sleep -Seconds 10
}
