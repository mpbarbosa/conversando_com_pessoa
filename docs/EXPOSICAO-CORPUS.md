# O corpus está no repositório público — levantamento

Levantado em 2026-10-19, só por leitura.

Todos os números abaixo vêm de um comando que acabou de correr, e o comando
está escrito ao lado. Onde não consegui estabelecer um facto, digo-o em vez de
estimar.

> ⚠️ **Duas frases deste cabeçalho caducaram, e ficam registadas em vez de
> apagadas** — é o hábito que as correcções 42 e 43 do
> [`CONTROLO.md`](CONTROLO.md) §4 acabaram de impor a este repositório, e seria
> absurdo não o aplicar ao documento que as motivou.
>
> 1. Dizia **«nada foi alterado: nem o repositório, nem o histórico, nem o
>    `.gitignore`, nem a visibilidade no GitHub»**. Era verdade quando foi
>    escrito. Desde então, e no mesmo dia: o `.gitignore` passou a excluir as
>    folhas de julgamento **por padrão** e não por nome (correcção **43**), e as
>    sete afirmações falsas do `README.md`, do `data/README.md`, do
>    `src/web/app.py`, do [`PRODUCAO.md`](PRODUCAO.md) e do `CONTROLO.md` §3 e
>    §5 foram corrigidas. **O histórico e a visibilidade continuam intactos**, e
>    **nada foi desversionado** — nem o corpus, nem a folha da fase 3B, nem os
>    cerca de onze ficheiros com versos. As opções C e D da §6 continuam por
>    decidir.
> 2. Dizia **«este ficheiro está no directório de rascunho da sessão, fora do
>    repositório, de propósito»**. Já não: está em `docs/`, versionado e
>    commitado a pedido do dono, para que o levantamento e as seis opções não
>    desapareçam com a sessão que os produziu. **A escolha de o pôr aqui é
>    dele**, e vale dizer o que ela implica: um documento que inventaria onde
>    está o material cujos termos de uso não estão confirmados passa a estar no
>    mesmo repositório público que o material. Fica neste commit e **não foi
>    empurrado** por esta sessão.

---

## 1. A afirmação que não se sustenta

`README.md`, secção *Corpus*:

> Os 2083 ficheiros **não estão no repositório**.

```
git ls-files data/pessoa_poems/ | wc -l          -> 2083
git ls-tree -r --name-only origin/main -- data/pessoa_poems/ | wc -l  -> 2083
git check-ignore -v data/pessoa_poems/poem_100.txt  -> (nada; sai 1)
gh repo view --json visibility                   -> "PUBLIC"
```

Estão versionados, estão no `origin/main`, não há regra de ignore que os cubra,
e o repositório é **público**.

| | |
|---|---|
| ficheiros | **2083** |
| volume | **1,3 MB** (1 365 981 bytes) |
| palavras | **241 250** |
| entrou em | **`396cca7`, 2025-10-24** — «Major project restructure and documentation» |
| commits que tocaram o corpus | **1** (só esse) |
| repositório criado | 2025-10-24 |
| público desde | a criação, tanto quanto consigo ver |

O repositório foi criado a 2025-10-24 e o corpus entrou **no segundo commit do
mesmo dia**. Ou seja: esteve lá desde o princípio, há **cerca de doze meses**, e
a mensagem do commit que o trouxe não o menciona.

---

## 2. A assimetria, que é o achado e não o acidente

O `.gitignore` deste repositório trata o assunto com cuidado explícito. Linhas
228–235:

> **Folhas de julgamento: contêm os poemas INTEIROS** (34.384 palavras, ~16% do
> corpo do corpus) porque um avaliador humano precisa de os ler para dar nota.
> **Fora do repositório público enquanto os termos de uso do Arquivo Pessoa não
> estiverem confirmados** — ver `data/README.md`, secção «Situação de direitos».

E funciona: as duas folhas nomeadas existem **só em disco**.

```
docs/fase-0/06b-folha-julgamento.md   55,4 KB   em disco, NÃO versionada  ✔
docs/fase-1/08-folha-julgamento.md   132,1 KB   em disco, NÃO versionada  ✔
```

Portanto o projecto gastou trabalho deliberado a manter **16%** do corpus fora
de um repositório público — enquanto **100%** dele já lá estava, há um ano, pela
porta ao lado. As duas decisões foram tomadas pela mesma pessoa, no mesmo
repositório, sobre o mesmo risco de direitos.

**E o mecanismo de exclusão é a causa da segunda falha.** O `.gitignore` exclui
as folhas **por nome exacto de ficheiro**, não por padrão. Logo uma folha de uma
fase posterior não está coberta:

```
git ls-files | grep -i folha-julgamento
  -> docs/fase-3b/01-folha-julgamento.md      VERSIONADA
grep -n folha-julgamento .gitignore
  -> 234: docs/fase-1/08-folha-julgamento.md
  -> 235: docs/fase-0/06b-folha-julgamento.md
```

`docs/fase-3b/01-folha-julgamento.md`: **9 075 palavras, 50 KB, 126 poemas
nomeados**, versionada e pública. É exactamente a categoria de ficheiro que o
comentário acima diz que não pode estar lá.

---

## 3. Corpos de poemas noutros ficheiros versionados

Varredura de 400 poemas ao acaso (semente fixa), procurando 32 caracteres da 3.ª
linha não-vazia de cada um em todos os ficheiros versionados **fora** de
`data/pessoa_poems/`:

```
docs/FASE-0-RELATORIO.md
docs/fase-0/prompts-bench.json          2 903 palavras
docs/fase-0/smoke-set.json
docs/fase-3b/01-folha-julgamento.md     9 075 palavras, 126 poemas
docs/fase-5f/01-chave.json
docs/fase-5f/01-itens.md
docs/fase-5o/01-amostras.json
docs/fase-5o/01-chave.json
docs/fase-5o/01-itens.md
src/guard.py
tests/test_guard.py
```

Uma varredura anterior, de 150 poemas, apanhou também
`docs/fase-1/07-plagio.json`, `docs/fase-1/07b-plagio-preventivo.json`,
`docs/fase-5d/01-chave.json`, `docs/fase-5d/01-itens.md`, `README.md`,
`docs/FASE-0.md`, `docs/FASE-6.md` e `tests/test_plagio.py`.

**Esta lista não é exaustiva** e não a apresento como tal: amostrei poemas, não
varri os 2083 contra todos os ficheiros. O que ela estabelece é a **forma** do
problema — os ficheiros de *itens*, *chave* e *amostras* das fases de medição
guardam o contexto que foi dado ao modelo, e esse contexto **é** o corpo dos
poemas recuperados. Remover `data/pessoa_poems/` não limpa isto.

Os casos em `src/guard.py` e nos testes são provavelmente amostras curtas de
uma linha ou duas, de outra natureza que uma folha de julgamento inteira.
**Não os classifiquei um a um.**

---

## 4. Alcance: o número que muda a natureza do problema

```
gh repo view --json forkCount,stargazerCount   -> 0 forks, 0 estrelas
gh api .../traffic/views                       -> 0 visitas, 0 únicas
gh api .../traffic/clones                      -> 289 clones, 128 ÚNICOS
```

**289 clones de 128 origens distintas, nas últimas duas semanas.** Zero visitas
no mesmo período.

O que isto permite concluir, e o que não permite:

- **Permite**: o conteúdo saiu. Qualquer remédio que reescreva o histórico ou
  torne o repositório privado **não recupera** o que 128 origens já têm.
- **Não permite** dizer quem. A métrica de clones do GitHub inclui os clones do
  próprio dono, os de CI e os de mirrors automáticos. 128 únicos com **zero
  visitas** é o padrão típico de clonagem automatizada (arquivadores,
  espelhos, recolha para treino), não de pessoas a navegar — mas **não consigo
  distinguir**, e a API não o diz.
- **Não permite** saber o alcance antes destes 14 dias. A janela de tráfego do
  GitHub é de duas semanas e não há histórico mais antigo. O repositório é
  público há **cerca de um ano**.

---

## 5. O que esta descoberta invalida

Não é só o `README`. A premissa propaga-se ao desenho do código e ao plano de
publicação, e em todos estes sítios está escrita como facto:

| onde | o que afirma | estado |
|---|---|---|
| `README.md` §Corpus | «os 2083 ficheiros não estão no repositório» | **falso** |
| `data/README.md` | os termos não estão confirmados «e devem ser confirmados antes de qualquer distribuição do corpus» | a distribuição **já aconteceu**, há um ano |
| `src/web/app.py`, cabeçalho | o servidor escuta em `127.0.0.1` porque «expor isto à rede era publicar esse material» | o material **já está publicado**; a protecção defende uma porta enquanto a outra está aberta |
| Portão **I7** da Fase 6 | «o corpo do poema não sai da máquina» | continua verdadeiro **sobre o servidor**, e irrelevante quanto ao corpus |
| `docs/PRODUCAO.md` §0.1, saída B | publicar sem o passo 9 evita «publicar transcrições» | **o raciocínio cai**: o que a rota serviria já está no repositório público |
| `docs/CONTROLO.md` §3 | a saída B como resposta ao bloqueio de direitos | mesma coisa |
| `docs/CONTROLO.md` §5 «Sobre direitos» | «**Sem impedimento legal.**» | é uma afirmação sobre a obra; a questão aberta era sempre a **transcrição**, e `data/README.md` sabe-o |

