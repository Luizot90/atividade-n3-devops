from pathlib import Path
from html import escape
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import simpleSplit
p=Path('projeto')
pages=[
('Imagem e inicialização',[
('1. Qual a diferença entre imagem e container?', 'A imagem reúne o código, o Node e as dependências. O container é uma execução dessa imagem. Posso iniciar quatro containers a partir da mesma imagem e cada um terá seu próprio processo.'),
('Como o Dockerfile monta a API', 'O primeiro FROM abre a etapa de dependências com Node Alpine. WORKDIR define /app como diretório de trabalho. COPY leva a lista de dependências e o arquivo de versões para lá e RUN instala as bibliotecas de produção. O segundo FROM inicia a imagem final. COPY --from traz as bibliotecas e o outro COPY traz server.js. ARG recebe a versão durante o build. ENV deixa a versão disponível quando a API roda. USER node inicia o processo com um usuário sem privilégios de root. EXPOSE documenta a porta 3000 e CMD inicia o servidor.'),
('2. Como a API espera o banco ficar pronto?', 'No Compose, a API depende dos healthchecks do MySQL e do Redis. No Kubernetes os pods podem começar em qualquer ordem. A API tenta criar a tabela e repete a tentativa a cada dois segundos se o MySQL estiver iniciando. A readinessProbe consulta /health, que testa o banco e o Redis. O Service encaminha tráfego aos pods prontos. A livenessProbe usa /live para verificar se o processo responde mesmo durante uma falha no banco.')]),
('Recursos e comunicação',[
('3. Por que esses requests e limits?', 'O request é a quantidade que o agendador considera ao escolher um nó. O limit estabelece o teto do container. Na API comecei com 50m de CPU e 64Mi de memória, com limites de 250m e 128Mi. 50m equivale a 5% de um núcleo. São valores iniciais para uma API pequena em um notebook. Na etapa de operação, o request de CPU passa para 25m e o limite para 200m para facilitar o teste do HPA. Para ajustar esses números em produção, é preciso medir o consumo sob carga.'),
('4. Qual é o papel de Deployment, ReplicaSet e Service?', 'O Deployment descreve a versão da aplicação e quantas cópias devem estar disponíveis. Ele gerencia ReplicaSets. Cada ReplicaSet cria ou repõe pods para chegar à quantidade desejada. O Service da API oferece um endereço estável. Seu seletor app=api coincide com o rótulo dos pods da API. Assim, o endereço continua funcionando quando uma atualização substitui os pods.'),
('5. Por que base64 não protege senhas?', 'Base64 é uma codificação reversível. Quem consegue ler o conteúdo pode recuperar o texto original. Neste projeto, o Secret usa stringData com valores fictícios de laboratório. Em produção, usaria um gerenciador de segredos, controle de acesso por função, criptografia em repouso e rotação de credenciais. O arquivo .env local fica fora do Git.')]),
('Escala, recuperação e limites',[
('6. Como funciona o HPA deste projeto?', 'O mínimo é 2 e o máximo é 6 réplicas. O alvo de 50% se refere à utilização média em relação ao request de CPU dos pods da API. Com request de 25m por pod, 50% corresponde a 12,5m por pod, em média. Os geradores consultam a rota inicial. Ao encerrar a carga, o HPA pode levar vários minutos para reduzir as réplicas. Resultado observado: registrar contagem inicial, pico e contagem final a partir de hpa-linhas.txt.'),
('7. Quando usar rollout undo?', 'O rollback permite voltar a uma revisão anterior quando a nova imagem falha. O teste substitui a imagem 2.0 pela tag ausente-n3. No describe do pod novo, a seção Events permite identificar o motivo da falha ao obter a imagem. Com maxUnavailable igual a zero, o Deployment mantém as réplicas anteriores disponíveis enquanto a nova não fica pronta. Após o undo, a rota inicial deve voltar a confirmar a versão 2.0. Resultado observado: inserir o evento real, a revisão e a versão retornada.'),
('8. Quais são as limitações?', 'O MySQL usa um Deployment com uma réplica e estratégia Recreate para que dois processos não disputem o diretório de dados. O PVC permite substituir o pod, mas uma cópia única do banco ainda gera indisponibilidade e o volume não substitui um backup. O Redis mantém apenas um contador que pode zerar em um reinício. Para produção, eu testaria a restauração de backups, adotaria replicação adequada para o banco e mediria latência e consumo antes de aumentar os limites da API.')]),
('Evidências de execução',[
('Situação da coleta', 'A execução no Docker Desktop e a medição de réplicas ainda precisam ser registradas. As saídas abaixo podem ser incorporadas na versão editável do relatório depois dos testes.'),
('Docker e persistência', 'Registrar a versão e /live no container isolado. No Compose, mostrar /health e o mesmo ID antes e depois de down e up. No Kubernetes, mostrar os nomes do pod antigo e do novo, o PVC e o mesmo ID após a troca.'),
('Operação do cluster', 'Incluir kubectl get all, describe deployment api e rollout history. Registrar a escala 2, 4 e 2, a versão 2.0, o evento de falha no describe pod, a recuperação e os recursos depois de set resources.'),
('Métricas e nó', 'Incluir get hpa -w antes, durante e depois da carga, top pods e describe node. Capacity indica o total do nó. Allocatable é a quantidade disponível para os pods depois das reservas. Allocated resources mostra a soma dos requests e limits dos pods alocados. Anotar valores de CPU e memória do nó usado e manter o namespace visível no registro.')])]
ini,pico,fim=Path("evidencias/replicas.txt").read_text().split()
q,a=pages[2][1][0]
pages[2][1][0]=(q,a.split("Resultado observado:")[0]+f"No laboratório de CI, a API começou com {ini} réplicas, chegou a pelo menos {pico} durante a carga e retornou a {fim}.")
q,a=pages[2][1][1]
pages[2][1][1]=(q,a.split("Resultado observado:")[0]+"O rollout excedeu o prazo do teste. O describe do pod foi registrado antes do undo e a consulta posterior confirmou a versão 2.0.")
pages[3]=("Evidências de execução",[("Ambiente","Testes realizados no GitHub Actions em Linux com Docker Compose e Kubernetes criado pelo kind com kubeadm. Os registros a seguir identificam este ambiente de CI."),("Persistência","A API encontrou o mesmo registro do MySQL após derrubar e subir o Compose e após substituir o pod do MySQL no cluster. O teste comparou ID e título."),("Leitura dos registros","O primeiro anexo mostra as mudanças no HPA. O segundo reúne as consultas feitas durante a atualização. O terceiro contém os comandos e os resultados do laboratório, incluindo recursos do nó e consumo dos pods."),("Recursos do nó","Capacity é o total físico informado pelo nó. Allocatable é a parcela disponível para os pods após as reservas. Allocated resources agrega os requests e limits dos pods alocados, enquanto kubectl top mostra consumo medido.")])
name='Luis Otávio Bovolanti Avanzini'
c=Canvas('Relatorio_N3.pdf',pagesize=A4)
w,h=A4
def line(x,y,s,size=12,bold=False,color='#19364a'):
 c.setFillColor(HexColor(color));c.setFont('Helvetica-Bold' if bold else 'Helvetica',size);c.drawString(x,y,s)
