# Fase 5H — trocar o modelo: o suspeito que sobra

Protocolo, **pré-registado antes de existir uma amostra**. É o passo 13 da lista
«[depois da Fase 5](CONTROLO.md)», e é o primeiro teste de modelo desta
sequência a começar com um instrumento **validado**.

**Objectivo:** decidir, por medição, se o défice da poética do Caeiro está no
**modelo**.

---

## 1. Porque é este o suspeito, e por eliminação medida

O défice está quantificado: na [Fase 5F](FASE-5F-RELATORIO.md), o Caeiro gerado
deu **0,675** contra **1,604** do Caeiro real na âncora 3a′ — uma distância de
**0,929** pontos numa escala de 0 a 2.

E três candidatos caíram, cada um por medição e não por suposição:

| candidato | o que o eliminou |
|---|---|
| **o contexto recuperado** | [Fase 5](FASE-5-RELATORIO.md), G2: 4 pares contra 4, IC95% [−0,25; +0,50] |
| **a forma interdictiva da persona** | [Fase 5G](FASE-5G-RELATORIO.md), G2 nas três leituras, IC95% [−0,30; +0,18] |
| **o chão ser real** | [Fase 5E](FASE-5E-RELATORIO.md): a âncora antiga reprovava 85% do Caeiro **autêntico** |

Sobram dois: o **conteúdo** da persona e o **modelo**. Esta fase mede o modelo,
porque é o único dos dois que se pode trocar sem reescrever nada.

---

## 2. A hipótese

**H5H:** o défice da poética do Caeiro depende do modelo gerador.

Operacionalmente: com o **mesmo prompt**, as mesmas opções de amostragem e a
mesma semente, um modelo diferente produz 3a′ diferente.

A predição contrária é concreta: se dois modelos de famílias diferentes e
tamanhos próximos derem a mesma poética, o défice não é deste modelo — é da
tarefa, do prompt que sobra, ou do que o corpus deixa aprender.

---

## 3. Desenho: ablação emparelhada, dois modelos

| | braço | modelo |
|---|---|---|
| **Q** | serviço | `qwen2.5:7b-instruct-q4_K_M` (7,6 B, Q4_K_M) |
| **L** | alternativa | `llama3.1:8b-instruct-q4_K_M` (8,0 B, Q4_K_M) |

**10 perguntas de Caeiro × 2 modelos × 3 repetições = 60 amostras, 30 pares.**

A persona é a **de serviço** (`src/voices.py`), não a variante afirmativa: a 5G
rejeitou H5B, logo a variante não entra, e o que interessa medir é o que o
utilizador recebe.

### 3.1 O confundidor que não existe, e a asserção que o prova

O risco óbvio de trocar o modelo é os dois receberem **contexto diferente**: se o
orçamento de prompt fosse contado com o tokenizador do gerador, cada modelo
caberia um número diferente de poemas e eu estaria a medir modelo **mais**
contexto.

**Não é o caso, e é verificável.** `src/tokens.py` documenta-o: o contador que o
`Pipeline` usa é o do **encoder e5**, não o do gerador — «dois tokenizadores
importam neste projecto e **não** são intercambiáveis». A selecção de chunks é
portanto independente do modelo.

O harness não confia nisto: para cada par, **recompõe o prompt com `montar` e
compara as cadeias `system` e `user` byte a byte entre os dois braços**, com
asserção. Se alguma diferir, a corrida aborta.

### 3.2 Configuração

| | valor |
|---|---|
| opções | `temperature=0,9` · `repeat_penalty=1,1` · `top_p=0,9` · `num_predict=220` · `num_thread=10` |
| recuperação | `TOP_K`=6 de `N_RERANK`=8, reordenação ligada |
| pipeline | completo, com repetição por plágio |
| semente | `20261006 + 100·r + i`, igual nos dois braços |

As opções são as de serviço e **não se afinam por modelo**. É uma decisão com
custo e fica declarada: o `repeat_penalty=1,1` e o `num_predict=220` foram
escolhidos na Fase 0 **para o qwen**, e há no `CONTROLO.md` uma pendência aberta
— «repetir o teste de voz do 8B com `repeat_penalty`». Afinar por modelo mediria
dois modelos **mais** duas afinações; não afinar mede o llama3.1 nas condições do
qwen. Esta fase faz a segunda, e o §9 diz o que isso limita.

### 3.3 A ordem de geração, e porque não é alternada

Os dois modelos geram em **blocos** — os 30 do qwen, depois os 30 do llama — e
não alternados por amostra. Alternar forçaria o Ollama a recarregar o modelo 60
vezes, e o `keep_alive` de 30 min existe precisamente para evitar isso.

O emparelhamento não sofre: é por `(pergunta, repetição)` e a semente é a mesma
nos dois braços, logo a ordem de geração não entra em nenhuma comparação.

---

## 4. A rubrica

| # | critério | como |
|---|---|---|
| **3a′** | **poética da voz** | à mão, às cegas, dois avaliadores — âncora da [5F](FASE-5F.md) §2. **Desfecho primário** |
| 3b | forma da voz | à mão, às cegas — âncora da [Fase 5](FASE-5.md) §5.2, inalterada. **Segundo desfecho, com portão** |
| 1 · 2 · 5 | verso · PT-PT · plágio | automáticos |

**3b tem portão aqui, ao contrário da 5G, e a razão é que o desenho mudou.** Na
5G a `forma` era byte a byte igual nos dois braços, logo mover 3b era sinal de
perturbação do prompt — um confundidor. Aqui o prompt é igual e o **modelo** é
que muda, logo uma diferença em 3b é uma diferença **real** entre modelos, e
conta para a decisão em vez de a contaminar.

