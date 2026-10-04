# Fase 5B — relatório: o instrumento saturou no chão, e a hipótese ficou sem teste

Protocolo em [`FASE-5B.md`](FASE-5B.md), pré-registado em `6cab876` **antes de
existir uma amostra**, com a estatística em `22fc07c` **antes de existir uma
pontuação**. As duas pontuações foram commitadas em `072795d` **antes de a chave
ser aberta**.

---

## 1. O que se decidiu

**O portão G4 disparou, nos dois avaliadores: inconclusivo por potência. Nada se
autoriza.** A `poetica` do Caeiro em `src/voices.py` fica como está.

E a razão não é o tamanho da amostra. São 30 pares, o triplo dos 10 que a Fase 5
teria tido nesta voz, e **22 deles empataram em 0–0**. O critério 3a não
distinguiu os braços porque não distingue nada nesta voz: está encostado ao
mínimo nas duas condições.

**A hipótese H5B não foi confirmada nem refutada — ficou sem teste.** É um
resultado diferente de «H5B é falsa», e a diferença importa: o instrumento com
que a íamos medir não tem resolução onde a medição precisava dela.

### O que esta fase estabelece, e é o seu resultado sólido

**O chão do Caeiro reproduz-se a n=10, com dois avaliadores cegos e três
repetições por célula.** O portão G0 estava escrito para disparar se a mediana
de 3a no braço de controlo fosse ≥ 1; não disparou. Mediana **0,0** em C e em P,
nos dois avaliadores.

A Fase 5 mediu isto a n=5, com um avaliador único e uma amostra por célula, e a
sessão que a escreveu avisou por escrito que metade do resultado por voz dela
vivia nessa fragilidade. **Vive-se agora a n=10, a 60 amostras e a dois
avaliadores independentes, e o número não se move.** É o número que essa sessão
pediu, e é o que esta fase tem de mais firme.

---

## 2. Os números

30 pares. Cada par é a mesma pergunta e a mesma repetição, com e sem as
interdições na cláusula poética. Desfecho primário: **3a, poética**.

| | avaliador | mediana C | mediana P | Δ (P−C) | IC95% | sinais P/C/= | d | p | portão |
|---|---|---|---|---|---|---|---|---|---|
| **3a** | **R1** | **0,0** | **0,0** | +0,100 | [−0,133, +0,333] | **4 / 3 / 23** | **7** | 1,000 | **G4** |
| **3a** | **R2** | **0,0** | **0,0** | +0,067 | [−0,100, +0,233] | **4 / 2 / 24** | **6** | 0,689 | **G4** |

O piso pré-registado era **d ≥ 8** pares discordantes. R1 tem 7, R2 tem 6, e o
`analisar.py` devolve G4 sem avaliar os outros portões — foi escrito assim antes
de existir pontuação, precisamente para que esta decisão não fosse minha agora.

**O piso não é o que salva H5B, e é importante dizê-lo.** Com 4 pares a favor de
P contra 3 a favor de C, o binomial dá p=1,000; com 4 contra 2, dá p=0,689. Se o
piso tivesse sido d ≥ 6 em vez de d ≥ 8, os dois avaliadores teriam caído em
**G2 — H5B rejeitada**. O que o piso faz é recusar **também** essa leitura, e a
razão está no §7 do protocolo: 6 ou 7 pares discordantes não licenciam
conclusão em nenhuma direcção.

Os restantes critérios, sem portão:

| critério | R1 Δ | R1 IC95% | R1 sinais | R2 Δ | R2 IC95% | R2 sinais |
|---|---|---|---|---|---|---|
| 3b forma | +0,067 | [−0,200, +0,333] | 7/6/17 | +0,067 | [−0,167, +0,300] | 5/4/21 |
| **4 responde** | +0,100 | [−0,033, +0,233] | 4/1/25 | **+0,233** | **[+0,067, +0,400]** | **8/1/21** |
| 1 é verso | 0 | [0, 0] | 0/0/30 | — | — | — |
| 2 PT-PT | +0,100 | [−0,067, +0,300] | 4/2/24 | +0,100 | [−0,067, +0,300] | 4/2/24 |
| 5 não plagia | −0,133 | [−0,400, +0,133] | 1/3/26 | — | — | — |

---

