# Fase 5 — a voz gerada é a voz pedida?

Protocolo, **pré-registado antes de medir**. Fecha a pergunta aberta desde a
Fase 1 Passo 7, e é o Passo 1 da lista «[depois, em ordem](CONTROLO.md)».

**Objectivo:** decidir, por medição, se o contexto recuperado afasta a geração
da voz pedida — e, se afastar, autorizar a intervenção no prompt que o corrija.

> **Emenda de 2026-10-03, declarada.** Este protocolo foi commitado em
> `c72f3a0` com **um** instrumento. Enquanto as amostras estavam a ser geradas
> descobriu-se que uma **sessão paralela** media a mesma pergunta aberta por
> outro caminho — identificabilidade da voz, com controlo de poemas reais e
> juízes mecânicos — e o utilizador decidiu **juntar os dois**. O §9 é esse
> segundo instrumento, e o desenho dele não é meu (ver o cabeçalho do §9).
>
> O que a emenda **não** toca: o conjunto fixo, a rubrica, as âncoras e os
> portões G0–G4 do Instrumento I, todos escritos antes de existir amostra e
> inalterados. A emenda **acrescenta** um instrumento e nada afrouxa — e
> nenhuma amostra havia sido julgada quando foi escrita.

> **Renumeração.** O §5 do [plano](PLANO-RAG-LOCAL.md) chama «Fase 5» à interface
> e ao backend remoto; essa passa a **Fase 6**. A ordem não é capricho: o
> `CONTROLO.md` §6 já a tinha escrito assim, e construir interface para uma voz
> que não foi medida é construir em cima de uma suposição.

---

## 1. Porque é esta a fase, e não a interface

Quatro fases seguidas — 2, 3, 3B e 4 — mediram **recuperação**. O produto é
**verso**. O nDCG@5 não mede verso: mede que poemas chegam ao prompt, e nada
diz sobre o que sai dele.

A pergunta aberta está registada no `CONTROLO.md` §5 desde a Fase 1, com o
mecanismo já identificado:

> «**Sem copiar, nem sempre é a voz pedida** — os versos originais explicam e
> atribuem significado, o que Caeiro proíbe.»

Isto é uma hipótese com mecanismo, e um mecanismo é falsificável. É o que esta
fase faz.

---

## 2. A hipótese, enunciada com precisão

**H:** o contexto recuperado degrada a *poética* da voz pedida.

O mecanismo proposto tem duas partes, e as duas estão no código:

1. O cabeçalho do prompt apresenta o contexto como
   «*Poemas teus, para terdes presente o registo e as imagens*»
   (`src/generation/prompt.py:_cabecalho`) — isto é, como **material de
   registo**.
2. A persona de Caeiro proíbe atribuir significado oculto
   (`src/voices.py`, `PERSONAS[(CAEIRO, PT)]`). Mas os poemas recuperados para
   uma pergunta de Caeiro são, muitos deles, poemas que **explicam** — a
   redundância temática do corpus garante-o.

Se o modelo tomar o contexto como **modelo do que dizer** em vez de registo de
**como dizer**, a poética da voz cede ao contexto. H prevê então que a mesma
pergunta, na mesma voz, **sem contexto**, produza poética mais fiel.

A predição contrária é igualmente concreta, e é o que torna isto uma medição:
sem contexto a resposta perde o fundamento, logo o critério «responde à
pergunta» deve **piorar**. Se nenhum dos dois efeitos aparecer, H cai.

---

## 3. Desenho: ablação emparelhada, duas condições

| | condição | o que corre |
|---|---|---|
| **A** | **com contexto** | `Pipeline.responder` completo: recuperação densa, reordenação, guardas, repetição por plágio |
| **B** | **sem contexto** | mesma persona no `system`, mesma pergunta, mesma semente, mensagem de utilizador **sem o bloco de poemas** |

A única diferença na mensagem do utilizador:

```
A:  Pergunta: {q}

    Poemas teus, para terdes presente o registo e as imagens:

    {poemas}

    Responde só com o poema.

B:  Pergunta: {q}

    Responde só com o poema.
```

O `system` é **byte a byte o mesmo** nas duas condições. A frase de
enquadramento do contexto sai em B porque sem poemas ela anuncia o que não está
lá; mantê-la mediria um prompt defeituoso em vez da ausência de contexto.

