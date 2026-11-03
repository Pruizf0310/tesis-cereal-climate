$mjoLogs = 'C:\Users\paola\Documents\ChatGPT\Tesis\outputs\maize_mjo_cinco_fases_20261009_165410'
$Host.UI.RawUI.WindowTitle = 'SALIDA EN VIVO | Maíz GEE | cinco fases'
$mjoOffsets = @{}
Write-Host 'SALIDA REAL DE LOS CINCO PROCESOS GEE' -ForegroundColor Cyan
Write-Host 'Las líneas nuevas aparecen conforme se procesan los píxeles.'
Write-Host 'El cálculo está en segundo plano; cerrar esta vista no lo detiene.'
Write-Host ''
foreach ($mjoPhase in @('VEG','FLO','REP','FIL','MAT')) {
    $mjoPath = Join-Path $mjoLogs ($mjoPhase + '.log')
    $mjoLast = Get-Content -LiteralPath $mjoPath -Tail 60 -Encoding utf8 | Where-Object { $_ -match '^Píxeles |^TERMINADO:|^RuntimeError:' } | Select-Object -Last 1
    Write-Host ('[' + $mjoPhase + '] ' + $mjoLast) -ForegroundColor Green
    $mjoOffsets[$mjoPhase] = (Get-Item -LiteralPath $mjoPath).Length
}
while ($true) {
    foreach ($mjoPhase in @('VEG','FLO','REP','FIL','MAT')) {
        $mjoPath = Join-Path $mjoLogs ($mjoPhase + '.log')
        $mjoStream = [System.IO.File]::Open($mjoPath, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
        try {
            if ($mjoStream.Length -lt $mjoOffsets[$mjoPhase]) { $mjoOffsets[$mjoPhase] = 0 }
            [void]$mjoStream.Seek($mjoOffsets[$mjoPhase], [System.IO.SeekOrigin]::Begin)
            $mjoReader = [System.IO.StreamReader]::new($mjoStream, [System.Text.Encoding]::UTF8)
            $mjoText = $mjoReader.ReadToEnd()
            $mjoOffsets[$mjoPhase] = $mjoStream.Position
            foreach ($mjoLine in ($mjoText -split "`r?`n")) {
                if ($mjoLine -match '^Píxeles |^TERMINADO:|^RuntimeError:|^Error|^Traceback') {
                    Write-Host ('[' + $mjoPhase + '] ' + $mjoLine)
                }
            }
        } finally { $mjoStream.Dispose() }
    }
    Start-Sleep -Seconds 2
}
