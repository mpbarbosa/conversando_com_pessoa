# Análise de sentimento neste projecto: não houve, e não serviria

Documento temático, escrito em 2026-10-12, quinto da série. **Não é uma fase.**

**Não há análise de sentimento, em sítio nenhum.** Verificado antes de escrever:

```
grep -rniE "sentiment|polarid|vader|textblob|afinn|valência|emolex|liwc" src/ tests/
```

não dá um único uso instrumental, e nenhuma das sete dependências de produção faz
análise afectiva.

**E ao contrário da [lematização](LEMATIZACAO.md), que foi recusada por decisão
explícita, esta nunca foi sequer considerada** — nunca houve uma pergunta neste
projecto que a análise de sentimento respondesse. O §4 argumenta que, se tivesse
havido, ela daria a resposta errada.

Mas há **três** coisas que se parecem com ela, e a primeira usa a palavra
«polaridade» a significar outra coisa.

---

## 1. «Polaridade» aqui é gramatical, e é um falso amigo

A [5B](../FASE-5B.md) tem «polaridade» por toda a parte. O que ela testou foi se
formular a persona **em negativo** causa o próprio defeito que proíbe, por nomear
o referente proibido — o «não penses num elefante».

| | |
|---|---|
| persona de produção | «Recusas a metafísica, a simbologia e a moral» |
| variante afirmativa | «Ficas na superfície das coisas, que é onde elas estão inteiras» |

E o protocolo declarou a confusão que isso contém, **antes** de medir:

> «A variante afirmativa faz **duas** coisas ao mesmo tempo: inverte a polaridade
> **e** deixa de nomear os referentes proibidos. As duas estão fundidas, e este
> desenho **não as separa**. […] Fica declarado aqui para que o relatório não
> possa apresentar «a negação estorva» quando o que foi medido é «a negação, **que
> nomeia**, estorva».»

**É polaridade de instrução, não valência de sentimento.** E a hipótese ficou sem
teste: o desfecho **saturou no chão** — 22 dos 30 pares empataram em 0–0 — e a
5B fechou inconclusiva por potência, nos dois avaliadores.

---

## 2. O que mais se aproxima na mecânica é o FAS da 5C

A [5C](../FASE-5C-RELATORIO.md) construiu um instrumento com **a mesma forma** de
um léxico de sentimento: 40 palavras derivadas do corpus por *log-odds*, e a
pontuação é a fracção de versos que contêm ao menos uma.

```
FAS(texto) = versos não vazios com ≥ 1 termo da lista ÷ versos não vazios
```

**O construto, porém, era «atribuição de sentido»** — a metafísica que Caeiro
recusa. Não valência.

### 2.1 E a composição da lista explica a confusão — medição nova

Classifiquei as 40 palavras ao escrever este documento. Nunca tinha sido feito:

| classe | n | palavras |
|---|---|---|
| **vocabulário afectivo** | **11** | `amor`, `horror`, `morte`, `alegria`, `tristeza`, `feliz`, `coração`, `abismo`, `mistério`, `calma`, `frio` |
| **2.ª pessoa** | **4** | `teu`, `tua`, `teus`, `tens` |
| funcionais / gramaticais | 13 | `sob`, `entre`, `pelo`, `pois`, `numa`, `qual`, `talvez`, `além`, `inda`, `outro`, `vai`, `somos`, `fui` |
| restantes | 12 | `sonho`, `sonhar`, `sentido`, `razão`, `futuro`, `dia`, `rua`, `mão`, `fim`, `alto`, `poder`, `passar` |

**Onze das 40 são afecto puro.** É por isso que o FAS correlacionaria com um
analisador de sentimento sem nunca medir sentimento — e é por isso que confundir
os dois é fácil.

**E quatro são o paradigma da segunda pessoa, que é o achado incómodo.** Caeiro
não se dirige a um «tu»; Reis dirige-se a Lídia constantemente. Logo quatro dos
quarenta discriminadores são **interlocutor**, não atribuição de sentido.

Era exactamente a ameaça que o protocolo da 5C declarou:

> «O contraste é «não-Caeiro PT», que mistura três poéticas. Parte do sinal pode
> ser **tópico** (Campos e a cidade, Reis e Lídia) e não atribuição de sentido.»

**A ameaça estava escrita e nunca foi isolada.** Esta contagem não a isola
também — mas nomeia-a: são `teu`, `tua`, `teus` e `tens`, e estão lá.

O instrumento **falhou na validação retida**: AUC de **0,869 em amostra** para
**0,544** em dados retidos. A [5C](../FASE-5C-RELATORIO.md) §5 atribui a
instabilidade a 39 poemas serem poucos e à falta de lematização; **esta
composição é uma terceira razão plausível**, e com o mesmo estatuto das outras
duas: plausível e não isolada.

---

