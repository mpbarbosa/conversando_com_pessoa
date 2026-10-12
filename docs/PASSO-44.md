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
[ ] A1  medir o antes: 31/1926, e as três classes
[ ] B1  tirar a linha; P1, P2, P3
[ ] C1  se autorizado: entra com comentario de proveniencia + teste do poem_1068
[ ] C2  relatorio neste ficheiro, em §6
[ ] C3  CONTROLO.md
```
