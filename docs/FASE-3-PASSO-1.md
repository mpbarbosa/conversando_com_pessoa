# Fase 3 / Passo 1 — Latência dos rerankers

Executado em 2026-10-01. Protocolo: [`FASE-3.md`](FASE-3.md) §3 Passo 1.

Passo **independente** do conjunto dourado e do índice: só precisa de pares
pergunta/texto, construídos do conjunto de fumo e do corpus. Executado fora de
ordem por isso, e porque é o portão que podia matar a fase inteira.

---

## Veredicto

**A Fase 3 é viável.** 23 das 27 configurações passam o portão de 6 s, e a
melhor faz 20 candidatos sem truncagem em **1,83 s**.

Mas o veredicto depende inteiramente da **escolha de modelo**, não da
truncagem nem do número de candidatos.

---

## Throughput real, n=20 sem truncagem

| reranker | params | 3100 tokens em | tokens/s |
|---|---|---|---|
| `mmarco-mMiniLMv2-L12-H384-v1` | ~120M | **1,83 s** | **1694** |
| `bge-reranker-base` | 278M | 5,89 s | 526 |
| `bge-reranker-v2-m3` | 568M | **34,59 s** | 90 |

**19x entre o mais pequeno e o maior, com apenas 4,7x de diferença em
parâmetros.** A razão é a dimensão oculta: o MiniLM-L12-H384 tem 384 contra
1024, e o custo das camadas densas escala com o quadrado dessa dimensão.

## Correcção à estimativa de `FASE-3.md` §1

A estimativa derivada era **~19 s** para 568M sobre 20 candidatos, extrapolando
179 tok/s do bi-encoder `bge-m3` medido na Fase 0.

**Medido: 34,59 s.** A estimativa estava **optimista por 1,9x**, não
pessimista. O cross-encoder de 568M faz 90 tok/s, metade do que assumi — um
cross-encoder processa a consulta e o documento na mesma passagem, e o lote de
20 não tem a eficiência de lote que o bi-encoder tinha ao processar 2083
documentos.

Portanto a conclusão de `FASE-3.md` §1 — «um reranker de 568M sobre 20
candidatos não cabe neste hardware» — **confirma-se, e com folga maior do que a
prevista**. O que a tornou irrelevante foi outra coisa: existe um reranker 19x
mais rápido.

> Nota de rigor: numa mensagem intermédia desta sessão afirmei que a
> extrapolação «falhou dramaticamente» e atribuí isso ao custo quadrático da
> atenção em sequências longas. **Essa explicação estava errada.** Baseei-a nos
> primeiros resultados visíveis, que eram do modelo pequeno, antes de o de 568M
> ter corrido. A estimativa estava certa em magnitude para o modelo a que se
> referia.

---

## Tabela completa

Mediana de 5 corridas, aquecimento descartado, entradas distintas em cada
corrida, `taskset -c 0-11`.

| reranker | n | truncagem | tok/doc | mediana | intervalo | portão |
|---|---|---|---|---|---|---|
| MiniLM ~120M | 4 | 120 | 116 | 0,11 s | — | ✅ |
| MiniLM | 8 | 120 | 118 | 0,16 s | 0,16–0,17 | ✅ |
| MiniLM | 4 | 256 | 168 | 0,17 s | — | ✅ |
| MiniLM | 4 | sem | 172 | 0,20 s | — | ✅ |
| bge-base 278M | 4 | 120 | 116 | 0,29 s | 0,27–0,70 | ✅ |
| bge-base | 4 | 256 | 168 | 0,54 s | 0,36–0,67 | ✅ |
| bge-base | 8 | 120 | 118 | 0,59 s | 0,57–0,63 | ✅ |
| bge-base | 4 | sem | 172 | 0,67 s | 0,34–1,06 | ✅ |
| MiniLM | 20 | 120 | 95 | 0,76 s | 0,42–1,74 | ✅ |
| MiniLM | 8 | 256 | 190 | 0,80 s | 0,17–1,04 | ✅ |
| MiniLM | 20 | 256 | 136 | 0,94 s | 0,90–0,96 | ✅ |
| MiniLM | 8 | sem | 231 | 1,06 s | 0,19–1,45 | ✅ |
| bge-base | 8 | 256 | 190 | 1,15 s | 0,60–1,15 | ✅ |
| bge-m3 568M | 4 | 120 | 116 | 1,21 s | 1,06–1,28 | ✅ |
| bge-base | 20 | 120 | 95 | 1,66 s | 1,60–2,11 | ✅ |
| **MiniLM** | **20** | **sem** | **155** | **1,83 s** | 1,23–1,99 | ✅ |
| bge-m3 | 4 | 256 | 168 | 2,03 s | 1,31–2,23 | ✅ |
| bge-base | 8 | sem | 231 | 2,05 s | 0,65–2,38 | ✅ |
| bge-m3 | 8 | 120 | 118 | 2,13 s | 2,03–2,30 | ✅ |
| bge-m3 | 4 | sem | 172 | 2,70 s | 1,49–4,15 | ✅ |
| bge-base | 20 | 256 | 136 | 3,15 s | 3,13–3,73 | ✅ |
| bge-m3 | 8 | 256 | 190 | 4,18 s | 2,19–4,29 | ✅ |
| bge-base | 20 | sem | 155 | 5,89 s | 3,61–**6,51** | ⚠️ |
| bge-m3 | 8 | sem | 231 | 7,76 s | 2,40–9,13 | ❌ |
| bge-m3 | 20 | 120 | 95 | 6,47 s | 5,65–8,59 | ❌ |
| bge-m3 | 20 | 256 | 136 | 15,56 s | 15,21–16,80 | ❌ |
| bge-m3 | 20 | sem | 155 | 34,59 s | 18,05–37,03 | ❌ |

