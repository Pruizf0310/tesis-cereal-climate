param([switch]$Terminal,[string]$Table='pares_anuales')
$ErrorActionPreference='Stop'
$viewerArgs=@('-u','-X','utf8',(Join-Path $PSScriptRoot 'visor_tabla_maestra.py'),'--table',$Table)
if ($Terminal) { $viewerArgs+='--terminal' }
& (Join-Path $PSScriptRoot '.venv\Scripts\python.exe') @viewerArgs
