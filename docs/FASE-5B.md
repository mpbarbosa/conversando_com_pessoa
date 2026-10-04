# Fase 5B — a persona do Caeiro, feita de interdições

Protocolo, **pré-registado antes de medir**. É o Passo 1 da lista «[depois da
Fase 5, o que ela deixou nomeado](CONTROLO.md)», e o passo que o relatório da
Fase 5 chamou «a entrada natural para uma Fase 5B».

**Objectivo:** decidir, por medição, se a poética do Caeiro falha por a persona
estar escrita como **interdições**, e — se falhar por isso — autorizar a
reescrita afirmativa em `src/voices.py`.

> **Nota sobre o que esta fase herda e o que não herda.** O relatório da Fase 5
> mediu que o Caeiro é a única das quatro vozes a **0,0 de mediana** na poética,
> e observou que é a única cuja persona é uma lista de proibições. A **ligação**
> entre as duas coisas é inferência, a n=5 por voz, e não medição. Esta fase
> trata-a como **hipótese a medir**, não como premissa. Formulação da sessão da
> Fase 5, e é a correcção mais importante ao ponto de partida desta.

---

## 1. Porque é esta a fase

Quatro fases — 2, 3, 3B e 4 — mediram recuperação. A Fase 5 mediu a voz e fechou
a pergunta aberta desde a Fase 1 Passo 7: a voz pedida **não se cumpre**, e o
contexto recuperado **não é a causa** (4 pares contra 4, IC95% [−0,25, +0,50]).
O Caeiro quebra a sua própria interdição sem contexto nenhum — «Sentido em cada
pedra», «Nas entrelinhas do que se desvanece».

O suspeito está eliminado por medição. Sobram dois: a **persona** e o **modelo**.
Esta fase ataca a persona, por ser a hipótese barata e por o Caeiro ter uma
propriedade que as outras três vozes não têm:

| voz | 3a na Fase 5 | a persona diz |
|---|---|---|
| **caeiro** | **0,0** | «**não** lhes atribuis», «**Não** pensas», «**Recusas**», «**Não** personificas nem a usas» |
| campos | 1,0 | «Sentes tudo em excesso», «Acumulas, enumeras, repetes» |
| ortónimo | 1,0 | «Não sabes quem és», e o resto afirmativo |
| reis | **2,0** | «És estóico», «Aceitas o destino», «Aconselhas a medida» |

A voz que passa é a que só manda fazer. A voz que falha é a que manda **não
fazer**. É uma correlação a n=4 vozes, e por isso é hipótese.

---

## 2. A hipótese, enunciada com precisão

**H5B:** a poética do Caeiro falha porque a persona a enuncia como interdições.

O mecanismo proposto é concreto, e é o que torna isto falsificável: uma
instrução negativa **tem de nomear o conteúdo proibido** — «significado oculto»,
«metafísica», «simbologia», «moral», «espelho de sentimentos» — e nomeá-lo
torna-o disponível. O modelo executa o referente em vez de o evitar.

H5B prevê então que a **mesma** poética, enunciada só por afirmações e sem
nomear os referentes proibidos, produza poética mais fiel nas mesmas perguntas.

A predição contrária é igualmente concreta: se a causa for o **conteúdo** da
persona, ou o modelo, a variante afirmativa não muda nada e H5B cai. É o que a
Fase 5 fez com a sua própria hipótese, e é o resultado mais provável a priori —
a Fase 0 já mediu que descrever a postura funciona melhor que nomear o
heterónimo, mas nunca mediu polaridade.

### 2.1 O que H5B funde de propósito, e não pode separar

A variante afirmativa faz **duas** coisas ao mesmo tempo: inverte a polaridade
**e** deixa de nomear os referentes proibidos. As duas estão fundidas, e este
desenho **não as separa**.

A fusão é deliberada, porque o mecanismo acima é sobre **nomear**: a polaridade
negativa é o veículo, o nome é a causa proposta. Separá-las exigiria um terceiro
braço — negação que não nomeia — e a n=30 pares isso divide a potência por uma
pergunta que só se põe se H5B sobreviver a esta.

Fica declarado aqui para que o relatório não possa apresentar «a negação
estorva» quando o que foi medido é «a negação, que nomeia, estorva».

---

## 3. Desenho: ablação emparelhada, dois braços

| | braço | `poetica` | tudo o resto |
|---|---|---|---|
| **C** | **controlo** | a de serviço, byte a byte (`src/voices.py`) | `Pipeline.responder` completo |
| **P** | **positiva** | a variante afirmativa do §4 | idem, byte a byte |

