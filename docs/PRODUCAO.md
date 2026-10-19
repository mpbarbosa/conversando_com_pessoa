# Produção — publicar da máquina de desenvolvimento, atrás de um túnel

Escrito em 2026-10-18, reescrito no mesmo dia. Duas decisões do dono fixam o
que este plano é:

1. **Saída B** (direitos): publica-se **sem o passo 9 da Fase 6** — as fontes
   saem como ids (`poem_1019`), e não há rota que devolva o corpo do poema.
2. **Saída D** (onde corre): a **máquina de desenvolvimento**, atrás de um
   **túnel gratuito**, sob a restrição de **não aumentar os custos actuais**.

Ambas estão registadas em [`CONTROLO.md`](CONTROLO.md) §3, com a data e com a
nota de que nenhuma das duas é consequência de uma medição.

> ⚠️ **A razão de ser da saída B cai, e o plano não a reescreve por isso.**
> Escolhi-a e escrevi-a a argumentar que não publicar o passo 9 evitava
> «publicar transcrições» cujos termos de uso não estão confirmados. Medido em
> 2026-10-19: **as transcrições já estão publicadas** — 2083 ficheiros,
> **241 250 palavras**, versionados em `396cca7` (2025-10-24) num repositório
> **público**, e o `data/README.md` registava a data de entrada enquanto o
> `README.md` afirmava o contrário. Correcção **42** do
> [`CONTROLO.md`](CONTROLO.md) §4.
>
> O que isto muda e o que não muda, porque não é tudo:
>
> - **A saída B continua a ser a decisão certa, por outra razão.** O §2.1
>   mostrou que ela não bastava e obrigou a escrever a retenção; o portão
>   **I7′** mede algo verdadeiro e que morde. Um serviço que não serve corpos é
>   melhor que um que serve, com ou sem repositório público.
> - **Mas deixou de ser uma protecção de direitos.** Era essa a função que eu
>   lhe dei no §0.1, e essa função não existe: o que o passo 9 serviria é o
>   que um `git clone` já traz. Chamar-lhe protecção de direitos depois de
>   saber isto seria a mesma confusão entre mecanismo e alcance que o §2 deste
>   plano identificou no portão I7.
> - **E o bloqueio que o §0.1 nomeava mudou de sítio.** Não é «não publicar o
>   serviço até confirmar os termos»; é que a publicação a confirmar aconteceu
>   há um ano, por outra porta. O levantamento e as opções estão feitos, e a
>   decisão sobre o repositório **está por tomar** — nada foi alterado no
>   histórico nem na visibilidade.

> ⚠️ **A primeira versão deste documento está retirada, e não foi guardada.**
> Foi escrita sobre o molde do repositório irmão `portal_brasileirao` — EC2,
> S3, OIDC, SSM, nginx, certbot, pacote promovido — e recomendava um EC2 de
> CPU grande; a restrição de custo eliminou-a horas depois. **O texto não está
> no histórico do git**: o ficheiro foi reescrito antes de qualquer commit,
> logo a versão de EC2 existiu só dentro daquela sessão e perdeu-se. Registo-o
> em vez de o omitir, porque é uma perda e não uma decisão: o que sobrevive
> dela é o que está resumido abaixo e em [`CONTROLO.md`](CONTROLO.md) §3 — e a
> conclusão que importa, **a saída D não é esse molde mais barato**. Não é um
> deploy reduzido. É outra coisa, com outros riscos, e o maior deles não é
> técnico nem de custo: é a sequência de medição deste repositório (§3).
>
> O que aquela versão continha e aqui não cabe, para quem o quiser refazer:
> as quatro peças do irmão que quebram este serviço se copiadas verbatim (o
> `proxy_read_timeout 30s` a cortar respostas de 34 s; o `proxy_buffering` a
> desfazer o fluxo NDJSON sem dar erro; o `gzip_types` sem
> `application/x-ndjson`; e `HEALTH_ATTEMPTS=30` curto para um arranque que
> pode tocar o índice). Todas quatro só se aplicam a um deploy com nginx, que
> a saída D não tem.

> ⚠️ **Procedência.** Os números do hardware desta máquina foram lidos **nela**
> hoje: `nproc` = 14, 30 GiB de RAM, 22 GiB disponíveis, `Linger=no`, Ollama em
> `~/.local/ollama/bin/ollama` e **fora do `PATH`**, sem `cloudflared` nem
> `tailscale` instalados, sem unidade de utilizador para o serviço. As
> latências (34 s por resposta, ~18 s até ao 1.º verso, 14–17 tok/s) vêm das
> Fases 0 a 5 **nesta mesma máquina**, e é essa coincidência que dá a esta
> saída a sua única vantagem real: **não há nada a remedir**. Nada aqui foi
> publicado nem testado através de um túnel.

---

## 0. O que a saída D ganha, e o que a torna difícil

**Ganha o que a opção do EC2 nunca ia ter: o hardware é o hardware medido.**
Os 34 s, os 18 s até ao 1.º verso, os 14–17 tok/s, o *throttling* a 101 °C — é
tudo desta máquina. O portão P1 da versão retirada existia para descobrir a
latência num servidor desconhecido; aqui não há portão a cumprir, porque a
resposta está nos relatórios. 14 núcleos e 22 GiB disponíveis contra os ~6–7
GiB que o modelo e o encoder pedem: **a máquina serve, e isso está medido, não
estimado.**

E o custo em nuvem é zero: um túnel de saída na camada gratuita não abre portas,
não aluga máquina e não cobra.

**O que a torna difícil é uma só coisa, e não é o túnel.** É que esta máquina
tem outro trabalho — é onde este repositório faz as suas medições — e a
afirmação de abertura do `README` depende delas:

> Não há aqui nenhuma decisão por preferência: as que importam têm número por
> trás.

Um URL público nesta máquina põe carga não registada no mesmo CPU que produz
esses números. A §3 é sobre isso, e é a secção que importa.

---

## 1. Isto não é «produção» no sentido do repositório irmão, e o documento não o vai dizer

O `portal_brasileirao` tem um documento de ambiente de produção que abre com a
frase certa: «a **máquina de desenvolvimento é outra máquina**», e fecha com
«não assuma que o comportamento de desenvolvimento, as portas, a versão do Node
ou a capacidade da máquina coincidem com este servidor».

Aqui **dev e prod são o mesmo computador**. O documento do irmão foi escrito
para evitar exactamente a confusão que a saída D institucionaliza. Então as
palavras mudam, e não por pudor:

| | |
|---|---|
| **o que é** | um serviço **pessoal, publicado**, na máquina do dono, acessível por URL, com disponibilidade igual à do portátil estar ligado e desocupado |
| **o que não é** | um ambiente de produção. Não há segunda máquina, não há recuo para um lançamento anterior noutro disco, não há CI a implantar, e não há separação entre quem edita o código e o que está a servir |
| **como se chama no repositório** | «o serviço público», e nunca «produção». `docs/production-environment-memory.md` **não** se escreve aqui: não há ambiente de produção para documentar |

O que **transfere** do irmão é a disciplina, não a infra-estrutura:

| ideia do irmão | aqui |
|---|---|
| verificar pela saúde do serviço, **nunca** pelo emblema do CI | §6: `/api/health` com o `sha` |
| o `sha` nomeia o commit de que o código a correr foi lançado | §6, lido do próprio checkout |
| recuar é instalar bytes que já existem, e **ensaia-se** | §5.2: o recuo é `git checkout` de uma etiqueta, e o ensaio é um portão |
| o estado que nenhum script regenera identifica-se e copia-se | §5.3: `data/sessoes.db`, quando o passo 8 da Fase 6 existir |

O que **não** transfere, e é a maior parte: EC2, S3 como unidade de lançamento,
OIDC, SSM, nginx, certbot, `rsync --delete`, `npm ci --omit=dev`,
`07_install_release.sh`, `rollback.yml`, agente CloudWatch. Nada disso tem
função numa máquina sem rede de entrada e sem segunda cópia. **Copiar esses
scriptes para aqui era cargo cult**, e a versão retirada deste documento tinha
três páginas a adaptá-los.

