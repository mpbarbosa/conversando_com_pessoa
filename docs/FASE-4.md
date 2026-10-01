# Fase 4 — Roteador de voz e enriquecimento de metadado

Protocolo de execução da Fase 4 de [`PLANO-RAG-LOCAL.md`](PLANO-RAG-LOCAL.md).

**Objectivo do plano:** duas entregas independentes.

- **A — Roteador automático de voz.** Centróide de embedding por heterónimo, ou
  uma chamada curta ao LLM. O modo explícito (`/caeiro`, `/campos`, …) mantém-se
  como override.
- **B — Enriquecimento offline.** Tema, tom e imagens por poema, gravados no
  `corpus.jsonl` e indexados junto do verso (§2, mitigação 2 do plano).

**Aceite do plano:** `recall@5` melhora no conjunto dourado; o roteador acerta a
voz em ≥80% de um conjunto rotulado à mão de 40 perguntas.

**Pré-requisitos:** Fase 1 completa. As Fases 2 e 3 não são pré-requisito de
nenhuma destas metades — e ambas terminaram sem ganho, o que é o facto central
do §1.

**Duração estimada no plano:** 2 dias. **Revista no §4.**

---

## 1. As duas metades não valem o mesmo, e a ordem do plano está trocada

| | A — roteador | B — enriquecimento |
|---|---|---|
| custo de medir | minutos (índice e perguntas já existem) | **3–7 h de máquina**, derivado no §3.3 |
| instrumento | **novo**, e mede uma coisa que ninguém mediu ainda | o conjunto dourado — o mesmo que vetou a Fase 2 e não conclui a Fase 3 |
| o instrumento consegue ver o ganho? | sim, com a ressalva do §2.1 | **não, sem uma ronda de julgamento nova** (§3.1) |
| resultado se falhar | fica a selecção explícita, que já funciona | 7 h gastas e um número que não distingue |

A Fase 2 deu +0,004 de nDCG@5 e baixou o `apt@3` de 95% para 90%. A Fase 3
inverte de sinal com o gabarito e deixa o `apt@3` nos 95%. A causa medida é a
mesma e está em [`CONTROLO.md`](CONTROLO.md): há **84 documentos de nota 2** no
gabarito, mediana de 4 por pergunta, e o top-5 leva cinco — reordenar troca
respostas boas por outras respostas boas.

**O enriquecimento não é reordenação**, e por isso o argumento do tecto não se
lhe aplica directamente: ele muda *o que está indexado*, podendo trazer poemas
que o encoder nunca aproximaria da pergunta. Mas é exactamente isso que o
instrumento não vê — um poema nunca julgado conta **0** (§3.1).

**Consequência: o roteador vem primeiro**, e o enriquecimento começa por decidir
o seu instrumento, não por construir o enriquecimento.

---

## 2. O roteador: o que a medição do plano mede, e o que não

### 2.1 O conjunto rotulado já existe, e está contaminado

O [`08-perguntas.json`](fase-1/08-perguntas.json) tem **40 perguntas, 10 por
voz**, escritas à mão. É literalmente o conjunto que o aceite pede.

Só que as perguntas foram escritas **para** uma voz. «o ruído das máquinas dá-me
uma espécie de febre» é de Campos porque foi escrita para Campos, e traz os
indícios de Campos no vocabulário. Um roteador acerta nela sem saber nada de
Pessoa.

**A exactidão neste conjunto é um limite superior, não uma estimativa.** Usá-la
como aceite é legítimo — é o aceite escrito — mas publicá-la sem a ressalva seria
o mesmo erro que o `util@3` saturado da Fase 0, em que até o controlo inglês fez
9/10.

### 2.2 Na tarefa real, muitas perguntas não têm uma voz certa

«o que é a saudade?» serve a Campos e ao ortónimo. «vale a pena preocupar-me com
o que não posso mudar?» é de Reis, e também de Caeiro. A exactidão contra
**uma** etiqueta mede a versão fácil do problema.

Isto não se resolve com mais perguntas: resolve-se admitindo que a etiqueta é um
**conjunto** de vozes aceitáveis. Um roteador que responde «Reis» a uma pergunta
cuja etiqueta é «Reis ou Caeiro» não errou.

### 2.3 O desenho da integração importa mais que os pontos percentuais

Um roteador com 85% de exactidão manda silenciosamente 15% das perguntas para a
voz errada, e o utilizador recebe um Caeiro quando queria um Reis — **~30 s de
espera por uma resposta que não pediu**.