## 3. Porque é que a fase não pôde testar a hipótese

A aritmética é curta e vale escrevê-la, porque é a lição desta fase.

Um teste de sinais emparelhado só vê os pares em que os dois braços diferem. Dos
30 pares, **22 (R1) e 23 (R2) empataram em 0–0**: as duas condições tiraram zero
na poética, logo o par não diz nada. Mais um empatou em 1–1. Sobram 7 e 6 pares
informativos.

Só **8 dos 30 pares** (R1) tiveram **alguma** das duas amostras acima de zero —
7 em R2. A medição não fracassou por ruído; fracassou por **saturação no
mínimo**.

E isto não se corrige com mais amostras. Com a taxa observada, chegar a d ≥ 8
exigiria por volta de 40 pares, e chegar a potência para detectar um efeito
pequeno exigiria muitos mais — mas o problema não é o n. É que uma escala de três
pontos cujo valor modal é 0 em 83–87% das amostras não tem onde registar uma
melhoria parcial. Um poema que passa de «filosofa em quatro versos» para
«filosofa em dois» continua a ser 0 pela âncora, e a âncora está certa: foi
escrita para julgar se a voz se cumpre, não para medir graus de incumprimento.

**O que falta é um desfecho com resolução no chão.** A âncora de 1 pede «uma
volta simbólica ou moral» e a de 0 vale para duas ou para dez; uma contagem de
voltas por poema, ou a fracção de versos que interpretam, distinguiria o que esta
escala funde. Isso é desenho de instrumento, e é a entrada da fase seguinte.

---

## 4. O confundidor que apareceu, e que a Fase 5 não podia ver

**As três amostras que R1 pontuou com 2 em 3a — as únicas 2 de toda a fase —
tinham, as três, um poema real de Caeiro no prompt, e as três estão no braço
P.** Duas delas são do mesmo par de poemas recuperados.

A mais clara é a **B35** (P, q06, r2), que o detector de plágio reprovou com
**33% dos versos copiados**:

| | |
|---|---|
| **real**, `poem_350` | «Vai Tejo abaixo indiferentemente. / Mas não é indiferentemente **por não se importar comigo** / E **eu não exprimir** desolação **com isto**... / É indiferentemente por **não ter sentido nenhum**» |
| **gerado**, B35 | «O vento sopra na mata sem querer. / Mas **não é** sem querer **por não amar** a mata, / E **eu não exprimir** saudade **com isto**... / É sem querer porque **nada dela importa**.» |

É o mesmo molde sintáctico, o mesmo movimento em três tempos, com os substantivos
trocados. `poem_350` estava no prompt de B35.

O mesmo molde aparece noutra forma com `poem_1096` (Caeiro XLIII, «Antes o voo da
ave, que passa e não deixa rasto… / Mostra que já esteve, o que não serve para
nada»), que foi recuperado para a q02 e produziu **B18** («Antes a sesta do
cão… / Mostra que falou, o que é desnecessário», braço P, reprovada por plágio) e
**B23** («Antes a sombra na parede… / Mostra que já esteve, o que não serve para
nada», braço C, **não** reprovada). As duas usam o molde; uma passa o detector e
a outra não, pela quantidade de palavras que sobrou.

**A leitura, e é incómoda.** No único sítio onde a poética desta voz chegou ao
topo da escala, chegou lá por **transposição de um original que estava no
prompt** — e não por a persona ter ensinado a postura. Se uma fase futura vier a
medir uma subida em 3a, tem de distinguir as duas coisas antes de a chamar
resultado, porque este instrumento pontua as duas igual.

Isto **não** contradiz a Fase 5, que mediu que o contexto não melhora a poética
em média. As duas coisas convivem: copiar é raro — 3 amostras em 60 — e o que é
raro não move uma média. O que a Fase 5 não podia ver é isto, porque teve **zero
plágio em 40 amostras** e nenhuma amostra de Caeiro acima de zero.

### O plágio, por braço

4 das 60 amostras foram reprovadas no critério 5, contra zero nas 40 da Fase 5:
**3 em P e 1 em C**, e 12 amostras precisaram de segunda tentativa, **6 em cada
braço**. Duas das quatro são fracas: B28 e B46 copiam «e nada mais do que isso»,
que é a própria frase da pergunta q08 e por acaso também está no `poem_3507`.
Sobram **B18 e B35, as duas no braço P**, e as duas são o molde.

