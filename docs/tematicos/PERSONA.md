# A persona: descrever a postura, e as regras que não descrevem o poeta

Documento temático, escrito em 2026-10-12, décimo segundo e último da série.
**Não é uma fase**, e é reunião — o [`voices.py`](../../src/voices.py) é citado em
seis dos outros onze documentos e não tinha nenhum.

**É o achado fundador do projecto, e três das suas regras foram depois medidas
como erradas.**

---

## 1. O achado: descrever o olhar, não nomear o heterónimo

> «A Fase 0 mediu isto: as duas amostras **10/10** de toda a fase vieram de
> prompts que descreviam **como** Caeiro olha («vê o que está lá, sem lhe
> atribuir significado oculto»), não de prompts que diziam «escreve como
> Caeiro». **Nomear o heterónimo produz pastiche; descrever a postura produz a
> voz.**»

É a decisão de que todo o resto decorre: as personas não dizem «és o Caeiro» —
dizem o que o Caeiro faz quando olha. E o
[`roteador.py`](../../src/roteador.py) herdou-a, com a nota de que «descreve a
**postura** de cada voz, não só o nome».

---

## 2. A estrutura: cinco blocos, e um deles é pago uma vez

O `system_prompt()` monta, por esta ordem:

| bloco | o que é |
|---|---|
| abertura + `poetica` | a postura — o achado do §1 |
| `forma` | versos, estrofes, dicção |
| `REGRAS_LINGUA` | ortografia pré-1990, ênclise, «tu», sem gerúndio |
| `REGRAS_NAO_COPIAR` | a regra preventiva do plágio |
| `REGRAS_SAIDA` | só o poema, sem preâmbulo, sem o nome do heterónimo |

**E tudo isto custa quase zero por pergunta**, porque vive no `system`, que é
prefixo estável em *cache*: os **313 *tokens*** da persona passam de **13,63 s a
0,91 s** da segunda pergunta em diante ([`TOKENIZACAO.md`](TOKENIZACAO.md) §3).

> **É o *cache* de KV que torna uma persona detalhada acessível.** Sem ele, a
> escolha entre «descrever a postura» e «nomear o heterónimo» teria sido entre
> qualidade e latência.

---

## 3. Os quatro modos de falha que as instruções combatem

Todos **medidos** na avaliação às cegas da Fase 0, não imaginados:

| | modo | o que foi observado |
|---|---|---|
| 1 | **resposta em latim** | a instrução «dicção clássica e latinizante» do Reis foi tomada à letra, e **uma amostra saiu inteiramente em latim agramatical** |
| 2 | **quebra de persona** | «(este poema não é do Reis, mas da minha voz…)», «Álvaro suspira» |
| 3 | **preâmbulo meta** | «Aqui está um breve poema em português europeu…» |
| 4 | **português do Brasil** | colocação proclítica sistemática **nos três modelos testados** |

O modo 1 deixou uma interdição explícita na persona do Reis — «a língua não é
latim: **nunca escrevas em latim**» — e é a razão de existir a guarda de idioma.

---

## 4. A regra que vale: o `REGRAS_NAO_COPIAR`

| | sem a regra | com a regra |
|---|---|---|
| mediana de versos copiados | **82%** | **0%** |

**É o maior efeito de produto do projecto** e está no
[`PLAGIO.md`](PLAGIO.md) §1. E note-se onde está: no `system`, logo custa **zero
por pergunta**, contra ~28 s de uma regeneração.

---

## 5. E três regras que não descrevem o poeta

Esta é a parte que as fases 5J a 5V acrescentaram, e nenhuma estava prevista.

| regra, em produção | o que o corpus diz | fase |
|---|---|---|
| **«Entre dez e vinte versos»** (e os outros três intervalos) | **os quatro** não descrevem o poeta: os **pisos** estão acima das medianas reais — o do Campos (15) acima de 14, o do ortónimo (12) acima de 9 | [5J](../FASE-5J-RELATORIO.md) · [5L](../FASE-5L.md) |
| **«Não uses gerúndio»** | Pessoa usa a perífrase progressiva em **101 poemas** — «Vou escrevendo os meus versos sem querer» | [5T §2](../FASE-5T-RELATORIO.md) |
| **«Colocação enclítica, sempre»** | procliticiza em **51 poemas** mesmo à régua estrita; e à régua da atracção o poeta está em **0,045** e os modelos em **0,052–0,062** — **indistinguíveis** | [5T §1](../FASE-5T-RELATORIO.md) |

