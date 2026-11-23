# Roteiro de execução e coleta | PowerShell

Execute na ordem, em um ambiente exclusivo da atividade. Confira o resultado antes do próximo bloco. Execute os comandos watch no terminal indicado. Os arquivos em evidencias/ registram somente o que tiver sido executado. Revise nomes de máquina, IPs e metadados locais antes de compartilhar.

## 1. Imagem e container

```powershell
$ns = 'n3-luisotavio'
New-Item -ItemType Directory -Force evidencias | Out-Null
Start-Transcript -Path evidencias/principal.txt
Write-Output "Aluno Luis Otávio | namespace $ns"
if (!(Test-Path .env)) { Copy-Item .env.example .env }
docker build --build-arg VERSION=1.0 -t n3-catalogo:1.0 ./app
docker run -d --name n3-teste -p 127.0.0.1:3001:3000 n3-catalogo:1.0
Invoke-RestMethod http://localhost:3001/live
Invoke-RestMethod http://localhost:3001/
docker rm -f n3-teste
```

O primeiro teste exercita o processo isolado. A conexão aos serviços é verificada na próxima etapa.

## 2. Compose e persistência

```powershell
docker compose up -d --wait
docker compose ps
Invoke-RestMethod http://localhost:3000/health
$jogo = Invoke-RestMethod -Method Post 'http://localhost:3000/jogos?titulo=Celeste'
$jogo
docker compose down
docker compose up -d --wait
(Invoke-RestMethod http://localhost:3000/jogos).jogos | Where-Object id -eq $jogo.id
docker compose down
```

Confira o mesmo ID e título. O volume dados é mantido por down. A opção -v apagaria o volume.

## 3. Kubernetes e persistência

```powershell
kubectl config current-context
kubectl get nodes
kubectl top nodes
kubectl apply -f k8s/
kubectl rollout status -n $ns deployment/api --timeout=5m
kubectl get all -n $ns
kubectl describe deployment api -n $ns
kubectl get pvc -n $ns
$base = 'http://localhost:31083'
Invoke-RestMethod "$base/health"
$registro = Invoke-RestMethod -Method Post "$base/jogos?titulo=Hades"
$registro
$antigo = kubectl get pod -n $ns -l app=mysql -o jsonpath='{.items[0].metadata.name}'
kubectl delete pod -n $ns $antigo
kubectl get pods -n $ns -l app=mysql
kubectl wait --for=condition=Ready pod -l app=api -n $ns --timeout=4m
```

A inicialização do MySQL pode continuar mesmo depois de o pod aparecer como Running. O bloco seguinte aguarda a saúde da aplicação e compara o registro.

```powershell
$ok = $false
foreach ($tentativa in 1..60) { try { $s = Invoke-RestMethod "$base/health" -TimeoutSec 3; if ($s.mysql -eq 'ok') { $ok = $true; break } } catch {}; Start-Sleep 2 }
if (!$ok) { throw 'Banco ainda indisponível. Veja os eventos e logs do MySQL.' }
(Invoke-RestMethod "$base/jogos").jogos | Where-Object id -eq $registro.id
kubectl get pods,pvc -n $ns
```

## 4. Escala manual

```powershell
kubectl scale deployment/api --replicas=4 -n $ns
kubectl rollout status deployment/api -n $ns
kubectl get deployment,pods -n $ns -l app=api
kubectl scale deployment/api --replicas=2 -n $ns
kubectl rollout status deployment/api -n $ns
kubectl get deployment,pods -n $ns -l app=api
```

## 5. Atualização para 2.0

Num segundo PowerShell, acompanhe as respostas durante a troca, usando a URL do NodePort. Encerre com Ctrl+C depois do rollout.

```powershell
& { while ($true) { try { "$(Get-Date -Format T) $(Invoke-RestMethod http://localhost:31083/ -TimeoutSec 2 | ConvertTo-Json -Compress)" } catch { "$(Get-Date -Format T) falha: $_" }; Start-Sleep -Milliseconds 300 } } | Tee-Object -FilePath evidencias/versoes.txt
```

No terminal principal:

```powershell
docker build --build-arg VERSION=2.0 -t n3-catalogo:2.0 ./app
kubectl set image deployment/api api=n3-catalogo:2.0 -n $ns
kubectl rollout status deployment/api -n $ns --timeout=4m
kubectl rollout history deployment/api -n $ns
Invoke-RestMethod "$base/"
```

## 6. Falha proposital e recuperação

```powershell
kubectl set image deployment/api api=n3-catalogo:ausente-n3 -n $ns
kubectl rollout status deployment/api -n $ns --timeout=75s
kubectl get pods -n $ns -l app=api
$pods = (kubectl get pods -l app=api -n $ns -o json | ConvertFrom-Json).items
$falho = ($pods | Where-Object { $_.spec.containers[0].image -eq 'n3-catalogo:ausente-n3' } | Select-Object -First 1).metadata.name
kubectl describe pod $falho -n $ns
kubectl rollout undo deployment/api -n $ns
kubectl rollout status deployment/api -n $ns --timeout=4m
kubectl rollout history deployment/api -n $ns
Invoke-RestMethod "$base/"
```

Registre a mensagem de Events e a versão servida após a recuperação. O timeout do rollout defeituoso faz parte do teste.

## 7. Recursos e métricas

```powershell
kubectl set resources deployment/api -n $ns --requests=cpu=25m,memory=64Mi --limits=cpu=200m,memory=128Mi
kubectl rollout status deployment/api -n $ns
$pod = kubectl get pods -l app=api -n $ns -o jsonpath='{.items[0].metadata.name}'
kubectl describe pod $pod -n $ns
kubectl top pods -n $ns
```

A coleta de métricas pode levar alguns ciclos após a troca dos pods.

## 8. HPA antes, durante e depois da carga

```powershell
if ((kubectl autoscale --help | Out-String) -match '--cpu-percent') { kubectl autoscale deployment api -n $ns --min=2 --max=6 --cpu-percent=50 } else { kubectl autoscale deployment api -n $ns --min=2 --max=6 --cpu=50% }
kubectl get hpa -n $ns
```

Em outro PowerShell, aberto na mesma pasta, inicie a coleta abaixo. Espere aparecer uma porcentagem antes de gerar carga. Mantenha o observador aberto até a redução de réplicas.

```powershell
"Namespace n3-luisotavio | antes, durante e depois da carga" | Out-File evidencias/hpa.txt
kubectl get hpa -n n3-luisotavio -w | Tee-Object -FilePath evidencias/hpa-linhas.txt
```

No terminal principal, use a rota que responde sem consultar o banco para concentrar o teste na CPU da API.

```powershell
kubectl create deployment carga -n $ns --image=busybox:1.36 -- sh -c 'while true; do wget -q -O /dev/null http://api:3000/; done'
kubectl scale deployment/carga --replicas=8 -n $ns
kubectl rollout status deployment/carga -n $ns
kubectl get hpa,pods -n $ns
kubectl top pods -n $ns
```

Aguarde até o observador mostrar mais de duas réplicas. Se o percentual continuar baixo, confira os pods de carga e suas requisições, depois aumente os geradores para 12 se o nó tiver capacidade. Se aparecer <unknown>, verifique kubectl top pods e kubectl describe hpa api antes de prosseguir.

```powershell
kubectl delete deployment carga -n $ns
kubectl describe hpa api -n $ns
```

Espere o observador registrar a redução. A estabilização padrão de descida costuma durar cerca de cinco minutos e a coleta pode demorar mais. Encerre o observador com Ctrl+C. Copie as linhas reais e anote mínimo, pico e valor final.

## 9. Nó e estado final

```powershell
kubectl get all -n $ns
kubectl describe deployment api -n $ns
kubectl rollout history deployment/api -n $ns
kubectl top pods -n $ns
$no = kubectl get pod -n $ns -l app=api -o jsonpath='{.items[0].spec.nodeName}'
Write-Output "Namespace $ns | nó $no"
kubectl describe node $no
Stop-Transcript
```

No describe node, Capacity é o total do nó. Allocatable é o que o nó oferece aos pods depois das reservas. Allocated resources soma os requests e limits declarados pelos pods alocados, inclusive de outros namespaces. Para consumo medido use top. Antes da entrega, confira as oito respostas e os arquivos de evidências no relatório.
