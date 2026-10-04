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

## 7. Instrumento II — identificabilidade

> **A correr.** Os dois juízes mecânicos sobre as três condições — A, B e 40
> poemas reais de controlo — estão em fila atrás da remedição dos centróides da
> Fase 4, que ocupa a CPU. Esta secção fica aberta e é preenchida quando a
> corrida fechar; a leitura final da fase depende dela, porque o portão G7 diz
> que se os dois instrumentos apontarem em sentidos contrários **nada se
> decide**.

Uma coisa já se pode dizer, e é uma ressalva que pertence ao corpo do relatório
e não às pendências: a diferença real-vs-gerado que esse instrumento vai
reportar está **encurtada por construção**. As descrições de voz do juiz LLM são
quase as personas do gerador, e um poema gerado foi escrito *para* casar com
aquela descrição. O confundidor empurra ao contrário da memorização dos reais, e
os dois não se cancelam de forma conhecida. Ver [`FASE-5.md`](FASE-5.md) §9.3.

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
[ ] D1  controlo de 40 poemas reais                          (a correr)
[ ] D2  centróides uma vez, sem os controlos, para os três grupos
[ ] D3  matrizes de confusão dos dois juízes nos três grupos
[ ] D4  diferenças A−real, B−real, A−B, e pares discordantes
[ ] D5  as cinco predições do §9.4 confrontadas
[~] C3  relatório: as ameaças repetidas; a concordância dos dois instrumentos
        fica pendente do Instrumento II
```

Fora do protocolo, e registado por ter aparecido pelo caminho: a conclusão da
Fase 4 sobre o espaço do e5 está mais forte do que a medição que a sustenta
(`6099e86`), e a remedição está a correr noutra sessão.

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

**O que a medição aponta** é que o défice de voz está na **persona** ou no
**modelo**, e o Caeiro é o caso a atacar primeiro: é o único a 0,0, e é o único
cuja persona é uma lista de **interdições** («não lhes atribuis significado
oculto», «recusas a metafísica», «não personificas») em vez de uma lista de
indicações. Um modelo de 7B a seguir interdições negativas é uma hipótese
concreta, barata de testar, e é a entrada natural para uma Fase 5B — depois de
pré-registada, e com o segundo avaliador que esta fase não teve.
