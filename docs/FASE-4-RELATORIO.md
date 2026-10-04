# Relatório da Fase 4 — roteador de voz, e o enriquecimento que não se faz

Executada em 2026-10-01. Protocolo em [`FASE-4.md`](FASE-4.md).

> ### ⚠️ Correcção de 2026-10-03: os centróides estavam contaminados
>
> Todos os números de embedding deste relatório foram medidos com centróides
> construídos sobre `Chunk.indexed_text`, que leva **«Autor — Título» à cabeça**,
> enquanto as consultas eram verso puro. Corrigido:
>
> | | publicado | corrigido |
> |---|---|---|
> | centróide, 40 perguntas | 45% | **68%** |
> | centróide, 80 poemas reais | 42% | **64%** |
> | probe, 80 poemas reais | 46% | **61%** |
>
> **Três consequências, e duas atingem conclusões deste relatório:**
>
> 1. A afirmação «**o espaço do e5 não separa estas vozes**» (§1.2) está
>    **refutada**. Separa-as a 68%.
> 2. A vantagem do roteador LLM cai de **+27 para +4 pontos**, que a n=40 não se
>    distinguem de zero. **O LLM não está estabelecido como melhor** que um
>    centróide corrigido — ver a ressalva no §1.1 e o que falta medir.
> 3. O «**colapso no Caeiro**» (§1.2) era artefacto: 19 erros a apontar-lhe
>    passam a 1, e o atractor que resta é o ortónimo, a classe maior.
>
> O que **sobrevive**: a refutação da hipótese do registo (poemas roteiam tão
> bem como perguntas, 64% contra 68%), a tabela de coerência igual entre vozes,
> o 3B contra o 7B, o conjunto adversarial e a ablação de indícios.
>
> Detalhe, dados e o que decidiria:
> [`fase-4/08-RELATORIO-REMEDICAO.md`](fase-4/08-RELATORIO-REMEDICAO.md).

**Resumo em três linhas.** O roteador de voz existe, está integrado em `/auto`, e
custa +0,5 s por pergunta. O enriquecimento offline **não se faz**, e a razão é
um número: 88% da falta do `nDCG@5` está em reordenar o que o índice já traz, e
só 12% em trazer o que ele não traz. E pelo caminho descobriu-se que a conclusão
de que a recuperação estava «no tecto» **estava errada**.

---

## 1. Parte A — o roteador

### 1.1 Nenhum método de embedding chega perto

40 perguntas rotuladas, 10 por voz ([`08-perguntas.json`](fase-1/08-perguntas.json)).
Portão do plano: 80%.

| roteador | exactidão | custo | dados |
|---|---|---|---|
| acaso (4 classes equilibradas) | 25% | — | — |
| **o que o sistema fazia** (`--voz pessoa`, ortónimo sempre) | **25%** | 0 | — |
| centróide de embedding por voz | **45%** → **68%** corrigido | µs | [`01`](fase-4/01-roteador.json) · [remedição](fase-4/08-RELATORIO-REMEDICAO.md) |
| vizinho mais próximo | **52,5%** | 6 ms | [`01`](fase-4/01-roteador.json) |
| voto@20 ponderado | 50% | 6 ms | [`01`](fase-4/01-roteador.json) |
| centróide com a média global subtraída | **32%** | µs | [`01b`](fase-4/01b-roteador.json) |
| regressão logística sobre os 2078 chunks | 42% | µs | [`01b`](fase-4/01b-roteador.json) |
| BM25, voz com mais pontos no top-20 | 45% | ~20 ms | [`02`](fase-4/02-roteador-llm.json) |
| chamada ao **qwen2.5:3b** | 42% | 0,6 s | [`02`](fase-4/02-roteador-llm.json) |
| chamada ao **qwen2.5:7b** | **72%** | **1,2 s** | [`02`](fase-4/02-roteador-llm.json) |

### 1.2 Duas explicações minhas, refutadas pela medição

**«O centróide colapsa porque a classe grande é dispersa.»** O centróide manda 17
dos seus 22 erros para o Caeiro, que é a voz **mais pequena** (127 chunks contra
1250 do ortónimo) — o inverso do que a tabela de riscos previa. A explicação
natural era a coerência interna: a média de 127 vectores parecidos aponta para
onde eles apontam, a de 1250 dispersos aponta para o centro do corpus.

Medido, não é isso:

| voz | chunks | coerência interna | similaridade ao centro do corpus |
|---|---|---|---|
| caeiro | 127 | 0,9339 | 0,9803 |
| campos | 455 | 0,9381 | 0,9841 |
| reis | 246 | 0,9386 | 0,9817 |
| ortónimo | 1250 | 0,9359 | **0,9969** |

As quatro são **igualmente coerentes** — e isto sobrevive à correcção de
2026-10-03: sem o nome dão 0,9299 / 0,9304 / 0,9301 / 0,9281, iguais entre si.
E um classificador supervisionado com pesos equilibrados colapsa no Caeiro do
mesmo modo (20 de 23 erros).

> **Mas o colapso que isto explicava era artefacto.** Sem o nome nos centróides,
> os erros que apontavam ao Caeiro caem de 19 para 1 nas perguntas. Fica uma
> medição correcta e uma inferência válida a explicar **um fenómeno que não
> existe** — ver [a remedição](fase-4/08-RELATORIO-REMEDICAO.md) §2.4.

**«É a travessia de registo: as perguntas são prosa chã, que é o registo do
Caeiro.»** Hipótese bonita, e testável: usar **poemas** como consulta em vez de
perguntas. Se o embedding soubesse distinguir as vozes, acertaria nos poemas.

| consulta | centróide | probe |
|---|---|---|
| 80 poemas, retirados do índice antes de treinar | **42%** | **46%** |
| as 40 perguntas | 45% | 42% |

**Poemas roteiam tão mal como perguntas.** Não é o registo da pergunta.

> **Corrigido em 2026-10-03.** A conclusão **relativa** sobrevive e é o que este
> passo existia para testar: corrigidos os centróides, poemas dão 64% e
> perguntas 68% — continuam a andar juntos, logo a hipótese do registo
> continua refutada. O que **não** se segue, e eu escrevi aqui, é que a culpa
> seja «do espaço»: o espaço separa as vozes a 68%, e os 42–46% mediam o nome do
> heterónimo nos centróides, não a geometria do estilo.

**O 3B a 42% contra o 7B a 72% diz o que isto é.** Não é uma tarefa de padrão
que um modelo pequeno apanhe com mais dados: é uma tarefa de **conhecimento**. O
3B não sabe quem é Ricardo Reis.

### 1.3 Os 72% não passam o portão, e o portão mede a versão fácil

As 40 perguntas foram escritas **para** uma voz, 10 por voz. «o ruído das
máquinas dá-me uma espécie de febre» é de Campos porque foi escrita para Campos.
Duas medições separam «o roteador sabe» de «a pergunta diz».

**Ablação de indícios.** 15 substantivos-assinatura trocados por paráfrase
neutra — `rebanho` → `algo ao longe`, `máquinas` → `em volta`, `o vinho … a
taça` → `o que é bom … o fim`, `o mar` removido ([`03-ablacao.json`](fase-4/03-ablacao.json)):

| | 40 perguntas | só nas 15 tocadas |
|---|---|---|
| qwen2.5:7b, perguntas cruas | 72% | 12/15 |
| qwen2.5:7b, perguntas abladas | **70%** | 11/15 |
| centróide, cruas → abladas | 45% → 42% | 6/15 → 5/15 |

**A exactidão não vinha das palavras que entregam a resposta.** Uma pergunta
mudou de certa para errada; duas mudaram de errada para certa — `q24` («os
deuses» → «aquilo que nos governa») e `q30` («beber o vinho» → «aproveitar o que
é bom»), ambas de Reis, ambas acertadas **só depois** de lhes tirar a assinatura.

**Conjunto adversarial.** 12 perguntas escritas sem voz em mente, etiquetadas com
o **conjunto** de vozes aceitáveis, e [pré-registadas num commit](fase-4/03-adversarial.json)
**antes** de qualquer roteador correr sobre elas — eu já tinha visto os 11 erros
do 7B nas 40 originais, logo etiquetar depois seria corrigir o exame depois de
ver as respostas.

| | voz primária | voz aceitável | controlos |
|---|---|---|---|
| «ortónimo sempre» | 25% | **58%** | 0/2 |
| centróide | 33% | 67% | 2/2 |
| **qwen2.5:7b** | 67% | **92%** (11/12) | **2/2** |

O único erro é `a02`, «vale a pena ter esperança?», onde propôs Caeiro e eu
aceitava Reis ou o ortónimo.

