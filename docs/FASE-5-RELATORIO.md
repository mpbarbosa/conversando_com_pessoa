# Fase 5 — relatório: a voz gerada não é a voz pedida, e o contexto não é a causa

Protocolo em [`FASE-5.md`](FASE-5.md), pré-registado em `c72f3a0` **antes de
existir uma amostra**, e emendado em `f66c918` para acolher o segundo
instrumento. As pontuações à mão foram commitadas em `7bcbbdb` **antes de a
chave ser aberta**.

---

## 1. O que se decidiu

**O portão G2 disparou: a hipótese H cai.** O contexto recuperado **não**
degrada a poética da voz pedida.

E cai levando consigo o mecanismo que estava escrito no `CONTROLO.md` §5 desde a
Fase 1, Passo 7:

> «Sem copiar, nem sempre é a voz pedida — os versos originais explicam e
> atribuem significado, o que Caeiro proíbe.»

A primeira metade é verdade e está agora medida: **nem sempre é a voz pedida**.
A segunda metade — a explicação — é falsa. O Caeiro quebra a sua própria
interdição **sem contexto nenhum**.

A pergunta aberta há quatro fases fecha-se assim: não com uma correcção ao
prompt do contexto, que era o que eu esperava autorizar, mas com a eliminação do
suspeito que eu próprio tinha nomeado.

**E os dois instrumentos concordam.** O Instrumento II, com juízes mecânicos que
não passam pelo meu juízo, também não corrobora H — o indício que tem aponta ao
contrário, e não atinge significância. O portão G7, que reservava a decisão para
o caso de discordarem, não dispara.

O que o Instrumento II acrescenta é uma distinção que o primeiro não podia ver:
**a voz gerada é tão identificável quanto Pessoa autêntico** (G5 dispara, +3
pontos no juiz com potência) **e ao mesmo tempo não cumpre a poética** (o Caeiro
a 0,0). Identificabilidade e poética não são a mesma coisa, e esta fase mede as
duas e mostra-as a divergir.

---

## 2. O número

20 perguntas julgadas, 5 por voz, cada uma gerada duas vezes: **A** pelo
pipeline completo e **B** com a mesma persona, a mesma pergunta e a mesma
semente, sem o bloco de poemas. 40 amostras, pontuadas às cegas sobre uma folha
embaralhada.

| critério | A | B | Δ (B−A) | IC95% | sinais B/A/= | portão |
|---|---|---|---|---|---|---|
| **3a poética** | 1,0 | 1,0 | +0,100 | [−0,250, +0,500] | **4 / 4 / 12** | **G2** |
| 3b forma | 1,0 | 1,0 | +0,350 | [+0,000, +0,700] | 7 / 2 / 11 | — |
| 4 responde | 2,0 | 2,0 | +0,100 | [−0,100, +0,350] | 2 / 1 / 17 | — |
| 1 é verso | 2,0 | 2,0 | 0 | [0, 0] | 0 / 0 / 20 | — |
| 2 PT-PT | 2,0 | 2,0 | +0,100 | [−0,150, +0,400] | 3 / 2 / 15 | — |
| 5 não plagia | 2,0 | 2,0 | 0 | [0, 0] | 0 / 0 / 20 | — |

**Quatro contra quatro** é o resultado mais nulo que 20 pares podem dar. O
intervalo de confiança contém zero com folga dos dois lados, e o portão G2
estava escrito como «≤10 pares a favor de B, ou IC95% a conter 0». Cumpre as
duas condições.

Médias, para quem preferir: 3a dá 1,15 em A contra 1,25 em B. Sete amostras com
nota 2 em A, oito em B.

### Os oito pares que não empataram

| a favor de **sem contexto** | a favor de **com contexto** |
|---|---|
| q05 caeiro · q13 campos · q14 campos · q21 reis | q01 caeiro · q15 campos · q22 reis · q34 ortónimo |

Está distribuído por três vozes em cada coluna. Não há um padrão por voz, e com
n=5 por voz não haveria potência para o ver se houvesse.

---

## 3. O mecanismo nomeado era falso: o Caeiro

Por voz, a poética:

| voz | A | B | leitura |
|---|---|---|---|
| **caeiro** | **0,0** | **0,0** | falha nas duas condições |
| campos | 1,0 | 1,0 | o excesso é declarado, não executado |
| ortónimo | 1,0 | 1,0 | o tema sem o duplo fundo |
| **reis** | **2,0** | **2,0** | passa nas duas condições |

