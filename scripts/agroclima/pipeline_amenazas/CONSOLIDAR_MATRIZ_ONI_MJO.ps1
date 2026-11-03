param(
    [string]$Output='',
    [string]$Python=(Join-Path $PSScriptRoot '.venv\Scripts\python.exe')
)
$ErrorActionPreference='Stop'
$matrixArgs=@('-u','-X','utf8',(Join-Path $PSScriptRoot 'consolidar_matriz_oni_mjo.py'))
if ($Output) { $matrixArgs+=@('--output',$Output) }
& $Python @matrixArgs
if ($LASTEXITCODE -ne 0) { throw 'Consolidacion incompleta. Revisar el error; usar solo resultados con completed.json.' }
