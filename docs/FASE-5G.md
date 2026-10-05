# Fase 5G — a Fase 5B remedida, com a régua endireitada

Protocolo, **pré-registado antes de existir uma amostra**. É o passo 10 da lista
«[depois da Fase 5](CONTROLO.md)», e fecha a sequência que a
[Fase 5B](FASE-5B-RELATORIO.md) abriu e não pôde resolver.

**Objectivo:** decidir, por medição, a hipótese H5B — que a poética do Caeiro
falha porque a persona a enuncia como **interdições** — com um desfecho que tem
folga para a medir.

---

## 1. Porque é que isto se repete, e o que mudou

A [Fase 5B](FASE-5B-RELATORIO.md) correu exactamente este desenho: dois braços,
30 pares, dois avaliadores cegos. Caiu em **G4 — inconclusivo por potência**, e
não por falta de amostras: **22 dos 30 pares empataram em 0–0** porque o
critério 3a tomava 3 valores em 60 amostras, 50 delas no mesmo.

Quatro fases foram gastas a descobrir porquê e a corrigi-lo:

| | |
|---|---|
| [5C](FASE-5C-RELATORIO.md) | tentou um desfecho lexical e rejeitou-o: AUC de 0,869 in-sample caía para **0,544** retida |
| [5D](FASE-5D-RELATORIO.md) | construiu um com resolução (38 valores contra 3) e apontou a âncora como suspeita |
| [5E](FASE-5E-RELATORIO.md) | mediu a âncora: dava a nota máxima a **3 de 20** poemas **autênticos** de Caeiro |
| [5F](FASE-5F-RELATORIO.md) | recalibrou-a — **16 de 24** retidos com nota máxima, e a discriminação subiu de 0,811 para **0,913** |

**O que mudou é só a régua.** A hipótese, os dois braços, a regra de reescrita
afirmativa, o harness e as 10 perguntas são os da 5B, byte a byte onde possível.
O desfecho passa a ser a âncora **3a′** da [Fase 5F](FASE-5F.md) §2.

E a folga que faltava existe: na 5F, a âncora nova deu mediana **2,0** ao Caeiro
real e **0,75** ao gerado. Há espaço para uma intervenção subir ou descer.

---

## 2. A hipótese, inalterada

**H5B:** a poética do Caeiro falha porque a persona a enuncia como interdições.

O mecanismo é o da 5B §2 e não se toca: uma instrução negativa **tem de nomear**
o conteúdo proibido — «significado oculto», «metafísica», «espelho de
sentimentos» — e nomeá-lo torna-o disponível.

A fusão declarada na 5B §2.1 mantém-se e continua a não ser separável por este
desenho: a variante afirmativa inverte a polaridade **e** deixa de nomear os
referentes. Separá-las pedia um terceiro braço.

---

## 3. Desenho: o da 5B, com amostras novas

| | braço | `poetica` |
|---|---|---|
| **C** | controlo | a de serviço, byte a byte (`src/voices.py`) |
| **P** | positiva | a variante afirmativa de [`fase-5b/personas_5b.py`](fase-5b/personas_5b.py), **inalterada** |

Tudo o resto é a 5B §3: as duas condições correm o pipeline completo com
contexto, `forma` e as três regras de língua, cópia e saída ficam byte a byte
iguais, e a persona entra por *monkeypatch* de `src.pipeline.persona`.
`src/voices.py` **não se toca**.

**10 perguntas de Caeiro × 2 braços × 3 repetições = 60 amostras, 30 pares.**

### 3.1 As amostras são novas, e porquê

A semente base muda de `20261003` para **`20261005`**. As 60 amostras da 5B
existem e estão commitadas, e seria mais barato reutilizá-las — **e seria
inválido**: eu li as 60 ao pontuá-las na 5B, e a âncora 3a′ foi escrita depois.
Pontuá-las agora com um desfecho escolhido após eu as conhecer é a pesca que a
5C e a 5E recusaram, cada uma contra o seu próprio interesse.

Com sementes novas, as amostras são outras e eu nunca as vi.

### 3.2 Potência, calculada antes de medir

A 5F mediu o desvio-padrão do grupo gerado: **0,657** na escala de 0 a 2
(agrupado, sem separar braços — a 5F proibia essa divisão e ela não foi feita).

Com 30 pares e correlação emparelhada plausível de ρ≈0,3:

| Δ a detectar | pares para 80% |
|---|---|
| 0,75 | 9 |
| **0,50** | **19** |
| 0,375 | 34 |
| 0,25 | 76 |

**30 pares detectam Δ ≥ 0,50 com ~80% de potência, e não detectam Δ ≤ 0,375.**
Fica escrito antes de medir, e o relatório tem de o repetir **qualquer que seja o
resultado**: um nulo nesta fase é um nulo *para efeitos de meio ponto*, não para
efeitos de qualquer efeito. É a leitura que a 5B não pôde dar porque lá a
saturação impedia qualquer cálculo.

---

## 4. A rubrica

| # | critério | como |
|---|---|---|
| **3a′** | **poética da voz** | **à mão, às cegas, dois avaliadores** — âncora da [5F](FASE-5F.md) §2 com as seis regras. É o desfecho primário |
| 3b | forma da voz | à mão, às cegas — **controlo interno**, ver G3 |
| 1 · 2 · 5 | verso · PT-PT · plágio | automáticos, como na 5B |

A âncora de **3b** é a da [Fase 5](FASE-5.md) §5.2, **inalterada**: a 5F
recalibrou só a poética, e mexer na forma aqui misturaria duas mudanças.

