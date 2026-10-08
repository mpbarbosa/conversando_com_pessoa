# Fase 5U — relatório: a causa que a 5Q nomeou é rara demais para explicar o que a 5Q mediu

**Protocolo:** [`FASE-5U.md`](FASE-5U.md), pré-registado em `8a0672e`.
**Analisador:** fixado em `1465aab`, **com o diário em 2 de 120 amostras**.
**Dados:** [`fase-5u/01-cru.jsonl`](fase-5u/) (120) ·
[`02-resultados.json`](fase-5u/) · [`03-sensibilidade.json`](fase-5u/)
**Produto:** nada. O U3 disparou e o §3.1 pré-escreveu que nesse caso não se mexe.

---

## 0. Os portões

| | | |
|---|---|---|
| **U1** a regra sustenta a ênclise | ❌ **não dispara** | e a diferença é **negativa**: A 0,0000 contra C 0,0408 |
| **U1′** o efeito é «sistemático» | ❌ não dispara | — |
| **U2** a regra sustenta a ortografia | ❌ **não dispara** | A 0,0000 contra C 0,0167 — **um** item marcado em 120 |
| **U3** o bloco é decoração | ✅ **dispara** | mas **dispara no chão**, e o §1 diz porquê |

**Pela decisão pré-escrita: o bloco é decoração e o passo 34 sai do prompt. Nada
é removido** — o §3.1 escreveu que remover é intervenção e pede pré-registo
próprio. Não removi.

---

## 1. O U3 disparou no chão, e isso não é a mesma coisa que ter resposta

Os números absolutos, que são o que decide a leitura:

| | braço C (completo) | braço A (ablado) |
|---|---|---|
| amostras | 60 | 60 |
| **próclise não licenciada** (régua pré-registada) | **2** ocorrências | **0** |
| **itens com marca ortográfica** (detector da 5R a 20×) | **1** | **0** |
| gerúndio progressivo | 2 itens | 2 itens |
| «você» | 0 | 0 |

**Duas ocorrências e um item.** Com essa contagem de eventos, nenhum desenho de
120 amostras distingue «a regra não faz nada» de «a regra faz algo e a taxa de
base é baixa demais para se ver». **Ausência de prova não é prova de ausência**,
e aqui a ausência é de **eventos**, não de efeito.

É a **quarta vez nesta sequência** que um instrumento satura num extremo — chão
na 5B, tecto na 5O, chão na 5Q, chão agora. A diferença é que desta vez o chão
está no braço que **devia** mostrar o defeito.

### 1.1 Uma régua mais estrita, posterior e declarada

Ao ler as amostras do braço A para verificar que continuavam em português
europeu, encontrei uma linha que a régua da [5T](FASE-5T-RELATORIO.md) **não
marca**:

> «Em cada instante **te vejo** a ti mesma.»

«Em» é preposição, está na mesma oração, logo a regra de atracção licencia. Mas
**uma preposição só atrai no infinitivo preposicionado** — «para se ver», «sem
me dizer» — e não em geral. A régua pré-registada é, nesse ponto, permissiva de
mais ([`sensibilidade.py`](fase-5u/sensibilidade.py)).

Com a preposição a licenciar **só adjacente** — e os outros atractores
(negação, subordinação, foco) a continuar a licenciar à distância:

| | poemas marcados | próclise | ênclise | proporção | Wilson95 |
|---|---|---|---|---|---|
| **corpus (Pessoa)** | 106/1926 = **5,50%** | 630 | 6909 | **0,0836** | — |
| **braço C** | 7/60 | **7** | 47 | **0,1296** | [0,064, 0,244] |
| **braço A** | 2/60 | **4** | 34 | **0,1053** | [0,042, 0,241] |

E aqui o detector marca defeitos **verdadeiros**: «pedra **me** dói», «cigarro
**me** bate», «universo **me** bate», «suspiro **me** traz», «tu **me**
deixas». São próclise brasileira inequívoca, e **estão no braço completo** — com
a instrução «colocação enclítica, **sempre**» no `system`.

### 1.2 O que sobrevive às duas réguas, e o que não

