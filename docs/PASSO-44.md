# Passo 44 — A linguagem meta deixa de ser motivo por si

**Pré-registado em 2026-10-12, antes de tocar em `src/`.** É uma correcção de
**produto**, não uma fase: o entregável são duas linhas no
[`src/guard.py`](../src/guard.py).

**Tem protocolo porque mexe numa guarda**, e a disciplina desta casa diz que uma
guarda se pré-registra — foi por isso que não a corrigi quando a medi, no
[`tematicos/ENTIDADES.md`](tematicos/ENTIDADES.md) §4.

---

## 1. O defeito, medido

O `_nomes_indevidos` marca **31 de 1926** poemas autênticos (**1,61%**) — dez
vezes a taxa do `lingua_errada` (0,16%) — **e rejeita**: o motivo entra em
`motivos` e faz `ok=False`.

| classe | n | |
|---|---|---|
| só nome de heterónimo | **17** | verdadeiro positivo por desenho |
| **só linguagem meta** | **13** | **falsos positivos** |
| ambos | 1 | verdadeiro positivo |

E os 13 são inequívocos:

```
poem_163   «A caligrafia rápida destes versos,»      <- 'estes versos'  (7 poemas)
poem_1068  «A alma da minha voz?»                     <- 'minha voz'    (7 poemas)
```

**Nenhum é meta-comentário.** São poemas a falar da sua própria caligrafia e da
sua própria voz, que é assunto de poesia. É o defeito da
[correcção 12](CONTROLO.md) noutro instrumento: ali a fracção de *stopwords*
media **registo** e chamava-lhe **língua**; aqui o `_RE_META` mede
**auto-referência** e chama-lhe **meta-comentário**.

---

## 2. A correcção, e vem do comentário que já estava escrito

O `_RE_META` existe, segundo o próprio código, para **licenciar** os nomes
ambíguos:

> «#: Nomes que coincidem com palavras comuns. **Só contam com linguagem meta à
> volta.**»

Mas o `_nomes_indevidos` faz mais do que isso — acrescenta `"linguagem meta"`
como achado **autónomo**:

```python
if tem_meta:
    achados.append("linguagem meta")      # <- isto é o defeito
    for n in _NOMES_AMBIGUOS:
        ...
```

**A correcção é tirar essa linha.** A linguagem meta passa a ser **só o portão**
dos nomes ambíguos, que é o que o comentário diz que ela é.

### 2.1 Porque é que isto não perde nenhum modo de falha conhecido

Os três modos observados na Fase 0, e onde ficam:

| caso observado | quem o apanha depois da correcção |
|---|---|
| «(…este poema não é do Reis, mas **da minha voz**…)» | **`Reis` + meta** — o portão dispara, o nome entra |
| «**Reis**, na minha voz» | idem |
| «**Álvaro** suspira em espírito de fuga» | `Álvaro` é **inequívoco**, nunca dependeu de meta |
| «Aqui está um breve poema em português europeu…» | o **`_RE_PREAMBULO`**, que é outro detector e remove o preâmbulo |

**Nenhum dos quatro depende de `"linguagem meta"` como achado autónomo.**

---

## 3. Portões

| | nome | dispara se | leitura, escrita agora |
|---|---|---|---|
| **P1** | **a guarda fica mais segura** | a marcação no corpus cai para **≤ 1,0%** *e* **todos** os casos restantes trazem nome de heterónimo | o falso positivo de auto-referência desaparece. **Predição escrita: 31 → 18 (0,93%)** — os 17 de nome e o 1 de ambos |
| **P2** | **sem regressão** | os testes passam, **incluindo** os que fixam os casos da Fase 0 (`test_guard.py` `QUEBRA`, `PREAMBULO`) | os modos de falha que a guarda existe para apanhar continuam apanhados |
| **P3** | **o portão dos ambíguos sobrevive** | `test_nome_ambiguo_com_linguagem_meta_e_apanhado` passa: «Reis, na minha voz» **é** apanhado e «Reis houve que nada souberam» **não** | a parte que funcionava não se estraga |
| **P4** | **não compensa** | a queda é menor que a predição, **ou** qualquer caso conhecido regride | **não entra**, e o relatório diz o quê |

