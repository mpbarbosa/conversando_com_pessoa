# A guarda de plágio: o maior efeito de produto do projecto

Documento temático, escrito em 2026-10-12, décimo da série. **Não é uma fase**, e
é **reunião e não descoberta** — os números todos já existiam, espalhados pelo
[`plagio.py`](../../src/plagio.py), pelo [`pipeline.py`](../../src/pipeline.py) e
por três fases.

**É aqui que está o número mais forte de todo o projecto: 82% → 0%.**

---

## 1. O problema: o modelo copia o contexto que lhe dão

O sistema é RAG. Põe poemas de Pessoa no prompt para o modelo reconhecer o
registo — e o modelo trata-os como material a repetir. Medido em 24 respostas
reais:

| | sem a regra preventiva | com a regra no `system` |
|---|---|---|
| mediana de versos copiados | **82%** | **0%** |
| respostas acima de 20% | **16/24 (67%)** | **3/24 (12%)** |

Por voz, sem a regra: **Caeiro 93%**, **ortónimo 100%**.

---

## 2. A métrica: n-gramas não servem, e o caso que o provou

O plano especificava «maior sobreposição de n-gramas (n=8)». A primeira
travessia completa do *pipeline* mostrou que não serve:

```
Nunca sei como se pode achar um poente triste.      <- 0,94 do contexto
Só se for por não ser madrugada.                    <- 0,76
Ambos existem; cada um seu caminho.                 <- 0,75
```

> «Três de oito versos eram cópia, e a sobreposição de 8-gramas era **2%**. A
> cópia é por **paráfrase ao nível do verso** — troca uma palavra, encurta,
> reordena — e n-gramas literais **não a vêem**.»

**É o mesmo problema que obrigou a trocar de métrica na deduplicação**, onde o
Jaccard de 4-gramas dava **0,457** a duas versões do mesmo poema e **0,480** a
poemas distintos — ou seja, ordenava-os ao contrário.

**A métrica que ficou:** fracção dos versos da **saída** que têm par próximo no
contexto, por similaridade de sequência (`difflib`) ao nível do verso.
**Assimétrica de propósito** — «o que interessa é quanto da resposta é
emprestado, não quanto do contexto foi usado».

### 2.1 Os três limiares, e os três são calibrados

| | valor | como foi fixado |
|---|---|---|
| `LIMIAR_VERSO` | **0,72** | há uma **lacuna limpa** em 24 respostas reais: as que copiam dão mediana 0,91 e **mínimo 0,79**; as limpas dão mediana 0,55 e **máximo 0,70**. 0,72 cai no meio, e «nenhuma resposta limpa é apanhada por engano» |
| `LIMIAR_FRACAO` | **0,10** | 0,0 e 0,10 dão o mesmo resultado (5 de 24), logo a regra efectiva é «**qualquer verso copiado dispara uma repetição**» |
| `MIN_PALAVRAS` | **3** | «E mais nada.» coincide por acidente e não é plágio |

E o `LIMIAR_FRACAO` tem o custo medido, não estimado:

```
0,10 -> 21% de repetição -> 33,8 s      0,20 -> 12% -> 31,5 s
0,40 ->  8% -> 30,3 s
```

> «Escolhido 0,10: os casos entre 0,10 e 0,20 são cópias literais de versos
> distintivos … e 33,8 s continua dentro do limite de 45 s. **Ser estrito é
> barato aqui.**»

---

## 3. Três mecanismos, em ordem de custo

| | onde | custo | o que faz |
|---|---|---|---|
| **1. regra preventiva** | `REGRAS_NAO_COPIAR` no `system` | **zero** por pergunta | é ela que faz os 82% → 0%, e vive no prefixo em *cache* |
| **2. reforço corrective** | `REFORCO`, acrescentado ao `user` na repetição | ~28 s | «na tentativa anterior **copiaste** versos dos poemas que te foram dados» |
| **3. troca de contexto** | `_repetir_sem` | incluído no 2 | **tira do contexto os poemas de que o modelo copiou** |

**A regra preventiva faz quase todo o trabalho**, e custa zero porque o `system`
é prefixo estável em *cache* (ver [`TOKENIZACAO.md`](TOKENIZACAO.md) §3). A
repetição é rede de segurança: dispara em ~21% dos casos e corrigiu 3 de 3.

**Custo médio esperado: 1,21 gerações, ou ~34 s.**

