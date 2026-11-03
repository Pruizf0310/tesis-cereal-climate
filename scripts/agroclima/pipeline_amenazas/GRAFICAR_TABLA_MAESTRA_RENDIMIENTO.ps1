param([string]$Output='',[int]$Dpi=220,[string]$Formats='png,svg')
$ErrorActionPreference='Stop'
$plotArgs=@('-u','-X','utf8',(Join-Path $PSScriptRoot 'graficar_tabla_maestra_rendimiento.py'),'--dpi',$Dpi,'--formats',$Formats)
if ($Output) { $plotArgs+=@('--output',$Output) }
& (Join-Path $PSScriptRoot '.venv\Scripts\python.exe') @plotArgs
if ($LASTEXITCODE -ne 0) { throw 'La ejecucion no termino; consultar error y no usar resultados sin completed.json.' }