---

## 2. O túnel faz o portão I7 passar e tira a protecção que ele codifica

Este é o primeiro dos dois achados do plano, e é da família que este
repositório conhece bem: **o mecanismo continua a dizer «certo» depois de
deixar de proteger.**

O portão **I7** da Fase 6 afirma: «`GET /api/poema/{id}` recusa pedidos de fora
de `127.0.0.1`; o servidor **não escuta noutro interface sem sinalizador
explícito**». O cabeçalho de `src/web/app.py` dizia porquê — a interface serve
corpos de poemas de um corpus cujos termos de uso não estão confirmados, e
«expor isto à rede era publicar esse material».

> ⚠️ **Essa razão caiu, e o argumento desta secção não depende dela.** O corpus
> **está** no repositório público desde 2025-10-24 (correcção **42**), logo o
> `bind` fechava esta porta enquanto a do repositório estava aberta, e o
> material que retinha é o mesmo que um `git clone` traz. O cabeçalho do
> `app.py` está corrigido. O que se segue continua a valer palavra por palavra,
> porque é sobre o **mecanismo** e não sobre os direitos: um portão que mede
> `bind` e afirma alcançabilidade continua a passar depois de deixar de medir o
> que afirma — e a correcção **40** mostrou que havia corpo a sair por três
> portas que nada disto cobria.

Um túnel não muda o `bind`. O `cloudflared` corre **nesta** máquina e liga-se
**de dentro** a `127.0.0.1:8000`. Portanto:

- o servidor continua a escutar em `127.0.0.1`,
- não há sinalizador explícito nenhum,
- o portão **I7 passa, literalmente, e continua a passar**,
- e o serviço está na internet.

A asserção estava a usar «escuta em `127.0.0.1`» como **medida** de «não é
alcançável de fora». Com um túnel, as duas deixam de ser a mesma coisa, e o
portão mede a que não importa.

**Isto não se resolve satisfazendo o I7. Resolve-se reescrevendo-o**, e a
reescrita é o passo 2 da §5:

> **I7′** — o corpo de um poema não sai desta máquina. Medido **de fora**:
> contra o URL público, `GET /api/poema/{id}` devolve 404 (a rota não existe,
> saída B) e nenhuma resposta de nenhuma outra rota contém uma linha de corpo
> de nenhum poema do corpus. O varrimento é o do portão **I6**, apontado ao
> fio HTTP em vez da base de dados.

E a decisão de desenho que o torna verdadeiro por construção, em vez de por
asserção: **a saída B não é «não construir o passo 9»**, é «o passo 9 não
existe enquanto houver túnel». Se um dia a saída A fechar e o passo 9 for
escrito, a rota nasce com a verificação de origem que o I7 original pedia — e
nessa altura o túnel passa a ser o problema, não a solução.

### 2.1 O passo 2, feito: a saída B não bastava, e o varrimento achou três portas

Escrito em 2026-10-19, depois do passo 2.

O raciocínio da §2 acima tinha um erro de omissão, e era confortável: dizia que
a saída B torna o I7′ «verdadeiro por construção», porque sem o passo 9 não há
rota que devolva corpo. **É verdade para a rota, e falso para o serviço.** O
`tests/test_i7.py` foi escrito a contar com uma passagem trivial e falhou em
três sítios — os três abertos **de propósito** pela Fase 6:

| # | por onde | porque é que a Fase 6 o abriu | medido |
|---|---|---|---|
| 1 | **os `fragmento` da tentativa plagiada** | §4.4: a tentativa rejeitada vai ao fio para o utilizador saber porque esperou 58 s em vez de 30 | **6 de 8 versos** do `poem_1005` no fio |
| 2 | **o evento `turno` da tentativa rejeitada**, com o texto inteiro | o mesmo §4.4, e a Fase 5Y sobre o que custa guardar só a última tentativa | os mesmos 6 |
| 3 | **`serial.verso_copiado`** | o comentário dizia «o verso **gerado** que copiou [...] sem o verso original» | verdade numa cópia com palavras trocadas; **falso à letra**, que é o caso em que o verso gerado **é** o original |

**O achado 1 é o que importa, e é de uma família que não se resolve a jusante.**
A tentativa sai **em fluxo, à medida que é gerada** — logo sai *antes* de a
guarda de plágio existir para a reprovar. Não há verificação no fim que a possa
apanhar: já saiu. É o parente exacto do que o `CONTROLO.md` §5 já registava
sobre o CLI («o streaming imprime antes de validar»), e o que muda com um túnel
é a consequência: ali o ecrã mostrava ao dono um verso que o dono tem no disco;
aqui publica-se.

**A correcção, e a decisão que ela obrigou a tomar.** `src/web/retencao.py`:
um filtro de fluxo **por linha**, que retém a linha cujo texto normalizado está
no corpus, e uma redacção genérica do `turno` já serializado. Fica em
`src/web/`, que é transporte — nada em `src/pipeline.py`, `src/guard.py` ou
`src/generation/`, como a §9 exige.

A decisão foi **o que retir**: a linha, e não o evento. Passar o I7′ deixando
de mandar a tentativa rejeitada era mais fácil e desfazia o §4.4, devolvendo o
utilizador aos 58 s sem explicação. Então o que sobrevive é tudo menos o verso:
`aprovado: false`, o veredicto, a fracção copiada, a lista de versos copiados —
com o campo `verso` vazio quando era o do corpus. O `test_i7.py` prende as
**duas** metades, porque proteger uma à custa da outra é regressão.

**O preço, contado e não estimado.** Protegem-se as linhas de 4 palavras ou
mais: 29 816 das 33 236 linhas distintas do corpus. Contra os **1 560 textos
gerados** que os dez `01-cru.jsonl` das Fases 5B a 5Z guardam — 16 866 linhas
de 4+ palavras —, a retenção acerta em **20 linhas (0,119%)**, em 12 textos, e
são **15 linhas distintas de 6 poemas**. Inspeccionadas uma a uma: **as 15 são
versos de Pessoa**, incluindo 8 linhas seguidas do `poem_3657` num texto só,
que é um poema inteiro reproduzido. **Zero falsos positivos em 1 560 textos
reais.**

**E o defeito do instrumento, que é o segundo deste portão.** A primeira versão
do varrimento partia a resposta por `\n` e comparava cada linha com o conjunto.
O fio é **NDJSON**: a mudança de linha de um verso é o par de caracteres `\n`
*dentro* de uma cadeia JSON, não uma linha do corpo HTTP. Partido assim, o fio
de uma geração inteira são seis linhas, e um verso no meio de uma delas nunca é
uma linha. **Com a retenção desligada em `app.py`, as oito asserções passaram
verdes.** Só a mutação o mostrou. Agora varre por subcadeia, no texto cru e nas
cadeias desserializadas — as duas, porque o cru não vê um verso com `"` dentro
e as cadeias não vêem corpo que viaje fora de um evento válido. Custa 19 ms por
resposta. O `CONTROLO.md` §4 ganha a entrada.

**O que o passo 2 não fecha.** A asserção plena do I7′ é «medido **de fora**,
contra o URL público», e não há URL: ele é o passo 6 sobre o passo 4. O que está
fixado é o varrimento contra a aplicação, que é a metade que apanha regressões;
a outra metade espera o túnel, e está escrita como pendente em vez de o portão
se dar por cumprido. Dar um portão por cumprido com metade da medição feita é
exactamente o que fez o I7 ser reescrito.

---

## 3. O conflito com a sequência de medição, que é o verdadeiro custo da saída D

O dono pediu explicitamente que esta secção existisse. É a mais importante do
documento.

### 3.1 O mecanismo que devia mediar o conflito **não existe**

O passo 7 da Fase 6 é o sentinela: `data/.medicao-a-correr`, verificado antes
de cada geração, reportado no `/api/estado`, com o portão **I8**. A Fase 6 está
no **passo 6 de 10**. O passo 7 **não está feito** — verificado hoje: zero
ocorrências de `medicao-a-correr` em `src/` e em `tests/`.

