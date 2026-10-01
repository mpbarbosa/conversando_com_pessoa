# Fase 0 — Relatório e decisão

Executada em 2026-09-30/10-01, nesta máquina. Protocolo:
[`FASE-0.md`](FASE-0.md). Plano que a motivou:
[`PLANO-RAG-LOCAL.md`](PLANO-RAG-LOCAL.md).

---

## Decisão

**Geração local é viável em qualidade, mas só com contexto curto.**

| Portão | Veredicto |
|---|---|
| Qualidade de voz | **PASSA** — llama3.1:8b e qwen2.5:7b, ambos mediana 7/10 |
| Latência a 1500 tokens de contexto | **FALHA** — 104–108 s, inutilizável |
| Latência a 500 tokens de contexto | **marginal** — 44 s |

A decisão não é a que o plano antecipava como provável. O plano previa que o
risco fosse a qualidade («nenhum modelo local de 4–8B escreve verso aceitável
em PT-PT: probabilidade média-alta»). Errou: a qualidade passou. O que falhou
foi a latência, e por um fator de 2–4x em relação à minha própria estimativa.

### Recomendação

**Local, `llama3.1:8b-instruct-q4_K_M`, contexto limitado a ~500 tokens**, com
o backend remoto construído como escape por trás da interface `Generator`.

Três razões, todas vindas da medição:

1. O teste de voz correu com prompts de ~80 tokens. **A qualidade 7/10 foi
   medida precisamente no regime de contexto curto** que a latência permite.
   Os dois regimes coincidem — não estou a extrapolar qualidade para um
   contexto que não testei.
2. O 8B deu as **únicas duas amostras 10/10** de toda a Fase 0, e foi o único
   modelo a usar colocação enclítica correcta de português europeu.
3. O Passo 6 descobriu que o corpus tem **forte redundância temática** — 67%
   dos candidatos agrupados são aproveitáveis. Logo o sistema não precisa de 5
   poemas no contexto; precisa de 1–2 aptos. Com mediana de ~97 tokens por
   poema, 500 tokens acomodam 3–4 poemas curtos.

Custo: ~44 s por resposta, dos quais ~28 s antes de aparecer o primeiro verso.
Com *streaming*, o utilizador vê o poema a formar-se durante os restantes 16 s.

**Antes de fixar esta decisão:** corrigir o `repeat_penalty` (ver §4) e repetir
o teste de voz do 8B. A degeneração observada pode ser defeito do meu arranque.

---

## 1. Ambiente e hardware

Python 3.12.3 via `uv`, `torch 2.14.1+cpu` (187 MB, contra ~2,5 GB da variante
CUDA), `sentence-transformers 6.1.0`. `cuda: False` confirmado.

Ollama 0.35.0 instalado **em espaço de utilizador** a partir do tarball oficial,
sem `sudo` e sem serviço systemd — desvio deliberado ao `curl | sh` que o
protocolo indicava, por não haver razão para alterar o sistema numa fase de
medição. Três modelos Q4_K_M, 11 GB.

Topologia relevante: 2 P-cores a 4400 MHz, 8 E-cores a 3600 MHz, 2 LP-E-cores a
2100 MHz. Medições com `taskset -c 0-11`, excluindo os LP-E.

---

## 2. Latência (Passo 4)

### Threads

Varredura no 7B a 1500 tokens: **monotónica**, sem saturação dentro de 0–11.

| threads | prefill tok/s | decode tok/s |
|---|---|---|
| 4 | 15,1 | 5,3 |
| 6 | 19,5 | 5,9 |
| 8 | 21,6 | 6,4 |
| **10** | **22,8** | **6,7** |

Excluir os LP-E foi correcto; dentro dos restantes, mais threads é melhor.

### Grelha a `threads=10`