### 3.1 O terceiro mecanismo existe por um caso observado

> «à pergunta «você conhece o senhor fernando pessoa?»: a primeira tentativa
> copiou **9 de 14 versos** do `poem_1164`, um deles à letra por substituição de
> palavras — `Natureza`→`Silêncio`, `brisa`→`luz`, `perceber`→`escutar`. A
> repetição, **com o mesmo contexto**, voltou **ao mesmo poema**: 5 de 14
> versos, máximo 0,82. Duas rejeições, ~80 s, e o utilizador interrompeu.»

E o raciocínio é o que distingue este mecanismo de «pedir melhor»:

> «O `REFORCO` já diz «não o reescrevas trocando uma palavra», e o modelo
> ignorou-o. Pedir melhor comportamento sobre o mesmo contexto é pedir ao modelo
> que **resista ao que lhe foi posto à frente**; tirar o poema do contexto
> **remove a ocasião**.»

**E não é só encolher:** o `montar` corta o contexto quando o orçamento acaba,
logo deixar um poema de fora **deixa entrar o seguinte** da recuperação. O modelo
recebe material novo, não menos material.

### 3.2 Com duas ressalvas que são de desenho

**O plágio é comparado contra tudo o que já foi mostrado no turno**, não só
contra o contexto da tentativa corrente — «tirar um poema do prompt não torna
aceitável devolvê-lo ao utilizador».

**E se não sobrar nenhum poema, mantém-se o contexto original**, porque «sem
contexto a resposta perde o fundamento, e um reforço textual é melhor que nada».

---

## 4. E o terceiro mecanismo contaminou cinco fases de medição

É a parte que este documento existe para ligar, e foi a
[5Y](../FASE-5Y-RELATORIO.md) que a descobriu.

**O `_repetir_sem` troca o contexto. Logo, numa fase emparelhada, um braço que
repetiu tem prompt diferente de um que não repetiu** — e a repetição é causada
pelo tratamento. **Não é um confundidor: é um mediador.**

| fase | células contaminadas |
|---|---|
| 5G | **40%** |
| 5B | 23% · **5M** 19% · **5H** 17% · 5X 15% · 5U 12% · 5W 10% · 5I 7% |

A auditoria verificou as conclusões: **o `+0,700` da 5H sobrevive** (`+0,660` nas
25 células limpas, p=0,0013) e com ele a troca de modelo em produção; **a célula
`reis/L` da 5M inverte** e cai.

E o [passo 43](../CONTROLO.md) corrigiu o que era corrigível: o `Turno` passou a
guardar **todas** as tentativas, para que a análise primária possa olhar para a
**primeira** — cujo prompt é idêntico entre braços por construção.

> **A lição é sobre bom produto.** O `_repetir_sem` foi desenhado contra um ciclo
> real e observado, e funciona. **E é por funcionar que estraga a medição:**
> quanto melhor o sistema se auto-corrige, menos a saída final revela do que o
> tratamento fez.

---

## 5. Resumo

1. **82% → 0%** de versos copiados é o maior efeito de produto do projecto, e
   vem da **regra preventiva**, que custa **zero** por pergunta.
2. **N-gramas não vêem esta cópia**: 3 de 8 versos copiados com sobreposição de
   8-gramas de **2%**, porque a cópia é por paráfrase ao nível do verso.
3. **Os três limiares são calibrados em dados reais**, e o do verso cai numa
   **lacuna limpa** entre 0,70 e 0,79.
4. **Ser estrito é barato**: 0,10 custa 21% de repetição e 33,8 s, dentro do
   limite de 45 s.
5. **O terceiro mecanismo remove a ocasião em vez de pedir melhor
   comportamento** — e deixa entrar material novo, não menos material.
6. **E é esse mecanismo que contaminou 7% a 40% das células de cinco fases**,
   porque é accionado pelo tratamento. O [passo 43](../CONTROLO.md) deu-lhe a
   observabilidade que faltava.

**Ficheiros:** [`src/plagio.py`](../../src/plagio.py) ·
[`src/pipeline.py`](../../src/pipeline.py) ·
[`src/voices.py`](../../src/voices.py) (`REGRAS_NAO_COPIAR`) ·
[`FASE-5Y-RELATORIO.md`](../FASE-5Y-RELATORIO.md) ·
`docs/fase-1/07-RELATORIO-PLAGIO.md`.
