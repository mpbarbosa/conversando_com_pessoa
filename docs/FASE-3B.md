# Fase 3B — reordenação, segunda tentativa: fechar o conjunto de candidatos

Protocolo. Reabre a [Fase 3](FASE-3.md), que terminou **inconclusiva**, com o
número que a [Fase 4](FASE-4-RELATORIO.md) produziu.

**Objectivo:** decidir a reordenação com uma medição cujo sinal não dependa de
qual gabarito se escolhe.

---

## 1. Correcção ao que eu próprio escrevi há um dia

O `CONTROLO.md` §6, que escrevi no fim da Fase 4, dava três razões para reabrir
isto. **Duas estavam erradas**, e o relatório da Fase 3 já dizia porquê:

| o que escrevi | o que a Fase 3 mediu |
|---|---|
| «a premissa da iGPU estava errada, e um cross-encoder é prefill puro» | irrelevante: «**a latência não é o obstáculo**» — `bge-m3` com 8 candidatos truncados a 120 tokens custa **2,0 s** contra ~30 s de geração |
| «o orçamento de latência pode mudar de forma» | o portão de 6 s foi cumprido por três configurações; nenhuma decisão ficou pendente de latência |
| «o ganho está quantificado» | **esta é a única que se mantém** |

Pior: a iGPU não se aplica mesmo. Os 6x de prefill foram medidos no backend
Vulkan do Ollama, e um cross-encoder corre em PyTorch, que não usa Vulkan. Era
preciso ONNX ou OpenVINO para lá chegar — e não é preciso, porque 2,0 s já
cabem.

**O obstáculo da Fase 3 foi o instrumento, não o modelo nem a máquina.** É esse
que esta fase ataca.

---

## 2. O problema, enunciado com precisão

A Fase 3 mediu o mesmo reranker contra três gabaritos e obteve três respostas:

| gabarito | candidatos julgados | denso | + rerank | Δ |
|---|---|---|---|---|
| original (denso + BM25 top-5) | 176 | 0,719 | 0,671 | **−0,048** |
| + candidatos da fusão | 209 | 0,677 | 0,678 | +0,001 |
| ampliado (tudo) | 291 | 0,638 | 0,712 | **+0,074** |

A causa é uma só: **um poema não julgado conta 0**. Logo o gabarito favorece
quem o construiu, e cada sistema novo que se mede obriga a ampliá-lo, o que
muda o número de todos os anteriores. O pool era **aberto**: crescia com cada
sistema testado.

### 2.1 A correcção: fechar o pool na fase de recuperação

Um reranker que opera sobre o **top-20 do denso** só pode promover documentos
desse top-20. Se **todos** os documentos do top-20 estiverem julgados, então:

1. nenhum documento que o reranker promova pode contar 0 por falta de
   julgamento — o viés que deu os −0,048 desaparece;
2. o pool deixa de depender de que sistemas se testam, porque é definido pela
   **recuperação**, que não muda;
3. o oráculo@20 deixa de ser um limite inferior e passa a ser exacto.

Medido: no top-20 denso das 20 perguntas julgadas há **370 poemas únicos**, dos
quais **228 julgados e 142 não**. Fechar o pool custa **142 julgamentos**.

É um número conhecido e pequeno, e é a diferença entre uma fase que decide e
uma fase que volta a não decidir.

### 2.2 O que isto não resolve

- **O avaliador continua a ser um só, e sou eu.** A Fase 3 §4 nomeou isto; não
  se resolve aqui.
- **Rerankers que operem mais fundo que 20** voltam a abrir o pool. A escolha
  de 20 é a profundidade que a Fase 3 usou e fica fixada como fronteira.
- **O nDCG@5 do denso vai descer outra vez**, porque o ideal cresce com cada
  nota 2 nova. É o comportamento correcto, e esta é a última vez que desce por
  esta razão — depois disto o pool está fechado.

---

## 3. Predições, escritas antes de medir

Para que o resultado possa contrariar-me:

1. **O denso desce de 0,640 para algo entre 0,55 e 0,62.** 142 candidatos novos,
   e pela taxa histórica (84 notas 2 em 291 julgamentos ≈ 29%) espero ~40 notas 2
   novas.
2. **O oráculo@20 mantém-se acima de 0,90.** Ele mede a melhor reordenação
   possível; mais notas 2 no top-20 ajudam-no e mais notas 2 no ideal
   prejudicam-no, e espero que se cancelem em grande parte.
3. **O `bge-m3` com truncagem a 120 fica positivo**, entre +0,03 e +0,09. Os
   +0,074 do gabarito ampliado vinham em parte de pooling a seu favor; os
   −0,048 do original vinham de pooling contra ele. Espero o meio.
4. **O `apt@3` continua em 95% e continua a não discriminar.** Já foi 95% nos
   três gabaritos.

Se a predição 3 sair negativa, a reordenação morre com um número limpo, e isso é
uma conclusão — ao contrário da da Fase 3.

---

## 4. Passos

### Passo 1 — Fechar o pool (o trabalho desta fase)

Gerar a folha dos 142 candidatos não julgados, por id, sem revelar a posição no
ranking do denso. Julgar com a mesma rubrica da Fase 1 Passo 8: `2` responde bem,
`1` serviria se nada melhor houvesse, `0` não serve.

**Aceite:** os 142 julgados, e o gabarito a passar de 291 para 433 julgamentos
com o top-20 denso das 20 perguntas **completamente** coberto.

### Passo 2 — Remedir tudo no pool fechado

Denso, oráculo@20, e as configurações de reranker que a Fase 3 pôs no quadro —
`bge-m3` a 8 e 20 candidatos, truncado a 120 e 256, e o `MiniLM-L12` como
controlo negativo.

**Aceite:** uma tabela em que o Δ de cada reranker é calculado sobre um pool que
nenhum deles ajudou a construir.

### Passo 3 — Decidir

| | critério |
|---|---|
| integrar | Δ nDCG@5 ≥ +0,03, latência ≤ 6 s, e `apt@3` não desce |
| não integrar | Δ ≤ 0 |
| zona cinzenta | 0 < Δ < 0,03: registar e **não** integrar, porque a Fase 3 já mostrou que ganhos desta ordem não sobrevivem a mudar o gabarito |

### Passo 4 — Integrar ou arquivar, como a Fase 3 fez

Se integrar: ligado ao pipeline, latência visível no CLI, e `rerank.py` deixa de
estar fora do caminho de execução. Se não: o resultado negativo fica escrito e o
código continua fora do caminho, não desligado por configuração.

---

## 5. Riscos

| Risco | Sinal | Resposta |
|---|---|---|
| Julgo os 142 a favor do reranker sem querer | — | folha por id, sem posição nem sistema; e a maioria dos 142 vem do fundo do top-20, que nenhum sistema promoveu ainda |
| O nDCG@5 desce tanto que deixa de ser comparável com o histórico | denso < 0,55 | é esperado e documentado; o que vale é o Δ no pool fechado, não o nível |
| O ganho cai na zona cinzenta | 0 < Δ < 0,03 | o Passo 3 já decidiu: não integrar |
| A fronteira de 20 é arbitrária | um reranker quer top-50 | fica fixada aqui; mudá-la reabre o pool e exige novo julgamento |

---

## 6. Checklist

```
[ ] 1  folha dos 142 candidatos gerada, por id, sem revelar ranking
[ ] 2  142 julgados com a rubrica da Fase 1 Passo 8
[ ] 3  gabarito em 433 julgamentos, top-20 denso completamente coberto
[ ] 4  denso e oráculo@20 remedidos no pool fechado
[ ] 5  rerankers remedidos; Δ sobre pool que nenhum ajudou a construir
[ ] 6  predições do §3 confrontadas com o medido, uma a uma
[ ] 7  decisão pelo critério do Passo 3, incluindo a zona cinzenta
[ ] 8  integrado com latência à vista, ou arquivado fora do caminho
```