| modelo | ctx | prefill | decode | total | % prefill | veredicto |
|---|---|---|---|---|---|---|
| 3B | 500 | 10,0 s | 6,1 s | 16,1 s | 62% | tolerável |
| 3B | 1500 | 31,4 s | 13,2 s | 44,6 s | 70% | marginal |
| 3B | 3000 | 75,7 s | 14,1 s | 89,8 s | 84% | inutilizável |
| 7B | 500 | 25,4 s | 18,6 s | 44,0 s | 58% | marginal |
| 7B | 1500 | 84,1 s | 23,5 s | 107,6 s | 78% | inutilizável |
| 7B | 3000 | 170,3 s | 20,6 s | 190,9 s | 89% | inutilizável |
| 8B | 500 | 28,1 s | 15,7 s | 43,8 s | 64% | marginal |
| 8B | 1500 | 83,4 s | 21,1 s | 104,5 s | 80% | inutilizável |
| 8B | 3000 | 192,1 s | 32,3 s | 224,4 s | 86% | inutilizável |

### Estimativa vs. medição

| | decode estimado | medido | prefill 1500 estimado | medido |
|---|---|---|---|---|
| 3B | 15–22 tok/s | **15,2** ✓ | 8–15 s | **31 s** ✗ |
| 7B | 6–9 tok/s | **6,7** ✓ | 20–45 s | **84 s** ✗ |
| 8B | 6–9 tok/s | **6,1** ✓ | 20–45 s | **83 s** ✗ |

O raciocínio por largura de banda de memória acertou no **decode**. Errou no
**prefill** por 2–4x: assumi que, sendo compute-bound, aproveitaria os 14
threads AVX2 — mas este é um chip U de 15–28 W com apenas **2 P-cores**.

A previsão central do plano — «o prefill domina a espera» — **confirmou-se, e
mais forte do que previsto**: 58% a 500 tokens, 80% a 1500, 89% a 3000.

**Consequência de projecto:** o contexto é a alavanca dominante, não o modelo.
Cortar o contexto de 1500 para 500 tokens poupa ~55 s; trocar o 8B pelo 3B ao
mesmo contexto poupa ~18 s e custa 2 pontos de qualidade.

---

## 3. Encoders (Passo 6)

### Resultado bruto, e por que não serve

| encoder | dim | maxlen | poemas/s | R@1 | R@5 | R@10 |
|---|---|---|---|---|---|---|
| bge-m3 | 1024 | 8192 | 1,2 | 3/13 | 5/13 | 5/13 |
| e5-base | 768 | 512 | 7,1 | 2/13 | 3/13 | 5/13 |
| MiniLM-L12 multilíngue | 384 | 128 | 43,8 | 1/13 | 4/13 | 7/13 |
| serafim-335m-ir | 1024 | 128 | 3,7 | 0/13 | 2/13 | 3/13 |
| **all-MiniLM-L6 (controlo)** | 384 | 256 | 59,3 | **0** | **0** | **0** |

O controlo negativo cumpriu: **0/13 em todos os k**, sobre 2083 documentos. O
conjunto de fumo tem sinal, e isto confirma empiricamente o diagnóstico inicial
de que o encoder inglês recuperava ruído neste corpus.

Mas o meu gabarito **nomeava um único poema aceitável por pergunta**, e isso é
inválido aqui. Pessoa escreveu dezenas de quadras sobre cada tema. Exemplo
concreto: para «ofereço-lhe o meu afecto e ela nem repara» eu esperava o
`poem_116`; o e5 devolveu o `poem_3040` («Entreguei-te o coração, / E que
tratos tu lhe deste!»), que é um casamento igualmente bom — e contou como erro.

### Correcção: pooling de relevância

Refiz a avaliação pelo método do TREC: agrupei o top-3 de todos os encoders,
deduplicado e **ordenado por id para não revelar o ranking de nenhum modelo**,
e julguei 125 candidatos pelo conteúdo. 10 das 13 perguntas.