**As duas condições correm o pipeline completo, com contexto.** Não é descuido:
a Fase 5 absolveu o contexto por medição, logo mantê-lo ligado é manter um
incómodo constante, e é o que o utilizador recebe. A recuperação depende da
pergunta e da voz, nunca do texto da persona (`Pipeline.recuperar`), logo os
dois braços vêem **os mesmos chunks** — o emparelhamento é exacto nessa parte.

### 3.1 O que fica fixo, byte a byte

Mudar só a `poetica` é a decisão central deste desenho, e protege três coisas:

| peça | porquê fica fixa |
|---|---|
| `Persona.forma` | a forma é o critério 3b, e a Fase 5 mediu que falha por razões próprias (14 zeros em 40). Mexer nela confundiria os dois critérios |
| `REGRAS_NAO_COPIAR` | é uma interdição, e é **carga útil medida**: na Fase 1 levou a mediana de versos copiados de 82% para 0%. Removê-la mediria outra coisa e devolveria plágio ao utilizador |
| `REGRAS_SAIDA`, `REGRAS_LINGUA` | interdições de meta e de língua, que governam preâmbulo e ortografia, não poética |

Daqui sai uma delimitação que o relatório tem de repetir: esta fase testa a
**forma interdictiva da cláusula poética**, e **não** «as interdições em geral».
Restam interdições no `system` nos dois braços, de propósito.

### 3.2 Configuração

| decisão | valor | porquê |
|---|---|---|
| gerador | `qwen2.5:7b-instruct-q4_K_M` | o de serviço |
| opções | `temperature=0,9` · `repeat_penalty=1,1` · `num_predict=220` | as de serviço |
| recuperação | `TOP_K`=6 de `N_RERANK`=8, reordenação **ligada** | a melhor medida (Fase 3B) |
| pipeline | completo, com repetição por plágio | é o que o utilizador recebe; as tentativas ficam por amostra |
| injecção da persona | *monkeypatch* de `src.pipeline.persona` no harness | `responder` chama `voices.persona` directamente. `src/voices.py` **não se toca** antes de a medição o autorizar |
| semente | `20261003 + 100·r + i`, igual em C e P | `i` índice da pergunta (0–9), `r` repetição (0–2) |

**A semente não é emparelhamento verdadeiro.** O `system` difere entre braços,
logo a sequência de tokens difere e a mesma semente não produz o mesmo sorteio.
Remove uma fonte de variância e torna a corrida reproduzível; não mais do que
isso. A Fase 5 tem o mesmo desvio, declarado do mesmo modo.

---

## 4. A variante afirmativa, e a regra que a produziu

A regra foi escrita **antes** do texto, e o texto **antes** de existir amostra.
É a única defesa contra a variante ser afinada até funcionar.

### 4.1 A regra de reescrita, pré-registada

1. **Cláusula a cláusula.** Cada oração da `poetica` de serviço tem uma
   correspondente na variante, com o **mesmo referente**. A tabela do §4.3 é o
   mapa, e é parte do pré-registo.
2. **Zero partículas negativas.** Nenhuma ocorrência, com fronteira de palavra,
   de `não`, `nunca`, `nem`, `sem`, `nada`, `recusas`, `recusa`, `proíbes`,
   `evitas`, `jamais`, `sequer`.
3. **Comprimento** em caracteres dentro de **±20%** do original, para que «mais
   instrução» não seja a explicação alternativa.
4. **Nenhum conteúdo poético novo**: nada que não seja inversão de polaridade de
   uma cláusula existente. Nenhuma imagem, nenhum exemplo, nenhum nome.
5. `forma` e as três regras do §3.1, **byte a byte**.

### 4.2 Verificação mecânica da regra

Corre em `fase-5b/verificar_personas.py` e o resultado vai no relatório:

| | C (serviço) | P (variante) | regra |
|---|---|---|---|
| partículas negativas | **6** (`não`×4, `nem`×1, `recusas`×1) | **0** | regra 2 |
| caracteres (normalizados) | 282 | 296 | razão **1,050**, dentro de 0,80–1,20 |

### 4.3 O mapa de cláusulas

| # | cláusula de serviço | referente | cláusula afirmativa |
|---|---|---|---|
| 1 | «Vês as coisas como elas são» | ver | **inalterada** |
| 2 | «e não lhes atribuis significado oculto» | significado oculto | «e o que elas são está todo à vista» |
| 3 | «um poente é um poente e não uma tristeza» | coisa ≠ sentimento | «um poente é um poente, e é isso que ele é» |
| 4 | «Não pensas sobre o que vês — vês» | pensar contra ver | «Vês o que vês, e o ver basta-te» |
| 5 | «Recusas a metafísica, a simbologia e a moral» | metafísica, símbolo, moral | «Ficas na superfície das coisas, que é onde elas estão inteiras» |
| 6 | «Não personificas a natureza nem a usas como espelho de sentimentos» | personificação, espelho | «A natureza está ali por sua conta, e continua igual quando passas» |