> ✅ **Deixou de ser verdade no mesmo dia**, e a medição acima fica como foi
> feita em vez de ser reescrita. O passo 7 está **feito** desde 2026-10-18:
> `src/web/sentinela.py`, com as duas correcções do §4 abaixo dentro — caminho
> **absoluto** e a asserção dos **dois checkouts** no portão I8.
>
> ✅ **E o guarda de alcance também, no mesmo dia.** O que a frase seguinte
> deste §3 diz — que o sentinela «resolve metade do problema» — era verdade
> enquanto só existia o guarda de **pedido** (o 409). O **passo 5 desta lista
> está feito** (2026-10-18): o ajudante `with` para e arranca o túnel, por
> indirecção (`src/web/tunel.py`), e a ordem está verificada por mutação. Logo
> o remédio em vigor **deixou de ser o 409** e passou a ser o túnel a cair, que
> é o que o §3.3 pede. O que **falta** para o D3 passar de facto é a unidade:
> não há túnel instalado nesta máquina, e por isso o túnel por omissão é o
> `TunelAusente` — declarado, e não silencioso. O §3.2 a seguir fica como foi
> escrito, porque é o argumento que fez o passo 5 existir.

O que existe é o trinco, e `src/web/app.py` já diz, em letra própria, o que ele
não cobre:

> ⚠️ O trinco é um `asyncio.Lock`, logo é **por processo**. Não protege contra
> um `gerar_amostras.py` de uma fase a falar com o mesmo Ollama, e esse é o
> modo de falha caro: o campo `segundos` do `01-cru.jsonl` da fase fica
> **ininterpretável**. O interbloqueio entre processos é o **passo 7**; até lá,
> **não correr o servidor com uma medição a decorrer é disciplina e não
> mecanismo**.

«Disciplina e não mecanismo» é uma salvaguarda aceitável quando o único cliente
do servidor é a pessoa que também lança as medições: ela sabe, e fecha a aba.
**Com um URL público, os clientes são estranhos que não sabem que há uma
medição a decorrer, e a disciplina deixa de ter onde se aplicar.**

Portanto: **o passo 7 da Fase 6 passa a ser pré-requisito do túnel**, e não um
passo posterior. Inverte a ordem do plano da Fase 6, que o punha antes da
persistência «porque é o que a torna segura de ter ligada» — a saída D leva
essa frase ao seu limite.

### 3.2 E o sentinela, como está especificado, resolve metade do problema

O I8 mede uma coisa: com o ficheiro presente, `POST /api/perguntar` devolve
**409** nomeando a fase e o PID, e os `segundos` de 10 gerações do servidor e de
10 de um script **não se sobrepõem no tempo**. Isso protege **a medição do
servidor**.

Não protege nada na direcção inversa, e sob a saída D a direcção inversa é a que
dói:

**(a) O público não chega ao sentinela a tempo.** O sentinela é verificado antes
da geração — bem. Mas o protocolo de calibração da Fase 0 §3.2 não pede
exclusividade do Ollama: pede exclusividade **do CPU**.

> **Fechar tudo o resto.** Navegador, IDE, contentores. Um Chrome com vinte abas
> consome os mesmos núcleos.
>
> **60 segundos de pausa** entre configurações, para o chip arrefecer.

Um pedido público que chega na pausa de 60 s não gera nada — e aquece o chip. O
`/api/estado` responde, a página serve-se, o encoder pode carregar. O
*throttling* térmico desta máquina foi medido **até 101 °C**, e a regra da casa
é «se as 3 corridas mostrarem tok/s em queda monotónica, isso **é** o sinal de
throttling térmico — registar o facto em vez de tirar a média e esconder». Sob a
saída D, essa queda monotónica passa a ter **duas** causas possíveis e
indistinguíveis: o chip, ou um estranho.

**(b) E o que se perde não se recupera depois.** Esta é a parte que a torna
grave em vez de inconveniente. Lendo um `01-cru.jsonl` dentro de seis meses, não
há como saber se uma célula lenta foi térmica ou foi tráfego. É o padrão que
este repositório já pagou uma vez, e está registado em `CONTROLO.md` como
«defeito encontrado nos meus próprios instrumentos»: o cache de KV reaproveitado
entre repetições de um *benchmark* **reportou prefill a 25 625 tok/s e invalidou
4 horas de dados**. A causa foi a mesma — uma variável não controlada no
instrumento, descoberta depois.

**(c) Na direcção do público, o 409 é a resposta errada.** As medições deste
repositório não duram segundos. A construção do índice é **383 s**; a Fase 5Z
são 60 amostras a ~34 s, meia hora só de geração; o enriquecimento que a Fase 4
vetou estava orçamentado em **3,2 a 7,5 horas**. Um serviço público que devolve
409 durante sete horas, nomeando «a fase e o PID» a quem perguntou por que é que
o fim do dia é melancólico, não está a ser honesto: está avariado com uma
mensagem interna.

### 3.3 A mitigação: o remédio do sentinela é parar o túnel, não devolver 409

A correcção é pequena e muda a natureza do mecanismo. **O sentinela deixa de ser
só um guarda de pedido e passa a ser um guarda de alcance.**

| | o I8 como está | o I8 sob a saída D |
|---|---|---|
| quem lê o ficheiro | `POST /api/perguntar` | **também** a unidade do túnel |
| o que acontece ao público | 409 com a fase e o PID | **o túnel desliga-se**: o visitante recebe a página de erro do fornecedor do túnel, que é a verdade («isto está fora de serviço»), e **não consome CPU desta máquina** |
| o que acontece ao servidor | continua a correr | continua a correr, local, para o dono |
| o que fica escrito | nada | **a janela**: início e fim de cada período sem túnel, no registo da fase |

Três peças, portanto, e as três são passos da §5:

1. **O passo 7 da Fase 6, como está especificado** — o ficheiro, a verificação,
   o `/api/estado`, o ajudante `with`. É pré-requisito, não é trabalho novo:
   está planeado e medido por um portão que já existe.
2. **O ajudante `with` passa a parar e a arrancar o túnel**, e não só a escrever
   o ficheiro. Uma fase de medição abre o contexto e o URL cai; fecha-o e volta.
   O dono não tem de se lembrar, que é a diferença entre mecanismo e disciplina.
   ✅ **Feito** em 2026-10-18 — ver o §3.4, que é onde ficam as três decisões de
   desenho que isto obrigou a tomar.
3. **A janela registada com as amostras.** Cada ficheiro de fase passa a trazer
   os instantes em que o túnel esteve de pé. É o que torna uma célula lenta
   interpretável por quem a ler depois — e é a lição das 4 horas invalidadas,
   aplicada antes de custar quatro horas.

### 3.4 O passo 5, feito: as três decisões que ele obrigou a tomar

Feito em 2026-10-18. `src/web/tunel.py` (novo) e o `medicao()` do
`src/web/sentinela.py`; 26 testes novos, em `tests/test_tunel.py` e na secção
D3 do `tests/test_sentinela.py`. **403 testes** (eram 377). Nada em `src/` fora
de `src/web/`.

**(a) O túnel entra por indirecção, e não como um `systemctl` em linha.** O
obstáculo é o facto do §5.1: **não há túnel instalado nesta máquina**, logo
este código foi escrito antes de haver o que parar. Um `systemctl --user stop`
em linha dentro do `medicao()` punha o mecanismo fora de alcance de um teste —
ou os testes mexiam nas unidades reais desta máquina, ou não verificavam nada.
Portanto o `medicao()` recebe um objecto que cumpre um `Tunel`, com uma
implementação real (`TunelSystemd`) e um duplo nos testes. Quando a unidade for
instalada — passo 4 — o trabalho é **nomeá-la** (`PESSOABOT_TUNEL`), e não
reescrever este código.