---

## Ressalvas

### Throttling térmico, grave

A temperatura do pacote chegou a **101 °C** em duas configurações, com crítico
a 110 °C. Começou a série a 53 °C.

Os intervalos largos são o sintoma, não ruído de medição:

| configuração | mediana | intervalo | razão max/min |
|---|---|---|---|
| bge-m3, n=8, sem | 7,76 s | 2,40–9,13 | **3,8x** |
| bge-base, n=8, sem | 2,05 s | 0,65–2,38 | **3,7x** |
| MiniLM, n=8, 256 | 0,80 s | 0,17–1,04 | **6,1x** |
| bge-m3, n=20, sem | 34,59 s | 18,05–37,03 | 2,1x |

Um factor de 6x entre a corrida mais rápida e a mais lenta da mesma
configuração significa que **a primeira corrida de cada configuração beneficia
de um chip frio** e as seguintes não. A mediana de 5 é mais robusta que a média,
mas estes números não têm a precisão que duas casas decimais sugerem.

**Não há pausa de arrefecimento entre configurações neste script** — ao
contrário do benchmark da Fase 0, que usava 90 s. Foi um descuido. Para medições
finais, repetir com pausa.

### O portão de 6 s está folgado, e isso é suspeito

Desenhei o portão para ser restritivo com base numa estimativa errada. Com 23
de 27 configurações a passar, o portão **não está a discriminar nada**. Nos
Passos 2 e 3 a decisão vai ser inteiramente de qualidade, não de latência — o
que inverte a premissa da fase.

### A qualidade em português europeu continua desconhecida

Nada aqui mede qualidade. O MiniLM é treinado em mMARCO, um corpus de
recuperação web traduzido — muito longe de poesia portuguesa de 1915. **Ser o
mais rápido não o torna o escolhido**; é exactamente o erro que cometi ao
recomendar o Serafim na bibliografia sem verificar o `max_seq_length`.

---

## Consequências para `FASE-3.md`

| § | Dizia | Passa a |
|---|---|---|
| §1 | 568M sobre 20 cand. ~19 s | **34,59 s** medido; conclusão mantém-se, com mais folga |
| §2.1 | MiniLM «custo relativo ~0,2» | **0,053** (1694 vs 90 tok/s) |
| §2.2 | reduzir candidatos corta custo | **desnecessário** com o MiniLM |
| §2.3 | truncar a 120 tokens | **desnecessário** com o MiniLM |
| §3 Passo 1 | portão de 6 s | **não discrimina**; manter como registo, decidir por qualidade |
| §3 Passo 2 | medir só as viáveis | **todas** as combinações de MiniLM e bge-base são viáveis |

## Próximo passo

O Passo 2 (qualidade) está **bloqueado** pelo conjunto dourado, que é
entregável do Passo 8 da Fase 1. E a Fase 1 está no Passo 3 (chunking).

O caminho mais curto para desbloquear tudo é retomar a Fase 1 no Passo 3.