### 3.1 Decisões de configuração, e porquê

| decisão | valor | porquê |
|---|---|---|
| gerador | `qwen2.5:7b-instruct-q4_K_M` | o de serviço (`src/generation/ollama.py`) |
| opções | `temperature=0,9` · `repeat_penalty=1,1` · `num_predict=220` | as de serviço; mudá-las mediria um sistema que ninguém usa |
| recuperação | `TOP_K`=6 de `N_RERANK`=8 candidatos |
| reordenação | **ligada** | é a melhor recuperação medida (Fase 3B, +0,090 nDCG@5). Se a voz falhar com o melhor contexto que temos, a culpa não é da recuperação |
| pipeline em A | **completo, com repetição por plágio** | é o que o utilizador recebe. O número de tentativas fica registado por amostra |
| amostras por célula | **1** | ver §8, ameaça declarada |
| semente | `20261003 + índice da pergunta`, igual em A e B | reprodutibilidade. O gerador de serviço **não** aceita semente (`OllamaGenerator._opcoes`); o harness injecta-a, e é o único desvio ao de serviço |

---

## 4. O conjunto fixo: as 20 perguntas já julgadas

As **20 perguntas do gabarito fechado** — `q01–q05`, `q11–q15`, `q21–q25`,
`q31–q35` de [`fase-1/08-perguntas.json`](fase-1/08-perguntas.json) — cinco por
cada uma das quatro vozes portuguesas.

**Desvio ao §6.2 do plano, que pede 25 perguntas:** estas 20 são as únicas cujo
nDCG@5 é **conhecido por pergunta** (Fase 3B). Isso permite uma pergunta que 25
perguntas novas não permitiriam — *recuperação melhor produz voz melhor?* — e
mantém o conjunto de geração alinhado com o de recuperação, em vez de criar um
segundo conjunto fixo a divergir do primeiro.

As vozes inglesas (`Search`, ortónimo EN) **ficam fora**: não há perguntas
julgadas para elas, e medi-las aqui seria medir sem gabarito.

---

## 5. A rubrica

| # | critério | 0–2 | como |
|---|---|---|---|
| 1 | **é verso?** | 0/2 | automático: `guard.e_verso` |
| 2 | **português europeu?** | 0–2 | automático: `guard.brasileirismos` no texto **cru** + `guard.fracao_lingua` |
| 3a | **poética da voz** | 0–2 | **à mão, às cegas** |
| 3b | **forma da voz** | 0–2 | **à mão, às cegas** |
| 4 | **responde à pergunta** | 0–2 | **à mão, às cegas** |
| 5 | **não plagia** | 0/2 | automático: `plagio.analisar` |

**Desvio ao §6.2:** o critério 3 («a voz é a pedida?») é **partido em dois**.
A hipótese H é sobre *o que a voz pode dizer* (poética), não sobre *como
escreve* (forma); juntá-los num número só esconderia exactamente o efeito que
se quer medir. Um Caeiro em verso livre curto que filosofa tem 3b=2 e 3a=0, e é
esse o caso que a pergunta aberta descreve.

### 5.1 Âncoras de 3a — poética, por voz

Escritas **antes de ver qualquer amostra**. É a única defesa real contra um
avaliador único: o que conta como 0 não pode ser decidido depois de ler o texto.

| voz | 2 | 1 | 0 |
|---|---|---|---|
| **Caeiro** | vê e não interpreta; nenhuma metafísica, símbolo, moral, nem natureza como espelho de sentimento | sensorial na maior parte, com **uma** volta simbólica ou moral | filosofa, interpreta, atribui significado oculto, personifica |
| **Campos** | excesso **executado**: acumula, enumera, repete, interrompe-se, contradiz-se; euforia e náusea | o sentimento está lá mas o excesso é **declarado** e não executado | contido e medido; Campos sem vertigem |
| **Reis** | medida, destino aceite sem o temer nem o amar, gozo breve do presente; dirige-se a Lídia/Neera/Cloe | a ética está lá mas sem interlocutor nem contenção | ética oposta (ânsia de mais, de durar), ou efusão |
| **Ortónimo** | fingimento, mistério, infância perdida, desencontro entre pensar e ser; o pensamento por baixo da música | o tema está lá sem o duplo fundo | tema alheio, ou confissão directa sem fingimento |