| afirmação | régua pré-registada | régua estrita | sobrevive? |
|---|---|---|---|
| **a regra não aumenta a próclise** — A ≤ C | −0,0408 | −0,0244 | ✅ **nas duas**, e em três estatísticas |
| a diferença é estatisticamente distinguível de zero | IC [−0,096, 0,000] | IC [−0,170, +0,174] | ❌ nem numa |
| **a predição da Fase 0 («próclise sistemática») não se reproduz** | sup de Wilson **0,1015** < 0,15 ✅ | sup **0,2413** > 0,15 ❌ | ⚠️ **só na pré-registada** |
| **nenhum dos braços iguala o poeta** | — | 0,1296 e 0,1053 contra **0,0836** | ✅ |

**O resultado honesto é o direccional**, e vale por ser consistente: três
estatísticas (proporção, fracção de itens, clíticos por item) × duas réguas =
**seis estimativas, todas com o mesmo sinal**. Remover a instrução **nunca**
piorou a superfície. Nenhuma isoladamente exclui zero.

### 1.3 E uma hipótese com sinal próprio, que nenhum portão previu

O bloco de língua traz **três exemplos com clítico** — «dói-me», «estende-se»,
«chama-a». **E exemplos escorvam:**

| | clíticos totais | por item |
|---|---|---|
| braço C | **54** | 0,90 |
| braço A | **38** | 0,63 |

Diferença −0,267, IC [−0,600, +0,050] — **contém zero**, logo é hipótese e não
achado. Mas o mecanismo é plausível e tem consequência: se o bloco aumenta o uso
de construções clíticas, aumenta a **exposição ao erro**, e o saldo da regra pode
ser **negativo** — mais ênclises certas *e* mais próclises erradas. Fica
**registado antes** de a ablação por regra correr.

---

## 2. O que isto faz ao passo 34, e é a parte que importa

A [5Q](FASE-5Q-RELATORIO.md) mediu AUC **0,938–1,000** nas três vozes e atribuiu
a causa a «competência de superfície em português europeu e em **forma de
verso**» — ortografia e gramática. Três fases foram atrás dessa atribuição:

| fase | o que foi medir | o que encontrou |
|---|---|---|
| [5R](FASE-5R-RELATORIO.md) | detectar a ortografia | impossível com 2083 poemas — e **três das minhas razões da 5Q citavam formas que estão em Pessoa**: o meu ouvido para «o que é brasileiro» erra **uma em três** |
| [5T](FASE-5T-RELATORIO.md) | detectar a gramática | **não há sinal**: 0,045 no poeta contra 0,052–0,062 nos modelos |
| **5U** | ver se a instrução sustenta a superfície | **os eventos são 7 e 1 em 120 amostras** |

**A causa atribuída é rara demais para carregar a detecção.** Em 120 amostras
frescas das três vozes que falham, há **sete** próclises brasileiras e **uma**
marca ortográfica. Juízes cegos separaram real de gerado a 0,938–1,000; isso não
se faz com um defeito que aparece em 7 de 60 textos.

> **Logo o que torna estas três vozes identificáveis continua sem nome.** A 5Q
> nomeou uma causa a partir das **razões escritas pelos juízes**, e três fases de
> medição mecânica não a encontram. O que resta por explorar é a **forma** —
> metro, rima, estrutura de verso — e aquilo a que nenhum dos meus instrumentos
> chega.

### 2.1 E o braço ablado continua a ser português europeu

Verificação qualitativa, porque um nulo não vale nada se o braço A tiver
produzido lixo:

```
Lídia, não te podes de mim separar:
Em cada instante te vejo a ti mesma.
Se me ficas tu, é um tempo sem tempo,
O mundo para na eternidade.
...
Pede-me aos deuses que seja igual,
Lídia.
```

**Sem o bloco de língua no `system`**: ênclise correcta («Pede-me»), próclise
licenciada («não te podes», «Se me ficas»), vocativo horaciano, «tu». O modelo
não precisou da instrução para isto.

---

## 3. Defeitos do meu próprio desenho, encontrados nesta fase