**Com um gabarito que admite mais de uma resposta certa, o roteador passa o
portão de 80% com folga.** Com etiqueta única, não passa. A diferença não está
no roteador — está em o problema não ter uma resposta só, o que o §2.2 do
protocolo previu antes de se medir. A comparação honesta é contra os 58% do
«ortónimo sempre», não contra os 25% do acaso.

Ressalva que fica: as perguntas e as etiquetas são da mesma pessoa, e essa
pessoa não é especialista em Pessoa. Isto mede concordância com um leitor
informado.

### 1.4 O custo real só apareceu a correr o CLI

O banco de ensaio dizia 1,2 s. A primeira pergunta real em `/auto` custou
**20,0 s** — porque no banco descartei uma chamada de aquecimento, logo medi o
caso quente, e o prefill a frio dos 331 tokens do `SYSTEM` a 16,5 tok/s dá
exactamente 20 s.

A pergunta grave era outra. A Fase 0 resolveu os 13,63 s de prefill da persona
pondo-a no `system`, que fica em cache: «13,63 s → 0,91 s da 2.ª pergunta». O
roteador tem um `system` **diferente**. Se o Ollama guardasse um prefixo por
slot, alternar roteador e gerador faria cada um invalidar o do outro, e a
persona voltaria a custar 20 s em **todas** as perguntas — o `/auto` passaria de
«+1 s» a «+40 s» e não seria ligável.

Medido ([`04-cache.json`](fase-4/04-cache.json)):

| | prefill do gerador, 3 perguntas |
|---|---|
| só o gerador | 0,72 · 0,66 · **0,57** s |
| alternado com o roteador | 0,81 · 0,67 · **0,52** s |

**O Ollama 0.35 mantém os dois prefixos.** Custo do `/auto` do 2.º turno em
diante: **+0,5 s**. Os 20 s a frio passaram para `aquecer()`, pago quando o
utilizador liga o roteador e anunciado («a aquecer o roteador (~20 s, uma vez)»),
em vez de cair sem aviso no meio do primeiro poema.

### 1.5 O que foi integrado

`/auto` liga o roteador; qualquer comando de voz desliga-o. A proposta aparece
**antes** de gerar, com os comandos de override na mesma linha:

```
você [auto·ortonimo]>   voz proposta: Álvaro de Campos (1.0 s) · /caeiro /campos /reis /pessoa para fixar outra
```

A 72%, uma pergunta em cada quatro vai para a voz errada. Em silêncio isso custa
~30 s de espera por uma resposta que ninguém pediu; com a proposta à vista custa
uma tecla. O roteador nunca decide sozinho, e quando não sabe — Ollama em baixo,
ou o modelo a divagar — mantém a voz corrente em vez de palpitar.

`search` não é roteável: propô-lo a uma pergunta em português trocaria a língua
da resposta sem o utilizador pedir.

---

## 2. Parte B — o enriquecimento não se faz, e há um número que o diz

### 2.1 A decomposição

O aceite do plano era «`recall@5` melhora no conjunto dourado». O portão do Passo
B1 era: medir se esse número **pode** melhorar, antes de pagar 3,2 a 7,5 h de
máquina.

A falta do `nDCG@5` parte-se em duas metades com destinos opostos, e o oráculo
sobre o top-20 — o melhor que qualquer reordenação da lista que o denso já traz
conseguiria — separa-as ([`05-tecto.json`](fase-4/05-tecto.json), n=20):

| | valor |
|---|---|
| nDCG@5 do denso | **0,640** |
| nDCG@5 do oráculo sobre o top-20 | **0,956** |
| falta até 1,0 | 0,360 |
| **recuperável por reordenar** | **0,316 — 88% da falta** |
| **exige trazer o que o índice não traz** | **0,044 — 12% da falta** |
| perguntas com o top-5 saturado | 3/20 (15%) |

**Veredicto: não enriquecer.** O enriquecimento ataca os 12%, custa 3,2–7,5 h de
máquina, e deixava 0,316 em cima da mesa. E o número dele é ainda **optimista
por defeito do instrumento**: pelo enviesamento de pooling do §3.1, um poema que
só o enriquecimento trouxesse nunca foi julgado e conta **0**, logo o
instrumento não consegue ver o ganho dele mesmo que exista.

As duas leituras dizem o mesmo: **o conjunto dourado não pode autorizar o
enriquecimento**, e enquanto não puder, diz que há 0,316 por reclamar noutro
sítio.