Três amostras não sustentam uma diferença por braço e não a reclamo. O que
sustentam é a nota de cautela acima.

---

## 5. Os dois avaliadores: concordam no veredicto e divergem na fronteira

| critério | κ | κ ponderado | concordância exacta | discordância máxima | média R1 / R2 |
|---|---|---|---|---|---|
| **3a poética** | **+0,301** | +0,400 | **81,7%** | 1 | 0,22 / 0,13 |
| 3b forma | +0,706 | +0,721 | 90,0% | 1 | 1,07 / 1,03 |
| 4 responde | +0,337 | +0,375 | 83,3% | 1 | 1,92 / 1,78 |

**O portão G5 não dispara:** os dois chegam a G4. Nenhum par discordou por mais
de um ponto, em nenhum critério, nas 60 amostras.

**O κ de 0,301 em 3a com 81,7% de concordância exacta não é contradição, é a
mesma saturação por outro lado.** Quando 50 e 52 das 60 notas são 0, a
concordância esperada por acaso já é altíssima, e o κ mede o que sobra acima
dela. O κ é o número honesto sobre quanto os dois avaliadores acrescentam um ao
outro **nos casos que distinguem**, e esse número é modesto. Declaro-o em vez de
citar os 81,7%.

Onde divergem é informativo, e é o que justifica ter havido dois:

- **R1 deu três 2; R2 não deu nenhum.** Nas três, R2 deu 1, e a volta que conta é
  defensável em todas — em B30, «Não busco na natureza uma moral oculta» é uma
  afirmação **sobre** a postura, e não a postura exercida. Eu sou mais generoso
  na fronteira 1/2, e sem R2 isso ficava invisível.
- **R2 encontrou um efeito em 3a que eu não encontrei**: a única amostra a que
  deu 0 no critério 4 foi a B29, «que responde à frase sobre gostar de alguém sem
  nunca tocar a pessoa nem a nitidez». Eu dei-lhe 1.

**A ameaça que isto não remove.** Os dois avaliadores são sessões do mesmo
modelo a ler as mesmas âncoras, e isto estava declarado no protocolo §6.3 antes
de existir pontuação: a concordância pode ser **erro correlacionado**. O κ mede
concordância, nunca correcção. R2 é mais fraco que um segundo avaliador humano e
não é equivalente a um.

E uma segunda, operacional: a restrição de leitura de R2 foi dada por
**instrução**, não imposta tecnicamente. A folha dele é uma cópia fora do
repositório, sem nome de fase e sem ligação nenhuma — `folha_r2.py` verifica que
o enquadramento não nomeia fase, desenho nem hipótese. Mas nada o impedia de ler
mais. Declara que não leu.

---

## 6. A variância dentro da célula — a primeira medição no projecto

A Fase 5 §8 declarou não medir isto: uma amostra por célula a `temperature=0,9`
é um sorteio, e qualquer leitura amostra a amostra era anecdótica. Aqui há três
repetições por célula, e o número é:

| braço | desvio médio em 3a | células com as 3 notas iguais | amplitude observada |
|---|---|---|---|
| C | 0,189 (R1) · 0,141 (R2) | 6 de 10 (R1) · 7 de 10 (R2) | 0–1 |
| P | 0,189 (R1) · 0,189 (R2) | 7 de 10 (R1) · 6 de 10 (R2) | 0–2 (R1) · 0–1 (R2) |

**Não se deve generalizar este número**, e a razão é a mesma de toda a fase: 3a
está no chão, e uma escala saturada tem pouca variância por construção. O que
isto mede é que a 0,9 de temperatura o modelo **falha de forma estável** nesta
voz — não que a geração seja reprodutível em geral. Para um critério com
resolução, a variância dentro da célula ainda está por medir.

O único sítio onde a amplitude chegou a 2 foi o braço P em R1, e são as células
da q06 e da q02 que produziram as três notas máximas — as do §4.

---

## 7. Instrumento II — a contagem lexical dos referentes nomeados

Mecânico, cego por construção, **sem portão**, e a predição de H5B era que a
contagem fosse maior em C.

