# Fase 5 — a voz gerada é a voz pedida?

Protocolo, **pré-registado antes de medir**. Fecha a pergunta aberta desde a
Fase 1 Passo 7, e é o Passo 1 da lista «[depois, em ordem](CONTROLO.md)».

**Objectivo:** decidir, por medição, se o contexto recuperado afasta a geração
da voz pedida — e, se afastar, autorizar a intervenção no prompt que o corrija.

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
| reordenação | **ligada** | é a melhor recuperação medida (Fase 3B, +0,090 nDCG@5). Se a voz falhar com o melhor contexto que temos, a culpa não é da recuperação |
| pipeline em A | **completo, com repetição por plágio** | é o que o utilizador recebe. O número de tentativas fica registado por amostra |
| amostras por célula | **1** | ver §8, ameaça declarada |
| semente | `20261003 + índice da pergunta`, igual em A e B | reprodutibilidade |

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

| voz | 2 | 1 | 0 |
|---|---|---|---|
| **Caeiro** | verso livre, linhas curtas, sem rima, pouca imagem, 10–20 versos | livre mas com imagem decorativa, ou fora do intervalo | rimado, ou prosa com enters, ou longo e ornamentado |
| **Campos** | versículo longo, respiração ampla, enumeração, anáfora, 15–30 versos | versículo presente mas curto, ou sem anáfora nem enumeração | verso curto regular, ou **truncado** antes de fechar |
| **Reis** | ode breve, estrofes de 3–4 versos, sem rima, **≤12 versos**, sintaxe latinizante | estrofes irregulares, ou dicção achatada | >12 versos, ou versículo longo, ou **em latim** |
| **Ortónimo** | metro regular **e** rima, quadras ou quintilhas, 12–20 versos | rima ou metro inconsistentes | verso livre sem metro nem rima |

Uma amostra **truncada** (`num_predict` esgotado) leva **0 em 3b** e é pontuada
normalmente nos outros critérios. Truncar é falha de forma, e já foi observada
duas vezes em Campos na Fase 4.

### 5.3 Âncoras de 4 — responde à pergunta

**2** responde ao que foi perguntado, na voz · **1** toca o tema mas responde a
outra coisa, ou responde em geral · **0** divaga, ou responde a um poema do
contexto em vez da pergunta.

O último caso é precisamente o que H prevê, e por isso está escrito como
âncora e não como observação.

### 5.4 Critério 5 em ambas as condições

`plagio.analisar` compara a resposta contra **os mesmos cinco chunks** nas duas
condições: os recuperados para aquela pergunta — em A estiveram no prompt, em B
não. Sobreposição em B não é cópia do contexto, é **memorização do modelo**, e
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

## 9. Entregáveis

```
docs/fase-5/gerar_amostras.py     harness das duas condições
docs/fase-5/01-amostras.md        40 amostras, embaralhadas, cegas
docs/fase-5/01-chave.json         o mapa — não abrir antes de 02
docs/fase-5/01-amostras.json      texto cru, métricas automáticas, tentativas
docs/fase-5/02-pontuacoes.json    3a, 3b, 4 à mão
docs/fase-5/03-resultados.json    sinais, IC95% bootstrap, medianas
docs/FASE-5-RELATORIO.md          o que os portões decidiram
```

## 10. Checklist do protocolo

```
[ ] A1  este documento commitado ANTES de qualquer amostra existir
[ ] A2  harness: condição A pelo pipeline, condição B sem contexto, system igual
[ ] A3  40 amostras geradas; métricas automáticas (1, 2, 5) calculadas
[ ] A4  embaralhamento com pares nunca adjacentes, chave em ficheiro separado
[ ] B1  3a, 3b e 4 pontuados às cegas nas 40 amostras
[ ] B2  pontuações commitadas antes de a chave ser aberta
[ ] C1  sinais, bootstrap e medianas calculados
[ ] C2  portão aplicado, e qual disparou declarado
[ ] C3  relatório, com as ameaças do §6 repetidas e não escondidas
```