### 2.2 E isto corrige uma conclusão minha, de duas fases atrás

O [`CONTROLO.md`](CONTROLO.md) afirmava:

> **A recuperação densa simples parece estar no tecto do que este corpus permite
> a k=5.** O caminho que resta não é melhorar o ranking.

**Está errado.** O oráculo@20 de 0,956 contra os 0,640 do denso diz que há 0,316
de nDCG@5 dentro de uma lista que o índice **já devolve** — e 17 das 20 perguntas
têm notas 2 no top-20 abaixo da 5.ª posição.

O erro foi de inferência, não de medição. As Fases 2 e 3 mostraram que *aqueles
dois métodos* não capturaram o ganho: a fusão RRF deu +0,004, e o cross-encoder
MiniLM inverte de sinal com o gabarito. Eu li isso como «não há ganho a
capturar». O argumento que construí — 84 notas 2, mediana de 4 por pergunta, o
top-5 só leva cinco, logo reordenar troca bom por bom — explica por que o
`apt@3` fica constante a 95%, e **não** por que o `nDCG@5` fica em 0,640. São
métricas diferentes: o `apt@3` pergunta «há uma nota 2 no top-3?», e satura; o
`nDCG@5` pergunta «quantas, e em que ordem?», e não satura.

O tecto é do MiniLM, não do corpus.

### 2.3 Consequência para o Passo B2

O B2 era «instrumento novo, ou enriquecimento». Não é nenhum dos dois: é
**reabrir a reordenação**, agora com um número a dizer o que ela vale. A Fase 3
mediu um reranker contra um portão de latência de 6 s e achou-o inconclusivo; o
que não se mediu foi um reranker capaz contra um orçamento de latência que a
[correcção da iGPU](fase-0/07-igpu-vulkan.md) já tinha reaberto.

Não é trabalho desta fase, e fica nomeado em vez de feito.

---

## 3. Números por pergunta

As três perguntas com o top-5 saturado são `q01`, `q13` e `q24` — e `q13` e `q24`
têm 1 e 2 notas 2 no gabarito, isto é, saturam por o gabarito ser pequeno, não
por o sistema ser bom. A pergunta mais rica, `q33`, tem **10** notas 2, leva 4 no
top-5 e tem 9 no top-20: oráculo 1,000 contra 0,661 obtidos.

---

## 4. Checklist do protocolo

```
[x] A1  centróides calculados; exactidão, confusão e margem nas 40 perguntas
[x] A1  portão de 80% aplicado — falhou em todas as variantes de embedding
[x] A1b diagnóstico: a hipótese da coerência refutada (0,934-0,939 nas quatro)
[x] A1c hipótese do registo refutada: poemas roteiam a 42-46%
[x] A2  roteador por LLM medido: 7b 72% / 1,2 s · 3b 42% / 0,6 s
[x] A3  conjunto adversarial de 12 perguntas, pré-registado em commit
[x] A3  ablação de 15 indícios medida: 72% -> 70%
[x] A4  roteador propõe no CLI; comando de voz continua override
[x] A4b cache de KV: alternar não invalida; +0,5 s por pergunta
[x] B1  falta do nDCG@5 decomposta: 88% reordenação / 12% trazer
[x] B1  portão aplicado: **não enriquecer**
[x] B2  decisão registada, e é «não enriquecer»
```

### O que não foi feito, e porquê

- **O enriquecimento offline.** Vetado pelo portão do B1, com o número acima.
- **O roteador por embedding em serviço.** Nenhuma variante passou dos 52,5%;
  `01-roteador.json` e os bancos ficam como registo, e nada disso entrou em
  `src/`.
- **Rotear em inglês.** O `SYSTEM` do roteador e as quatro vozes roteáveis são
  portuguesas; `/auto` recusa-se em `/en` em vez de propor fora do que foi
  medido.

### Observado pelo caminho, fora do âmbito

Duas respostas de Campos saíram **truncadas** aos 220 tokens (`✂ truncada` no
rodapé) nas corridas de verificação do `/auto`. A forma de Campos pede «entre
quinze e trinta versos» de versículo longo, e isso não cabe em 220 tokens — o
`NUM_PREDICT` foi subido de 150 para 220 na Fase 1 por causa de uma ode de Reis
cortada, e Reis tem no máximo doze versos. Não é defeito desta fase e não foi
tocado.