### 5.2 Âncoras de 3b — forma, por voz

> **Alterada em 2026-10-06 pela [Fase 5L](FASE-5L.md) (passo 22): saíram as
> contagens de versos por poema.** A versão original está logo abaixo, e a nota
> de compatibilidade no §3 da 5L — **as pontuações de 3b anteriores a essa data
> não são comparáveis com as posteriores**, porque a cláusula retirada tinha sido
> aplicada em 68 de 69 casos aplicáveis.
>
> Autorização: [5J §1](FASE-5J-RELATORIO.md) (o intervalo é descritivamente falso
> em 3 das 4 vozes), [5K §3](FASE-5K-RELATORIO.md) (como detector está
> **invertido**: AUC = 0,000 no Caeiro) e [5L §2.1](FASE-5L.md) (os **quatro**
> intervalos premeiam acima do poeta uma distribuição que não é a dele —
> inclusive o do Reis, que está descritivamente correcto).
>
> **O comprimento do poema continua a ser medido**, ao nível do **conjunto** e não
> da amostra: ver o passo 21 e a calibração da [5K](FASE-5K-RELATORIO.md).

| voz | 2 | 1 | 0 |
|---|---|---|---|
| **Caeiro** | verso livre, linhas curtas, sem rima, pouca imagem | livre mas com imagem decorativa | rimado, ou prosa com enters, ou ornamentado |
| **Campos** | versículo longo, respiração ampla, enumeração, anáfora | versículo presente mas curto, ou sem anáfora nem enumeração | verso curto regular, ou **truncado** antes de fechar |
| **Reis** | ode breve, estrofes de 3–4 versos, sem rima, sintaxe latinizante | estrofes irregulares, ou dicção achatada | versículo longo, ou **em latim** |
| **Ortónimo** | metro regular **e** rima, quadras ou quintilhas | rima ou metro inconsistentes | verso livre sem metro nem rima |

Uma amostra **truncada** leva **0 em 3b** e é pontuada normalmente nos outros
critérios. Truncar é falha de **fecho** — a amostra está incompleta —, e não um
juízo de intervalo; detecta-se sem juízo pelo campo `truncada`
(`done_reason == "length"`, ver [5J §2.3](FASE-5J-RELATORIO.md)). É a **única**
regra mecânica de comprimento que fica no 3b.

**O que fica e não está testado:** os limiares de **estrofe** (`3–4 versos`,
`quadras ou quintilhas`) e de **verso** (`linhas curtas`, `versículo longo`) são
comprimentos de estrofe e de linha, não de poema, e a 5J mediu só o poema. Pela
mesma lógica podem ter o mesmo defeito — está nomeado como passo aberto.

<details>
<summary><b>A âncora original (Fase 5, 2026-10-03) — para ler as pontuações até 2026-10-06</b></summary>

| voz | 2 | 1 | 0 |
|---|---|---|---|
| **Caeiro** | verso livre, linhas curtas, sem rima, pouca imagem, 10–20 versos | livre mas com imagem decorativa, ou fora do intervalo | rimado, ou prosa com enters, ou longo e ornamentado |
| **Campos** | versículo longo, respiração ampla, enumeração, anáfora, 15–30 versos | versículo presente mas curto, ou sem anáfora nem enumeração | verso curto regular, ou **truncado** antes de fechar |
| **Reis** | ode breve, estrofes de 3–4 versos, sem rima, **≤12 versos**, sintaxe latinizante | estrofes irregulares, ou dicção achatada | >12 versos, ou versículo longo, ou **em latim** |
| **Ortónimo** | metro regular **e** rima, quadras ou quintilhas, 12–20 versos | rima ou metro inconsistentes | verso livre sem metro nem rima |

Uma amostra **truncada** (`num_predict` esgotado) leva **0 em 3b** e é pontuada
normalmente nos outros critérios. Truncar é falha de forma, e já foi observada
duas vezes em Campos na Fase 4.

</details>

### 5.3 Âncoras de 4 — responde à pergunta