| encoder | maxlen | poemas/s | apt@3 | ganho@3 |
|---|---|---|---|---|
| bge-m3 | 8192 | 1,2 | 6/10 | **56,7%** |
| e5-base | 512 | 7,1 | 5/10 | 50,0% |
| MiniLM-L12 | 128 | 43,8 | 6/10 | 50,0% |
| serafim-335m-ir | 128 | 3,7 | 6/10 | 48,3% |
| all-MiniLM-L6 (controlo) | 256 | 59,3 | 2/10 | 35,0% |

**A diferença entre os três multilíngues viáveis está dentro do ruído** a n=10
com avaliador único. Não afirmo que o bge-m3 ganhou.

### Decisão: `intfloat/multilingual-e5-base`

Assenta em propriedades técnicas, não na métrica ruidosa:

- **`serafim-335m-ir` desqualificado**: `maxlen=128` trunca mais de um quarto
  dos poemas, e é lento (3,7 poemas/s). Recomendei-o na bibliografia a partir
  do artigo sem verificar o limite de sequência da variante `-ir`.
- **`MiniLM-L12` desqualificado** pelo mesmo `maxlen=128`, apesar de ser 6x
  mais rápido.
- **`bge-m3` desqualificado por custo**: 1,2 poemas/s = **30 min** por
  reconstrução do índice, para uma vantagem que estes dados não estabelecem.
- **`e5-base`**: `maxlen=512` cobre 96% dos poemas inteiros, embeda o corpus em
  ~5 min, empata em qualidade. Exige prefixos `query: ` / `passage: ` — sem
  eles degrada em silêncio.

---

## 4. Defeitos encontrados na própria Fase 0

Registados porque dois deles teriam produzido dados falsos convincentes.

### 4.1 Reaproveitamento de KV cache invalidava o prefill

O benchmark enviava o mesmo prompt 4 vezes. O log do servidor revelou
`cached n_tokens = 1803` e «need to evaluate at least 1 token». Medido
isoladamente:

| | `prompt_eval_count` | duração | tok/s reportado |
|---|---|---|---|
| 1ª corrida (a frio) | 1804 | **30,70 s** | 58,8 |
| 2ª corrida (mesmo prompt) | 1804 | **0,07 s** | **25 625** |

A contagem de tokens **não muda**, só a duração colapsa — por isso o defeito
não é detectável olhando para `prompt_eval_count`. O benchmark teria reportado
25 625 tok/s de prefill.

Em produção o contexto RAG muda a cada pergunta, logo o prefill relevante é a
frio. Correcção: prefixo variável no início do prompt, que invalida o cache por
prefixo. Verificada antes de relançar: duas corridas consecutivas, 32,8 s e
33,7 s.

### 4.2 A flag de throttling é não-informativa

Ao reduzir as repetições de 3 para 2, «queda monotónica» passou a significar
apenas «rep2 < rep1» — 50% por puro ruído. A flag disparou em quase todas as
configurações e **deve ser ignorada** nesta corrida.

A temperatura subiu de 55 °C para 81 °C durante a primeira configuração, o que
motivou aumentar a pausa de 60 s para 90 s. A primeira configuração da
varredura (4 threads) arrancou a 72 °C por calor residual e está ligeiramente
penalizada; a tendência monotónica não depende dela.

### 4.3 `repeat_penalty` não foi definido

O teste de voz definiu `temperature`, `top_p`, `seed`, `num_predict` e
`num_thread`, mas **não** `repeat_penalty`. O 8B degenerou em ciclo no prompt
mais longo. Pode ser defeito do arranque, não do modelo. **A repetir antes de
concluir sobre o 8B em forma longa.**

### 4.4 A avaliação de voz não foi cega

O protocolo pedia pontuar sem ver o nome do modelo. Não foi feito: as amostras
estão agrupadas por modelo no ficheiro. Viés real, não corrigível a posteriori.

---

