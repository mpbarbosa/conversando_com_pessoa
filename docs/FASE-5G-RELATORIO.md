# Fase 5G — relatório: a medição correu, e as interdições não são a causa

Protocolo em [`FASE-5G.md`](FASE-5G.md), pré-registado em `2bebf5a` **antes de
existir uma amostra**. As duas pontuações foram commitadas em `12b1dc6` **antes
de a chave ser aberta**.

---

## 1. O que se decidiu

**O portão G2 disparou: H5B cai.** A forma interdictiva da cláusula poética do
Caeiro **não** é a causa do défice.

E disparou nas três leituras — a estimativa conjunta, R1 e R2, cada uma por si.
**G5 não dispara**, G4 não dispara, G3 não dispara.

| leitura | mediana C | mediana P | Δ (P−C) | IC95% | sinais P/C/= | d | p | portão |
|---|---|---|---|---|---|---|---|---|
| **conjunta** | 0,75 | 0,50 | **−0,050** | **[−0,300; +0,183]** | **9 / 8 / 13** | **17** | 1,000 | **G2** |
| R1 | 0,00 | 0,00 | −0,100 | [−0,433; +0,233] | 4 / 8 / 18 | 12 | 0,388 | G2 |
| R2 | 1,00 | 1,00 | +0,000 | [−0,300; +0,300] | 7 / 6 / 17 | 13 | 1,000 | G2 |

O portão **G0** disparou em R2 — mediana 1,0 no braço de controlo — e fica
registado como o protocolo manda: o chão de 0,0 que a Fase 5B mediu era do
**instrumento**, não da geração.

---

## 2. O que esta fase prova antes de provar qualquer coisa sobre a hipótese

**A medição correu.** É o resultado que seis fases de instrumentação existiram
para produzir, e vale escrevê-lo em primeiro lugar:

| | Fase 5B (âncora antiga) | Fase 5G (âncora 3a′) |
|---|---|---|
| pares discordantes | **7** (R1) · 6 (R2) | **17** (conjunta) · 12 · 13 |
| pares empatados em 0–0 | **22 de 30** | — |
| empates totais | 23 · 24 | **13** · 18 · 17 |
| portão | **G4** — inconclusivo por potência | **G2** — veredicto |

A 5B não pôde testar H5B. A 5G testou-a. A diferença é inteiramente a régua: as
mesmas 10 perguntas, os mesmos dois braços, o mesmo harness com uma linha
mudada, o mesmo n.

---

## 3. O tamanho do nulo, e o que ele exclui

O protocolo §3.2 escreveu, **antes de medir**, que 30 pares detectam Δ ≥ 0,50 a
~80% e não detectam Δ ≤ 0,375. O relatório tinha de repetir isto qualquer que
fosse o resultado, e repete.

**Mas o intervalo medido é mais estreito do que o cálculo a priori prometia:**
IC95% de **[−0,300; +0,183]** na escala de 0 a 2. A leitura correcta é o
intervalo, não o cálculo:

> Os dados são incompatíveis com a variante afirmativa ajudar mais do que
> **0,18 pontos**, e com ela prejudicar mais do que 0,30. O efeito das
> interdições, se existir, é **menor que um décimo da escala**.

Para dar escala: a distância entre o Caeiro **real** e o Caeiro **gerado**,
medida na 5F com a mesma âncora, é de **0,93 pontos** (1,60 contra 0,67).
O efeito máximo compatível com estes dados é um quinto disso.

**H5B cai, portanto, com uma afirmação positiva por baixo:** qualquer que seja a
causa do défice do Caeiro, a forma interdictiva da cláusula poética explica no
máximo uma pequena fracção dela.

---

## 4. A fragilidade principal: os avaliadores concordaram pouco

É a pior concordância de toda a sequência e vai antes de qualquer leitura fina:

| | 3a′ |
|---|---|
| κ ponderado linear | **0,334** |
| concordância exacta | **48,3%** |
| discordância máxima | 2 |
| médias | R1 **0,48** · R2 **1,07** |