**2** responde ao que foi perguntado, na voz · **1** toca o tema mas responde a
outra coisa, ou responde em geral · **0** divaga, ou responde a um poema do
contexto em vez da pergunta.

O último caso é precisamente o que H prevê, e por isso está escrito como
âncora e não como observação.

### 5.4 Critério 5 em ambas as condições

`plagio.analisar` compara a resposta contra **o mesmo conjunto de chunks** nas
duas condições: os `TOP_K`=6 recuperados para aquela pergunta — em A estiveram
no prompt (os que couberam no orçamento), em B nenhum esteve. Sobreposição em B não é cópia do contexto, é **memorização do modelo**, e
mede-se com o mesmo instrumento por ser o mesmo risco para o utilizador.

Plágio contra o corpus inteiro (2083 poemas) **não** é medido aqui.

---

## 6. Cegueira

O procedimento de Fase 0 §5.3 falhou por ler as amostras agrupadas por modelo.
Aqui a mecânica impede-o:

1. `gerar_amostras.py` grava as 40 amostras em `01-amostras.md`, **embaralhadas**
   com semente fixa, com identificadores opacos `A01`–`A40`, mostrando só
   pergunta e texto. O mapa `id → (pergunta, condição)` vai para
   `01-chave.json`.
2. O embaralhamento garante que **duas amostras da mesma pergunta nunca ficam
   adjacentes**: ler o par em sequência é reconhecer a condição.
3. As pontuações são escritas em `02-pontuacoes.json` e **commitadas** antes de
   a chave ser aberta.

### Ameaças a esta cegueira, declaradas

- **O avaliador consegue adivinhar a condição.** Uma amostra sem contexto pode
  ser visivelmente mais magra, e uma amostra com contexto pode ecoar vocabulário
  dos poemas. A cegueira reduz o viés; não o elimina.
- **Avaliador único**, e o mesmo que escreveu as personas, o prompt e esta
  rubrica. **Não é medição intersubjectiva.** As âncoras pré-registadas são a
  mitigação, não a solução; a solução é o segundo avaliador ou o LLM-juiz do
  §6.2, e fica para a Fase 5B.
- As âncoras são de **mim para mim**. Qualquer pessoa que repita isto deve
  esperar desacordo nas fronteiras 1/2.

O **Instrumento II (§9) não tem nenhuma destas ameaças**: os juízes são
mecânicos e cegos por construção. Não substitui a rubrica — mede outra coisa —
mas dá à mesma hipótese H um teste que não passa pelo meu juízo, e é por isso
que a leitura robusta desta fase é a **concordância dos dois instrumentos**.

---

## 7. Portões, pré-registados

Estatística, a mesma da Fase 3B (`fase-3b/bench_significancia.py`), sem scipy:
**teste de sinais** sobre os 20 pares e **IC95% por bootstrap emparelhado**,
B=10000, semente 3. Por voz há n=5: só a **direcção** se lê, nunca significância.

| | portão | condição | o que autoriza |
|---|---|---|---|
| **G0** | **chão** | mediana de 3a em A **= 2** e ≥18/20 com 3a=2 | a pergunta aberta **fecha**: o contexto não degrada a poética. A rubrica passa a instrumento de regressão e a Fase 6 arranca |
| **G1** | **H confirmada** | 3a de B > 3a de A em **≥13 dos 20** pares *e* IC95% do Δ emparelhado **não contém 0** | H aceita-se: autoriza **uma** intervenção no prompt — reformular o enquadramento do contexto como registo e não como modelo — medida na Fase 5B com este mesmo instrumento |
| **G2** | **H rejeitada** | ≤10 pares a favor de B, ou IC95% a conter 0 | H cai. A pergunta aberta fecha com «o contexto não é a causa»; se 3a continuar baixo, a causa é a **persona** ou o **modelo**, e isso é outra fase |
| **G3** | **o custo** | ler 4 e 5 em conjunto com G1 | se B ganhar em 3a **e** perder em 4, a decisão **não** é remover o contexto — remover o contexto é remover o RAG, que é o projecto. É reformulá-lo |
| **G4** | **inconclusivo** | 11 ou 12 pares a favor de B | registado como inconclusivo, como a Fase 3 foi. Não se decide nada, e o desempate é o segundo avaliador — não mais uma corrida |