O Caeiro é a voz que falha, e falha **igual** com e sem contexto. As citações
são das amostras da condição **B**, sem um poema no prompt:

- «**Sentido em cada pedra**» — atribui significado por extenso, que é a
  interdição literal da persona (`src/voices.py`: «não lhes atribuis significado
  oculto»);
- «**Nas entrelinhas** do que se desvanece, descobro um rumo novo a seguir» —
  ler entrelinhas é o oposto exacto do que Caeiro faz;
- «a brisa **esquece** a minha passagem», «a terra **sente**, em leve abraço» —
  personificação, que a persona também proíbe;
- «**saudade de não-ser**», «Silencio a voz da existência» — metafísica pura.

Nenhuma destas veio de um poema recuperado, porque não havia poema recuperado.

Um par ilustra o contrário, e vale registá-lo para não parecer que o contexto
nunca faz nada: na **q21** («tenho medo de qualquer mudança»), a amostra **com**
contexto endossou o medo e pediu permanência — «Que não mude, este meu destino
tão calmo» —, que é a ética oposta à de Reis; a amostra **sem** contexto
aconselhou a não temer, que é a postura dele. Mas é **um** par de vinte, e os
outros dezanove não seguem nenhum padrão.

---

## 4. O critério que falha é a forma, e não estava na hipótese

3b dá Δ=+0,350, sinais **7 contra 2** a favor de sem contexto, e IC95% de
[+0,000, +0,700]. É a única diferença com sinal consistente que esta fase
encontrou.

**Não decide nada, e isso estava escrito antes de medir.** A hipótese era sobre
poética; 3b não tem portão. E o limite inferior do intervalo encostado a zero é
exactamente a situação que a [Fase 2](FASE-2-RELATORIO.md) rejeitou — «+0,004 é
ruído a n=20» — só que maior. Quem quiser isto como resultado tem de o
pré-registar e medir de novo.

O que **é** sólido é o nível: 3b tem 14 zeros nas 40 amostras, e as causas são
nomeáveis uma por uma. Nenhuma é o contexto:

| causa | voz | observado |
|---|---|---|
| mais de doze versos | reis | 16 versos onde a persona diz «no máximo doze» |
| quadras curtas em vez de versículo | campos | quatro estrofes de quatro versos curtos, onde a persona pede «versículo longo, de respiração ampla» |
| verso livre sem metro nem rima | ortónimo | a persona pede «metro regular e rima, quadras ou quintilhas» |
| rima onde não devia haver | caeiro | «esquecimento/pensamento», e a persona diz «sem rima» |
| **truncatura** | campos (3x) | `num_predict=220` esgotado a meio de «Perdidos os», «desconhec» |

A truncatura era **pendência conhecida** antes desta fase: o `CONTROLO.md` já
tinha «num_predict=220 corta o versiculo longo de Campos (visto 2x na Fase 4)».
Aconteceu três vezes em 40 — duas em A, uma em B — e é a única causa de forma
com correcção óbvia e barata.

---

## 5. Uma correcção ao meu próprio instrumento, antes dos números dele

O critério 2 deu, na primeira passagem, **mediana 0,0 nas duas condições**: 38
das 40 amostras reprovadas. Era defeito meu.

Pus `PISO_LINGUA=0,50` no harness e apliquei-o a `guard.fracao_lingua`, que
conta **stopwords**. O 0,50 é o `MIN_FRACAO_DICIONARIO`, que se aplica a
`_fracao_reconhecida`, o **dicionário**. O piso real das stopwords é **0,12**, em
`guard.lingua_errada` — e o docstring dessa função avisa precisamente disto:

> «É português inequívoco — `silêncio`, `raízes`, `descalços` — mas telegráfico,
> sem artigos nem preposições, logo sem as palavras funcionais que a fracção
> conta. **O limiar media registo e chamava-lhe língua.**»

Repeti, no meu instrumento de medição, o erro que o código que eu estava a usar
documenta na própria função. A mediana de `fracao_lingua` nestas 40 amostras é
0,394, o que é normal em verso e reprova com folga um piso de 0,50.

Com o instrumento certo — `lingua_errada` a 0,12, `brasileirismos`, e o
dicionário a 0,50 onde ele pertence — o critério 2 **passa**: mediana 2,0, 35
amostras sem um único brasileirismo, 4 com um, e uma só a zero. A que ficou a
zero é a amostra degenerada do §6. Os valores errados estão preservados em
`c2_pt_errado_piso050` e a correcção em
[`fase-5/corrigir_c2.py`](fase-5/corrigir_c2.py).