---

## 5. Os portões

Primário na **estimativa conjunta** dos dois avaliadores. Teste de sinais exacto
sobre os pares discordantes e IC95% por bootstrap emparelhado, B=10000, semente
3. Piso de potência d ≥ 8.

| | portão | condição (conjunta, 30 pares) | o que decide |
|---|---|---|---|
| **M1** | **H5H confirmada** | em 3a′: binomial p ≤ 0,05 a favor de um dos braços **e** IC95% a excluir 0 | o modelo importa. **Autoriza investigar a troca** — não a troca |
| **M2** | **H5H rejeitada** | p > 0,05 **ou** IC95% a conter 0, com **d ≥ 8** | o défice **não** é deste modelo. Sobra o conteúdo da persona, a tarefa, ou o corpus — e nenhum se resolve trocando de gerador |
| **M3** | **a troca não sai de graça** | M1 a disparar **e** o braço vencedor em 3a′ a perder em 3b, ou no critério 2, ou no 5 | a autorização do M1 fica **condicionada**: investiga-se a troca sabendo o que ela custa, e o relatório nomeia o custo |
| **M4** | **inconclusivo por potência** | d < 8 | nada se decide |
| **M5** | **os avaliadores discordam** | R1 e R2, em separado, chegam a portões diferentes entre M1, M2 e M4 | publica-se a discordância e **nada se autoriza** |

**M1 autoriza investigar, não trocar, e é deliberado.** Trocar o modelo de serviço
é uma decisão de produto com custos que esta fase não mede: latência, memória,
as guardas de língua calibradas na Fase 0 para o qwen, e o roteador da Fase 4.
Uma fase de 60 amostras numa voz não autoriza isso, e dizê-lo agora evita
reclamá-lo depois.

### 5.1 Sem portão, mas relatado

- **Latência por amostra**, nos dois braços. Pesa na decisão que o M1
  desbloquearia e não é um resultado sobre a hipótese.
- **Truncaturas**, tentativas por plágio, e brasileirismos por braço.
- **A distância ao Caeiro real**: a 5F mediu 1,604 nos poemas autênticos com
  esta âncora. Fica como régua externa para ler as duas médias — e é uma
  comparação **entre amostras**, não um teste.

---

## 6. Potência, calculada antes de medir

A 5G mediu o desvio-padrão das diferenças emparelhadas em 3a′: **0,674**. Com 30
pares e teste bilateral a 0,05:

| Δ a detectar | pares para 80% |
|---|---|
| 0,50 | 17 |
| **0,40** | **25** |
| 0,35 | 32 |
| 0,25 | 60 |

**30 pares detectam Δ ≥ 0,40 a ~80%.** E a referência útil está a 0,929 — a
distância entre o Caeiro real e o gerado: se o modelo explicasse metade dela,
esta fase vê-o com folga. Se explicar um quinto, não.

O relatório repete isto **qualquer que seja o resultado**, e dá o IC medido como
a afirmação inferencial, porque na 5G o intervalo saiu mais estreito do que o
cálculo a priori prometia.

---

## 7. Cegueira

1. As 60 amostras vão para `01-itens.md` embaralhadas por semente fixa, com
   identificadores opacos `H01`–`H60`, e duas da mesma pergunta nunca
   adjacentes. **A folha é escrita por `folha.py` e não pelo harness** — na 5G o
   harness herdado escreveu a âncora errada, e esta fase não repete isso.
2. A chave fecha e abre só depois de as duas pontuações estarem commitadas.
3. R2 recebe cópia fora do repositório, sem nome de fase, verificada por
   **fronteira de palavra**, e **sem saber que há dois modelos** — o
   enquadramento não pode conter «modelo», «gerador», «qwen» nem «llama».

### 7.1 Uma fuga de cegueira específica desta fase

Modelos diferentes têm tiques diferentes, e eu conheço os do qwen por ter lido
~240 amostras dele nesta sequência. **Posso reconhecer o braço pelo estilo**, e
isso é mais provável aqui do que em qualquer fase anterior.

Não o sei remover. O que há: R2 nunca viu amostra nenhuma de nenhum dos dois, e
o M5 bloqueia a autorização se os dois avaliadores divergirem de veredicto. E a
direcção do viés **não é previsível** — eu não tenho preferência declarada entre
os modelos —, o que é diferente de todas as fases anteriores, onde a direcção era
previsível e declarei-a.

---

## 8. O que esta fase não mede

- **O `qwen2.5:3b`**, que está instalado. Um terceiro braço diria se o défice é
  de **capacidade**; fica nomeado para quem o quiser medir.
- **Opções afinadas por modelo.** Ver §3.2.
- **As outras três vozes**, nem a forma como cada modelo as serve.
- **O custo da troca**: latência sim (sem portão), mas não memória, não as
  guardas de língua da Fase 0, não o roteador da Fase 4.
- **Modelos remotos.** O `AnthropicRemote` do plano é outra fase.

---

## 9. Checklist

```
[ ] A1  protocolo commitado antes de existir qualquer amostra
[ ] A2  asserção de prompt byte a byte igual entre braços, em todos os 30 pares
[ ] A3  60 amostras, semente base 20261006, geradas em blocos por modelo
[ ] A4  folha escrita por folha.py com a âncora 3a′; chave fechada
[ ] B1  R1 pontua 3a' e 3b às cegas, com razão por amostra
[ ] B2  R2 pontua, cego ao desenho e à existência de dois modelos
[ ] B3  as duas pontuações commitadas antes de a chave abrir
[ ] C1  sinais e bootstrap na conjunta; portões M1–M5
[ ] D1  relatório, com a potência do §6 repetida e a latência relatada
```