A alternativa custa um caracter: o roteador **propõe** e o CLI mostra a proposta
antes de gerar. Com a proposta à vista, um erro custa uma tecla; sem ela, custa
meia resposta. O aceite do plano fala de exactidão; a decisão de desenho é
anterior e fica registada aqui: **o roteador nunca decide em silêncio.**

---

## 3. O enriquecimento: o instrumento não consegue ver o ganho

### 3.1 O enviesamento de pooling, aplicado a esta fase

[`tests/test_retrieval_gold.py`](../tests/test_retrieval_gold.py) escreve o
procedimento obrigatório: ao avaliar um sistema novo, agrupar também o seu
top-5, julgar os candidatos que surjam pela primeira vez, e só então comparar.
A Fase 2 cumpriu-o — a fusão trouxe 33 candidatos nunca julgados, 12 com nota 2,
e sem os julgar o resultado negativo teria sido artefacto.

O enriquecimento é o sistema que mais candidatos novos trará, porque é o único
que muda a superfície indexada. **Medi-lo sem uma ronda de julgamento é
garantir-lhe um resultado negativo por construção.**

### 3.2 E parte do que falta não é recuperável de todo

O `nDCG@5` do denso é **0,638** com os 291 candidatos julgados depois da Fase 3.
(Escrevi 0,677 na primeira versão deste protocolo, que é o valor de depois da
Fase 2; o `FASE-3-RELATORIO.md` registou a descida e o `CONTROLO.md` não a
propagou.) Falta decompor essa falta em duas parcelas com destinos opostos:

| parcela | natureza | o enriquecimento ajuda? |
|---|---|---|
| mais documentos de nota 2 que lugares no top-5 | **estrutural** | não — nenhum sistema a resolve a k=5 |
| notas 2 no fundo da lista, abaixo de 5 | de ranking | talvez, e a Fase 3 já falhou aqui |
| notas 2 **nunca julgadas** porque nenhum sistema as trouxe | invisível ao instrumento | é precisamente o alvo dele |

O Passo B1 mede a primeira. Se ela explicar quase toda a falta, o aceite do
plano — «`recall@5` melhora» — é inalcançável por motivo aritmético, e tem de
ser substituído antes de se gastar a máquina.

### 3.3 O custo, derivado de números medidos

2062 poemas, um prompt por poema. A instrução vai no `system` e fica em cache; o
poema é conteúdo novo em cada chamada, logo **o prefill não é amortizável**.

Mediana de 93 tokens por poema (Fase 1), ~40 tokens de saída (tema, tom, três
imagens). Taxas medidas em [`fase-0/04b`](fase-0/04b-analise-latencia.txt) e
[`fase-0/07`](fase-0/07-igpu-vulkan.md):

| via | prefill | decode | por poema | 2062 poemas |
|---|---|---|---|---|
| qwen2.5:7b, CPU | 14,2 tok/s → 6,5 s | 6,7 tok/s → 6,0 s | 12,5 s | **7,2 h** |
| qwen2.5:7b, iGPU | 89 tok/s → 1,0 s | 3,30 tok/s → 12,1 s | 13,1 s | **7,5 h** |
| qwen2.5:3b, CPU | 31,4 tok/s → 3,0 s | 15,2 tok/s → 2,6 s | 5,6 s | **3,2 h** |

Duas coisas que a tabela diz e que eu não esperava:

**A iGPU não ajuda aqui.** O palpite natural — «é um lote prefill-bound, e a
iGPU faz 6x no prefill» — está errado porque os poemas são curtos: 93 tokens de
entrada contra 40 de saída, e o decode domina. O ganho de 5,5 s no prefill é
comido pelos 6 s que o decode perde.

**O 3B é 2,3x mais rápido, e a qualidade do metadado passa a ser a do 3B.** O
gerador é o 7B por decisão medida da Fase 0 (7,0 às cegas contra 6,5). Enriquecer
com o 3B é uma segunda decisão, independente, e tem de ser escrita como tal.

---

## 4. Passos

### A1 — Roteador por centróide, medido no conjunto existente (1 h)

Tudo o que é preciso já está no disco: `index.npy` tem 2290 vectores, cada chunk
tem a sua voz, e há 40 perguntas rotuladas.

```
para cada voz em (caeiro, campos, reis, ortonimo):
  centroide[voz] = média normalizada dos vectores dos chunks dessa voz (pt)
rotear(pergunta) = argmax_voz  encode_query(pergunta) · centroide[voz]
```

Medir, nas 40 perguntas: exactidão global, exactidão por voz, matriz de confusão
e a **margem** entre o 1.º e o 2.º classificado.