**Mas o instrumento certo continua fraco, e o número não deve ser lido como
absolvição.** `brasileirismos` é uma lista de 14 palavras e não apanha colocação
pronominal. A olho, nas 40 amostras: «Uma mão **se recua**», «**meus passos** de
neblina», «nada sou mais do que o que **enxergas**». São marcadores brasileiros
que o detector não conta e que a Fase 0 já tinha observado como sistemáticos
neste modelo. O critério 2 passa **pelo instrumento que existe**, e o
instrumento não chega.

---

## 6. O que mais apareceu

**Zero plágio em 40 amostras.** Nem uma. E também não na condição B, onde a
comparação é contra poemas que o modelo **nunca viu** — nenhuma sobreposição por
memorização detectável com este instrumento. A regra preventiva no `system`, que
na Fase 1 levou a mediana de versos copiados de 82% para 0%, continua a valer.
Três perguntas em A precisaram de uma segunda tentativa; nenhuma de uma
terceira.

**Uma amostra degenerou por completo**, e é um modo de falha novo neste
projecto. Na q13 (campos, «o ruído das máquinas dá-me uma espécie de febre»), a
condição A saiu com as palavras **coladas sem espaços**:

```
Acidadeestende-seemumamáquina
Dasmãosdadasasárvoresdasilêncios
```

A anáfora e a acumulação são de Campos; o poema não existe. Foi a única das 40,
e foi a única amostra que `lingua_errada` reprovou — corretamente, porque não
tem palavras reconhecíveis. **As âncoras não previam degeneração** e eu decidi
como pontuar no momento, o que está declarado no `02-pontuacoes.json`: o gesto
anafórico conta na poética, a forma destruída é 0, e como resposta é 0. É a
decisão mais discutível deste julgamento.

Aconteceu com contexto. Com `repeat_penalty=1,1`, que a Fase 0 introduziu
precisamente para travar o ciclo degenerado do llama3.1. É **n=1** e não
sustenta nada; fica registado para o caso de voltar.

---

## 7. Instrumento II — identificabilidade, por juízes mecânicos

Três configurações de juiz sobre três grupos: as 20 amostras de A, as 20 de B, e
40 poemas reais do corpus, com os 55 poemas que entraram em algum prompt
excluídos do controlo. Os centróides calculam-se uma vez, já sem os controlos, e
servem os três grupos.

| juiz | A | B | real | A−real | B−real | A−B |
|---|---|---|---|---|---|---|
| centróide `com_nome` (a pré-registada) | 35% | 40% | **45%** | −10 | −5 | −5 |
| centróide `sem_nome` (a corrigida) | **65%** | 40% | **62%** | **+3** | **−22** | **+25** |
| qwen2.5:7b | 65% | 65% | **45%** | **+20** | **+20** | 0 |

### 7.1 O teste emparelhado, e o que ele recusa

As 20 perguntas são as mesmas nas duas condições, logo a identificação é
emparelhada. Teste de sinais exacto sobre os pares discordantes:

| juiz | só A acerta | só B acerta | n discordantes | p (1 lado) | p (2 lados) |
|---|---|---|---|---|---|
| centróide `com_nome` | 2 | 3 | 5 | 0,500 | 1,000 |
| centróide `sem_nome` | **7** | 2 | 9 | **0,090** | 0,180 |
| qwen2.5:7b | 3 | 3 | 6 | 0,656 | 1,000 |

**Nada atinge significância.** Os 25 pontos de diferença do centróide corrigido
assentam em **nove** pares discordantes, sete deles a favor de A, e sete de nove
dá p=0,090 a um lado. É direcção, não é resultado — e o §9.5 do protocolo
escreveu-o antes de existir número: «os pares discordantes a n=20 raramente dão
significância — este instrumento é **corroborativo**, não decisivo».

### 7.2 Os portões

**G6 não dispara.** Exigia pares discordantes desequilibrados a favor de **B**
nos dois juízes. Nenhum juiz os dá: o corrigido aponta ao contrário (7 contra
2), o LLM empata 3-3, e o contaminado dá 2 contra 3 em cinco pares. **H não é
corroborada pela via mecânica**, e o indício que existe é contra ela.