**G1 não pode disparar se G0 disparar**, e é deliberado: se a poética já está no
máximo em A, não há folga para o contexto estar a comer.

### A pergunta secundária, sem portão

Cruzar 3a de A com o nDCG@5 por pergunta da Fase 3B. **Não tem portão e não
decide nada**: n=20 com nDCG numa gama estreita não sustenta correlação. Fica
registado como observação, e é declarado aqui para não ser apresentado depois
como se fosse resultado.

---

## 8. O que esta fase não mede

- **Variância dentro da célula.** Uma amostra por célula, a `temperature=0,9`.
  A Fase 0 observou variância grande (llama3.1 de 10/10 a 4/10 entre prompts).
  Os 20 pares diluem o ruído na comparação **agregada**; qualquer leitura
  amostra a amostra é anecdótica, e é assim que será escrita.
- **«Vale como poema»** — o critério 5 da rubrica de Fase 0. É juízo estético, e
  com avaliador único não é falsificável. Fora.
- **Memorização contra o corpus inteiro.**
- **Latência.** Sem portão: B é por construção mais rápido, e isso não é
  resultado.
- **As vozes inglesas.**

---

## 9. Instrumento II — identificabilidade da voz, por juízes mecânicos

> **O desenho deste instrumento não é meu.** Veio de uma sessão paralela que
> media a mesma pergunta aberta por outro caminho, num `docs/FASE-VOZ.md` que
> nunca foi commitado; a corrida dela morreu a 12 de 24 gerações sem persistir
> nada, logo não há dados dela nesta fase — só o desenho, as armadilhas que ele
> evita e as predições do §9.4, que ela escreveu antes de existir amostra.
> Os ficheiros originais foram removidos na fusão, e é por isso que o desenho
> está transcrito aqui e no cabeçalho de `fase-5/identificar.py`.

### 9.1 O que este instrumento acrescenta ao primeiro

O Instrumento I **auto-calibra-se**: compara duas condições do mesmo sistema,
logo não precisa de saber quanto vale um 2 em absoluto. A identificabilidade
**não** se auto-calibra. Se um juiz identificar a voz pedida em 55% das
amostras, isso é bom ou mau? Não se sabe — falta saber quantas vezes identifica
Pessoa **autêntico**.

E não é hipotético neste projecto: a Fase 4 Passo A1c mediu o centróide de
embedding sobre poemas **reais** tirados do índice e obteve **42–46%**
(34/80 por centróide, 37/80 por sonda). Para esse instrumento, 45% sobre
gerados é **indistinguível de Pessoa verdadeiro**. Sem controlo, 45% seria
chamado falhanço — e seria medir o instrumento em vez do sistema. É a mesma
lição do `util@3` da Fase 0, que saturou até o controlo inglês fazer 9/10.

**Reporta-se a diferença, nunca o nível.**

### 9.2 O que corre

| grupo | n | o que é |
|---|---|---|
| **A, com contexto** | 20 | as amostras da condição A do Instrumento I |
| **B, sem contexto** | 20 | as da condição B |
| **real** | 40 | poemas do corpus, 10 por voz, **excluindo** tudo o que entrou no prompt de alguma geração |

Correr os juízes sobre as **duas** condições é o que a fusão acrescenta ao
desenho original, que só tinha o pipeline completo: a identificabilidade fica
emparelhada por pergunta, e dá um teste **mecânico** da mesma hipótese H.

Dois juízes, de propósito com defeitos opostos:

| juiz | força | defeito |
|---|---|---|
| **centróide de embedding** | não pode memorizar: só vê geometria de estilo | fraco — 42–46% em poemas reais, contra um piso de 25% |
| **qwen2.5:7b** | forte, e é conhecimento real de Pessoa | pode ter **memorizado** os reais do pré-treino |

### 9.3 As três armadilhas, e como são evitadas

1. **O centróide exclui os poemas de controlo.** Um poema real está no índice;
   deixá-lo no centróide da sua própria voz é pedir ao juiz que reconheça o que
   já viu, não que classifique por estilo.
2. **Os três grupos enfrentam um juiz idêntico.** Os centróides calculam-se
   **uma vez**, já sem os controlos, e usam-se nos três grupos. Excluir os reais
   só quando se julgam reais daria instrumentos diferentes a grupos diferentes,
   e a diferença deixaria de significar nada.
