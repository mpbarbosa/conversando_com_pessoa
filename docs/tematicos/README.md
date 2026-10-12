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
| [`ENTIDADES.md`](ENTIDADES.md) | não há NER, e não faria falta: sete entidades num mundo fechado. O difícil é `Reis`/`Campos`/`Pessoa` serem palavras comuns — e **uma medição nova**: o detector rejeita 1,61% dos poemas autênticos |
| [`SENTIMENTO.md`](SENTIMENTO.md) | não houve, e **não serviria**: as regras 3 e 4 da âncora dependem de negação e retracção, a que um léxico de afecto é cego. Mais a composição das 40 palavras do FAS, que é medição nova |
| [`DADOS.md`](DADOS.md) | três famílias heterogéneas; os **153 poemas ingleses que tratei como ruído**, em três lugares do código; e o esquema dos meus próprios dados a derivar de 27 para 18 campos a meio da sequência |
| [`TRANSFERENCIA.md`](TRANSFERENCIA.md) | **nada foi treinado e é tudo transferência**: cinco modelos pré-treinados, o reranker do MS MARCO como controlo negativo, e o que transferiu ser **família e não escala** |
| [`AUMENTO.md`](AUMENTO.md) | não há, porque não há treino — mas há **três sínteses**, e o que as separa é o propósito: duas construíram nulos e funcionaram, uma construiu um instrumento e falhou |
| [`MULTITAREFA.md`](MULTITAREFA.md) | um modelo, duas tarefas opostas (verso a 0,9 e classificação a 0,0), e o custo da partilha medido **antes** de mexer: **72% → 68%**. Mais o mesmo padrão a vazar no `Chunk` e a não vazar no encoder |
| [`PLAGIO.md`](PLAGIO.md) | **o maior efeito de produto do projecto: 82% → 0%**. Porque n-gramas não vêem esta cópia, os três limiares calibrados, e o mecanismo que remove a ocasião em vez de pedir melhor comportamento — e que contaminou cinco fases |
| [`BUSCA.md`](BUSCA.md) | **produção usa só o denso**: a Fase 2 é um resultado negativo declarado (+0,004, e o `apt@3` cai). Porque o RRF funde por ordem, porque o `k=60` não foi afinado, e porque não há FAISS |
| [`PERSONA.md`](PERSONA.md) | **descrever a postura produz a voz; nomear produz pastiche** — o achado fundador. E **três das suas regras não descrevem o poeta**, as três em produção |

## Duas regras, que vêm do resto do projecto

**Dizem onde eu errei.** Um documento temático que só conte a versão que ficou de
pé é propaganda. Os doze que aqui estão nomeiam as correcções do
[`CONTROLO.md`](../CONTROLO.md) §4 que lhes dizem respeito — a 16, a 30 e a 33 na
tokenização e a 12 nas *stopwords* — e a lematização diz onde a sua própria
ausência custou, que é a 5C.

**Não substituem o `CONTROLO.md`.** O §4 continua a ser o registo das
correcções, e o §2 o das fases. Isto é uma leitura transversal, para quem chega
e quer entender um assunto sem reconstruir vinte fases pela ordem em que
aconteceram.
