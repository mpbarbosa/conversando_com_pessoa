# Fase 0 / Passo 5 — avaliação do teste de voz

Rubrica de [`FASE-0.md`](../FASE-0.md) §5.3, 0–2 por critério, máximo 10:
1 **é verso?** · 2 **português europeu?** · 3 **a voz pedida?** ·
4 **cumpre a forma?** · 5 **vale como poema?**

## Enviesamentos desta avaliação — ler antes dos números

**Avaliador único**, e o mesmo que desenhou a rubrica e escreveu os prompts.
Não é medição intersubjectiva.

**O cego falhou.** O meu próprio protocolo (§5.3) diz «pontue sem olhar o nome
do modelo, se conseguir». Não consegui: li as amostras agrupadas por modelo,
como o ficheiro as grava. Portanto sabia a origem de cada amostra ao pontuar.
É um viés real e não corrigível a posteriori. Para o repetir às cegas seria
preciso reescrever o `teste_voz.py` para gravar as amostras embaralhadas com um
mapa separado.

**Cobertura:** 22 das 30 amostras (8 do 3B, 7 do 7B, 7 do 8B). As restantes não
foram lidas.

---

## Pontuações

### qwen2.5:3b-instruct-q4_K_M

| amostra | verso | PT-PT | voz | forma | poema | total |
|---|---|---|---|---|---|---|
| caeiro #1 | 2 | 1 | 1 | 1 | 1 | **6** |
| caeiro #2 | 2 | 1 | 1 | 1 | 0 | **5** |
| campos #1 | 2 | 0 | 1 | 2 | 1 | **6** |
| campos #2 | 2 | 0 | 1 | 1 | 0 | **4** |
| reis #1 | 2 | 0 | 0 | 0 | 0 | **2** |
| ortonimo #1 | 2 | 1 | 1 | 0 | 1 | **5** |
| pt_pt #1 | 2 | 1 | — | 1 | 1 | **5** |
| pt_pt #2 | 2 | 0 | — | 0 | 0 | **2** |

**Mediana: 5/10.** Falhas concretas: repete o texto do prompt de volta
(caeiro #2 devolve «sem lhes atribuir significado oculto», que era instrução
minha); «a gente vê» e «grama» (brasileirismos); «Devei, sem te dar razão»
(agramatical); mistura tratamento «tu» com «seus» na mesma estrofe; ignora por
completo a forma de Reis.

### qwen2.5:7b-instruct-q4_K_M

| amostra | verso | PT-PT | voz | forma | poema | total |
|---|---|---|---|---|---|---|
| caeiro #1 | 2 | 2 | 2 | 2 | 1 | **9** |
| caeiro #2 | 2 | 2 | 2 | 2 | 1 | **9** |
| campos #1 | 2 | 0 | 2 | 2 | 1 | **7** |
| reis #1 | 2 | 1 | 1 | 1 | 0 | **5** |
| ortonimo #1 | 2 | 2 | 2 | 1 | 1 | **8** |
| pt_pt #1 | 2 | 0 | — | 1 | 1 | **4** |
| pt_pt #2 | 2 | 0 | — | 1 | 1 | **4** |

**Mediana: 7/10.** O melhor em compreensão de voz: «É só uma árvore, ao fim do
dia» e «Nenhuma ideia lhe cai, / Nenhuma sombra de pensamento» são Caeiro a
sério. Falhas: **«fumaça»** (PT-PT é «fumo») e colocação proclítica brasileira
sistemática («te arrebela», «te segura», «se desenha»); salada agramatical em
Reis («ouro alvina», «a cada esplêndido», «a frias»).

### llama3.1:8b-instruct-q4_K_M

| amostra | verso | PT-PT | voz | forma | poema | total |
|---|---|---|---|---|---|---|
| caeiro #1 | 2 | 2 | 2 | 2 | 2 | **10** |
| caeiro #2 | 2 | 2 | 2 | 2 | 2 | **10** |
| campos #1 | 1 | 1 | 1 | 1 | 0 | **4** |
| reis #1 | 2 | 1 | 1 | 1 | 1 | **6** |
| ortonimo #1 | 2 | 1 | 2 | 1 | 1 | **7** |
| pt_pt #1 | 2 | 1 | — | 2 | 2 | **7** |
| pt_pt #2 | 1 | 1 | — | 0 | 0 | **2** |

**Mediana: 7/10**, com a maior variância dos três.

O melhor e o pior do conjunto. As duas amostras de Caeiro são as únicas 10/10
de toda a Fase 0, e são o único caso em que um modelo usou **colocação
enclítica correcta de português europeu**: «estende-se», «bate-lhe»,
«acorda-lhe», «aquecendo-a». A amostra 2 é Caeiro puro — «a árvore está ali»,
sem metafísica, verso livre curto.

Mas **degenera em ciclo** no prompt de Campos, que é o mais longo:

```
um estar que se torna, sem estar, sem estar,
um estar que se esvai, sem estar, sem presença,
um estar que se torna, sem estar, sem estar,
```

Causa provável: não defini `repeat_penalty` nas opções do Ollama — só
`temperature`, `top_p`, `seed`, `num_predict` e `num_thread`. É um defeito do
meu arranque, não necessariamente do modelo. **Corrigir antes de concluir
qualquer coisa sobre o 8B em forma longa.**

---

## Critérios eliminatórios (§7.2)

> «Critério 2 (PT-PT) com 0 em mais de metade das amostras → o modelo escreve
> em PT-BR.» · «Critério 1 (é verso?) com 0 na maioria → fatal.»

| modelo | zeros em PT-PT | zeros em verso | elimina? |
|---|---|---|---|
| 3B | 4 de 8 (metade) | 0 | não, mas na fronteira |
| 7B | 3 de 7 | 0 | não |
| 8B | 0 de 7 | 0 | não |

**Nenhum modelo é eliminado.** Mas a colocação pronominal brasileira aparece
nos três e, no 7B, com marcador lexical (`fumaça`). O prompt atenua, não
resolve: é um candidato natural a few-shot de época na Fase 1.

## Portão de qualidade (§7.2)

| modelo | mediana | leitura |
|---|---|---|
| **8B llama3.1** | **7/10** | voz local viável |
| **7B qwen2.5** | **7/10** | voz local viável |
| 3B qwen2.5 | 5/10 | marginal |

**A qualidade passa o portão. A latência é que não.**
