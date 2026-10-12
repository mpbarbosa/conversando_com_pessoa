# Documentos temáticos

Um documento entra aqui quando reúne, **por assunto**, o que está espalhado por
várias fases e por vários ficheiros de `src/`.

**Não são fases.** Não têm protocolo, não têm portões, não decidem nada e não
medem nada de novo. O que medem já foi medido, e cada número tem de vir de um
ficheiro citado — ou, quando é novo (uma contagem contra o corpus, feita ao
escrever), tem de dizer que foi feito ali.

| | |
|---|---|
| [`TOKENIZACAO.md`](TOKENIZACAO.md) | os dois tokenizadores e porque não são intercambiáveis; de onde vêm o 480 e o 300; o *cache* de KV; e o que custou a omissão do `contador()` |
| [`STOPWORDS.md`](STOPWORDS.md) | as três listas e porque só uma remove; `guard-PT − lexical = {'mais', 'não'}`; e o limiar de língua que estava certo com o instrumento errado |
| [`LEMATIZACAO.md`](LEMATIZACAO.md) | **não houve**, e é decisão nomeada na Fase 2 com custo medido na 5C; mais o sítio onde lematizar teria destruído o instrumento de rima da 5V |

## Duas regras, que vêm do resto do projecto

**Dizem onde eu errei.** Um documento temático que só conte a versão que ficou de
pé é propaganda. Os três que aqui estão nomeiam as correcções do
[`CONTROLO.md`](../CONTROLO.md) §4 que lhes dizem respeito — a 16, a 30 e a 33 na
tokenização e a 12 nas *stopwords* — e a lematização diz onde a sua própria
ausência custou, que é a 5C.

**Não substituem o `CONTROLO.md`.** O §4 continua a ser o registo das
correcções, e o §2 o das fases. Isto é uma leitura transversal, para quem chega
e quer entender um assunto sem reconstruir vinte fases pela ordem em que
aconteceram.
