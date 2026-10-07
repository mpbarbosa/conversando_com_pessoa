# Fase 5N — relatório: 145% de capacidade não compram o que 5% compraram

**Protocolo:** [`FASE-5N.md`](FASE-5N.md), pré-registado em `4e00eca`.
**Dados:** [`fase-5n/01-cru.jsonl`](fase-5n/) · [`03-pontuacoes.json`](fase-5n/)
(commitadas antes de abrir a chave) · [`04-resultados.json`](fase-5n/)

---

## 0. Os portões

| | | |
|---|---|---|
| **N1** a capacidade tem tracção | ❌ **não dispara** | Δ=+0,400 a favor do 7b, mas **p=0,12** e IC a incluir 0 |
| **N2** a capacidade não explica a 5H | ✅ **dispara** | **+145%** de parâmetros compram +0,400 (n.s.); **+5%** compraram +0,700 |
| **N3** inconclusivo por potência | ❌ não dispara | d=15, acima do piso de 8 |
| **N4** o 3b também perde na forma | ✅ dispara | KS 0,383 contra 0,288; mediana 8,0 contra 11,5 do poeta |

**Em uma frase.** Um salto de **145%** de parâmetros **dentro da mesma família**
rende **+0,400 em 3a′ e não é significativo**; o salto de **5%** que a
[5H](FASE-5H-RELATORIO.md) mediu, com **mudança de família**, rendeu **+0,700**
com p=0,0002. **A capacidade não explica o resultado da 5H.**

---

## 1. N1 e N2 — a dose-resposta

| | 3a′ média | | |
|---|---|---|---|
| **Q** = `qwen2.5:7b` (7,6B) | **0,960** | | |
| **T** = `qwen2.5:3b` (3,1B) | **0,560** | | |
| **Δ (Q − T)** | **+0,400** | IC95% **[−0,08; +0,88]** | **p=0,1185** · d=15 (11 Q / 4 T) |

O **N1 não dispara**: pedia p ≤ 0,05 **e** IC a excluir 0, e falha nos dois. O
ponto estimado favorece o modelo maior, e a demonstração não existe.

**E o N3 não dispara**, logo isto **não é falta de potência** pelo critério
pré-registado: 15 pares discordantes contra um piso de 8. É um efeito moderado
medido com potência suficiente para o piso, e o intervalo continua a cruzar zero.

### 1.1 O N2, que é o desfecho que importa

| comparação | salto de capacidade | Δ em 3a′ | |
|---|---|---|---|
| `qwen3b` → `qwen7b` *(esta fase)* | **+145%** | **+0,400** | p=0,12, n.s. |
| `qwen7b` → `llama3.1:8b` *([5H](FASE-5H-RELATORIO.md))* | **+5%** | **+0,700** | p=0,0002 |

**Se a capacidade fosse o motor, o salto de 145% teria de render mais do que o de
5%. Rende menos, e nem significativamente.** O ganho da 5H não é de capacidade.

> **O que isto não é, e estava escrito no §3.1 antes de medir.** Não trato
> `0,700 − 0,400 = 0,300` como a parte «de família». As duas comparações não estão
> na mesma escala, não há garantia de linearidade na capacidade, e uma delas é
> n.s. **O argumento é a ordenação, não a subtracção.**

### 1.2 A contaminação declarada inflacionava, na direcção prevista

O §2.3 nomeou 5 itens do braço Q cujo texto eu tinha impresso nesta sessão, e
declarou que o viés **inflacionaria o Δ**. Ao pontuar **reconheci 4 deles** —
`N11` pelo texto todo, `N23`, `N48` e `N58` pela última linha.

| | Δ | IC95% | p |
|---|---|---|---|
| **primário**, sem os 5 pares | **+0,400** | [−0,08; +0,88] | **0,1185** |
| sensibilidade, com os 30 | +0,467 | [+0,03; +0,90] | 0,0636 |