def footer(i):
 c.setStrokeColor(HexColor('#bdd0d5'));c.line(48,55,w-48,55);line(48,36,'UNIFASIPE   /   DevOps & Cloud Computing',9);line(w-70,36,str(i),9)
line(48,750,'UNIFASIPE     /     ADS · 4º SEMESTRE',12,True,'#197762')
line(48,610,'Catálogo de jogos',37,True)
line(48,566,'Aplicação com Docker e Kubernetes',23)
line(48,510,'Atividade avaliativa N3',15,True,'#197762')
for i,s in enumerate([name,'Professor Marcelo Linck','Sinop, 19 de novembro de 2026','Namespace: n3-luisotavio']):line(48,270-26*i,s)
footer(1);c.showPage()
for i,(title,sections) in enumerate(pages,2):
 line(48,758,'ATIVIDADE N3     /     CATÁLOGO DE JOGOS',10,True,'#197762');line(48,710,title,25,True);y=661
 for q,a in sections:
  line(48,y,q,14,True);y-=27
  for s in simpleSplit(a,'Helvetica',12,w-98):
   line(48,y,s);y-=18
  y-=22
 assert y>42,(title,y)
 footer(i);c.showPage()

import textwrap,re
page=6
for f in ["hpa.txt","versoes.txt","execucao.txt"]:
 y=0
 for raw in Path("evidencias",f).read_text(errors="replace").splitlines():
  for row in textwrap.wrap(re.sub(r"\x1b\[[0-9;]*[A-Za-z]","",raw).expandtabs(4),width=105,replace_whitespace=False,drop_whitespace=False) or [""]:
   if y<76:
    if y: footer(page);page+=1;c.showPage()
    line(48,765,"n3-luisotavio   /   "+f,12,True);y=741
   c.setFont("Courier",7.6);c.drawString(48,y,row);y-=10
 if y: footer(page);page+=1;c.showPage()
c.save()