**G7 não dispara, e os dois instrumentos concordam.** O portão cobria «os dois
instrumentos apontam em sentidos contrários». Não apontam: o Instrumento I não
encontrou diferença na poética (4 contra 4) e o Instrumento II não encontra
diferença significativa na identificabilidade (p=0,18). Os dois **rejeitam H**,
e o segundo acrescenta, sem o estabelecer, um indício de que o contexto **ajuda**
em vez de prejudicar.

**G5 dispara — e a acção que eu lhe prescrevi não se segue.** A condição era
«A − real ≥ 0, ou dentro do ruído, nos dois juízes», e cumpre-se: +3 no centróide
corrigido e +20 no LLM. **A voz gerada é tão identificável quanto Pessoa
autêntico.** Mas o que eu escrevi que isso autorizaria — «o esforço sai da voz e
vai para outro critério» — **está errado**, e é esta fase que produz a prova:

> o Instrumento I mede o Caeiro a **0,0 de mediana na poética**, a pior das
> quatro vozes, e o Instrumento II identifica-o **ao nível do Caeiro real**.

Quando escrevi G5 estava a tratar identificabilidade como substituto de «a voz
está certa». Não é. Um poema pode exibir todos os marcadores de superfície de
uma voz e violar o que essa voz pode dizer. O portão disparou e a prescrição
dele não vale: **o que sai é a identificabilidade como medida de voz, não o
esforço na voz.**

### 7.3 O juiz LLM está saturado pelo confundidor, e o nível dele não se usa

O confundidor declarado no §9.3 — as descrições do juiz são quase as personas do
gerador — não é ressalva de margem: **domina o resultado**. O juiz dá 65% aos
gerados nas duas condições e **45% a Pessoa autêntico**. Ordena a imitação 20
pontos acima do original, porque os poemas gerados foram escritos *para* casar
com a descrição que ele tem à frente.

Um juiz assim não tem resolução para comparar duas imitações, e 65% nas duas
condições, idêntico, é o que a saturação parece. **A leitura de A-vs-B é a do
centróide corrigido**, e a razão não é dar o resultado que convém: o juiz LLM tem
um confundidor identificado, quantificado em +20 pontos e com mecanismo, e o
centróide não tem nenhum dos dois confundidores que lhe foram atribuídos.

O que isto deixa como regra, e é o que vale para fora desta fase: **um juiz cujas
descrições derivam das personas do gerador não mede cumprimento de persona em
nenhuma direcção, porque é circular.**

### 7.4 Por voz, com o n à vista

Centróide corrigido, A contra real, ao lado da poética do Instrumento I:

| voz | gerado (A) | real | Δ | poética (Instr. I) |
|---|---|---|---|---|
| caeiro | 2/5 = 40% | 7/10 = 70% | −30 | **0,0** |
| campos | 4/5 = 80% | 10/10 = 100% | −20 | 1,0 |
| **reis** | 4/5 = 80% | 4/10 = 40% | **+40** | **2,0** |
| ortónimo | 3/5 = 60% | 4/10 = 40% | +20 | 1,0 |

**A coluna não ordena nada.** Se um défice de poética aparecesse como défice de
identificabilidade, o Reis — a voz que o gerador cumpre melhor, 2,0 — não estaria
no topo com +40. E **a n=5 uma amostra vale 20 pontos**: os −30 do Caeiro são
uma amostra e meia, e nenhum destes Δ sobrevive a trocar um poema.

Uma primeira versão desta tabela aqui tinha **duas** linhas — Caeiro e o juiz
LLM — e sugeria que o centróide é mais sensível ao défice do Caeiro do que o LLM.
Com as quatro vozes à vista isso não se sustenta, e a correcção é da sessão
paralela, que verificou os números em vez de os aceitar.

### 7.5 Uma replicação independente

O centróide corrigido dá **62%** em 40 poemas reais aqui; a remedição da Fase 4
deu **64%** em 80 poemas, noutra sessão, com outro conjunto e outra semente. A
correcção dos centróides reproduz-se, e isso vale mais do que qualquer dos dois
números sozinho.

E o contrário também fecha: a variante `com_nome` dá **45%** em reais, dentro dos
42–46% que a Fase 4 publicou. O instrumento contaminado reproduz o número
contaminado — que é a confirmação de que o diagnóstico do defeito estava certo.

### 7.6 As cinco predições do §9.4, confrontadas

Escritas pela sessão paralela antes de existir amostra, que é o que as torna
refutáveis em vez de leitura retrospectiva.