3. **O prompt do juiz LLM é novo.** O da Fase 4 classifica *perguntas* («qual
   voz responderia a isto?»); este classifica *poemas* («quem escreveu isto?»).
   Os 72% **não transferem**, e é o controlo de reais que calibra este prompt.

E três confundidores, que ficam declarados por não serem evitáveis:

- **Os vectores do índice levam «Autor — Título» à cabeça**
  (`Chunk.indexed_text`), logo os centróides carregam o nome do heterónimo. Os
  três grupos são julgados como verso puro contra esses centróides, logo isto
  deprime o **nível** dos três por igual e deixa a **diferença** interpretável.
  O nível só é comparável com os 42–46% da Fase 4, que partilham o defeito.

  **E o defeito é maior do que a comparabilidade de nível.** No Passo A1c da
  Fase 4 (`fase-4/bench_roteador_c.py:91–95`) os poemas de teste são encodados
  como `query` a partir de `chunk.text` — verso puro — contra centróides
  construídos de `indexed_text`, que leva o **nome do heterónimo** à cabeça. O
  nome é o indício mais discriminativo que existe para esta tarefa, está no
  centróide e não está em consulta nenhuma: o instrumento estava handicapado e
  os 42–46% saem **subestimados**. Para esta fase não há problema — os três
  grupos partilham o handicap e o que se reporta é a diferença — mas a conclusão
  que a Fase 4 tirou daquele número, «o espaço do e5 não separa estas vozes»,
  **está mais forte do que a evidência permite**. A decisão de usar o roteador
  por LLM aguenta-se (72% contra ≤52,5%, e todas as variantes de embedding
  partilham o handicap, logo a ordenação entre elas mantém-se); a afirmação
  sobre o espaço não. Achado de uma sessão paralela, verificado aqui no código;
  a correcção pertence à Fase 4 e não a esta.

  **Emenda de 2026-10-03, depois de as 40 amostras existirem e antes de o
  Instrumento II correr.** A remedição da Fase 4 quantificou o defeito: com
  centróides de `c.text` em vez de `indexed_text`, a exactidão sobre poemas sobe
  de 42–46% para **64–69%**. O defeito valia **23 pontos**, e a afirmação da
  Fase 4 está **refutada**, não só enfraquecida — o espaço do e5 separa estas
  vozes. Isso **esvazia a razão** que este protocolo deu para usar
  `idx.vectores`: era a comparabilidade com os 42–46%, e esse número é agora
  um artefacto conhecido. O Instrumento II passa a correr **duas variantes de
  centróide** — `com_nome` (a pré-registada, que não se apaga) e `sem_nome` (a
  corrigida, 23 pontos mais forte) — e reportam-se as duas. Os portões G5–G7
  **não mudam**: são sobre diferenças entre grupos, e um juiz mais forte mede a
  mesma diferença com menos ruído. A predição 1 do §9.4 — «o centróide não
  distingue gerados de reais, por não ter potência» — passa a ser testável com
  um instrumento que tem potência, e é o que ela merecia.
- **A memorização dos reais pelo juiz LLM** infla os reais, logo **alarga** a
  diferença real-vs-gerado: agrava a conclusão em vez de a inventar.
- **As descrições de voz do juiz LLM são quase as personas do gerador**, e isso
  empurra no sentido contrário: um poema gerado foi escrito *para* casar com
  aquela descrição, logo o juiz favorece os gerados e **encurta** a diferença.
  Os dois confundidores do LLM têm sinais opostos e não se somam — mais uma
  razão para a leitura robusta ser a concordância com o centróide, que não tem
  nenhum dos dois.

### 9.4 Predições, da sessão paralela, escritas antes de existir amostra

1. **O centróide não distingue gerados de reais.** Reais 42–46% (já medido);
   gerados em ±8 pontos disso, logo um instrumento **sem potência** para esta
   pergunta — e nesse caso serve de controlo negativo do juiz, não de medida.
2. **O LLM acerta mais em reais que em gerados.** Reais acima de 60%, gerados
   abaixo. É a predição central: a diferença **é** o défice de voz.