O critério 4 (responde à pergunta) **sai**. Na 5B não teve portão, e foi nele
que apareceu o único intervalo a excluir zero — um achado que a 5B declarou não
ser resultado e remeteu para pré-registo próprio. Medi-lo outra vez sem portão
convidaria à mesma tentação; medi-lo com portão seria duas hipóteses numa fase.

---

## 5. Os portões

Primário na **estimativa conjunta** dos dois avaliadores por amostra — a
correcção da 5D, que a 5F confirmou valer a pena: lá, dois avaliadores com
discordância de 2 pontos em 4 de 64 itens chegaram ao mesmo veredicto porque os
portões corriam na conjunta.

Estatística: **teste de sinais exacto sobre os pares discordantes** e **IC95% por
bootstrap emparelhado**, B=10000, semente 3. A mesma da 5B, e com o mesmo piso.

| | portão | condição (conjunta, 30 pares) | o que autoriza |
|---|---|---|---|
| **G0** | **o chão não se reproduz** | mediana de 3a′ em **C** ≥ 1 | registar que o chão da 5B era do instrumento e não da geração. Não decide, qualifica |
| **G1** | **H5B confirmada** | binomial exacto bilateral p ≤ 0,05 a favor de **P** nos pares discordantes, **e** IC95% do Δ a excluir 0, **e** G3 a não disparar | autoriza substituir a `poetica` do Caeiro em `src/voices.py` pela variante afirmativa, **e** reescrever as outras três personas pela mesma regra |
| **G2** | **H5B rejeitada** | p > 0,05 **ou** IC95% a conter 0, com **d ≥ 8** pares discordantes | H5B cai **para efeitos de Δ ≥ 0,50** (§3.2). A forma interdictiva da cláusula poética não é a causa, e o que sobra é o conteúdo da persona ou o modelo |
| **G3** | **especificidade** | \|Δ3b\| ≥ \|Δ3a′\| e no mesmo sentido | a `forma` é byte a byte igual nos dois braços; mover 3b tanto como 3a′ é perturbação geral do prompt. **G1 não pode ser lido como confirmação** se disparar |
| **G4** | **inconclusivo por potência** | **d < 8** pares discordantes | nada se decide. Com a resolução da âncora nova isto é agora improvável, e se acontecer é um resultado sobre o desfecho e não sobre H5B |
| **G5** | **os avaliadores discordam** | R1 e R2, corridos em separado, chegam a portões diferentes entre G1, G2 e G4 | **publica-se a discordância e nada se autoriza.** A conjunta decide, mas uma divergência de veredicto por avaliador é informação que não se esconde |

---

## 6. Cegueira

Idêntica à da 5B §6.2, com as correcções que as fases seguintes ensinaram:

1. As 60 amostras vão para `01-amostras.md` embaralhadas por semente fixa, com
   identificadores opacos `G01`–`G60`, e duas da mesma pergunta nunca adjacentes.
2. A chave fecha em `01-chave.json` e abre só depois de as duas pontuações
   estarem commitadas.
3. R2 recebe uma cópia **fora do repositório**, sem nome de fase e sem ligação
   nenhuma, verificada por **fronteira de palavra** — a verificação por substring
   reprovou duas vezes, na 5B por «braço» dentro de «abraço» e na 5D por «real»
   dentro de «realidade».
4. **Os numerais romanos não se aplicam**: são 60 amostras geradas e nenhuma os
   tem. A fuga de cegueira que a 5E fechou não existe aqui.

### 6.1 Ameaça nova, que as fases anteriores não tinham

**Eu escrevi a âncora 3a′** (Fase 5F) e sou um dos avaliadores desta fase. Na
5F a retenção defendia-me; aqui não há retenção possível, porque o que está a
ser medido são amostras novas e não a âncora.

O que limita o dano: a âncora está **escrita e commitada** com seis regras para
os casos difíceis, e R2 aplica-a sem saber que é nova, sem saber que houve uma
antiga, sem saber que há braços e sem saber a hipótese. Se eu a aplicar de forma
enviesada a favor de P, R2 não o reproduz.

---

## 7. O que esta fase não mede

- **Negação sem nomear.** A fusão do §2 pede um terceiro braço.
- **«As interdições em geral.»** Três blocos de interdições ficam no `system` nos
  dois braços, e um deles — `REGRAS_NAO_COPIAR` — é carga útil medida (82% → 0%
  de versos copiados na Fase 1).
- **As outras três personas.** É o que G1 autorizaria.
- **O critério 4.** Ver §4.
- **Efeitos abaixo de Δ=0,375.** Ver §3.2, e o relatório repete-o.

---

## 8. Checklist

```
[ ] A1  protocolo commitado antes de existir qualquer amostra
[ ] A2  verificar_personas.py volta a passar (a variante é a da 5B, inalterada)
[ ] A3  60 amostras com semente base 20261005, persistidas por linha
[ ] A4  embaralhamento sem pares adjacentes; chave fechada
[ ] B1  R1 pontua 3a' e 3b às cegas, com razão por amostra
[ ] B2  R2 pontua, cego ao desenho, aos braços e à hipótese
[ ] B3  as duas pontuações commitadas antes de a chave abrir
[ ] C1  sinais sobre os discordantes e bootstrap, na conjunta
[ ] C2  portões aplicados; G3 e G5 verificados; por avaliador em separado
[ ] D1  relatório, com a potência do §3.2 repetida qualquer que seja o resultado
```