**A 5L removeu os intervalos do *instrumento* de medida e eles ficaram na
*instrução* de geração.** O projecto passou a medir sem o intervalo e a
continuar a pedi-lo — e isso é o [passo 24](../CONTROLO.md), que continua aberto.

### 5.1 E a quarta regra está certa

«Usa «tu», não «você»»: `você` aparece em **4 de 1926** poemas (**0,21%**). É a
única das quatro de língua que o corpus confirma, e foi a única que gerou código
— o aviso que entrou na guarda pela [5T](../FASE-5T-RELATORIO.md).

---

## 6. Mexer na instrução deu sinal negativo **duas vezes**

É o resultado que mais pesa sobre o que fazer a seguir.

| | o que mudou | resultado |
|---|---|---|
| [5I](../FASE-5I-RELATORIO.md) | reforço de comprimento | saldo líquido **negativo** |
| [5W](../FASE-5W-RELATORIO.md) | directiva de rima explícita | **0,10 contra 0,35** do controlo — pior nas três medidas |

E a [5U](../FASE-5U-RELATORIO.md) ablou o `REGRAS_LINGUA` inteiro: **remover a
instrução nunca piorou a superfície** — seis estimativas com o mesmo sinal — e
nenhuma excluiu zero, porque o braço de base tinha **2 ocorrências de próclise e
1 marca ortográfica em 60 amostras**.

**O braço de exemplo da 5W é o único candidato vivo:** não fez dano nenhum e
moveu metro (0,665 → 0,708), versos (9 → 12) e léxico (4 → 1 suspeita) na
direcção do poeta — **menos a rima**. É a hipótese de **escorva** que a 5U
deixou registada: exemplos parecem fazer mais do que directivas, e continua a não
haver potência para o afirmar.

> **A instrução existe, é explícita, e é ignorada.** O ortónimo gerado rima a
> 0,2167, que é **exactamente o seu próprio nulo de permutação**, com «Metro
> regular e **rima**» no `system` ([5V](../FASE-5V-RELATORIO.md)). Reforçá-la dá
> sinal negativo; exemplificá-la move tudo menos a rima; e a descodificação não
> chega lá ([5X](../FASE-5X-RELATORIO.md), [5Z](../FASE-5Z.md)).

---

## 7. E uma afirmação do ficheiro que estava errada

O `INTERDICOES` — 14 substituições PT-BR → PT-PT medidas na Fase 0 — tinha na
docstring que era «usada **na instrução** e na guarda de saída».

**Na instrução nunca foi.** `grep` dá `guard.py`, `cli.py` e uma referência do
`lexico.py`, e nada que chegue ao `system_prompt`. Corrigido em 2026-10-08, ao
preparar a ablação da 5U — que precisava de saber **com exactidão** o que estava
a remover.

---

## 8. Resumo

1. **Descrever a postura produz a voz; nomear o heterónimo produz pastiche** — as
   duas amostras 10/10 da Fase 0.
2. **O *cache* de KV é o que torna isso acessível**: 313 *tokens* a 0,91 s da
   segunda pergunta em diante.
3. **Os quatro modos de falha foram medidos**, não imaginados — incluindo uma
   amostra inteiramente em latim.
4. **A regra que vale é a do plágio**: 82% → 0%, a custo zero por pergunta.
5. **Três das regras não descrevem o poeta**, e as três estão em produção: os
   quatro intervalos de versos, o gerúndio (101 poemas) e a ênclise absoluta (51).
6. **Mexer na instrução deu sinal negativo duas vezes**, e ablá-la nunca piorou
   nada.
7. **A única via viva é exemplificar em vez de instruir**, e não tem potência.

**Ficheiros:** [`src/voices.py`](../../src/voices.py) ·
[`src/generation/prompt.py`](../../src/generation/prompt.py) ·
[`FASE-5J-RELATORIO.md`](../FASE-5J-RELATORIO.md) ·
[`FASE-5T-RELATORIO.md`](../FASE-5T-RELATORIO.md) ·
[`FASE-5W-RELATORIO.md`](../FASE-5W-RELATORIO.md) ·
[`CONTROLO.md`](../CONTROLO.md) passo 24.
