#!/usr/bin/env bash
set -Eeuo pipefail
ns=n3-luisotavio
mkdir -p evidencias
exec > >(tee evidencias/execucao.txt) 2>&1
echo "Namespace: $ns | Luis Otávio | GitHub Actions, Linux, Kubernetes kind/kubeadm"
set -x
docker build -t n3-catalogo:1.0 app
docker run -d --name api-isolada -p 127.0.0.1:3001:3000 n3-catalogo:1.0
curl -fsS --retry 15 --retry-connrefused http://localhost:3001/live
docker rm -f api-isolada
cp .env.example .env
docker compose up -d --wait
docker compose ps
base=http://localhost:3000
salvar(){ curl -fsS -X POST "$base/jogos?titulo=$1" | tee /tmp/jogo.json; }
conferir(){ curl -fsS "$base/jogos" | jq -e --slurpfile item /tmp/jogo.json '.jogos | any(. == $item[0])'; cat /tmp/jogo.json; }
salvar Celeste
docker compose down
docker compose up -d --wait
conferir
docker compose down
if ! command -v kind; then go install sigs.k8s.io/kind@v0.27.0; export PATH="$(go env GOPATH)/bin:$PATH"; fi
kind create cluster --name n3 --wait 3m
kind load docker-image n3-catalogo:1.0 --name n3
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/download/v0.8.0/components.yaml
kubectl patch deployment metrics-server -n kube-system --type=json -p '[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'
kubectl apply -f k8s/
k(){ kubectl -n "$ns" "$@"; }
ready(){ k rollout status deployment/api --timeout=5m; }
ready
base="http://$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' n3-control-plane):31083"
curl -fsS "$base/health"
salvar Hades
k get pods,pvc
k delete pod -l app=mysql
for i in {1..90}; do curl -fsS --max-time 3 "$base/health" && break; sleep 2; done
conferir
k get pods,pvc
for n in 4 2; do k scale deployment/api --replicas="$n"; ready; k get deployment,pods -l app=api; done
docker build --build-arg VERSION=2.0 -t n3-catalogo:2.0 app
kind load docker-image n3-catalogo:2.0 --name n3
(while true; do curl -fsS -m 3 "$base/" || echo 'FALHA HTTP'; echo; sleep 0.5; done) > evidencias/versoes.txt 2>&1 &
monitor=$!
k set image deployment/api api=n3-catalogo:2.0
ready
kill "$monitor" || true
curl -fsS "$base/" | jq -e '.versao=="2.0"'
k rollout history deployment/api
k set image deployment/api api=n3-catalogo:ausente-n3
if k rollout status deployment/api --timeout=70s; then exit 1; fi
k get pods -l app=api
falho=$(k get pods -l app=api -o json | jq -r '.items[]|select(.spec.containers[0].image=="n3-catalogo:ausente-n3")|.metadata.name' | head -1)
k describe pod "$falho"
k rollout undo deployment/api
ready
curl -fsS "$base/" | jq -e '.versao=="2.0"'
k set resources deployment/api --requests=cpu=25m,memory=64Mi --limits=cpu=200m,memory=128Mi
ready
pod=$(k get pod -l app=api -o jsonpath='{.items[0].metadata.name}')
k describe pod "$pod"
if kubectl autoscale --help | grep -- '--cpu-percent' >/dev/null; then k autoscale deployment api --min=2 --max=6 --cpu-percent=50; else k autoscale deployment api --min=2 --max=6 --cpu=50%; fi
k get hpa -w > evidencias/hpa.txt &
watcher=$!
for i in {1..36}; do val=$(k get hpa api -o jsonpath='{.status.currentMetrics[0].resource.current.averageUtilization}'); [[ -n "$val" ]] && break; sleep 5; done
k get hpa
inicial=$(k get deployment api -o jsonpath='{.spec.replicas}')
k create deployment carga --image=busybox:1.36 -- sh -c 'while true; do wget -q -O /dev/null http://api:3000/; done'
k scale deployment/carga --replicas=12
pico=$inicial
for i in {1..48}; do n=$(k get hpa api -o jsonpath='{.status.currentReplicas}'); if (( n > pico )); then pico=$n; fi; if (( pico > 2 )); then break; fi; sleep 5; done
k get hpa
k top pods
k delete deployment carga
(( pico > 2 ))
for i in {1..100}; do final=$(k get hpa api -o jsonpath='{.status.currentReplicas}'); [[ "$final" == 2 ]] && break; sleep 5; done
[[ "$final" == 2 ]]
k get hpa
kill "$watcher" || true
k get all
k describe deployment api
k rollout history deployment/api
k top pods
kubectl describe node n3-control-plane
printf '%s %s %s\n' "$inicial" "$pico" "$final" > evidencias/replicas.txt