**R2 pontuou mais do dobro de R1 em média**, e é a segunda fase seguida em que
isto acontece: na 5F foram 30 notas máximas contra as minhas 16, aqui 25 contra
7. Duas fases independentes, amostras diferentes, mesmo padrão — **não é ruído, é
uma diferença sistemática de leitura da fronteira 1/2.**

O protocolo não pôs um piso de concordância (pôs G5, sobre veredictos), e por
isso isto não é uma falha de portão. É uma fragilidade declarada, e tem duas
consequências:

1. **Não invalida o veredicto.** As três leituras chegam a G2 por si, e com
   intervalos que se sobrepõem. Um desacordo de nível que não muda a *diferença
   entre braços* é ruído aditivo que o emparelhamento absorve — e é exactamente
   para isto que uma ablação emparelhada serve.
2. **Limita o uso futuro da âncora** para efeitos pequenos. Com κ de 0,334, esta
   âncora não serve para medir diferenças de um quarto de ponto, e o passo 12 da
   lista do `CONTROLO.md` — apertá-la na fronteira 1/2 — passa de desejável a
   necessário.

**R2 nomeou a fronteira de dentro da cegueira**, e é a melhor pista para a
apertar: «quando a personificação era incidental e o fecho era deflacionário, dei
1 em vez de 0 (G24, G34, G56) — deixo isto explícito». Eu dei 0 às três. É a
regra 5 a tocar a coluna do 1, e a âncora não diz qual ganha.

---

## 5. Uma observação pós-hoc, declarada como tal

O nulo não é plano: é uma **quase-anulação**. Somando os Δ por pergunta:

| | q01 | q02 | q03 | q04 | q05 | q06 | q07 | **q08** | q09 | q10 |
|---|---|---|---|---|---|---|---|---|---|---|
| Σ Δ | +0,5 | +0,5 | +1,0 | −0,5 | 0 | +1,0 | +0,5 | **−3,5** | −1,0 | 0 |

**A q08 sozinha carrega o sinal negativo**, com os três pares contra P. Sem ela,
as outras nove somam +3,00, isto é Δ = **+0,11** — e continua dentro do
intervalo, e continua muito abaixo do detectável.

**Isto não é um resultado e não se lê como um.** É uma análise de subgrupo feita
depois de ver os dados, sobre n=3 pares. O que ela diz de útil é o contrário de
um achado: **que o ponto estimado de −0,05 é ruído**, porque o sinal inverte ao
remover uma pergunta de dez. O que não muda com a remoção é a magnitude — nenhum
subconjunto produz Δ próximo de 0,50.

A q08 é «um rebanho a passar numa encosta, e nada mais do que isso», e é a
pergunta cujas amostras começam a repetir a própria frase da pergunta. Fica
registado para quem desenhar a próxima, sem interpretação.

---

## 6. O que mais apareceu

**Zero truncaturas em 60**, contra 1 na 5B e 3 em 40 na Fase 5 — e era esperado,
porque o Caeiro pede dez a vinte versos curtos. **Duas amostras plagiaram**, uma
de cada braço, as duas na q08, contra 4 na 5B. 18 precisaram de segunda
tentativa, 10 em P e 8 em C.

**Um numeral romano solto** («XLIV») apareceu no meio da amostra G23 — vocabulário
de estrutura do corpus a vazar para a geração. Declarei-o no meu ficheiro de
pontuação antes da chave; não afecta 3a′ e pesou em 3b. É novo neste projecto e
não tem explicação medida: o `poem_id` de Caeiro traz numerais romanos no texto,
e algum deles estava no contexto.

**3b não se moveu** em nenhuma leitura (Δ = +0,033 nas três), que é o
comportamento esperado de um critério cuja âncora é byte a byte igual nos dois
braços. G3 não disparou em nenhuma, logo o efeito nulo em 3a′ não é perturbação
geral do prompt.

---

## 7. Ameaças