**(b) A ausência é declarada, e um nome errado não é ausência.** Sem
`PESSOABOT_TUNEL` há `TunelAusente`, que não faz nada e **diz** que não faz
nada: é o estado desta máquina hoje, e uma fase corre. Com a variável a nomear
uma unidade que não existe, **falha** — porque `systemctl --user stop` de uma
unidade inexistente devolve **0**, e sem verificar o `LoadState` isso dava
«túnel parado» com o URL de pé. É a correcção **39** outra vez («não dá erro:
dá respostas erradas»), agora com o público do outro lado.

**(c) Quando parar o túnel falha, a fase não arranca.** Esta é a decisão que o
§2.4 da Fase 6 **não** responde: aquele sentido único — «o servidor é que cede
à medição, nunca o contrário» — fala de quem cede entre o servidor e a fase, e
aqui quem pode ceder é a **medição**. Deixar uma fase correr com o túnel de pé
é precisamente o que invalida os dados que ela vai produzir. Decide a
assimetria de custos, que é a aritmética do §3.2 (b):

| | custo | recupera-se? |
|---|---|---|
| a fase **não arranca** | ler a mensagem e correr um comando | sim, repete-se |
| a fase arranca com o túnel de pé | até as **3,2–7,5 h** do orçamento do enriquecimento | **não**: daqui a seis meses, num `01-cru.jsonl`, uma célula lenta pode ser térmica ou pode ser um estranho |

Logo o `parar()` levanta, o `medicao()` **retira o sentinela que já tinha
escrito** — senão um túnel avariado deixava o `POST /api/perguntar` a devolver
409 por causa de uma fase que nunca começou, que é o 409 de sete horas do §3.2
(c) sem fase nenhuma do outro lado — e a fase não começa.

**E a direcção inversa é assimétrica de propósito:** quando **arrancar** falha,
no fim, a fase já correu e os dados são bons. Levantar ali trocava um resultado
válido por uma excepção, ou pior, tapava a excepção do corpo da fase (há um
teste para isso). O túnel em baixo é, além disso, a direcção segura e
**auto-anunciada** — o visitante recebe a página do fornecedor, o `/api/estado`
continua a servir o dono em local — logo avisa, com o nome da unidade e o
comando, e não levanta.

**A ordem, e que ela está verificada por mutação.** Parar vem imediatamente
depois do `escrever` e arrancar imediatamente antes do `limpar`, por fora: o
ficheiro já existe quando o URL cai e ainda existe quando ele volta, e **nunca
há um instante com túnel de pé e medição a correr**. Trocadas as duas chamadas,
caem os **três** testes da ordem e nenhum outro — verificado a correr, não
presumido.

**E o portão I4 não ganhou trabalho nenhum.** Ninguém pergunta nada ao túnel no
caminho do `GET /api/estado`: quem fala com a unidade é o `medicao()`, que
corre no processo da **fase** e nunca no do servidor. Os 7,9 µs sem ficheiro e
15,6 µs com ele continuam a descrever o que o I4 mede, e há um teste que cai se
alguém puser uma pergunta ao túnel no `a_correr()` ou no `componente()` — antes
de o I4 precisar de ser medido outra vez.

**O que o D3 ainda não pode medir.** O portão exige o URL a deixar de responder
em menos de 10 s e a voltar em menos de 30 s, com zero pedidos atendidos no
registo do túnel. Nada disso é mensurável sem unidade: **o D3 fica aberto**, e
o que está feito é o mecanismo que ele vai medir.

### 3.5 E uma regra que não é mecanismo nenhum, mas tem de ficar escrita

**Nenhuma fase de medição se corre com o túnel de pé**, e a partir do passo 7 isso
é imposto pelo ajudante. Mas há um caso que o ajudante não cobre e vale nomear:
o `pytest` são **377 testes, ~2 minutos**, e saturam o CPU. Correr a bateria de
testes não é uma fase de medição, não escreve sentinela, e aquece o chip tanto
como uma. Se a corrida seguinte for uma medição, os 60 s de pausa da Fase 0 §3.2
contam **depois dos testes**, não depois da edição.

---

## 4. Dois checkouts, e o defeito que isso cria no sentinela

O serviço público **não pode servir o checkout de trabalho**. É onde se edita;
um `git switch` a meio de uma fase, ou um passo 7 a meio de ser escrito, ficaria
no ar. Portanto duas cópias na mesma máquina:

| | onde | o que corre | `data/` |
|---|---|---|---|
| **trabalho** | `~/Documents/GitHub/conversando_com_pessoa` | o CLI, o `pytest`, as fases de medição | o `data/` actual |
| **serviço** | um segundo checkout, numa etiqueta fixa | só o `src/web/app.py` por `uvicorn` | o seu próprio `data/` |

Partilham o que é caro e imutável: **o Ollama e o modelo de 4,9 GB** (um
processo, uma cópia em memória) e o cache do Hugging Face para o encoder. O
índice são 7,0 MB e pode ser duplicado sem pensar.

> ⚠️ **A frase que estava aqui dizia que o `data/pessoa_poems/` «duplica-se ou
> liga-se por *symlink*, e não há razão de direitos para preferir uma das duas
> — já está fora do repositório nas duas». As duas metades são falsas desde a
> correcção 42:** os 2083 ficheiros **estão** versionados, logo um
> `git clone --local` traz-nos com os objectos ligados por `hardlink` e **não
> há nada para ligar nem para escolher**. O que o clone não traz são os
> artefactos ignorados — `corpus.jsonl` e `index.*`, 12,9 MB — e esses
> copiam-se, porque reconstruí-los custa 40 s e 383 s. Ver a §5.4.

**E aqui está o defeito**, que vale nomear porque o passo 7 ainda não está
escrito e portanto isto é entrada de desenho e não correcção — **e foi assim
que entrou**: o passo 7, escrito nesse mesmo dia, nasceu já com o caminho
absoluto, e está registado como correcção **39** no
[`CONTROLO.md`](CONTROLO.md) §4, a primeira dessa lista a ser apanhada antes de
custar algo:

> O sentinela está especificado como **`data/.medicao-a-correr`** — caminho
> **relativo ao checkout**. Com dois checkouts há **dois `data/`**, a fase
> escreve no seu e o serviço verifica o outro. **O ficheiro nunca é visto, o
> `/api/estado` diz que está tudo bem, e o mecanismo que existe para tornar o
> túnel seguro está silenciosamente desligado.**

É o modo de falha do manifesto do índice outra vez — «não dá erro: dá respostas
erradas» — e desta vez no instrumento que protege as medições.

A correcção, para entrar no passo 7 **antes** de ele ser escrito: o sentinela
vive num **caminho absoluto, único na máquina**, fora de qualquer checkout —
`~/.local/state/pessoabot/.medicao-a-correr` — com a variável
`PESSOABOT_SENTINELA` a poder sobrepô-lo para os testes. E o portão I8 ganha uma
asserção: **a fase escreve de um checkout e o servidor, no outro, vê-o.** Sem
essa asserção, o I8 passa nos testes (um processo, um directório) e falha na
máquina.

---

## 5. Os passos

A ordem é a das dependências. Os passos 1 e 2 são da Fase 6 e não deste plano —
estão aqui porque o túnel não deve existir antes deles.