**E duas destas são minhas.** Escrevi o `PRODUCAO.md` §0.1 e a entrada do
`CONTROLO.md` §3 afirmando que o corpus não estava no repositório. Tomei-o do
`README` e **não verifiquei**, num documento cujo assunto era precisamente o
risco de publicar o corpus. Um `git ls-files data/pessoa_poems/ | wc -l` tinha
resolvido, e é o primeiro comando que devia ter corrido.

---

## 6. As opções

Nenhuma é minha para escolher: a decisão é de direitos e é do dono. Apresento-as
com o que cada uma faz **e o que não faz**.

### A — Confirmar os termos do Arquivo Pessoa

A saída A do `PRODUCAO.md` §0.1, que já estava nomeada como «em curso».

É **a única que resolve** em vez de mitigar. Se os termos permitirem
redistribuição, não houve exposição nenhuma — houve um `README` errado durante
um ano, o que é um defeito de documentação e não de direitos. Se não
permitirem, é o que diz qual das opções abaixo é necessária.

`data/README.md` registou a tentativa falhada de 2026-10-01 (sem resposta na
porta 443, `http=000`). **Não voltei a tentar** nesta sessão.

### B — Tornar o repositório privado

Imediato, reversível, e para a clonagem a partir de agora.

**Não recupera os 128.** E tem um custo que vale pesar: este repositório é, em
boa parte, um registo metodológico — 10 correcções a afirmações próprias,
defeitos nos próprios instrumentos, resultados negativos publicados. Fechá-lo
esconde isso junto com o corpus.

### C — Remover o corpus do `HEAD`, mantendo o histórico

`git rm -r --cached data/pessoa_poems/` mais regra no `.gitignore`.

Honesto sobre o que faz: um clone novo deixa de trazer o corpus na árvore de
trabalho, e **o histórico continua a servi-lo** a quem souber pedir um commit
antigo. É meia medida, e é importante não a vender como mais do que é.

### D — Reescrever o histórico para excisar o corpus

Tecnicamente **tratável de forma invulgar**: um só commit (`396cca7`) tocou o
corpus, o que é o melhor caso para um `git filter-repo`.

Três custos, e o terceiro é o que normalmente decide:

1. **Não recupera os 128 clones.** Nada recupera.
2. **O GitHub mantém objectos desreferenciados acessíveis** por SHA depois de um
   `push --force`, até o suporte fazer uma limpeza a pedido. Reescrever sem
   abrir o pedido ao suporte deixa o conteúdo acessível a quem tenha o SHA.
3. **Reescreve todos os SHA posteriores**, e este repositório **cita SHA na
   documentação** — o `CONTROLO.md` refere, por exemplo, a adenda `742b9f6`.
   Todas essas referências passam a apontar para nada. Num repositório cujo
   valor é o registo, isso é dano real.

### E — Corrigir o mecanismo, independentemente das outras

O `.gitignore` exclui folhas de julgamento **por nome exacto**, e foi por isso
que a da fase 3B passou. Uma regra por padrão (`*folha-julgamento*`, ou
`docs/**/0*-itens.md`) cobre as fases futuras, que é o que um nome não faz.

Isto é verdade e vale fazer **qualquer que seja** a decisão sobre A–D, e é a
única da lista que não depende de uma questão de direitos.

### F — Corrigir as afirmações falsas nos documentos

As sete linhas da §5. É independente de tudo o resto e, no hábito desta casa,
entra no `CONTROLO.md` §4 como correcção numerada — incluindo a minha, que é a
que escreveu o risco num documento sobre o risco.

---

## 7. O que eu recomendaria, se me pedissem

Por ordem, e com a razão:

1. **E e F agora** — não dependem de nenhuma questão aberta, e deixar um
   `README` a afirmar o contrário do que o repositório faz é o estado pior de
   todos: é a afirmação que me enganou a mim.
2. **A em paralelo**, porque é a única que fecha a questão.
3. **B se quiser parar a clonagem enquanto A não responde** — barato e
   reversível, e a métrica de clones justifica-o.
4. **C e D só depois de A responder.** Se os termos permitirem redistribuição,
   nenhuma delas é necessária; se não permitirem, a escolha entre meia medida e
   reescrita com perda de referências faz-se com essa informação, e não antes.

E uma nota sobre ordem que é fácil de inverter: **D antes de A** gasta o dano
às referências do `CONTROLO.md` possivelmente sem necessidade nenhuma.