A cláusula 5 é a que mais mostra o mecanismo: a variante **não nomeia**
metafísica, simbologia nem moral. É isso que o §2.1 diz estar fundido.

---

## 5. O conjunto fixo: as 10 perguntas de Caeiro

As **10** perguntas de Caeiro do gabarito dourado,
[`fase-1/08-perguntas.json`](fase-1/08-perguntas.json) `q01`–`q10`.

A Fase 5 usou **5** (`q01`–`q05`), as únicas com nDCG@5 conhecido por pergunta.
Aqui entram as dez, e a razão é potência: metade do resultado por voz da Fase 5
vive a n=5, onde **uma** amostra vale 20 pontos de mediana. Esta fase é a
primeira com alguma potência sobre o Caeiro, e a sessão da Fase 5 pediu
explicitamente o número.

**10 perguntas × 2 braços × 3 repetições = 60 amostras**, logo **30 pares**.

As 3 repetições por célula pagam a ameaça que a Fase 5 §8 declarou não medir — a
`temperature=0,9` faz de uma amostra por célula um sorteio. Aqui a variância
dentro da célula fica medida e entra no relatório.

### 5.1 Uma ameaça que vem das próprias perguntas

`q06`–`q10` **enunciam a postura de Caeiro na própria pergunta**: «as coisas não
escondem nenhum sentido por baixo de si», «pensar estraga o que se está a ver»,
«aprender a ver é mais difícil do que aprender a pensar». Uma pergunta que já
diz o que a persona manda fazer pode levantar 3a nos **dois** braços e comprimir
a diferença.

Pré-registo a leitura estratificada: **`q01`–`q05`** (as da Fase 5, e as únicas
comparáveis com ela) e **`q06`–`q10`** (novas), relatadas em separado. Os
portões aplicam-se ao conjunto das dez; os estratos são descritivos e **não
decidem nada**, a n=15 pares cada.

---

## 6. A rubrica e os dois avaliadores

A rubrica é a da [Fase 5 §5](FASE-5.md), **inalterada**, e as âncoras de 3a e 3b
do Caeiro são as da Fase 5 §5.1–5.2, **escritas antes de existir qualquer amostra
desta fase ou daquela**. É a defesa mais forte que esta fase tem: o que conta
como 0 no Caeiro foi fixado por outra fase, para outra hipótese.

| # | critério | como |
|---|---|---|
| 1 | é verso? | automático, `guard.e_verso` |
| 2 | português europeu? | automático, `guard.brasileirismos` + `guard.lingua_errada` a **0,12** |
| **3a** | **poética da voz** | **à mão, às cegas, por dois avaliadores** — é o desfecho primário |
| 3b | forma da voz | à mão, às cegas, por dois avaliadores — controlo interno (§7, G3) |
| 4 | responde à pergunta | à mão, às cegas, por dois avaliadores |
| 5 | não plagia | automático, `plagio.analisar` contra os chunks recuperados |

O critério 2 usa o piso **certo** desde o início: `lingua_errada` a 0,12, e o
dicionário a 0,50 onde pertence. A Fase 5 usou 0,50 nas stopwords, reprovou 38
de 40 amostras e teve de se corrigir a si mesma (`fase-5/corrigir_c2.py`). O
erro está documentado e não se repete.

### 6.1 Os dois avaliadores, e porque são dois

A lacuna mais séria da Fase 5, pelas suas próprias palavras: «**avaliador
único**, e o mesmo que escreveu as personas, o prompt e esta rubrica». Esta fase
tem dois, e nenhum é primário:

| | avaliador | o que sabe |
|---|---|---|
| **R1** | esta sessão | tudo: escreveu a variante, o protocolo e os portões |
| **R2** | um avaliador independente, cego ao desenho | **só** as âncoras do Caeiro e a folha embaralhada. Não sabe que há dois braços, nem qual é a hipótese, nem que existe um tratamento |

R2 ser cego ao **desenho** — e não só à condição — é o ponto. A ameaça nomeada
não é «leu as amostras agrupadas», é **autoria**: R1 prevê que a variante
funcione, e R1 pontua. R2 não tem predição a confirmar porque não sabe que há
uma.

**Os portões correm duas vezes, uma por avaliador, e o veredicto exige
concordância** (§7, G5). É a mesma postura da Fase 5 com os seus dois
instrumentos: discordarem não decide nada.