**Excluí-los baixou o Δ e afastou o p de 0,05, exactamente como previsto.** A
exclusão pré-registada mudou a leitura: com os 30, o IC excluiria zero. É o caso
em que declarar a contaminação antes serviu para alguma coisa — se tivesse
decidido depois, teria tido duas leituras à escolha.

---

## 2. N4 — o 3b perde também na forma, e por onde

Mecânico, sem avaliador, com o critério calibrado na [5K](FASE-5K-RELATORIO.md):

| | KS ao Caeiro real | mediana de versos |
|---|---|---|
| **T** = `qwen2.5:3b` | **0,383** | **8,0** |
| **Q** = `qwen2.5:7b` | 0,288 | 13,5 |
| *Caeiro real* | — | *11,5* |
| *p95 do nulo a n=30* | *0,197* | |

Nenhum dos dois cabe no intervalo de amostragem do poeta. O 3b está mais longe e
escreve mais curto.

**E uma coincidência que vale nomear:** a mediana do `qwen2.5:3b` é **8,0** e a do
`llama3.1:8b` é **7,5** ([5M](FASE-5M-RELATORIO.md)), contra **13,5** do
`qwen2.5:7b`. **Escrever curto é partilhado pelo qwen pequeno e pelo llama**, logo
não é assinatura de família — é mais consistente com ser o que acontece quando a
instrução de comprimento da persona não pega.

### 2.1 O 3b como critério, e a ressalva que o torna incomparável

Com a âncora **nova** da [5L](FASE-5L.md) (sem contagem de versos): Δ(Q − T) =
**+0,520**, IC95% [+0,16; +0,88], **p=0,0490**. O 7b bate o 3b na forma julgada à
mão.

Era secundário e não é portão. **E não se compara com nenhum 3b da 5H** — a
âncora mudou a 2026-10-06 e a nota de compatibilidade está no §3 da
[5L](FASE-5L.md).

---

## 3. O bónus, que é o resultado mais incómodo da fase

O braço Q foi pontuado **três vezes**, às cegas, com a **mesma** âncora: por R1 e
R2 da [5H](FASE-5H-RELATORIO.md) (a mesma sessão, em 2026-10-06) e por mim nesta
fase, **noutra sessão**, nos mesmos 30 itens.

| | média 3a′ | distribuição 0 / 1 / 2 |
|---|---|---|
| **R1** — a sessão que escreveu o protocolo **e a âncora** | **0,50** | **20 / 5 / 5** |
| **R2** — segundo avaliador da 5H, cego ao desenho | **1,00** | 9 / 12 / 9 |
| **R3** — eu, nesta fase, outra sessão | **0,97** | 13 / 5 / 12 |

| par | κ linear | concordância exacta |
|---|---|---|
| **R1 – R2** *(a mesma sessão)* | **+0,464** | 57% |
| R1 – R3 *(sessões distintas)* | +0,512 | 60% |
| **R2 – R3** *(sessões distintas)* | **+0,607** | **63%** |

**Duas coisas saem daqui, e apontam em sentidos opostos.**

**A boa.** A ameaça de **erro correlacionado** que a [5B](FASE-5B-RELATORIO.md)
nomeou — «são sessões do mesmo modelo a ler as mesmas âncoras» — **não se
confirma**: a concordância **entre** sessões (0,512 e 0,607) é **igual ou melhor**
que a concordância **dentro** da mesma sessão (0,464). Se houvesse erro
correlacionado por sessão, esperava-se o contrário. É a primeira vez que a
sequência mediu isto.

**A má, e é sobre todos os níveis publicados.** O **R1 é o discrepante**: pontuou
**0,50** onde dois leitores independentes pontuaram 1,00 e 0,97 — metade. E R1 é
o avaliador que **escreveu a âncora**. Nos mesmos 30 itens, 20 zeros contra 9 e
13.