| # | passo | entrega | portão |
|---|---|---|---|
| 1 | **Passo 7 da Fase 6**, com a correcção do caminho absoluto da §4: sentinela, verificação antes de cada geração, `/api/estado`, ajudante `with` | o servidor e uma medição deixam de se atropelar | **I8**, com a asserção dos dois checkouts |
| 2 | ✅ **feito** (2026-10-19) — **o portão I7 reescrito como I7′** (§2) e fixado por teste (`tests/test_i7.py`, 8 testes). **E a surpresa: a saída B não bastava.** O varrimento achou **três outras portas** por onde o corpo saía, e obrigou a escrever a retenção (`src/web/retencao.py`) — §2.1 | o portão volta a medir o que protege, e o corpo deixou de sair por onde ninguém olhava | **I7′**, na metade que não precisa do túnel |
| 3 | ✅ **feito** (2026-10-19) — **`/api/health`** (§6), com o `sha` lido **à importação** e a raiz derivada do módulo (§6.1) | uma rota que diz de que `sha` o serviço foi lançado, e não de que `sha` está o disco | **D1** ✅ |
| 4 | 🔶 **instalado** (2026-10-19), **D2 por medir** — **segundo checkout e unidades de utilizador** (§5.1): `pessoabot.service` e `ollama.service` em `systemctl --user`, com `loginctl enable-linger`. `src/web/unidades.py`, `src/web/instalar.py`, `src/web/__main__.py`, 17 testes (§5.4) | o serviço sobrevive a um logout e a um reinício | **D2**, e as duas metades dele **só o dono as pode correr** |
| 5 | ✅ **feito** (2026-10-18) — **o túnel ligado ao sentinela** (§3.3, peça 2; as decisões no §3.4): o ajudante `with` para e arranca a unidade, por indirecção, porque não há unidade. **Parar que falha ⇒ a fase não arranca** | o ajudante derruba e devolve o URL. **A unidade em si é o passo 4**, logo o D3 fica aberto | **D3**, ainda não mensurável |
| 6 | **Fechar o serviço a estranhos antes de o abrir** (§7): autenticação na camada gratuita do fornecedor do túnel, com lista de endereços de correio | o URL funciona para quem o dono convidar | **D4** |
| 7 | **A janela registada** (§3.3, peça 3): o ajudante escreve os instantes de túnel de pé no ficheiro da fase | uma célula lenta é interpretável daqui a seis meses | **D5** |
| 8 | **Recuo** (§5.2): o serviço corre numa etiqueta; recuar é `git checkout` da anterior e reiniciar a unidade. **Ensaiado** | recuar é um comando, e foi ensaiado | **D6** |
| 9 | **Limite de pedidos** (§7), e só então abrir ao público, se o dono quiser | um cliente em ciclo não nega o serviço nem mata as medições | **D7** |
| 10 | **Cópias de `data/sessoes.db`**, se e quando o passo 8 da Fase 6 existir (§5.3) | o estado dos utilizadores sobrevive | **D8** |
| 11 | **Fechar**: `README` (§8), `CONTROLO.md`, e `docs/producao/SERVICO.md` escrito **a partir da máquina**, com a proveniência de cada número | o serviço documentado | — |

Os passos 1–2 são o que torna o túnel defensável. Os 3–5 são o serviço. Os 6–9
são o que o torna seguro de deixar ligado. Os 10–11 fecham.

### 5.1 As unidades, e três factos desta máquina

Verificados hoje, nela:

- **`Linger=no`.** Unidades de utilizador morrem quando a sessão termina. Um
  serviço que cai ao fechar a sessão gráfica não é um serviço: `loginctl
  enable-linger` é o passo 4, e é a diferença entre «corre» e «fica a correr».
- **O Ollama está em `~/.local/ollama/bin/ollama` e fora do `PATH`.** Foi uma
  decisão da Fase 0 — instalado «em espaço de utilizador a partir do tarball
  oficial, sem `sudo` e sem serviço systemd — desvio deliberado ao `curl | sh`
  [...] por não haver razão para alterar o sistema numa fase de medição». Sob a
  saída D essa decisão **mantém-se** (continua a não haver razão para mexer no
  sistema), e o que muda é só que passa a haver uma unidade de **utilizador** a
  arrancá-lo, com o caminho absoluto escrito no `ExecStart`. Não se põe no
  `PATH`: isso mexia no ambiente do dono para resolver um problema da unidade.
- **Não há `cloudflared` nem `tailscale` instalados.** O túnel é software novo
  nesta máquina, e é a única dependência nova que a saída D traz.

E a dependência entre as unidades é a do plano da Fase 6, não mais forte:
`After=ollama.service` e **não `Requires=`**. O `/api/estado` foi desenhado para
reportar «Ollama em baixo» com o remédio em vez de o processo morrer, e o portão
**I3** mede-o. Uma dependência rígida desfazia uma decisão medida.

`OLLAMA_KEEP_ALIVE` longo, ou o modelo descarrega entre perguntas e a primeira
de cada ciclo paga o carregamento inteiro — num serviço com tráfego esparso, que
é o que isto vai ser, essa é **a latência típica** e não um caso de arranque.

### 5.2 Recuar, sem S3 e sem segunda máquina

O irmão recua instalando bytes que o S3 já tem. Aqui a unidade de lançamento é
**uma etiqueta do git**, e o recuo é `git checkout` da anterior no checkout do
serviço, mais `systemctl --user restart`. Mais simples, e com duas armadilhas que
o portão **D6** mede:

- **as dependências podem ter mudado** entre etiquetas, e o `pip install` do
  recuo tem de correr (é o mesmo motivo pelo qual o `06_redeploy.sh` do irmão
  corre `npm ci` no recuo e não só restaura o `dist/`);
- **o índice pode não corresponder.** O manifesto compara encoder, assinatura do
  corpus, contagem e ordem, e **devolve `None` em vez de reconstruir em
  silêncio**. Num recuo isso é o comportamento certo e a consequência é má: o
  serviço arranca e a primeira pergunta reconstrói o índice durante **383 s** de
  CPU saturado. Portanto o recuo **verifica o manifesto antes de reiniciar** e
  recusa-se se divergir — a única peça do plano retirado que sobrevive inteira.

### 5.3 O estado que nenhum script regenera

Hoje: **nenhum**. `data/sessoes.db` é o passo 8 da Fase 6 e não existe. O
corpus, o `corpus.jsonl` e o índice são todos reconstruíveis a partir dos 2083
ficheiros, e esses ~~não estão no repositório mas estão na máquina~~ **estão nos
dois** — versionados desde `396cca7` (2025-10-24), ver a correcção **42**. Para
este parágrafo a diferença é a favor: um checkout do serviço traz o corpus com
ele, logo não há nada a copiar à parte nem a buscar a um balde. Para tudo o
resto, é o §0.1.

Quando o passo 8 existir, `data/sessoes.db` passa a ser essa peça, no checkout
do **serviço** — e não no de trabalho. A cópia é um `sqlite3 .backup` num
temporizador de utilizador, e o que a torna uma cópia é o **ensaio de restauro**
(**D8**). O portão **I6** da Fase 6 — «a base não contém corpos de poemas», zero
acertos num varrimento — ganha aqui uma segunda função: é também o que diz que
esta cópia não é uma cópia do corpus, e portanto que pode ir para onde o corpus
não pode.

### 5.4 O passo 4, instalado: onde vive, o que custa, e as duas metades do D2

Escrito em 2026-10-19. `src/web/unidades.py` (as unidades),
`src/web/instalar.py` (a instalação, com `--ensaio`), `src/web/__main__.py` (o
`ExecStart`), `tests/test_unidades.py` com 17 testes.

**Onde vive:** `~/.local/share/pessoabot/servico`, debaixo do mesmo `pessoabot`
que o sentinela já usa (`~/.local/state/pessoabot/`), para quem procurar
encontrar as duas peças no mesmo sítio. O plano não tinha escolhido o sítio.

**O que custa em disco, medido nesta máquina:**

| | |
|---|---|
| `git clone --local` | os objectos vão por `hardlink`, e os **8,4 MB** de corpus versionado vêm com eles |
| `corpus.jsonl` + `index.*` | **12,9 MB**, copiados: estão no `.gitignore`, e reconstruí-los custava **40 s** e **383 s** |
| `.venv` próprio | **1,3 GB** |
| Ollama, modelo de 4,9 GB, cache do Hugging Face (11 GB) | **partilhados** |
| **total novo** | **~1,32 GB**, contra **108 GB** livres |

O `.venv` é próprio e não partilhado, e é decisão e não omissão: partilhar o do
checkout de trabalho deixava um `pip install` de desenvolvimento mudar, **nesse
instante**, o que o serviço corre — a acoplagem que o segundo checkout existe
para cortar. E o passo 8 corre `pip install` no recuo, logo o serviço tem de ter
onde o correr.