| | predição | veredicto |
|---|---|---|
| 1 | o centróide não distingue gerados de reais, por não ter potência | **refutada em parte**: distingue B de real por −22 pontos, mas não A de real (+3). Tem potência, e tem-na só numa das condições |
| 2 | o LLM acerta mais em reais que em gerados; reais >60%, gerados <60% | **refutada e invertida**: reais 45%, gerados 65% nas duas condições |
| 3 | Campos o mais identificável; Reis e ortónimo os mais confundidos | **confirmada**: Campos 10/10 em real, Reis e ortónimo 4/10 cada |
| 4 | o critério 2 falha com frequência | **refutada pelo instrumento**, qualitativamente certa — ver §5 |
| 5 | o critério 5 quase não falha | **confirmada**: zero em 40 |

---

## 8. As ameaças, repetidas e não escondidas

- **Avaliador único**, e o mesmo que escreveu as personas, o prompt, a rubrica e
  as âncoras. **Não é medição intersubjectiva.** As âncoras pré-registadas e as
  razões por amostra são o que permite discordar de mim sem repetir a corrida;
  não são o mesmo que um segundo avaliador.
- **A cegueira é parcial.** Uma amostra sem contexto pode ser visivelmente mais
  magra, e eu conhecia o desenho. Reduz o viés, não o elimina.
- **Uma amostra por célula**, a `temperature=0,9`. Os 20 pares diluem o ruído na
  comparação agregada; qualquer leitura amostra a amostra é anecdótica, e as do
  §3 e do §6 estão escritas como tal.
- **Por voz, n=5.** Lê-se direcção, nunca significância. O «Caeiro a 0,0» é uma
  mediana de cinco.
- **Duas decisões de fronteira** foram minhas e estão declaradas: o interlocutor
  nomeado não foi exigido para Reis, e a degeneração foi pontuada por critério
  improvisado.

---

## 9. O que não foi feito, e porquê

- **Cruzar 3a com o nDCG@5 por pergunta.** O protocolo já dizia que esta
  observação não tinha portão e não decidia nada. Fica sem fazer por uma razão
  prática: o `fase-3b/03-resultados.json` guarda **agregados**, não o nDCG por
  pergunta, e recalculá-lo não se justifica para uma observação pré-declarada
  como inconclusiva.
- **O LLM-juiz da rubrica** do §6.2 do plano. O Instrumento II tem juízes
  mecânicos, mas para **identificação**, não para a rubrica. A rubrica continua
  com um avaliador único, e é a lacuna mais séria desta fase.
- **As vozes inglesas**, sem perguntas julgadas.
- **Plágio contra o corpus inteiro.**

---

## 10. Checklist do protocolo

```
[x] A1  protocolo commitado antes de qualquer amostra existir (c72f3a0)
[x] A2  harness: A pelo pipeline, B sem contexto, system byte a byte igual
[x] A3  40 amostras geradas; métricas automáticas calculadas
[x] A4  embaralhamento sem pares adjacentes, chave em ficheiro separado
[x] B1  3a, 3b e 4 pontuados às cegas nas 40 amostras
[x] B2  pontuações commitadas antes de a chave ser aberta (7bcbbdb)
[x] C1  sinais, bootstrap e medianas calculados
[x] C2  portão aplicado: **G2**, e a hipótese H cai
[x] D1  controlo de 40 poemas reais, 55 ids excluídos por terem entrado no prompt
[x] D2  centróides uma vez, sem os controlos, para os três grupos
[x] D3  matrizes de confusão dos três juízes nos três grupos
[x] D4  diferenças A−real, B−real, A−B, e pares discordantes com teste de sinais
[x] D5  as cinco predições do §9.4 confrontadas uma a uma
[x] C3  relatório: ameaças repetidas, e os dois instrumentos **concordam** —
        G5 dispara, G6 e G7 não
```

Fora do protocolo, e registado por ter aparecido pelo caminho: a conclusão da
Fase 4 sobre o espaço do e5 saiu de um instrumento handicapado (`6099e86`). A
remedição, feita na sessão paralela (`a259b24`), fechou: o defeito valia **23
pontos** em perguntas e 22 em poemas, e a afirmação «o espaço do e5 não separa
estas vozes» está **refutada** — separa-as a 68% em perguntas e 64–69% em
poemas. O colapso no Caeiro que a Fase 4 observou era artefacto do nome: 19
erros passam a 1.