## 5. Correcções ao plano

| § do plano | Dizia | Medição |
|---|---|---|
| 1.1 | prefill 1500 tok: 8–15 s (3B), 20–45 s (7–8B) | **31 s / 84 s** |
| 1.1 | «o prefill domina a espera» | confirmado, 58–89% |
| 4.1 | encoder: `multilingual-e5-base` | **mantido**, agora por medição |
| 6.1 | conjunto dourado com «1–3 poemas esperados» | **inválido** — exige gabarito múltiplo ou julgamento do top-k |
| 7.2 | risco principal: qualidade de voz (média-alta) | **não se materializou** — o risco era a latência |
| bibliografia 4.1 | Serafim como candidato preferencial | **desqualificado** (`maxlen=128`) |

### Achados novos no corpus

- **Duplicados por tradução**: `poem_1794` é a *Ode Marítima* (`poem_135`) em
  inglês. A deteção por hash exacto não os apanha.
- **Duplicados por variante**: `poem_17` e `poem_23` são dois esboços da mesma
  ode de Reis. O e5 devolveu o `poem_23` em 2º lugar e a métrica contou erro.
- **Redundância temática forte**: 67% dos candidatos agrupados são
  aproveitáveis, e o `util@3` saturou — até o controlo inglês fez 9/10. A minha
  nota «1» (adjacente) foi permissiva demais, mas o facto de fundo é real: o
  corpus é tematicamente uniforme. **Isto favorece o desenho de contexto
  curto.**

---

## 6. Próximos passos

1. Corrigir `repeat_penalty` e repetir o teste de voz do 8B (§4.3)
2. Repetir a avaliação de voz **às cegas**, com amostras embaralhadas (§4.4)
3. Remedir o throughput do e5 sem contenção de rede — os tempos do Passo 6
   foram colhidos durante os downloads dos modelos
4. Actualizar a §6.1 do plano: gabarito de relevância múltipla
5. Acrescentar à Fase 1 a detecção de duplicados por tradução e por variante
6. Fase 1 com orçamento de contexto de **500 tokens**, não 1500

---

## 7. Entregáveis

| Ficheiro | Conteúdo |
|---|---|
| [`fase-0/01-ambiente.txt`](fase-0/01-ambiente.txt) | versões, `cuda: False` |
| [`fase-0/02-modelos.txt`](fase-0/02-modelos.txt) | modelos e tamanhos |
| [`fase-0/03-calibracao.txt`](fase-0/03-calibracao.txt) | topologia, energia, temperatura |
| [`fase-0/04-bench-geracao.json`](fase-0/04-bench-geracao.json) | medições brutas |
| [`fase-0/04b-analise-latencia.txt`](fase-0/04b-analise-latencia.txt) | análise contra o orçamento |
| [`fase-0/05-teste-voz.md`](fase-0/05-teste-voz.md) | **30 amostras cruas** |
| [`fase-0/05-avaliacao-voz.md`](fase-0/05-avaliacao-voz.md) | rubrica preenchida |
| [`fase-0/06-bench-encoders.json`](fase-0/06-bench-encoders.json) | medições brutas |
| [`fase-0/06b-folha-julgamento.md`](fase-0/06b-folha-julgamento.md) | 163 candidatos agrupados |
| [`fase-0/06c-julgamentos.json`](fase-0/06c-julgamentos.json) | julgamentos de relevância |
| [`fase-0/06d-rescore.txt`](fase-0/06d-rescore.txt) | reavaliação |
| [`fase-0/smoke-set.json`](fase-0/smoke-set.json) | 13 pares — semente do conjunto dourado |
| 4 scripts | `bench_geracao.py`, `teste_voz.py`, `bench_encoders.py`, `pool_julgamento.py` |

---

# Adenda — as três correcções (2026-10-01)

As três pendências da §6 foram executadas. **Duas mudam conclusões.**