**Uma peça que o plano não previa: `python -m src.web`.** A unidade precisa de
um `ExecStart`, e se ele fosse `uvicorn src.web.app:app --host 127.0.0.1 --port
8000` o interface e a porta passavam a existir em **dois** sítios — as
constantes `HOST`/`PORTA` do `app.py`, que até aqui **não eram lidas por
ninguém**, e um ficheiro de unidade que nenhum teste lê. E o que divergia era
precisamente a decisão que o portão I7′ protege: um `--host 0.0.0.0` numa
unidade é o «copiado de um tutorial» que a Fase 6 listou como risco. Há um teste
a proibir `--host`, `--port` e `0.0.0.0` no ficheiro da unidade.

**As quatro decisões das unidades, e as quatro mutações que as prendem:**

| decisão | o que se perdia | mutação verificada |
|---|---|---|
| `ExecStart` **absoluto** | o Ollama está fora do `PATH` por decisão da Fase 0, e o `PATH` de uma unidade não é o do dono: `ExecStart=ollama serve` falha com «not found» depois de funcionar na consola | `ollama serve` solto → **3 testes falham**, um deles o do próprio `systemd-analyze` |
| `After=` e **não** `Requires=` | desfazia a decisão medida do portão I3: o `/api/estado` reporta «Ollama em baixo» com o remédio em vez de o processo morrer, e com `Requires=` um Ollama caído levava com ele a página que sabia explicar a avaria | `Requires=ollama.service` → falha |
| `WantedBy=default.target` | só `start` dava um serviço que corre hoje e não volta amanhã — «funciona e não fica a funcionar», que é o que o D2 nega | `graphical-session.target` → falha |
| nunca o checkout de **trabalho** | é a regra da §4, e a que um `--destino` distraído quebra | o instalador **recusa** com código 2, e há teste |

E o validador: **`systemd-analyze --user verify`**, o do próprio systemd, sobre
as unidades geradas. Um `configparser` diz que o ficheiro é um INI; só o systemd
diz que é uma unidade — e foi ele que apanhou o `ExecStart` não executável.

**As duas metades do D2, e porque é que esta sessão não as pode medir.** O
portão afirma que *fechar a sessão gráfica* e *reiniciar a máquina* deixam o
serviço de pé. Nenhuma das duas é coisa que um processo a correr dentro dessa
sessão possa fazer e ver o resultado. Então o que está feito é deixar a máquina
no estado em que o D2 é mensurável, e o instalador imprime os dois comandos que
o medem:

1. fechar a sessão gráfica, voltar a entrar, e `curl -s http://127.0.0.1:8000/api/health`;
2. reiniciar, e correr o mesmo `curl` **antes** de abrir a sessão gráfica — por
   SSH, ou num terminal virtual.

Em ambos o `sha` tem de ser o do checkout do **serviço**. Enquanto os dois não
forem corridos, o **D2 está por medir, e não cumprido** — e é por isso que a
tabela do §9 o marca 🔶 e não ✅.

⚠️ **Uma ressalva sobre o `systemctl --user` desta máquina:** responde
`degraded`, e já respondia **antes** deste passo. A unidade falhada é do snap
(`app-snap\x2duserd\x2dautostart@autostart.service`) e não deste repositório.
Fica escrito para que `degraded` não seja lido como consequência do passo 4
quando o D2 for medido.

---

## 6. `/api/health`, e porque é que o `/api/estado` não serve

`GET /api/estado` já existe e é bom no que faz: prontidão por componente, sem
carregar nada, com o portão **I4** a exigir resposta em menos de 100 ms
**durante** uma geração. Não serve de sonda de serviço, por duas razões:

1. **Não diz de onde o código veio.** É a lição do irmão: o `sha` estampado é a
   verificação forte, o `uptime` a fraca.
2. **`pronto` é `false` antes da primeira pergunta, por construção.** Está na
   docstring: «o índice só se verifica quando há corpus carregado, e o corpus só
   se carrega na 1.ª pergunta». Uma sonda que exigisse `pronto` reprovava todos
   os arranques saudáveis; uma que aceitasse `pronto: false` não verificava nada.
   O campo a ler é o `pode_perguntar`, que foi acrescentado precisamente por este
   defeito ter sido observado a correr.

Aqui o `sha` é mais simples que no irmão, porque **não há passo de construção e
há um checkout**: lê-se por `git rev-parse --short HEAD` no arranque, e
guarda-se. Sem CI a estampar nada.

```json
{"status":"ok","sha":"dfeec8a","etiqueta":"servico-2026-10-18",
 "builtAt":"2026-10-18T09:12:04Z","python":"3.12.3",
 "modelo":"llama3.1:8b-instruct-q4_K_M","indice":"aceito",
 "pode_perguntar":true,"medicao_a_correr":false}
```

- `python` de `sys.version_info` — o que o processo **reporta**, não o que um
  ficheiro diz que devia ser.
- `modelo` é o que está **configurado**; o `/api/estado` é que diz se o Ollama o
  tem. É a distinção que o irmão faz com `provider`.
- `indice`: o manifesto foi aceite, ou **qual** dos quatro campos divergiu. Lê-se
  de `diagnosticar_indice`/`manifesto_cru`, que já existem em
  `src/web/estado.py`.
- `medicao_a_correr`: o sentinela da §3. Num serviço cujo URL cai durante as
  medições, é o campo que explica a queda ao próprio dono.

### 6.1 O passo 3, feito: as duas decisões e os dois desvios ao exemplo

Escrito em 2026-10-19. `src/web/saude.py`, a rota em `src/web/app.py`,
`tests/test_saude.py` com 13 testes.

**Decisão 1: o `sha` lê-se à importação, e não por pedido.** Não por custo — são
**3,6 ms**, medidos. É porque o campo afirma *de que código este processo foi
lançado*, e um `git rev-parse` por pedido dizia a verdade sobre o disco e
**mentia sobre o processo**: depois de um `git checkout` no checkout do serviço,
o `uvicorn` continua a correr os módulos que já importou, e a sonda passava a
nomear código que não está em memória. Seria a forma exacta do que este plano
corrige em toda a parte — o mecanismo a dizer «certo» depois de deixar de
descrever o que protege —, e no sítio mais caro de todos, porque é esta sonda
que o passo 8 usa para confirmar um recuo. Consequência aceite e escrita:
**reiniciar é o que actualiza o `sha`**, que é como o recuo funciona de qualquer
maneira.

Isto não se mede com um cliente: os dois desenhos devolvem o mesmo `sha`
enquanto o `HEAD` não se mexer, e o errado só aparece com o serviço de pé e sem
ninguém a olhar. Fixa-se por **inspecção do código** — a rota não pode conter
chamada ao `git` —, com a disciplina que o portão I1 já usa para comparar as
duas chamadas a `Pipeline(...)`.