3. **Campos é o mais identificável; Reis e o ortónimo os mais confundidos.** O
   versículo longo é assinatura de superfície; a Fase 4 viu o Reis a 0,5 e o
   roteador a trocar Reis por ortónimo e por Caeiro.
4. **O critério 2 falha com frequência** — a `FASE-1.md` registou «PT-BR
   persiste apesar do few-shot».
5. **O critério 5 quase não falha** — a regra preventiva levou a mediana de
   versos copiados de 82% para 0%.

As duas primeiras são as que valem; são as que a sessão paralela assinalou como
tal, e são as únicas em que este instrumento tem alguma potência.

### 9.5 Portões do Instrumento II

| | portão | condição | o que autoriza |
|---|---|---|---|
| **G5** | **a voz não se vê** | A − real ≥ 0, ou dentro do ruído, nos **dois** juízes | a voz gerada é tão identificável quanto Pessoa autêntico neste instrumento. O esforço sai da voz e vai para outro critério |
| **G6** | **H, pela via mecânica** | pares discordantes desequilibrados a favor de **B** nos dois juízes | corrobora H independentemente da minha rubrica; soma-se a G1 |
| **G7** | **discordância** | os dois instrumentos apontam em sentidos contrários | **nada se decide.** A rubrica à mão fica em suspeita, como a Fase 3 ficou inconclusiva, e o desempate é um segundo avaliador humano |

**Potência, declarada antes de medir:** 20 por condição e 5 por voz por
condição. Por voz lê-se **direcção**, nunca significância, e os pares
discordantes a n=20 raramente dão significância — este instrumento é
**corroborativo**, não decisivo. Ter controlo de n igual é o que torna a leitura
possível; sem ele seria comparar contra um absoluto inventado.

---

## 10. Entregáveis

```
docs/fase-5/gerar_amostras.py     harness das duas condições
docs/fase-5/01-amostras.md        40 amostras, embaralhadas, cegas
docs/fase-5/01-chave.json         o mapa — não abrir antes de 02
docs/fase-5/01-amostras.json      texto cru, métricas automáticas, tentativas
docs/fase-5/02-pontuacoes.json    3a, 3b, 4 à mão
docs/fase-5/01-cru.jsonl          diário de bordo (só em re-corridas: ver nota)
docs/fase-5/03-resultados.json    sinais, IC95% bootstrap, medianas
docs/fase-5/identificar.py        Instrumento II: controlo real + dois juízes
docs/fase-5/04-identificacao.json matrizes, diferenças, pares discordantes
docs/FASE-5-RELATORIO.md          o que os portões decidiram
```

**Nota sobre o `01-cru.jsonl`:** não existe para esta corrida, e a razão fica
registada em vez de corrigida. A persistência incremental foi acrescentada ao
harness **durante** a geração das 40 amostras, depois de a sessão paralela
perder 12 gerações por só serializar no fim; o processo já a correr tinha o
código antigo em memória e escreveu só os ficheiros finais. O diário serve
re-corridas e retomas, não esta. Os tempos e o diagnóstico por amostra estão no
`01-chave.json`.

## 11. Checklist do protocolo

```
[ ] A1  este documento commitado ANTES de qualquer amostra existir
[ ] A2  harness: condição A pelo pipeline, condição B sem contexto, system igual
[ ] A3  40 amostras geradas; métricas automáticas (1, 2, 5) calculadas
[ ] A4  embaralhamento com pares nunca adjacentes, chave em ficheiro separado
[ ] B1  3a, 3b e 4 pontuados às cegas nas 40 amostras
[ ] B2  pontuações commitadas antes de a chave ser aberta
[ ] C1  sinais, bootstrap e medianas calculados
[ ] C2  portão aplicado, e qual disparou declarado
[ ] D1  controlo de 40 poemas reais, sem sobreposição com o que entrou no prompt
[ ] D2  centróides calculados UMA vez, sem os controlos, para os três grupos
[ ] D3  matrizes de confusão dos dois juízes nos três grupos
[ ] D4  diferenças A−real, B−real, A−B, e os pares discordantes por juiz
[ ] D5  as cinco predições do §9.4 confrontadas uma a uma
[ ] C3  relatório, com as ameaças do §6 repetidas e não escondidas, e a
        concordância (ou não) dos dois instrumentos como leitura final
```