## A.1 `repeat_penalty` — resolvido

Definido a **1,1** (default do llama.cpp). A degeneração em ciclo
**desapareceu em todas as amostras de Campos**, e o estilo acumulativo
sobreviveu — a amostra A09 corre 22 versos longos sem repetir.

Tensão registada: o estilo de Campos *é* anafórico («Olho pró lado da barra,
olho pró Indefinido, / Olho e contenta-me ver»). Penalizar repetição combate o
estilo-alvo, logo 1,1 é deliberadamente moderado. Valores altos esterilizariam
Campos.

## A.2 Avaliação às cegas — **corrige a recomendação**

Novo teste, amostras agrupadas por prompt mas embaralhadas quanto ao modelo,
com ids opacos e chave em ficheiro separado. Pontuadas 25 de 30 sem acesso à
chave.

| modelo | enviesada | **às cegas** | n | min–max |
|---|---|---|---|---|
| qwen2.5:7b | 7 | **7,0** | 9 | 2–10 |
| llama3.1:8b | 7 | **6,5** | 8 | 3–10 |
| qwen2.5:3b | 5 | **4,5** | 8 | 3–7 |

O viés era moderado em magnitude (−0,5) mas **específico e consequente**: na
ronda enviesada atribuí as duas únicas amostras 10/10 ao 8B, e construí a
recomendação sobre isso («o 8B deu as únicas duas amostras 10/10, e foi o único
a usar enclíticas PT-PT corretas»). Às cegas, **o 7B também produziu um 10/10**
e também usou enclíticas corretas.

### Recomendação revista

**`qwen2.5:7b-instruct-q4_K_M`** em vez do 8B. Razões:

- Qualidade **indistinguível** a este n (7,0 vs 6,5, com variância de 2 a 10).
  Não afirmo que o 7B ganhou; afirmo que a razão que eu tinha para preferir o
  8B era um artefacto do viés.
- Marginalmente mais rápido no regime que importa: 25,4 s de prefill a 500
  tokens contra 28,1 s do 8B.
- Menor em disco: 4,7 GB contra 4,9 GB.

A decisão é fraca e deve ser revista com o conjunto dourado da Fase 1. Ambos
ficam configuráveis.

## A.3 Throughput do e5 — **a minha ressalva era infundada**

| batch_size | tempo | poemas/s |
|---|---|---|
| **8** | **194,2 s** | **10,7** |
| 16 | 278,5 s | 7,5 |
| 32 | 304,8 s | 6,8 |
| 64 | 312,8 s | 6,7 |
| *original, com contenção (bs=16)* | *293,1 s* | *7,1* |

A contenção de rede valia **5%** (278,5 s limpo vs 293,1 s contaminado). A
ressalva que levantei no relatório era excessivamente cautelosa: os números
originais estavam bons.

Mas a remedição encontrou outra coisa: **lote 8 é 1,6x mais rápido que lote
64**, o inverso do esperado. Com `batch_size=8` o corpus embeda em 3,2 min.
Fixar esse valor na Fase 1.

## A.4 Modos de falha novos, vistos às cegas

Quatro, nenhum detectado na primeira ronda:

1. **Resposta inteiramente em latim** (A13, qwen 7B). A instrução «dicção
   clássica e latinizante» foi tomada à letra. E o latim é agramatical
   («Vitam brevis»).
2. **Quebra de persona nomeando o heterónimo** — A14: «(este poema não é do
   Reis, mas da minha voz...)»; A16: «Reis, na minha voz»; A10: «Álvaro
   suspira». O modelo **descreve** o heterónimo em vez de **ser** ele.
3. **Preâmbulo meta** — A26: «Aqui está um breve poema em português europeu,
   falando da...», apesar de o prompt pedir «responde apenas com o poema».
4. **Ortografia brasileira**, agora com casos concretos: `ator` (PT-PT
   *actor*), `demônios` (*demónios*), `espetáculo` (*espectáculo*), `refletem`
   (*reflectem*), `galhos` (*ramos*).