| | o defeito | consequência |
|---|---|---|
| 1 | **os braços não foram intercalados** — o `for braco in BRACOS` é o ciclo exterior, logo as 60 do C correram **todas antes** das 60 do A | a **latência não é interpretável**: A dá 42,4 s medianos contra 37,2 s do C **apesar de** ter ~117 *tokens* menos de prefill. Ordem, temperatura do CPU e estado da cache estão confundidos com o braço. Os desfechos de defeito não dependem de tempo e sobrevivem |
| 2 | **ablar um bloco não muda só o seu conteúdo: muda a estrutura do prompt** | o braço A teve **3 falhas de guarda** contra **0** do C — «não parece verso» e duas **quebras de persona** («Álvaro de Campos, linguagem meta»). E o `REGRAS_SAIDA`, que proíbe exactamente isso, **não foi ablado**. Tirar 97 *tokens* do `system` mexe na saliência do que fica. O §4.2 antecipou a mudança de *tokens* e leu-a só como **latência** |
| 3 | a régua pré-registada licenciava **qualquer preposição à distância** | encontrado a ler uma linha do braço A, não por análise. Corrigido como sensibilidade declarada (§1.1) |

---

## 4. O que isto decide, e o que não

**Não decide se o bloco é portante.** O U3 disparou pela letra, e a letra não
tem poder: 7 eventos no braço de base. A leitura que o §3.1 lhe pré-escreveu —
«o passo 34 sai do prompt» — **fica sustentada por outra via**, e não por esta:
sai do prompt porque a **causa não está nomeada**, não porque se tenha provado
que instruir não funciona.

**Não autoriza remover o bloco.** O §3.1 já o dizia, e agora há uma razão a mais:
o defeito nº 2 do §3 mostra que removê-lo mexe em mais do que nele.

**Não mede a ortografia.** O detector da 5R a 20× tem **6% de cobertura** (medido
naquela fase) e deu **um** evento em 120. A regra da ortografia pré-1990 fica
**sem leitura** — e isso é falha do instrumento disponível, não resultado.

**Corrige a atribuição da 5Q**, que é o que a fase entrega: a ortografia e a
gramática **não podem** explicar um AUC de 0,938–1,000, porque não acontecem com
frequência suficiente.

### O que fica na mesa

1. **A forma de verso, agora como única candidata nomeada** do passo 34 — e sem
   nenhum instrumento construído. A [5M](FASE-5M-RELATORIO.md) mediu
   **comprimento**; metro, rima e estrutura estrófica nunca foram medidos.
2. **Reabrir a pergunta «o que dá os textos por gerados»** sem partir das razões
   dos juízes. O caminho limpo existe e está medido: o **AUC ao poeta** da
   [5F](FASE-5F.md)/[5O](FASE-5O-RELATORIO.md) é mecânico e corpus-fundado, e
   nunca foi corrido nas três vozes que falham.
3. **A ablação por regra**, com a hipótese de escorva do §1.3 registada e com os
   braços **intercalados**. Só vale a pena com uma taxa de base que dê eventos —
   e esta fase mostra que a taxa de base não dá.
4. **O passo 24 continua sem autorização e agora sem obstáculo medido:** nada
   aqui diz que o bloco de língua faz trabalho, e nada diz que não faz.

> **A lição, e é a décima.** As nove anteriores são sobre instrumentos e sobre a
> ordem em que se olha. Esta é sobre **a diferença entre uma causa atribuída e
> uma causa medida**.
>
> A 5Q produziu um número forte (AUC 0,938–1,000) e, ao lado dele, as **razões
> escritas pelos juízes**. Tratei as razões como achado e passei três fases a
> persegui-las: uma fechou a detecção por tamanho de corpus, outra não achou
> sinal, esta mostra que os eventos são sete em cento e vinte. **A razão que um
> juiz escreve é uma hipótese sobre o seu próprio processo, não uma medição
> dele** — e a 5R já me tinha avisado, ao mostrar que uma em três das minhas
> razões citava formas que estão em Pessoa.
>
> **O número da 5Q continua de pé; a explicação nunca esteve.** Três fases a
> instrumentar a explicação errada é o custo de não ter separado as duas coisas
> quando as publiquei juntas.