**Aceite:** ≥80% de exactidão, como o plano pede.
**Portão:** se passar, o A2 fica em espera e segue-se para A3 — uma chamada ao
LLM que custa segundos não se justifica contra um produto interno que custa
microssegundos e já acerta.

### A2 — Roteador por chamada ao LLM, só se o A1 falhar (2 h)

Uma chamada curta: a pergunta, os quatro nomes, uma palavra de resposta. ~60
tokens de entrada, 3 de saída → ~4,5 s em CPU, a somar aos ~30 s da resposta.

**Aceite:** ≥80% **e** o acréscimo de latência fica visível no CLI. Se o A1 já
passou, este passo não corre.

### A3 — A ressalva do §2.1, medida em vez de afirmada (2 h)

Duas medições que separam «o roteador sabe» de «a pergunta diz».

1. **Conjunto adversarial:** 12 perguntas novas, escritas sem voz em mente, cada
   uma com o **conjunto** de vozes aceitáveis (§2.2). Exactidão com etiqueta
   múltipla.
2. **Ablação de indícios:** nas 40 originais, retirar os substantivos que são
   assinatura de voz (`máquinas`, `Lídia`, `rebanho`) e remedir. A queda é a
   medida da contaminação.

**Aceite:** não há portão. É a ressalva que acompanha o número do A1, e existe
para o relatório não afirmar mais do que mediu.

### A4 — Integração: o roteador propõe, não decide (2 h)

Modo automático no CLI, com a proposta à vista antes de gerar (§2.3), e a
selecção explícita a continuar a ser override absoluto. A margem do A1 decide se
há um limiar abaixo do qual o roteador diz «não sei» e mantém a voz corrente.

**Aceite:** uma sessão em que a voz proposta é visível, mudável por tecla, e o
`/caeiro` continua a ganhar sempre.

### B1 — A falta é recuperável? (2 h, antes de gastar máquina)

Decompor o `nDCG@5 = 0,638` do denso nas parcelas do §3.2: para cada uma das 20
perguntas julgadas, quantos documentos de nota 2 existem, quantos cabem no
top-5, e quantos estão julgados mas abaixo da posição 5.

**Aceite:** uma tabela que diga quanto do 0,323 que falta é estrutural.
**Portão:** se a parcela estrutural explicar ≥80% da falta, o aceite do plano
para o enriquecimento é aritmeticamente inalcançável, e o B2 passa a ser
**definir um instrumento novo**, não enriquecer.

### B2 — Instrumento, ou enriquecimento (variável)

Conforme o portão do B1. Se for preciso instrumento novo, as duas opções já
nomeadas no repositório são o oráculo de qualidade (§6.4 do plano: corpus inteiro
na janela de 1 M do `claude-opus-5`, ~2 USD) e uma ronda de pooling sobre o
top-10. Nenhuma das duas é enriquecimento, e nenhuma se decide aqui — decide-se
com o número do B1 à frente.

---

## 5. Riscos

| Risco | Sinal | Resposta |
|---|---|---|
| O 80% do A1 vem da contaminação do conjunto | A3 mostra queda grande na ablação | o número do A1 publica-se **com** a queda ao lado; não se publica sozinho |
| O centróide colapsa no ortónimo | 1250 dos 2290 chunks são dele; exactidão alta nele e baixa nos outros | a matriz de confusão do A1 mostra-o; centróide não é afectado por tamanho de classe, a prior implícita do embedding é |
| Gastar 7 h a enriquecer para um número que não distingue | — | é o portão do B1, e é a razão de ele existir |
| Enriquecer com o 3B e atribuir a qualidade ao 7B | — | decisão escrita em separado no §3.3 |
| O roteador erra em silêncio | utilizador recebe voz que não pediu | §2.3: propõe, não decide |

---

## 6. Checklist

```
[ ] A1  centróides calculados; exactidão, confusão e margem nas 40 perguntas
[ ] A1  portão de 80% aplicado, e o A2 só corre se falhar
[ ] A3  conjunto adversarial de 12 perguntas com etiqueta múltipla
[ ] A3  ablação de indícios medida, e a queda publicada ao lado do número do A1
[ ] A4  roteador propõe no CLI; selecção explícita continua override
[ ] B1  falta do nDCG@5 decomposta em estrutural / ranking / não julgada
[ ] B1  portão aplicado: enriquecer, ou definir instrumento novo
[ ] B2  decisão registada, incluindo se for «não enriquecer»
```