| braço | ocorrências | amostras com ≥1 | média | por palavra |
|---|---|---|---|---|
| **C** | **11** | 8 de 30 | 0,37 | tristeza 3 · espelho 3 · sentido 2 · oculta 1 · oculto 1 · significado 1 |
| **P** | **7** | 6 de 30 | 0,23 | sentido 2 · tristeza 2 · oculta 1 · moral 1 · espelho 1 |

A direcção é a que H5B prevê, e **é tudo o que se pode dizer**. Quatro
ocorrências de diferença em 60 amostras não sustentam nada, e o §7.1 do protocolo
já tinha escrito porque é que este instrumento não pode decidir mesmo que a
diferença fosse grande: **P não contém estas palavras por construção**, e o
`REGRAS_SAIDA` proíbe repetir as palavras das instruções nos dois braços, logo um
simples eco de vocabulário do prompt produziria este resultado sem nenhuma
diferença de poética. O instrumento não separa eco de *priming*.

Registado como indício de mecanismo compatível, e nada mais.

---

## 8. O único intervalo que excluiu o zero, e porque não é resultado

**R2 mediu, no critério 4 (responde à pergunta), Δ=+0,233 com IC95% de [+0,067,
+0,400], 8 pares a favor de P contra 1, d=9 e p=0,039.** É o único intervalo de
toda a fase que não contém zero.

**Não é resultado, por três razões, e nenhuma delas é escolhida agora:**

1. **O critério 4 não tem portão.** O protocolo §7 pré-registou um só desfecho
   primário, 3a, e listou 4 entre os critérios sem portão. Promover 4 a resultado
   depois de ver que foi ele que se moveu é exactamente o que o pré-registo
   existe para impedir.
2. **R1 não o reproduz.** 4 pares contra 1, d=5, p=0,375, IC95% [−0,033,
   +0,233] a conter zero. A regra desta fase é a concordância dos dois
   avaliadores, e aqui não há.
3. **É a situação que a Fase 2 rejeitou**, e de que a Fase 5 se queixou no seu
   próprio §4: um limite inferior encostado a zero, com o avaliador a ser o
   mesmo que pontua tudo.

Fica declarado como **hipótese para pré-registar**, e com uma formulação
concreta, porque é plausível: uma persona que diz o que fazer pode deixar mais
atenção para a pergunta do que uma que diz o que não fazer. Quem a quiser medir
pré-registe o critério 4 como desfecho primário, com os dois avaliadores, e
meça de novo. Este número não serve, e citá-lo como achado seria o erro que a
Fase 5 cometeu com o seu portão G5.

---

## 9. O que esta fase não mediu

- **As outras três personas.** Era o que G1 autorizaria, e G1 não disparou.
- **«As interdições em geral».** Ver o §3.1 do protocolo: três blocos de
  interdições ficaram no `system` nos dois braços, e um deles — o
  `REGRAS_NAO_COPIAR` — é carga útil medida (82% → 0% de versos copiados na Fase
  1). Esta fase testou a forma interdictiva **da cláusula poética**, e nada mais.
- **Negação sem nomear.** O §2.1 declarou a fusão antes de medir: a variante
  afirmativa inverte a polaridade **e** deixa de nomear os referentes, e este
  desenho não as separa. Pede um terceiro braço.
- **A sombra lexical** do §11 do relatório da Fase 5, cuja lista teria de vir dos
  113 poemas reais de Caeiro. A contagem do §7 vem do tratamento e não é essa.
- **O modelo.** Continua a ser o suspeito que sobra, e a seguir à ressalva do §3
  é agora o mais forte.
- As vozes inglesas, as três vozes com 3a ≥ 1, a latência, e o `num_predict` do
  Campos.

---

## 10. Checklist do protocolo

