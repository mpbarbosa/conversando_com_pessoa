# Aumento de dados neste projecto: três sínteses, e o que as separa é o propósito

Documento temático, escrito em 2026-10-12, oitavo da série. **Não é uma fase.**
Companheiro do [`TRANSFERENCIA.md`](TRANSFERENCIA.md): um é sobre o que não se
treinou, este é sobre o que se sintetizou.

**Não há aumento de dados no sentido habitual, e por razão estrutural: não há
treino.** Sem conjunto de treino, não há o que aumentar.

**Mas o projecto sintetiza dados três vezes** — e a lição desta linha está na
diferença entre os propósitos:

| | o que sintetizou | para quê | resultado |
|---|---|---|---|
| [5R](../FASE-5R-RELATORIO.md) | **2013 variantes** ortográficas | construir um **instrumento** | ❌ **falhou** |
| [5K](../FASE-5K-RELATORIO.md) | sub-amostras do corpus real | construir um **nulo** | ✅ mudou uma decisão |
| [5V](../FASE-5V-RELATORIO.md) | finais de verso embaralhados | construir um **nulo** | ✅ foi o que decidiu a fase |

> **Sintetizar dados para medir o acaso é sólido. Sintetizar dados para definir
> um critério reproduziu o erro da 5E** — derivar o critério do mesmo sítio onde
> está a coisa a julgar.

---

## 1. A síntese que falhou: as 2013 variantes da 5R

A 5R gerou variantes ortográficas a partir do vocabulário do corpus, por
**transformação mecânica** em três classes:

| classe | transformação | variantes |
|---|---|---|
| **B** | acento omitido (`silêncio` → `silencio`) | **1284** |
| **C** | acento substituído (`ténue` → `tênue`) | **649** |
| **A** | consoante muda reduzida (`objecto` → `objeto`) | **80** |
| | | **2013** |

**E foi validada em dados retidos**, o que é o desenho certo: derivar da metade
A e medir na metade B, precisamente para não repetir a circularidade da
[5C](../FASE-5C-RELATORIO.md).

**Falhou de qualquer maneira:** **2,18%** de falsos positivos na metade retida,
contra um limiar de 1%. E a razão é estrutural e não de desenho — as formas
canónicas que interessavam aparecem **8, 7 e 2** vezes em 2083 poemas, logo
nenhum limiar de frequência as separa das homografias reais (`avô`/`avó`, 4 e 2
ocorrências).

**Porque é que esta síntese é diferente das outras duas:** as variantes **eram o
instrumento**. A lista gerada era o critério de julgamento, e um critério gerado
do corpus herda as lacunas do corpus. A validação retida protegeu da
circularidade e **não protegeu de medir a coisa errada** — nove dos casos
marcados eram gralhas da transcrição, em que o detector estava **certo** e a
métrica contava como erro.

---

## 2. As sínteses que funcionaram: dois nulos

### 2.1 A 5K: sub-amostras reais, sem reposição

```python
def nulo(reais: list[int], n: int, rng, b: int = 10_000) -> list[float]:
    """KS de sub-amostras reais (sem reposição) contra o corpus completo."""
```

Dez mil sub-amostras do **próprio corpus**, para responder a «quanto é que esta
distância dá por ruído de amostragem?». E mudou uma decisão:

> **o nulo assintótico era conservador por 46%** — 0,278 contra os **0,190**
> medidos a n=30 —, logo medir o chão em vez de o estimar transformou uma decisão
> à tangente numa decisão com folga.

**Sem reposição é deliberado**: com reposição, uma sub-amostra pode repetir o
mesmo poema e a distância encolhe artificialmente.

### 2.2 A 5V: finais de verso embaralhados entre poemas

Para medir rima faz falta saber **quanto é que o português rima por acaso** — e
em português quase tudo acaba em vogal. O nulo embaralha os finais de verso
**entre poemas da mesma voz**, preservando o número de versos de cada poema e a
bolsa de terminações da voz.