## 3. Há um construto afectivo medido — e é o inverso do sentimento

O critério **D** da [5D](../FASE-5D.md) e a âncora **3a′** da
[5F](../FASE-5F.md) medem **personificação e falácia patética**:

> «atribui a uma coisa acto mental, vontade ou sentimento, ou usa a natureza como
> **espelho de sentimento**: «a montanha sorri», «o riacho esquece a fonte»,
> «praia desolada»»

Isto não pergunta *que* sentimento o texto tem. Pergunta se o texto **projecta
sentimento nas coisas** — e para Caeiro isso é um defeito, proibido na persona:
«não personificas a natureza nem a usas como espelho de sentimentos».

> **Um analisador de sentimento diria «negativo» a «praia desolada». O
> instrumento deste projecto diz «Caeiro não escreveria isto».** São perguntas
> ortogonais, e só uma delas interessava.

---

## 4. E se tivesse havido, daria a resposta errada

Este é o argumento que fecha, e não é de preferência: é de construto. A âncora
3a′ tem **seis regras de fronteira**, decididas antes de pontuar, e **duas delas
são precisamente aquilo em que um léxico afectivo falha**:

| regra | o que diz |
|---|---|
| **3** | «**Atribuição negada não conta como atribuição.** «Não lhes atribuo significado oculto», «não busco na natureza uma moral» não abrem porta nenhuma» |
| **4** | «**Atribuição posta e depois retirada conta como fechada.** «Se às vezes digo que as flores sorriem… não é porque eu julgue que há sorrisos nas flores» é retracção, e o poema é candidato a **2**» |

**Um instrumento de saco de palavras não distingue «atribuo-lhes significado
oculto» de «não lhes atribuo significado oculto».** O vocabulário é o mesmo; a
pontuação é **0** num caso e **2** no outro. E a regra 4 é pior ainda: o poema
*contém* a personificação, em extensão, e **conta a favor** por a retirar
depois.

Acrescente-se a regra 2 — «a tautologia deflacionária é a assinatura, não um
defeito»: «as coisas são só o que são» é a marca da voz, e tem valência **zero**
em qualquer léxico.

> **O construto central deste projecto é sensível a negação e a retracção.** É
> exactamente a classe de fenómeno em que a pontuação lexical de afecto é cega —
> e a âncora precisou de seis regras escritas à mão, mais três fases a falhar
> (5B, 5C, 5D), para a apanhar.

---

## 5. Onde o afecto aparece, e é como dado e não como medida

| | onde | o que é |
|---|---|---|
| **na persona** | `voices.py` | «Alternas entre euforia e náusea de existir» é instrução de **registo** ao Campos, não medição |
| **numa consulta do gabarito** | `avaliacao.py` | «ofereço-lhe o meu afecto e ela nem repara» é a pergunta que mostrou que o gabarito único era inválido — o encoder devolveu «Entreguei-te o coração, / E que tratos tu lhe deste!», casamento igualmente bom contado como erro. **Daí a relevância graduada e o nDCG@5** |
| **no corpus** | — | `coração` aparece 148 vezes fora de Caeiro e **zero** nele. É o `log_odds` mais alto da lista FAS, e é dado de entrada |

Nos três casos o afecto é **material**, não instrumento.

---

## 6. Resumo

1. **Não houve análise de sentimento**, e ao contrário da lematização nunca foi
   sequer considerada — não havia pergunta que ela respondesse.
2. **«Polaridade» na 5B é gramatical**, do tipo «não penses num elefante», e a
   hipótese ficou **sem teste** por saturação no chão (22 de 30 pares a 0–0).
3. **O FAS da 5C tem a mecânica de um léxico de sentimento** e outro construto —
   e **11 das suas 40 palavras são afecto puro**, o que explica a confusão.
4. **Quatro são o paradigma da 2.ª pessoa** (`teu`, `tua`, `teus`, `tens`), o que
   nomeia a ameaça de tópico que a 5C declarou e nunca isolou. Terceira razão
   plausível para o colapso de 0,869 para 0,544, com o mesmo estatuto das outras:
   não isolada.
5. **O construto afectivo que existe é o inverso do sentimento**: mede se o texto
   **projecta** sentimento nas coisas, não que sentimento tem.
6. **E um léxico de afecto daria a resposta errada**, porque as regras 3 e 4 da
   âncora dependem de **negação** e **retracção**, a que um saco de palavras é
   cego.

**Ficheiros:** [`FASE-5B.md`](../FASE-5B.md) §2.1 ·
[`FASE-5C-RELATORIO.md`](../FASE-5C-RELATORIO.md) §5 ·
[`FASE-5F.md`](../FASE-5F.md) §2.1 ·
[`src/avaliacao.py`](../../src/avaliacao.py) ·
[`docs/fase-5c/01-validacao.json`](../fase-5c/) (a lista das 40).
