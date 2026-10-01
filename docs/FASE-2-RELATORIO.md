# Fase 2 — Busca híbrida: **resultado negativo**

Executada em 2026-10-01. Protocolo: [`FASE-2.md`](FASE-2.md).

---

## Decisão

**A fusão não entra no sistema.** O denso sozinho mantém-se.

| sistema | nDCG@5 | apt@3 | latência |
|---|---|---|---|
| **denso (`multilingual-e5-base`)** | **0,677** | **95%** | 332 ms |
| BM25 | 0,464 | 65% | 4 ms |
| RRF 1:1 | 0,670 | 90% | 389 ms |
| RRF 2:1 a favor do denso | 0,681 | 90% | 546 ms |
| RRF 1:2 a favor do BM25 | 0,580 | 85% | 706 ms |

A melhor fusão dá **+0,004** de nDCG@5, ruído a n=20, e o `apt@3` **cai de 95%
para 90%** em todas as configurações. O critério do Passo 3 era «supera a melhor
das duas listas isoladas»; não supera.

Nenhuma profundidade de fusão ajuda: 5 → 0,616 · 10 → 0,640 · 20 → 0,670 ·
40 → 0,621.

---

## 1. Por que falhou, com a causa medida

A hipótese da fase era forte: a sobreposição entre o top-5 denso e o top-5 BM25
é de **mediana 1/5** e **zero em 9 das 40 perguntas**. Duas listas que concordam
tão pouco são o caso em que o RRF costuma dar mais.

E a fusão **de facto encontra coisas boas**: trouxe 33 candidatos ao top-5 que
nunca tinham sido julgados, e **12 têm nota 2**.

Mas:

| | documentos de nota 2 no top-5, somados em 20 perguntas |
|---|---|
| denso | **40** |
| fusão | **39** |

**A fusão troca respostas boas por outras respostas boas.** Há 70 documentos de
nota 2 no gabarito, mediana de 3 por pergunta, e o top-5 só leva cinco.

É a **redundância temática medida na Fase 0** — 67% dos candidatos agrupados
eram aproveitáveis — a limitar o que a fusão pode ganhar. Num corpus onde cada
pergunta tem três respostas certas, diversificar a recuperação não melhora uma
métrica que já está saturada de respostas certas.

### O que isto implica para a Fase 3

O mesmo tecto aplica-se ao reranker. Se há mediana de 3 respostas de nota 2 e o
denso já põe 2 no top-5, reordenar os 20 candidatos vai mexer em quais, não em
quantos. **A Fase 3 deve ser medida com esta expectativa**, e o portão de
qualidade deve exigir mais que +0,01 para justificar a latência.

---

## 2. O procedimento de pooling salvou a medição

O relatório do conjunto dourado marcou como obrigatório: agrupar o top-5 do
sistema novo e julgar os candidatos que surgirem, antes de comparar.

Foi executado: **33 candidatos novos em 17 das 20 perguntas**, dos quais 12 com
nota 2. Sem isso, a fusão teria sido medida contra um gabarito que não conhecia
12 das respostas que ela encontra, e o resultado negativo teria sido um
artefacto em vez de um facto.

Efeito colateral: o gabarito cresceu de 176 para **209** candidatos julgados, e
a linha de base do denso **desceu de 0,719 para 0,677** — porque o ideal cresceu.
Isso é correcto: um gabarito mais completo dá números mais baixos e mais
verdadeiros.

---

## 3. Normalização ortográfica: mantida como correcção de defeito

O Passo 1 media o BM25 com e sem normalização. **Zero diferença:** 0,464 e 65%
nas duas.

Pelo critério do protocolo, removia-se. Mas a medição é **não-informativa** e
não negativa: nenhuma das 20 perguntas contém `cousa` nem `p'ra`. Em teste
dirigido a camada funciona — a consulta «coisa» passa a alcançar 1 de 5 poemas
com «cousa», e as consultas com elisão mudam de resultado.

E corrige um defeito real: o tokenizador reduzia **`p'ra` ao token `ra`**, que é
lixo. 95 ocorrências nas duas grafias de apóstrofo do corpus (U+0027 e U+2019).

Mantida, com a afirmação rebaixada: **é correcção de bug, não melhoria de
recuperação.** Custa 0,3 s de construção e 1,1 ms por consulta.

### A tabela é muito menor do que o plano previa, e o que ficou de fora importa

Construída do corpus, com distância de edição ≤ 2 e filtro à mão.

**Entra:** elisões (245 ocorrências em 80 formas) e a alternância `ou`/`oi`
(13 pares — `coisa`/`cousa` 387/39, `ouro`/`oiro`, `ouço`/`oiço`,
`loura`/`loira`, `papoila`/`papoula`).

**Fica de fora todo o sinal de acento.** O meu gerador de candidatos usou
«acento» como sinal de equivalência **apesar de a `FASE-2.md` já dizer** «sem
remoção de acentos — em português o acento distingue palavras». Propôs fundir
`para`/`pára`, `pais`/`país`, `bebe`/`bebé`, `faca`/`faça`, `sois`/`sóis`,
`dois`/`dóis`, `mares`/`marés`, `seria`/`séria` — pares de palavras diferentes.

Dos 11 candidatos com razão de frequência extrema, 8 são palavras distintas ou
infinitivos com clítico (`esquecê-lo`, `deixá-lo`). Os 3 restantes — `duvida`,
`gloria`, `angustia` — são plausivelmente gralhas de transcrição, mas nos três
a forma sem acento **também é um verbo válido**. São 8 ocorrências em 229 mil
palavras: risco real por ganho nulo.

**`facto`/`fato` fica de fora:** em português europeu são palavras diferentes.

---

## 4. O que fica no repositório

| ficheiro | estado |
|---|---|
| `src/retrieval/normalize.py` | **em uso**, ligado ao BM25 |
| `src/retrieval/lexical.py` | **em uso** no pooling do gabarito |
| `src/retrieval/fusion.py` | **não ligado ao pipeline**; testado e disponível |
| `src/retrieval/search.py` | idem |

A fusão fica no repositório e **fora do caminho de execução**, não desligada por
configuração — um componente desligado por omissão é dívida.

Há duas razões para a guardar e não a apagar: o tecto que a limita é o `top_k`
de 5 contra a redundância do corpus, e ambos podem mudar — um conjunto dourado
maior, ou um orçamento de contexto que permita mais poemas, alteram o cálculo.
Se nada disso acontecer, apagar.

---

## 5. Limitações desta medição

| | |
|---|---|
| **n = 20** perguntas julgadas | +0,004 não é distinguível de ruído, e também não o seria −0,004 |
| avaliador único | o mesmo que escreveu as perguntas e os julgamentos |
| `k=60` não afinado | deliberado: 20 perguntas não bastam para o ajustar sem sobreajustar |
| metade do gabarito por julgar | q06–q10, q16–q20, q26–q30, q36–q40 |

Se as 20 perguntas restantes forem julgadas e a fusão passar a ganhar por uma
margem clara, esta decisão deve ser revista. **O resultado negativo é sobre
estes 20, não sobre a ideia.**
