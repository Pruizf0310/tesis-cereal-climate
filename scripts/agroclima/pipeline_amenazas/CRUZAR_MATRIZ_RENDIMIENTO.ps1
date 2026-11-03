param([string]$Output='')
$ErrorActionPreference='Stop'
$yieldArgs=@('-u','-X','utf8',(Join-Path $PSScriptRoot 'cruzar_matriz_rendimiento.py'))
if ($Output) { $yieldArgs+=@('--output',$Output) }
& (Join-Path $PSScriptRoot '.venv\Scripts\python.exe') @yieldArgs
if ($LASTEXITCODE -ne 0) { throw 'Cruce incompleto: consultar error y no usar resultados sin completed.json.' }