Para esta fase o defeito foi inócuo na diferença, mas não no desenho: foi por
causa dele que o Instrumento II passou a correr **duas** variantes de centróide
em vez da contaminada sozinha, e é a variante corrigida que tem potência (§7).
A variante contaminada reproduz aqui os 45% da Fase 4, o que fecha o diagnóstico
pelos dois lados.

---

## 11. O que isto autoriza, e o que não

**Autoriza fechar a pergunta aberta da Fase 1 Passo 7.** Está medida, e a
resposta é: a voz pedida não se cumpre, o contexto não é a causa, e a rubrica
passa a instrumento de regressão — qualquer mudança de prompt mede-se com estas
20 perguntas e estas âncoras.

**Não autoriza a intervenção no prompt do contexto** que o portão G1 teria
autorizado. G1 não disparou, e reformular o enquadramento do contexto seria
agora mexer no que a medição acabou de absolver.

**Não autoriza, muito menos, tirar o contexto.** O critério 4 não caiu sem
contexto (2 pares a favor de B, 1 de A, 17 empates), e é tentador ler isso como
«o RAG não serve para nada». Seria ler mal: o critério 4 mede **responder à
pergunta**, não estar **fundamentado no corpus**. Um poema pode responder à
pergunta sem nenhum fundamento em Pessoa, e 17 empates dizem exactamente que
este critério não distingue as duas coisas. Medir o fundamento é outro
instrumento, e esta fase não o tem.

**Não autoriza o que o portão G5 dizia que autorizaria.** G5 disparou — a voz
gerada é tão identificável quanto Pessoa autêntico — e eu tinha escrito que isso
mandava o esforço «sair da voz e ir para outro critério». Não manda, e a prova é
desta fase: o Caeiro é identificado ao nível do Caeiro real **e** tem 0,0 de
mediana na poética. Ao escrever G5 tratei identificabilidade como substituto de
«a voz está certa», e os dois instrumentos juntos mostram que não é. O que sai é
a identificabilidade como medida de voz.

**O que a medição aponta** é que o défice está na **persona** ou no **modelo**, e
o Caeiro é o caso a atacar primeiro: é o único a 0,0, e é o único cuja persona é
uma lista de **interdições** («não lhes atribuis significado oculto», «recusas a
metafísica», «não personificas») em vez de indicações. Um 7B a cumprir
interdições negativas é uma hipótese concreta e barata de testar, e é a entrada
natural para uma Fase 5B — pré-registada, e com o segundo avaliador que esta
fase não teve.

### A hipótese da sombra lexical, e a defesa que ela precisa

Fica **declarada como hipótese**, não como achado: se o centróide separa o
Caeiro gerado do real (−30 pontos, a n=5) sem verificar proposição nenhuma,
talvez a interdição deixe rasto **lexical** — «entrelinhas», «sentido»,
«destino», «não-ser» movem o vector mesmo que o embedding não julgue o que o
poema afirma.

É falsificável por ablação de palavras, com os centróides em cache, e **não foi
corrida nesta fase por potência**: são 5 poemas de Caeiro, e mover a
identificação de 2/5 para 1/5 ou 3/5 não distingue a hipótese de nada. Pelo
critério desta casa — a Fase 2 rejeitou +0,004 por ser ruído a n=20 — aceitar
±20 pontos a n=5 seria incoerente.

Para ter potência precisa das **10** perguntas de Caeiro do conjunto dourado,
repetições por célula, e uma regra de selecção das palavras com uma propriedade
que não é a óbvia:

> **A lista não pode ser derivada dos poemas gerados, nem por contraste com os
> reais.** Se as palavras-alvo forem «as que aparecem no Caeiro gerado e não no
> real», a ablação move o vector na direcção certa **por construção** e o teste
> confirma-se a si mesmo. Pré-registar essa lista não defende nada: o vício não
> é ver os resultados, é a **regra de selecção olhar para o contraste que é o
> resultado.** A lista tem de vir de fora da amostra — do vocabulário de
> atribuição de significado que os **113 poemas reais** de Caeiro
> caracteristicamente **negam**, e que estão fora do conjunto de teste.

É o mesmo princípio das duas defesas que esta fase já usou: o controlo de poemas
reais vem de fora do tratamento, e os centróides excluem os controlos. Nos três
casos o que protege a medição não é a ordem temporal, é a **independência entre
a regra e a quantidade medida**. Formulação da sessão paralela, e é a parte
reutilizável de toda esta troca.