### 6.2 Cegueira

1. `gerar_amostras.py` grava as 60 amostras em `01-amostras.md`, **embaralhadas**
   com semente fixa, com identificadores opacos `B01`–`B60`, mostrando só
   pergunta e texto. O mapa `id → (pergunta, braço, repetição)` vai para
   `01-chave.json`.
2. O embaralhamento garante que **duas amostras da mesma pergunta nunca ficam
   adjacentes**.
3. As pontuações dos **dois** avaliadores vão para `02-pontuacoes.json` e
   `02-pontuacoes-r2.json`, e são **commitadas antes** de a chave ser aberta.

### 6.3 Ameaças a esta cegueira, declaradas

- **Seis amostras por pergunta na mesma folha.** A Fase 5 tinha duas. Com seis,
  um avaliador que saiba que há dois braços pode tentar agrupá-las em 3+3 e
  inferir a condição. **R1 sabe e está exposto a isto; R2 não sabe que há
  braços.** É a razão técnica, e não só retórica, para R2 existir.
- **Os dois avaliadores são sessões do mesmo modelo a ler as mesmas âncoras.** A
  concordância pode ser **erro correlacionado** e não confirmação independente. O
  κ mede concordância, nunca correcção. Fica declarado: isto é mais fraco que um
  segundo avaliador humano, e não é equivalente.
- **A variante foi escrita por quem prevê que funcione.** A regra do §4.1, o mapa
  de cláusulas e a verificação mecânica do §4.2 são a mitigação; não a solução.
- **Uma amostra sem contexto não existe aqui**, logo a ameaça da Fase 5 («a
  condição é visível por magreza») não se aplica — os dois braços têm contexto.

---

## 7. Portões, pré-registados

Estatística, a mesma da Fase 3B e da Fase 5 (`fase-3b/bench_significancia.py`),
sem scipy: **teste de sinais exacto** e **IC95% por bootstrap emparelhado**,
B=10000, semente 3.

**Mudança deliberada ao teste de sinais da Fase 5, e a razão.** A Fase 5 escreveu
os seus portões sobre **todos** os 20 pares («≥13 dos 20»), e depois mediu 12
empates em 3a — o portão de confirmação ficou inalcançável por construção. Aqui
o teste de sinais corre sobre os **pares discordantes**, que é o teste de sinais
como ele é, e a potência é protegida por um piso explícito.

Desfecho primário: **3a do Caeiro**, 30 pares, por avaliador.

| | portão | condição | o que autoriza |
|---|---|---|---|
| **G0** | **o chão não se reproduziu** | mediana de 3a em **C** ≥ 1 nas 10 perguntas | nada cai, mas **registar** que o 0,0 da Fase 5 era de n=5 e não se reproduziu a n=10. Os outros portões leem-se com isto declarado, e a inferência da Fase 5 fica mais fraca do que estava |
| **G1** | **H5B confirmada** | nos pares discordantes, os a favor de **P** dão binomial exacto bilateral **p ≤ 0,05** contra p=0,5, **e** IC95% do Δ emparelhado **não contém 0**, **e** G3 não dispara | autoriza substituir a `poetica` do Caeiro em `src/voices.py` pela variante do §4, **e** reescrever as outras três personas pela mesma regra do §4.1, medidas com as 20 perguntas da Fase 5 |
| **G2** | **H5B rejeitada** | p > 0,05 no binomial **ou** IC95% a conter 0, com **d ≥ 8** pares discordantes | H5B cai. A forma interdictiva da cláusula poética **não** é a causa, e o que sobra é o **conteúdo** da persona ou o **modelo** — e isso é um teste de modelo, não mais prompt |
| **G3** | **especificidade** | \|Δ3b\| ≥ \|Δ3a\| **e** no mesmo sentido | a `forma` é byte a byte igual nos dois braços, logo mover 3b tanto como 3a é sinal de **perturbação geral do prompt**, não de efeito na poética. **G1 não pode ser lido como confirmação de H5B** se G3 disparar |
| **G4** | **inconclusivo por potência** | **d < 8** pares discordantes, em qualquer direcção | registado como inconclusivo, como a Fase 3 foi. Nada se decide, e o desempate é mais repetições por célula — não outro desenho |
| **G5** | **os avaliadores discordam** | R1 e R2 chegam a portões diferentes entre G1, G2 e G4 | **nada se autoriza.** O relatório publica os dois e a fase fecha inconclusiva. É a mesma regra do G7 da Fase 5 |

**G0 e G1 podem disparar juntos**, ao contrário do par G0/G1 da Fase 5. Aqui G0
não é um tecto: se C já estiver em 1, há folga para subir até 2, e o que G0 faz é
obrigar a declarar que o ponto de partida mudou.