### 3.1 A decisão, pré-escrita

| | decisão |
|---|---|
| **P1, P2 e P3** | **entra em `src/guard.py`**, com a proveniência no comentário e um teste novo que fixa um dos 13 casos reais — `poem_1068`, «A alma da minha voz?» — para que a regressão seja impossível em silêncio |
| qualquer um falha | não entra |

## 4. O que este passo não faz

- **Não mexe no `_RE_PREAMBULO`**, que é outro detector e trata do modo 3.
- **Não mexe nos 17 casos de nome.** Pessoa nomear Caeiro dentro de um poema é
  verdadeiro positivo por desenho: numa **resposta gerada**, nomear o heterónimo
  é quebra de persona. O preço — 17 poemas autênticos não passariam — fica
  declarado e não corrigido, porque corrigi-lo exigia distinguir «poema que
  nomeia» de «comentário que nomeia», e isso não tem critério mecânico à vista.
- **Não mede o efeito em respostas geradas.** A guarda rejeita menos; se isso
  muda a taxa de rejeição em produção, mede-se quando houver amostras com o
  `historico` do [passo 43](CONTROLO.md).

---

## 5. Lista de verificação

```
[x] A1  medido o antes: 31/1926 = 1,61%, e as tres classes (17/13/1)
[x] B1  linha tirada. P1 DISPARA, P2 DISPARA, P3 DISPARA
[x] C1  entrou, com a proveniencia no comentario e tres testes novos
[x] C2  relatorio no §6
[x] C3  CONTROLO.md
```

---

## 6. Relatório

### 6.1 Os portões

| | | |
|---|---|---|
| **P1** a guarda fica mais segura | ✅ **dispara** | **18/1926 = 0,93%**, e **zero** casos sem nome de heterónimo |
| **P2** sem regressão | ✅ dispara | a *suite* passa, `QUEBRA` e `PREAMBULO` incluídos |
| **P3** o portão dos ambíguos sobrevive | ✅ dispara | «Reis, na minha voz» é apanhado; «Reis houve que nada souberam» não |

**E a predição estava escrita antes: «31 → 18 (0,93%)».** Saiu **18 (0,93%)** —
os 17 de nome e o 1 de ambos, exactamente como o §3 previa. Não é mérito de
previsão: é aritmética, porque a correcção remove uma classe inteira e a classe
estava contada. **Mas estava contada antes, e é isso que faz a diferença entre
uma predição e uma descrição.**

### 6.2 O que entrou

Uma linha **retirada** do `_nomes_indevidos` — `achados.append("linguagem
meta")` —, treze de comentário com a proveniência, e **três testes**:

| teste | o que fixa |
|---|---|
| `test_auto_referencia_poetica_nao_e_quebra_de_persona` | o `poem_1068` **verbatim**, «A alma da minha voz?» |
| `test_linguagem_meta_sozinha_nao_e_achado` | «A caligrafia rápida destes versos» não produz motivo |
| `test_linguagem_meta_continua_a_licenciar_o_nome_ambiguo` | o portão, e que `"linguagem meta"` **não** volta à lista |

O primeiro usa um poema real do corpus, e é deliberado: é o argumento que o
[`tematicos/STOPWORDS.md`](tematicos/STOPWORDS.md) §3.2 registou — uma amostra
inventada por mim concorda comigo; a observada não.

### 6.3 O que fica

**Os 18 que sobram são poemas em que Pessoa nomeia um heterónimo** — «Desembrulhar-me
e ser eu, não Alberto Caeiro», a nota biográfica de Campos. Numa resposta
**gerada** isso é quebra de persona, logo a guarda está a fazer o que lhe
mandaram. **0,93% de material autêntico continua a não passar**, e isso fica
declarado: o §4 diz porque não tentei corrigi-lo.