> **A consequência, dita sem dramatizar.** Um Δ **emparelhado** sobrevive a um
> desvio sistemático de nível, porque o desvio cancela na diferença — logo o
> **+0,700 da 5H** não fica em causa por isto, e a 5H reportou-o em três leituras
> precisamente para o proteger. **O que fica em causa são os níveis absolutos de
> 3a′** publicados ao longo da sequência: «o Caeiro dá 0,0 de mediana», «R2
> pontuou o dobro de R1». Lidos como propriedades do gerador, são **em parte
> propriedades do avaliador**, e o factor é de **dois**.

---

## 4. O que isto autoriza, e o que não

**Autoriza atribuir o resultado da 5H à família e não à capacidade**, dentro da
gama medida. É o N2, e é a pergunta do passo 18.

**Não autoriza dizer que a capacidade é irrelevante.** O N1 falha por não
atingir o limiar, não por o efeito ser zero: o ponto estimado é **+0,400** a
favor do maior, com 11 pares contra 4. A leitura certa é «**não se mostrou** que
145% de capacidade melhorem o 3a′», e não «mostrou-se que não melhoram» — o
precedente é o I2 da [5I](FASE-5I-RELATORIO.md).

**Não autoriza usar o 3b em produção.** Perde em 3a′ (ponto estimado), perde no
3b à mão (p=0,049) e perde na forma mecânica (N4). O que **ganha** é velocidade —
**19,2 s contra 35,5 s** de mediana, ~1,8× — e isso não entra em portão nenhum,
como o §4.4 declarou.

**Não decide a troca de modelo**, que continua bloqueada no **passo 25** (uma
âncora 3a′ por voz).

**Não separa capacidade de família dentro da família llama.** O `llama3.1:3b`
não está instalado. «É família» significa **«não é capacidade na família qwen,
nesta gama»** — o §3.2 já o dizia.

**E não é uma medição de dois avaliadores.** Esta fase tem **um** (eu), contra os
dois de todas as fases desde a 5B. O §3 mostra que isso importa: o nível depende
do avaliador por um factor de dois. O Δ emparelhado é mais robusto, mas a fase é
mais fraca nesse eixo do que as anteriores, e é uma limitação e não uma ressalva.

### O que fica na mesa

1. **O passo 25** continua a ser o que bloqueia: uma âncora 3a′ por voz.
2. **Um nível de referência para o 3a′.** O §3 mostra que o nível não é
   reprodutível entre avaliadores. Pontuar os **poemas reais** de Caeiro com a
   âncora da 5F — como a [5E](FASE-5E-RELATORIO.md) fez com a antiga — dava uma
   âncora de nível a que cada sessão se podia calibrar. É barato e resolve a
   parte má do §3.
3. **O passo 24** (corrigir as personas), que a [5M §3.1](FASE-5M-RELATORIO.md)
   já tem com predição direccional, e a que o §2 desta fase acrescenta uma
   observação: escrever curto é partilhado pelo qwen pequeno e pelo llama.
4. **A fronteira 1/2 da âncora**, pela terceira fase seguida. O `N40` desta folha
   nega o sentido oculto quatro vezes e depois diz «a luz do sol que canta»: dei
   1, e um avaliador podia dar 2. É o passo 12 do `CONTROLO.md`, intocado.

> **A lição, e é sobre o que um portão consegue proteger.** O §2.3 declarou a
> contaminação **antes** de eu pontuar, com os ids escritos, e isso valeu
> exactamente o que devia valer: ao pontuar reconheci 4 dos 5 itens, a exclusão
> baixou o Δ de +0,467 para +0,400 e afastou o p de 0,05. **Se tivesse decidido a
> exclusão depois de ver os dois números, teria tido duas leituras à escolha e
> nenhuma razão pública para preferir uma.** É o caso mais limpo da sequência em
> que pré-registar mudou a conclusão, e mudou-a contra o que eu esperava.