- **Eu escrevi a âncora 3a′ e sou um dos avaliadores**, e aqui não havia retenção
  possível (§6.1 do protocolo). O que limita o dano: R2 aplicou-a sem saber que
  era nova nem que havia braços, e **chegou ao mesmo portão**. Se eu a estivesse
  a aplicar enviesado a favor de P, R2 não o reproduziria — e o Δ de R2 é
  exactamente **0,000**.
- **A fusão de polaridade e nomeação** (§2 do protocolo, herdada da 5B §2.1)
  continua sem ser separável: a variante afirmativa inverte a polaridade **e**
  deixa de nomear os referentes. H5B cai como foi formulada; «a negação que não
  nomeia» nunca foi testada e precisa de um terceiro braço.
- **Os dois avaliadores são sessões do mesmo modelo.** Ressalva de sempre, e
  nesta fase é a mais relevante de todas, porque o κ é baixo: a concordância que
  há pode ser erro correlacionado, e o desacordo que há é real.
- **Uma só voz, um só modelo, um só conjunto de 10 perguntas.** H5B cai para o
  Caeiro, no qwen2.5:7b, nestas perguntas.

---

## 8. Checklist

```
[x] A1  protocolo commitado antes de existir amostra (2bebf5a)
[x] A2  verificar_personas.py passa: 0 partículas negativas em P contra 6, razão 1,050
[x] A3  60 amostras com semente base 20261005, 59,5 min, persistidas por linha
[x] A4  embaralhamento sem pares adjacentes; chave fechada; ids corrigidos
        (B→G) e folha reemitida com a âncora certa, antes de eu ler uma amostra
[x] B1  R1 pontuou 3a' e 3b às cegas, com razão por amostra
[x] B2  R2 pontuou, cego ao desenho, aos braços e à hipótese
[x] B3  as duas pontuações commitadas antes de a chave abrir (12b1dc6)
[x] C1  sinais sobre os discordantes e bootstrap, na conjunta
[x] C2  portões aplicados: **G2** nas três leituras. G0 em R2, G3 e G4 e G5 não
[x] D1  a potência do §3.2 repetida, e o IC medido declarado como mais estreito
```

---

## 9. O que isto autoriza, e o que não

**Não autoriza tocar em `src/voices.py`.** G1 não disparou. A variante afirmativa
fica em [`fase-5b/personas_5b.py`](fase-5b/personas_5b.py), medida duas vezes e
não adoptada — e agora com um intervalo que diz quão pouco ela faz.

**Autoriza fechar H5B**, que esteve aberta desde o relatório da Fase 5. A forma
interdictiva da cláusula poética não é a causa; o efeito dela é menor que um
décimo da escala, contra uma distância real-para-gerado de 0,93 pontos.

**Autoriza fechar a sequência de instrumentação.** A âncora 3a′ foi construída
para esta medição e funcionou: d passou de 7 para 17, e o veredicto é o mesmo nas
três leituras.

**Não autoriza ler o §5** como se dissesse algo sobre a q08.

**E aponta o suspeito que sobra.** Eliminados o contexto (Fase 5, G2), a forma
interdictiva da persona (esta fase, G2) e a hipótese de que o chão fosse real
(Fase 5E), o que resta do défice de 0,93 pontos entre o Caeiro real e o gerado
é o **conteúdo** da persona ou o **modelo** — e o modelo é agora o mais forte,
por eliminação, pela primeira vez com as alternativas medidas em vez de
supostas.

### O que fica na mesa

1. **Trocar o modelo e remedir com esta âncora.** É o primeiro teste de modelo
   desta sequência que tem um instrumento validado à partida. O `CONTROLO.md`
   tem desde a Fase 0 a nota de que o llama3.1:8b e o qwen2.5:7b se comportam de
   forma diferente na voz, nunca medida com rubrica.
2. **Apertar a âncora na fronteira 1/2** — passo 12, agora necessário e não
   desejável, com a fronteira nomeada por R2 no §4.
3. **Replicar a separação real/gerado com portão** — passo 11, ainda em aberto.
4. O terceiro braço de «negação que não nomeia», se alguém quiser desfazer a
   fusão do §2.
