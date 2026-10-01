# A repetição voltava ao mesmo poema

Medido em 2026-10-01, `qwen2.5:7b-instruct-q4_K_M`, temperatura 0,9, sem semente.
Script: [`bench_repeticao.py`](bench_repeticao.py) · dados: [`09-repeticao.json`](09-repeticao.json)

## O que foi observado

A correr o chatbot, à pergunta «você conhece o senhor fernando pessoa?», voz
Caeiro. A primeira tentativa copiou **9 de 14 versos** do `poem_1164`, um deles
à letra, por substituição de palavras:

| similaridade | a resposta | `poem_1164` |
|---|---|---|
| **1,00** | Não sei bem como nem o quê... | Não sei bem como nem o quê... |
| 0,96 | Assim, porque assim **a** sinto, é que é meu dever | Assim, porque assim **o** sinto, é que é meu dever |
| 0,90 | E eu fico confuso, perturbado, querendo **escutar** | …querendo **perceber** |
| 0,81 | Só tenho que sentir **paz** porque é **luz** | Só tenho que sentir **agrado** porque é **brisa** |

`Natureza`→`Silêncio`, `brisa`→`luz`, `quente`→`noite`, `perceber`→`escutar`.

A repetição, com o mesmo contexto e o `REFORCO`, voltou **ao mesmo poema**:
5/14, máximo 0,82. Duas rejeições, ~80 s, e o utilizador interrompeu.

O `REFORCO` diz, literalmente, «não reutilizes nenhum verso nem o reescrevas
trocando uma palavra». O modelo ignorou-o duas vezes. **Pedir melhor
comportamento sobre o mesmo contexto é pedir ao modelo que resista ao que lhe
foi posto à frente.**

## Desenho da medição, e o primeiro desenho que falhou

A primeira versão fazia correr a 1.ª tentativa e só comparava as políticas se
ela plagiasse. Resultado: **0 de 3 perguntas plagiaram** — incluindo esta, com o
mesmo `poem_1164` no contexto. Com temperatura 0,9 e sem semente o plágio é
estocástico; o que foi visto no terminal era uma amostra, não um comportamento
determinista. Condicionar a medição a re-observar um evento raro desperdiça
gerações.

A versão válida toma o ponto de partida **da observação** — sabe-se que copiou
do `poem_1164` — e corre só as repetições, 5 em cada política:

- **A (antes)** contexto `poem_1164`, `poem_384`
- **B (agora)** contexto `poem_1130`, `poem_384`

O `poem_1130` não é um lugar vazio: `montar` corta o contexto quando o orçamento
de 300 tokens acaba, logo tirar um poema **deixa entrar o seguinte da
recuperação**. O modelo recebe material novo, não menos material.

Os versos são comparados contra **tudo o que foi mostrado no turno**, e não só
contra o contexto da tentativa corrente: tirar um poema do prompt não torna
aceitável devolvê-lo ao utilizador.

## Resultado

| política | plagiou | reincidiu no `poem_1164` | fracção média | máx média |
|---|---|---|---|---|
| A | **4/5** | **3/5** | 0,311 | 0,890 |
| B | **1/5** | **0/5** | 0,178 | 0,661 |

Mas o resumo esconde a forma da distribuição, que é o que interessa:

| | A | B |
|---|---|---|
| corridas com **zero** versos copiados | **0/5** | **4/5** |
| copiou do poema proibido | 3/5 | 0/5 |
| copiou de outro poema | 2/5 | 1/5 |
| fracção nas corridas que falharam | 0,08 – 0,57 | **0,89** |

**O A copia sempre algo.** Nenhuma das cinco corridas ficou a zero: a fracção vai
de 0,083 a 0,571, e três das cinco foram ao poema que o reforço proibia.

**O B ou não copia nada, ou copia por inteiro.** Quatro corridas com zero versos
copiados, e uma com 89% e máximo 1,00 — do `poem_1130`, o poema que acabou de
entrar no contexto.

## O que isto quer dizer, e o que não quer

**O mecanismo faz o que foi desenhado para fazer:** a reincidência no poema
copiado passa de 3/5 a 0/5. E o efeito agregado é real — 4/5 contra 1/5 de
rejeições, 0/5 contra 4/5 de respostas inteiramente próprias.

**Não remove a tendência, remove o atractor.** A falha única do B foi a mais
grave das dez corridas em fracção copiada. Tirar um poema do contexto não ensina
o modelo a não se encostar a um poema; tira-lhe aquele a que se estava a
encostar, e às vezes aparece outro. Com `MAX_TENTATIVAS = 2` não há terceira
ronda para tirar o segundo.

**n=5, uma pergunta, uma voz.** Chega para a decisão (B é melhor que A em todas
as métricas medidas) e não chega para uma taxa. O que falta medir: mais
perguntas, e se a relocação do atractor é frequente ou foi azar nesta.

Um número lateral, da corrida que falhou: **0 de 3 primeiras tentativas
plagiaram**, contra 1 de 1 na sessão do utilizador. O plágio não é o estado
normal destas respostas — é um evento. Isso enquadra o que esta correcção vale:
age só quando a primeira tentativa falha, e essa não é a maioria dos casos.