**É o que tornou a fase legível.** Sem ele, «o ortónimo gerado rima a 0,2167»
não quer dizer nada; com ele, **0,2167 é exactamente o p99 do próprio nulo** — o
que significa *não rima nada*.

E a mesma técnica apanhou um artefacto: o Caeiro, verso livre, «rimava» a
**0,6417** por **repetir palavras**, e cai a 0,1583 — **abaixo do próprio nulo**
— quando os pares de palavra idêntica saem.

---

## 3. Um quarto caso, de outra natureza: a variante da 5B

A [5B](../FASE-5B.md) não sintetizou **dados** — sintetizou o **tratamento**:
reescreveu a persona do Caeiro em afirmativo, com cinco regras mecânicas
pré-registadas e verificadas por *script*:

1. **cláusula a cláusula**, com o mesmo referente;
2. **zero partículas negativas** — nenhum `não`, `nunca`, `nem`, `sem`, `nada`,
   `recusas`, `proíbes`, `evitas`, `jamais`, `sequer`;
3. **comprimento a ±20%**, «para que *mais instrução* não seja a explicação
   alternativa»;
4. **nenhum conteúdo poético novo** — nenhuma imagem, nenhum exemplo, nenhum
   nome;
5. a `forma` e as três regras de língua **byte a byte**.

**A regra 3 é a interessante**: é uma restrição sobre o aumento para que a
manipulação não traga consigo um confundidor. É o mesmo cuidado que a 5Z pôs ao
asserir que cada braço difere de produção **só** no `repeat_penalty`.

A fase ficou **inconclusiva por potência** — 22 dos 30 pares empataram em 0–0.

---

## 4. O que o projecto usa em vez de aumentar

| | |
|---|---|
| **replicação com sementes fixas** | 3 repetições por célula na 5H e 5M, 2 nas restantes, com `SEMENTE_BASE + 100*r + i` |
| **bootstrap de agrupamentos** | reamostra `(voz, pergunta)`, não amostras |
| **permutação** | para nulos de rima e para testes de ordenação |

**E a 5K mediu o preço de confundir replicação com n:**

> «o **n efectivo** de um desenho agrupado é o número de **agrupamentos**, não de
> amostras — as 30 amostras de 10 perguntas × 3 repetições valem **n≈10**, e a
> essa resolução **metade do resultado da fase desaparece**.»

**Repetir uma célula não produz informação nova sobre a célula.** É a armadilha
mais parecida com aumento de dados que este projecto encontrou, e custou metade
de uma fase.

---

## 5. Resumo

1. **Não há aumento de dados**, porque não há treino.
2. **Três sínteses, e o propósito separa-as**: duas construíram **nulos** e
   funcionaram; uma construiu um **instrumento** e falhou.
3. **A 5R gerou 2013 variantes e validou-as em dados retidos** — desenho certo —
   e falhou por o corpus ter 8, 7 e 2 ocorrências das canónicas que interessavam.
4. **O nulo da 5K mudou uma decisão**: o assintótico era conservador por 46%.
5. **O nulo da 5V tornou a fase legível** e apanhou um artefacto de repetição que
   inflava a rima do Caeiro de 0,16 para 0,64.
6. **A 5B sintetizou o tratamento**, com uma restrição de comprimento a ±20% para
   que «mais instrução» não fosse a explicação alternativa.
7. **E repetir uma célula não é aumentar o n**: 30 amostras valem n≈10, e a essa
   resolução metade de uma fase desapareceu.

**Ficheiros:** [`docs/fase-5r/derivar.py`](../fase-5r/) ·
[`docs/fase-5k/calibrar.py`](../fase-5k/) ·
[`docs/fase-5v/forma.py`](../fase-5v/) ·
[`docs/fase-5b/personas_5b.py`](../fase-5b/) ·
[`FASE-5B.md`](../FASE-5B.md) §4.1.
