# Catálogo de jogos | Atividade N3

Luis Otávio Bovolanti Avanzini · ADS, 4º semestre · UNIFASIPE

API Node.js com MySQL para guardar títulos e Redis para contar consultas. A versão aparece em GET /. GET /live verifica o processo e GET /health consulta os dois serviços. POST /jogos?titulo=Celeste cadastra um título. GET /jogos lista os registros e incrementa o contador.

## Como executar no Windows

Abra o PowerShell na pasta que contém este README. O roteiro completo está em **comandos.md**. Use um cluster de laboratório no Docker Desktop (Kubernetes com kubeadm, contexto docker-desktop), com armazenamento dinâmico e metrics-server funcionando. Os nomes e portas devem estar livres.

1. Copie .env.example para .env. Os valores de exemplo servem apenas para o exercício.
2. Construa e teste a imagem conforme a primeira seção do roteiro. Suba a aplicação com docker compose up -d --wait. A URL do Compose é http://localhost:3000.
3. No Kubernetes, confirme que os nós conseguem usar a imagem local. Execute kubectl apply -f k8s/ e acompanhe o rollout. A URL do NodePort é http://localhost:31083. Se o NodePort não estiver exposto pelo ambiente, mantenha **kubectl port-forward -n n3-luisotavio svc/api 8083:3000** aberto em outro terminal e use http://localhost:8083. Reabra o encaminhamento caso o pod selecionado seja substituído.
4. Se os pods mostrarem ErrImagePull para uma tag válida, verifique o contexto e o armazenamento de imagens do Docker Desktop. Em um cluster remoto, publique ambas as tags em um registro seu, ajuste a referência do Deployment e use esse mesmo prefixo nos comandos de atualização.
5. Execute as etapas de comandos.md e confira os resultados em cada uma. Para finalizar o relatório, abra relatorio.html no navegador, edite os trechos indicados, importe o registro de texto e use “Salvar em PDF”. Revise os dados locais antes de publicar. O Git deve ignorar .env e a pasta evidencias/.

## Organização da entrega

app/ contém o código e a imagem. k8s/ contém os manifestos. comandos.md documenta os testes. Publique a pasta do projeto em um repositório seu e entregue o link junto com o PDF final. Se for privado, conceda acesso ao professor.

## Verificação adicional no GitHub Actions

Coloque o conteúdo da pasta projeto na raiz da branch main ou n3-devops-luisotavio. O fluxo “Testes da N3” usa um runner Linux com Docker e um cluster kind criado com kubeadm. Em Actions, abra a execução e baixe o artefato registros-n3. Quando todos os testes passam, ele inclui Relatorio_N3.pdf e os registros usados para produzir o documento. Uma execução interrompida pode conter apenas registros parciais. Para o ambiente solicitado no enunciado, siga o roteiro de Docker Desktop ou use o Killercoda.