**Decisão 2: a raiz é derivada do módulo, não do `cwd`.** `RAIZ =
Path(__file__).resolve().parents[2]`. O `cwd` de uma unidade de utilizador é o
que o `WorkingDirectory` disser, e com **dois checkouts** (§4) um `git` do
directório errado respondia **com sucesso** e com o `sha` do checkout de
trabalho enquanto o serviço corria o outro. É palavra por palavra o defeito do
sentinela com o `data/.medicao-a-correr` relativo (`CONTROLO.md` §4 #39), e tem
a mesma correcção e o mesmo tipo de asserção: o teste lança um processo **dentro**
de um segundo checkout, construído de propósito com um `sha` diferente, e exige
que o `sha` que sai continue a ser o deste repositório. Verificado a morder:
com `RAIZ = Path.cwd()`, falha.

**Dois desvios ao exemplo da §6, registados em vez de feitos de passagem:**

| no exemplo | aqui | porquê |
|---|---|---|
| `builtAt` | **`commit_em`** | **não há passo de construção para datar** — é a premissa da saída D —, e o nome afirmava um que não existe; e o resto do fio deste repositório é português em `snake_case` (`pode_perguntar`, `medicao_a_correr`, `n_palavras`). O valor é a data do commit do `HEAD`, normalizada a UTC com `Z`: o `%cI` do git traz o desvio de quem fez o commit (`-03:00` nesta máquina), e duas sondas a comparar fusos comparam cadeias que diferem por motivo nenhum. **Não** é o instante do arranque: o `uptime` é a verificação fraca que a §6 recusa |
| `"indice": "aceito"` | **`"indice": {"aceito": …, "detalhe": …}`** | um cliente que queira o booleano não devia ter de ler prosa para o obter, e é a forma que o `/api/estado` já dá a cada componente |

**E um campo a mais: `motivos`.** `status: "degradado"` sozinho manda quem opera
abrir o `/api/estado` para descobrir o que a sonda já sabe. Vai em texto, por
componente.

**O `status` não é construído sobre `pronto`, e é o §6 ponto 2 a funcionar.**
Lê-se o `pode_perguntar` mais a condição de o `sha` existir — uma sonda que
devolve `ok` sem saber nomear o código é pior do que não haver sonda. Está
medido nos dois sentidos: com o Ollama em baixo **não** é `ok`; com tudo de pé
**é** `ok` embora o `pronto` do `/api/estado` seja `false`, que é o estado de
todos os arranques saudáveis antes da 1.ª pergunta.

**Uma medição a correr dá `degradado`**, com `medicao_a_correr: true` e a fase
nomeada nos motivos. Não é avaria — o `/api/estado` chama-lhe cedência —, mas o
serviço de facto não responde, e sob a saída D o URL **cai** durante as medições
(passo 5). Uma sonda que dissesse `ok` aí deixava o dono a procurar a avaria que
ele próprio causou.

**A `etiqueta` é `null` hoje, e isso é o estado verdadeiro:** não há etiquetas
neste repositório, e criá-las é o passo 8. A leitura está exercitada contra um
checkout com etiqueta, para não ser código que só se estreia quando alguém
depender dele.

**E o portão I7′ do passo 2 mordeu no dia seguinte a nascer.** A rota nova fez
`test_i7_o_varrimento_cobre_todas_as_rotas` falhar antes de qualquer teste do
passo 3 a tocar, que é exactamente para o que a cobertura de rotas existe.
Deixou de ser hipótese: está medido uma vez.

---

## 7. Um cliente em ciclo, que aqui não é um risco de disponibilidade

No plano retirado isto era um item «nomeado para depois». Sob a saída D sobe a
primeiro, e por uma razão que não é a óbvia.

A aritmética: um trinco, uma geração de cada vez, ~34 s por resposta.

```
3600 s / 34 s  ≈  105 respostas por hora,  no melhor caso
```

Um URL público não aumenta esse número — aumenta a fila. E **um** cliente em
ciclo consome a fila toda: todos os outros recebem 409. Isso é mau num serviço
qualquer. Aqui é pior, e é o argumento da §3 outra vez: **um cliente em ciclo
põe esta máquina a 100% de CPU indefinidamente, e com ela morrem as medições do
repositório** — não as que estiverem a correr, que o sentinela protege, mas a
disponibilidade da máquina para as fazer.

Portanto a ordem dos passos 6 e 9 é deliberada: **fechar antes de abrir.**

- **Passo 6, antes do URL ser útil a alguém:** autenticação na camada gratuita
  do fornecedor do túnel, com lista de endereços de correio. O serviço fica
  acessível a quem o dono convidar. Custo zero, e resolve o abuso por não haver
  público.
- **Passo 9, só se o dono quiser abrir de facto:** limite de pedidos por
  endereço na camada gratuita, mais o 409 que já existe. E uma medição antes de
  abrir: quanto tempo leva um cliente em ciclo a pôr o `p95` de geração fora do
  orçamento (**D7**).

Recomendação: **ficar no passo 6.** Um serviço que responde em verso a quem for
convidado entrega tudo o que a Fase 6 construiu, e não põe as medições do
repositório à mercê de quem encontrar o URL.

---

## 8. O que o `README` passa a dizer, e o que não pode continuar a dizer

A primeira frase do `README` é:

> Corre **inteiramente local**: índice e encoder nesta máquina, geração num
> Ollama local, sem chamada a API externa e sem credenciais.

Sob a saída D **continua verdadeira, inteira**, e vale notar porque é que isso
não é sorte: a saída D foi escolhida em vez da geração remota precisamente por
não mexer nesta afirmação. Índice, encoder e geração continuam nesta máquina;
não há API externa; não há credenciais.

O que o `README` **não** pode continuar a implicar é que o serviço é
inalcançável de fora. Duas frases a acrescentar, e nenhuma a remover:

- que existe um URL, que corre nesta máquina, e que a disponibilidade é a dela;
- que o URL **cai durante as medições**, por desenho, com o apontador para a §3.

E a §Estado ganha a linha da Fase 6 com os passos 7 e 2 feitos por este plano, e
o passo 9 **nomeado como não-feito por decisão de direitos**, não por falta de
tempo.

---

## 9. Portões

Os dois primeiros são da Fase 6, reescritos; os restantes são deste plano.

| portão | afirmação | como se mede |
|---|---|---|
| **I8′ — a medição e o serviço não se atropelam, com dois checkouts** | o sentinela atravessa checkouts | a fase escreve o sentinela do checkout de trabalho e o serviço, no **outro** checkout, vê-o: `/api/estado` mostra-o e `POST /api/perguntar` recusa. Com o caminho relativo da especificação original, este portão **falha** — é o seu objectivo |
| **I7′ — o corpo não sai desta máquina** 🔶 **metade medida** | o túnel não publica o corpus | **de fora**, contra o URL: `GET /api/poema/{id}` dá 404, e o varrimento do I6 apontado ao fio HTTP dá **zero** acertos de qualquer linha de corpo de qualquer poema. **Feito (2026-10-19):** o varrimento contra a aplicação, `tests/test_i7.py`, 8 testes, com a cobertura de rotas a falhar se nascer uma rota não varrida, e verificado a morder por mutação das duas metades da retenção. **Falta:** correr o mesmo varrimento **de fora**, contra o URL do túnel — passo 6 sobre o passo 4 |
| **D1 — a saúde não mente** ✅ | `/api/health` nomeia o código a correr | o `sha` devolvido é o do `HEAD` do checkout do serviço, em 3 arranques seguidos. Com o Ollama em baixo, `status` não é `ok`. **Feito (2026-10-19):** `tests/test_saude.py`, 13 testes — os 3 arranques são **3 processos** e não 3 chamadas num só, e acrescentou-se a asserção que o enunciado não tinha: o `sha` é o do checkout do **serviço** e não o do `cwd`, medido com um processo lançado dentro de um segundo checkout. Quatro mutações verificadas a morder. §6.1 |
| **D2 — o serviço sobrevive à sessão** 🔶 **instalado, por medir** | não é um processo de terminal | com `enable-linger`, fechar a sessão gráfica e reiniciar a máquina deixam o serviço de pé e o URL a responder. **Feito (2026-10-19):** a instalação, e 17 testes sobre o que torna o D2 possível — caminhos absolutos, `After` sem `Requires`, `WantedBy=default.target`, nunca o checkout de trabalho, e o `systemd-analyze --user verify` do próprio systemd; quatro mutações a morder. **Falta:** as duas metades que só o dono pode correr — um logout e um reinício (§5.4) |
| **D3 — o túnel obedece ao sentinela** | uma fase derruba o URL, e devolve-o | abrir o ajudante `with`: o URL deixa de responder em **menos de 10 s**; fechá-lo: volta em menos de 30 s. E durante a janela, **zero** pedidos atendidos — verificado no registo do túnel, não por intenção |
| **D4 — fechado antes de aberto** | estranhos não chegam ao serviço | de um endereço não convidado, o URL devolve o ecrã de autenticação do fornecedor e **nunca** toca no `uvicorn` — verificado nos registos do serviço, que não registam o pedido |
| **D5 — a janela fica escrita** | uma célula lenta é interpretável | o ficheiro de uma fase corrida sob o ajudante contém os instantes de túnel de pé, e eles **não se sobrepõem** aos instantes das amostras |
| **D6 — o recuo recua** | voltar a uma etiqueta é um comando | de uma etiqueta deliberadamente doente para a anterior: `pip install` corre, o manifesto é verificado **antes** do reinício, e `/api/health` devolve o `sha` anterior. Ensaiado, não presumido |
| **D7 — o limite limita** | um cliente em ciclo não ocupa a fila toda | com o limite activo, um cliente em ciclo recebe recusa do fornecedor e o `p95` de geração dos outros fica dentro do orçamento. **Só é exigido se o passo 9 for feito** |
| **D8 — a cópia restaura** | a cópia de `sessoes.db` é uma cópia | restauro num directório limpo e as sessões de antes a aparecerem. **Só é exigido se o passo 8 da Fase 6 existir** |

E a asserção de não-regressão: **`pytest` continua verde** (441 testes em
2026-10-19, eram 424 depois do passo 3, 411 depois do passo 2, 403 depois do
passo 5 e 377 antes dele), e deste plano muda em `src/` apenas o que o passo 7 da Fase 6 já
autorizava (o sentinela), o `src/web/tunel.py` do passo 5, a rota
`/api/health` com o `src/web/saude.py`, o `src/web/unidades.py`, o
`src/web/instalar.py` e o `src/web/__main__.py` do passo 4, o teste do I7′ —
**e o
`src/web/retencao.py` que o passo 2 obrigou a escrever, mais a ligação dele no
`src/web/app.py`** (§2.1). Nada em `src/pipeline.py`, `src/grafo.py`,
`src/guard.py`, `src/retrieval/` ou `src/generation/`. Um plano de publicação
que precise de mexer na política está mal desenhado.

> ⚠️ **O passo 2 mexeu num portão da Fase 6, e isso tem de ficar dito.** O
> **I1** — «a API não decide nada», o `Turno` igual campo a campo nos três
> braços — passou a comparar o `Turno` **publicado**: serializado *e* com a
> retenção aplicada aos três lados (`_publicado`, em `tests/test_perguntar.py`).
> O `Turno` que os três braços produzem continua idêntico, que é o que o I1
> afirma; o que difere é a publicação, e o CLI e o grafo não publicam nada.
> Comparar sem isso era exigir que a API publicasse o corpus para o portão
> passar — e a retenção aplica-se aos dois lados, logo uma API que retivesse
> mais continuava a divergir e a falhar. O teste do ciclo de repetição ganhou
> uma asserção de que a retenção **morde nesse caso**, para o `_publicado` não
> poder virar um `serial.turno` com passos a mais.

---

## 10. O que este plano deixa nomeado

| # | o que | porque fica de fora |
|---|---|---|
| 1 | **Confirmar os termos de uso do Arquivo Pessoa** (saída A) | é o que desbloqueia o passo 9 da Fase 6 e o painel do poema. Não é trabalho de publicação: é um pedido a terceiros, e `data/README.md` já registou a tentativa falhada de 2026-10-01 |
| 2 | **Licença do código** | `README` §Licença: «código sem licença declarada». Um serviço público com origem num repositório público sem licença é uma ambiguidade que se resolve com uma linha. Não bloqueia nenhum passo; bloqueia chamar-lhe terminado |
| 3 | **`AnthropicRemote`** | continua a ser a resposta ao tecto de ~105 respostas/hora, e continua a **mudar a afirmação** de «sem chamada a API externa e sem credenciais». Fase própria, com medição comparada de qualidade contra as âncoras das Fases 5F–5Y |
| 4 | **Uma segunda máquina** | é o que tornaria isto «produção» no sentido do irmão, e separaria quem edita de quem serve. Custa dinheiro, que é a restrição de onde este plano partiu |
| 5 | **Os dados de roteamento acumulados pelo serviço** | §3.5 da Fase 6 já o nomeou. Um serviço convidado muda a população de perguntas em relação ao conjunto rotulado de 40, e comparar é outra fase |
| 6 | **`src/{main,model,retriever}.py`** | o sistema anterior, de Flan-T5; o `retriever.py` importa um `faiss` que não está nas dependências. O checkout do serviço corre-os em zero linhas. Removê-los é limpeza, não publicação |

---

## 11. Resumo numa página

**Duas decisões fixam o plano:** publicar **sem o passo 9 da Fase 6** (as
fontes são ids, não corpos) e publicar **desta máquina atrás de um túnel
gratuito**, por a restrição de custo eliminar qualquer EC2.

**A vantagem é real e é uma só:** o hardware é o hardware medido. 14 núcleos,
30 GiB, 22 disponíveis contra ~6–7 de que o modelo e o encoder precisam, e as
latências dos relatórios (34 s, 18 s até ao 1.º verso) descrevem **esta**
máquina. Não há nada a remedir, e o portão de latência do plano retirado
desaparece.

**O molde do repositório irmão quase não transfere.** Sem segunda máquina e sem
rede de entrada, o EC2, o S3, o OIDC, o SSM, o nginx, o certbot e o
`rsync --delete` não têm função. Transfere a disciplina: `sha` na saúde,
verificar pelo serviço e nunca pelo emblema, e ensaiar o recuo.

**O túnel faz o portão I7 passar e tira a protecção que ele codifica** — o
servidor continua a escutar em `127.0.0.1` e está na internet. O portão
reescreve-se para medir o que protege: o corpo não sai, medido **de fora**.
Está feito desde 2026-10-19 na metade que não precisa do túnel, e o §2.1
registra o que o varrimento encontrou: **a saída B não bastava.** Havia três
outras portas — os fragmentos da tentativa plagiada, o `turno` dela, e o verso
copiado que à letra **é** o original —, e a primeira sai **em fluxo**, antes de
a guarda de plágio poder reprovar, logo nenhuma verificação a jusante a apanha.
A correcção é uma retenção por linha em `src/web/retencao.py`, que retém o
verso e deixa passar a explicação; custa 20 linhas em 16 866 de texto gerado
real (0,119%), e as 20 são versos de Pessoa. **E o varrimento, na primeira
versão, não mordia:** partia o fio por `\n`, o fio é NDJSON, e com a retenção
desligada passava verde.

**O verdadeiro custo é a sequência de medição desta casa.** O mecanismo que
devia mediar o conflito — o sentinela do passo 7, portão I8 — **não existia** à
data em que este plano foi escrito (está feito desde 2026-10-18, e com ele o
passo 5: o ajudante derruba o túnel, e o §3.4 regista as três decisões que isso
obrigou a tomar — a indirecção, a ausência declarada, e a fase a recusar
arrancar se o túnel não cair). O argumento abaixo é o que os fez existir, e
o código diz hoje que até lá «não correr o servidor com uma medição a decorrer é
disciplina e não mecanismo». Com um URL público não há onde aplicar disciplina,
logo **o passo 7 passa a pré-requisito do túnel**. E o sentinela como está
especificado resolve metade: protege a medição do servidor e não protege a
medição do público que aquece o chip na pausa de 60 s, nem o público de um 409
que dura sete horas. O remédio passa a ser **parar o túnel**, com a janela
registada ao lado das amostras — porque a alternativa é um `01-cru.jsonl` em que
uma célula lenta pode ser térmica ou pode ser um estranho, e isso não se
descobre depois. É a lição das 4 horas que o cache de KV invalidou, aplicada
antes de custar quatro horas.

**E um defeito a corrigir antes de o código existir:** com dois checkouts há
dois `data/`, e o sentinela especificado como caminho relativo **nunca é visto**
— passa nos testes, falha na máquina. Caminho absoluto, e o I8 ganha a asserção
de que atravessa checkouts.

**Fechar antes de abrir.** Um trinco a 34 s dá ~105 respostas/hora e **um**
cliente em ciclo consome-as todas, pondo a máquina a 100% e levando as medições
com ele. Autenticação gratuita com lista de convidados é o passo 6; abrir ao
público é o passo 9, e a recomendação é ficar no 6.