Um achado positivo: **`alcatifa`** (A08) é lexicalmente europeu.

Os quatro modos são alvos de engenharia de prompt na Fase 1, e os três
primeiros são detectáveis por pós-processamento determinístico.

## A.5 Efeito nos documentos

| Documento | Alteração |
|---|---|
| `FASE-0-RELATORIO.md` §Decisão | gerador passa a `qwen2.5:7b`; ver A.2 |
| `FASE-1.md` §0 | idem, e `batch_size=8` |
| `FASE-1.md` §Passo 5 | acrescentar guarda contra quebra de persona e preâmbulo meta |

---

# Correcção de facto (2026-10-01, durante a Fase 1 Passo 2)

**A §3 e a §5 deste relatório descrevem mal o par `poem_17`/`poem_23`.**

Escrevi que eram «dois esboços da mesma ode de Reis». **Não são.** Medido:
similaridade ao nível do verso de **0,111**, Jaccard de 4-gramas de palavra de
0,0199. Partilham apenas o primeiro verso — «Sofro, Lídia, do medo do
destino.» — e divergem por completo a partir daí. São duas odes distintas com
o mesmo incipit, e Reis fez isso com frequência: o corpus tem **18 grupos de
incipit partilhado, 40 poemas** («Coroai-me de rosas» abre 3 odes diferentes,
«Olho os campos, Neera» abre 4).

O que **se mantém** é o argumento para que a métrica dependia: o `poem_23` é
uma resposta legítima à pergunta sobre medo da mudança, porque é a mesma ode
temática, e o gabarito de um só poema contou-o como erro. A conclusão sobre a
invalidez do gabarito único não muda; a descrição do mecanismo estava errada.

**E a §A.4 subestimou os duplicados.** A contagem de «1 par exacto» era do hash
sobre os ficheiros em bruto. Sobre o corpo limpo e normalizado são **3 pares
exactos**, e há **18 grupos de variantes** — esboços, revisões, transcrições
divergentes e contenção (`poem_12` tem 26 versos, todos presentes nos 47 de
`poem_619`). No total, **21 poemas** são duplicados de outro.


---

# Correcção de premissa (2026-10-01): a iGPU existe e é utilizável

Este relatório diz «CPU-only» em §1 e em todas as decisões que dela derivam.
**A premissa estava incompleta.**

Concluí «sem GPU» de `nvidia-smi` ausente. Vi o `lspci` reportar «Intel
Corporation Meteor Lake-P [Intel Graphics]» e tratei-o como irrelevante **sem
verificar**. O Ollama 0.35.0 detecta-a por Vulkan e desliga-a por omissão.

Medido com `OLLAMA_IGPU_ENABLE=1`:

| | CPU | iGPU | razão |
|---|---|---|---|
| prefill (421 tok, pt) | 14,2 tok/s | **89,1 tok/s** | **6,28x** |
| prefill (360 tok, en) | 16,6 tok/s | **85,8 tok/s** | 5,20x |
| **decode** | 5,2–7,1 tok/s | **3,30 tok/s** | **0,55x** |

**Nenhuma decisão deste relatório muda.** Na carga real o decode domina — a iGPU
ganha 21 s na primeira pergunta de cada voz e perde 20 s em todas as outras, e o
cache de prefixo faz com que quase todas sejam «outras». A CPU continua certa, e
é por isso que o Ollama a prefere por omissão.

**Mas o §7.1 desta fase rejeitou o contexto de 1500 tokens por causa de 84 s de
prefill, e na iGPU seriam ~17 s.** Se o contexto voltar a ser o constrangimento,
essa rejeição deve ser reavaliada.

Detalhe e reprodução: [`fase-0/07-igpu-vulkan.md`](fase-0/07-igpu-vulkan.md).
