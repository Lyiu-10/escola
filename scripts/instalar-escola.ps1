# No PC, sem admin: agenda a Escola no logon (127.0.0.1:8792) e cria o atalho "Escola" na área de trabalho.
# Pode rodar de novo: a tarefa e o atalho são recriados.
$ErrorActionPreference = 'Stop'

$repo = 'C:\Users\peric\Desktop\Projetos\escola'
$venv = Join-Path $repo '.venv\Scripts'

# --- tarefa: no logon, na sessão do usuário (sem senha); se cair, volta em 1 minuto ---
# Prioridade 4 (normal): na 7, a padrão do Agendador, o disco fica em prioridade baixa e o Python levou mais
# de 30 s só para ler os próprios módulos (24/10/2026).
$acao = New-ScheduledTaskAction -Execute (Join-Path $venv 'pythonw.exe') -Argument '-m escola' -WorkingDirectory $repo
$gatilho = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$config = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 5 -RestartInterval (New-TimeSpan -Minutes 1) -Priority 4
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName 'thalia escola' -Action $acao -Trigger $gatilho -Settings $config -Principal $principal -Force | Out-Null
Start-ScheduledTask -TaskName 'thalia escola'
Write-Host 'Tarefa "thalia escola" instalada e ligada (sobe sozinha no logon).'

# --- busca semanal da situação dos concursos (edital, inscrição, datas) ---
# Roda todo dia às 10h (ou no primeiro momento em que o PC estiver ligado); o próprio comando só busca quando a
# última busca boa tem 7 dias. Assim uma segunda com o PC desligado, ou uma busca que falhou, não perde a semana.
$acao = New-ScheduledTaskAction -Execute (Join-Path $venv 'pythonw.exe') -Argument '-m escola situacao' -WorkingDirectory $repo
$gatilho = New-ScheduledTaskTrigger -Daily -At 10am
$config = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 1) -Priority 4
Register-ScheduledTask -TaskName 'thalia escola situacao' -Action $acao -Trigger $gatilho -Settings $config -Principal $principal -Force | Out-Null
Write-Host 'Tarefa "thalia escola situacao" instalada (todo dia às 10h; busca de 7 em 7 dias).'

# --- atalho na área de trabalho: abre a Escola no navegador ---
$atalho = Join-Path ([Environment]::GetFolderPath('Desktop')) 'Escola.url'
$linhas = @('[InternetShortcut]', 'URL=http://127.0.0.1:8792/')
$icone = Join-Path $repo 'src\escola\web\icones\escola.ico'
if (Test-Path $icone) { $linhas += @("IconFile=$icone", 'IconIndex=0') }
Set-Content -Path $atalho -Value $linhas -Encoding ASCII
Write-Host 'Atalho "Escola" criado na área de trabalho.'