```
[x] A1  protocolo commitado antes de qualquer amostra existir (6cab876), e a
        estatística antes de qualquer pontuação (22fc07c)
[x] A2  verificar_personas.py: 0 partículas negativas em P contra 6 em C,
        razão de comprimento 1,050, forma e as três regras byte a byte iguais
[x] A3  60 amostras (10 × 2 × 3), persistidas por linha, tentativas registadas;
        asserção de recuperação igual entre braços verificada em todas
[x] A4  embaralhamento sem pares da mesma pergunta adjacentes, chave fechada
[x] B1  R1 pontuou 3a, 3b e 4 nas 60, às cegas, com razão por amostra
[x] B2  R2 pontuou as mesmas 60, cego ao desenho, em folha sem nome de fase
[x] B3  as duas pontuações commitadas antes de a chave abrir (072795d)
[x] C1  sinais sobre os discordantes, bootstrap B=10000 semente 3, medianas
[x] C2  portões aplicados duas vezes: **G4** nos dois. G0 não dispara, G5 não
        dispara. G3 disparou em R2 e é discutido no §2
[x] C3  κ simples e ponderado, variância dentro da célula, estratos
[x] D1  instrumento II: 11 ocorrências em C contra 7 em P
[x] E1  relatório, com as ameaças do §6.3 repetidas e a delimitação do §3.1
```

Fora do protocolo, e registado por ter aparecido pelo caminho: o confundidor do
§4, que nenhum dos portões previa.

---

## 11. O que isto autoriza, e o que não

**Não autoriza mexer em `src/voices.py`.** G1 não disparou. A variante afirmativa
fica em [`fase-5b/personas_5b.py`](fase-5b/personas_5b.py), medida e não
adoptada.

**Não autoriza dizer que H5B é falsa.** G4 não é G2. Com 6 e 7 pares
discordantes, a direcção observada é a que H5B prevê nos dois avaliadores e no
instrumento II, e nenhuma das três diferenças chega perto de significância. Quem
quiser afirmar que as interdições não são a causa tem de medir com um
instrumento que tenha resolução no chão.

**Não autoriza o número do critério 4.** Ver o §8.

**Autoriza fechar uma ressalva da Fase 5**, e é a parte que se pode levar daqui:
o chão do Caeiro não era artefacto de n=5 nem de avaliador único. Reproduz-se a
n=10, a 60 amostras, com três repetições por célula e com um segundo avaliador
que não sabia o que estava a medir. A inferência da Fase 5 sobre **onde** está o
défice fica mais forte; a inferência sobre **a causa** continua sem medição.

**E autoriza uma correcção ao meu próprio pré-registo**, que é o que esta fase
deixa de mais útil para a seguinte. Escrevi um protocolo cuidadoso — âncoras
herdadas de outra fase, dois avaliadores, piso de potência, portão de
especificidade — e nenhuma dessas defesas serviu para nada, porque falhei em
verificar antes de medir a única coisa que decidia se a medição era possível: **a
Fase 5 já tinha publicado que o Caeiro dá 0,0 de mediana em 3a, e eu desenhei
sobre esse critério uma ablação emparelhada**. Um piloto de seis amostras teria
mostrado a saturação em vinte minutos, e teria custado 1/10 da corrida.

A lição é generalizável e vai para o `CONTROLO.md`: **antes de pré-registar uma
ablação emparelhada, verificar que o desfecho tem variância na condição de
controlo.** Um desfecho saturado não produz pares discordantes, e um protocolo
sem pares discordantes é inconclusivo por construção, por muito bem escrito que
esteja.

### A entrada da fase seguinte

Duas, e a primeira é pré-requisito da segunda:

1. **Um desfecho com resolução no chão do Caeiro.** A âncora de 0 funde «uma
   volta a mais que 1» com «filosofa de ponta a ponta». Uma contagem de voltas
   interpretativas por poema, ou a fracção de versos que atribuem significado,
   dá uma escala contínua onde esta dá um ponto. Pode ser validada contra os 113
   poemas reais de Caeiro, que devem pontuar no extremo oposto — e essa
   validação é exactamente o que o juiz de identificação da Fase 5 não tinha.
2. **Então, e só então, a repetição desta fase.** O desenho dos dois braços, a
   regra de reescrita e o harness ficam escritos e verificados; o que falta é o
   instrumento. Com um desfecho contínuo, 30 pares chegam para uma estimativa com
   intervalo, e a hipótese das interdições — que continua a ser a mais barata de
   todas as que sobram — fica finalmente testável.

E uma cautela que a fase seguinte herda do §4: medir o plágio e a sobreposição
com os poemas do prompt **por amostra**, e não só como critério de aprovação,
porque a única vez que a poética chegou ao topo foi por transposição de um
original que estava no prompt.