**O piso de d ≥ 8.** É pré-registado e não negociável depois de ver os dados. O
critério desta casa está escrito na Fase 2 — «+0,004 é ruído a n=20» — e aceitar
um veredicto com 3 ou 4 pares discordantes seria incoerente com isso.

### 7.1 Instrumento II — a contagem lexical dos referentes nomeados

Mecânico, cego por construção, e **sem portão**.

A lista de alvos é **os referentes que a persona C nomeia**, com variantes
morfológicas, e vem da tabela do §4.3 — logo do **tratamento**, nunca das
amostras:

```
significado, significados, sentido, sentidos, oculto, oculta, ocultos, ocultas,
metafísica, metafísico, símbolo, símbolos, simbologia, simbólico, moral, morais,
espelho, espelhos, tristeza, tristezas
```

Predição de H5B: a contagem é **maior em C**. Mede o mecanismo, não o desfecho.

**Porque não tem portão, e porque isso não é modéstia.** P **não contém** estas
palavras, por construção, e o `REGRAS_SAIDA` já proíbe repetir as palavras das
instruções nos dois braços. Um eco de vocabulário do prompt produziria este
resultado **sem** nenhuma diferença de poética, e este instrumento não separa
«eco» de «priming». Dá evidência de mecanismo se H5B passar pelo desfecho
primário; sozinho não decide nada, e não pode ser apresentado como se decidisse.

### 7.2 O que corre sem portão e fica como observação

- **Variância dentro da célula** em 3a, por braço: o desvio entre as 3
  repetições da mesma pergunta. É a primeira medição disto no projecto.
- **κ de Cohen** entre R1 e R2 em 3a, 3b e 4, nas 60 amostras, e a concordância
  exacta em percentagem.
- Os estratos `q01`–`q05` e `q06`–`q10` do §5.1.
- Critérios 1, 2, 4 e 5, e as **truncaturas** — pendência conhecida desde a Fase
  4 (`num_predict=220`), e o Caeiro pede 10–20 versos curtos, logo não se espera
  que apareçam aqui.

---

## 8. O que esta fase não mede

- **As outras três personas.** A reescrita das outras três é o que G1
  autorizaria, e não o que esta fase faz. Medi-las aqui seria medir quatro
  hipóteses com a potência de uma.
- **«As interdições em geral».** Ver §3.1: três blocos de interdições ficam no
  `system` nos dois braços, e um deles é carga útil medida.
- **Negação sem nomear.** Ver §2.1. Pede um terceiro braço.
- **A sombra lexical** do relatório da Fase 5 §11, que precisa de regra de
  selecção vinda de fora da amostra e de potência própria. A contagem do §7.1
  **não é** essa medição: a lista desta vem do tratamento, a daquela teria de vir
  dos 113 poemas reais de Caeiro.
- **O modelo.** Se H5B cair, o suspeito seguinte é o 7B, e é outra fase.
- **As vozes inglesas**, e as três vozes com 3a ≥ 1.
- **Identificabilidade.** A Fase 5 mediu que o Caeiro é identificado ao nível do
  Caeiro **real** e tem 0,0 na poética: identificabilidade não é proxy de «a voz
  está certa», e o portão G5 da Fase 5 teve de registar que a sua prescrição não
  se seguia. Não se repete aqui.
- **Latência**, e o `num_predict` do Campos.

---

## 9. Checklist do protocolo

```
[ ] A1  protocolo commitado antes de qualquer amostra existir
[ ] A2  verificar_personas.py: 0 partículas negativas em P, razão de
        comprimento em 0,80–1,20, forma e as três regras byte a byte iguais
[ ] A3  60 amostras geradas (10 perguntas × 2 braços × 3 repetições),
        persistidas incrementalmente, com as tentativas por amostra
[ ] A4  embaralhamento sem pares da mesma pergunta adjacentes, chave fechada
[ ] B1  R1 pontua 3a, 3b e 4 nas 60 amostras, às cegas
[ ] B2  R2 pontua as mesmas 60, cego ao desenho e sem a hipótese
[ ] B3  as duas pontuações commitadas antes de a chave ser aberta
[ ] C1  sinais sobre os pares discordantes, bootstrap e medianas, por avaliador
[ ] C2  portões aplicados duas vezes; G5 verificado
[ ] C3  κ de Cohen, variância dentro da célula, estratos
[ ] D1  instrumento II: contagem lexical dos referentes nomeados
[ ] E1  relatório, com as ameaças do §6.3 repetidas e a delimitação do §3.1
```
