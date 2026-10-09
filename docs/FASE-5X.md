# Fase 5X — A descodificação, e a hipótese de que a penalização proíbe a rima

**[Passo 17](CONTROLO.md), e a via que a [5W](FASE-5W-RELATORIO.md) deixou
aberta.** Pré-registada em 2026-10-09, **antes de qualquer amostra**.

---

## 1. A hipótese, e é mecanística

A [5W](FASE-5W-RELATORIO.md) fechou o prompt como via para a forma, com três
apoios: a instrução existe e é ignorada, reforçá-la dá sinal **negativo**,
exemplificá-la move tudo menos a rima. **O que o W4 autorizou foi a
descodificação.**

E há uma hipótese específica, que não é «experimentar parâmetros»:

> **`repeat_penalty` penaliza *tokens* repetidos. A rima **é** repetir uma
> terminação.**

O `llama.cpp` divide os *logits* dos *tokens* que apareceram nos últimos
`repeat_last_n` — que o projecto **não define**, logo é a omissão do Ollama,
**64**. Duas rimas alternadas num poema estão a ~15–25 *tokens* de distância,
**dentro da janela**. Se a terminação portuguesa for um *token* próprio — `ade`
em «estabilidade»/«tranquilidade», `ia` em «havia»/«servia» —, a opção que existe
para evitar degeneração está **activamente a penalizar a segunda rima**.

### 1.1 E a constante nunca foi medida

`REPEAT_PENALTY = 1.1` é **a única das quatro opções de descodificação sem
comentário de proveniência** em [`ollama.py`](../src/generation/ollama.py). Entrou
na Fase 0 por um motivo registado na tabela de defeitos do `CONTROLO.md` §4 —
«`repeat_penalty` não definido: 8B degenerou em ciclo; atribuído ao modelo em vez
do arranque» — e **nunca foi remedida**, nem quando o modelo mudou na
[5S](FASE-5S-RELATORIO.md).

> **Não posso inspeccionar as fronteiras de *token* do llama localmente** — o
> tokenizador está atrás de autenticação e o `prompt_eval_count` do Ollama dá
> contagens, não fronteiras. Logo a hipótese **vai a teste pela sua predição** e
> não pela sua mecânica, e isso está declarado.

---

## 2. Os três braços

Muda-se **só** o dicionário de `_opcoes`, por subclasse, sem tocar em `src/`.

| braço | `repeat_penalty` | `temperature` | |
|---|---|---|---|
| **B** | **1,1** | **0,9** | produção |
| **P** | **1,0** (desligada) | 0,9 | a hipótese do §1 |
| **T** | 1,1 | **0,5** | o outro lado do [passo 17](CONTROLO.md): menos entropia, mais formulaico |

**Voz única: o ortónimo**, que é onde o fosso está medido (densidade de rima
**0,0997** no poeta contra **0,0095** no gerado, [5W §1](FASE-5W-RELATORIO.md)) e
onde a persona **manda** rimar.

**10 perguntas × 2 repetições × 3 braços = 60 amostras**, braços
**intercalados** (o defeito nº 1 da [5U](FASE-5U-RELATORIO.md)), mesmas sementes,
mesmo modelo.

### 2.1 O desfecho é contínuo, e a potência está calculada

**Densidade de rima** — pares de versos que partilham a chave sobre pares
possíveis, com os pares de palavra igual excluídos. É a lição da
[5W §1](FASE-5W-RELATORIO.md): o binário «o poema rima» deitava fora um factor
de dez.

**E a potência vem medida da 5W**, não estimada: com 20 amostras por braço, o
IC95 por *bootstrap* da diferença de densidades tinha meia-largura de **~0,008**
sobre uma base de 0,0095. **Logo este desenho detecta uma duplicação da
densidade e não menos**, e o §3 fixa o limiar em cima disso.

---

## 3. Portões

| | nome | dispara se | leitura, escrita agora |
|---|---|---|---|
| **X1** | **a penalização proíbe a rima** | densidade(**P**) − densidade(**B**) com IC95 a **excluir zero** e positiva | a hipótese do §1 confirma-se: a opção que existe para evitar degeneração estava a custar a rima |
| **X2** | **menos entropia dá mais rima** | densidade(**T**) − densidade(**B**) com IC95 a excluir zero e positiva | o passo 17 tem uma direcção, e é a temperatura |
| **X3** | **sem degeneração** | em nenhum braço de intervenção sobem: linhas duplicadas, plágio, truncatura, falhas de guarda; nem desce o `e_verso`; nem o metro se afasta do 0,7572 do poeta mais que o B | **tem veto.** O `repeat_penalty` existe por causa de um ciclo degenerado; desligá-lo sem medir isso seria repetir o defeito que o criou |
| **X4** | **a descodificação também não** | nem X1 nem X2 | então **nem o prompt nem a descodificação** alcançam a forma, e o que sobra é afinação ou aceitar que o produto serve uma voz. É o resultado mais consequente que esta fase pode dar |

### 3.1 A decisão, pré-escrita — e **não** é embarcar

| | decisão |
|---|---|
| **X1 ou X2**, com **X3** | **não embarca nesta fase.** O `_opcoes` é **global** e o [Caeiro é a única voz que funciona](FASE-5O-RELATORIO.md) (AUC ao poeta **0,526**). Mudar a constante mexe-lhe sem medição. Fica autorizado **abrir uma fase de verificação de dano no Caeiro**, e só depois embarcar |
| **X1 ou X2**, sem **X3** | não embarca, e o relatório diz o que degenerou |
| **X4** | nada entra; declara-se a via fechada |

**É a disciplina da [5S](FASE-5S-RELATORIO.md) aplicada antes e não depois:**
aquela fase descobriu, a duas linhas de `grep`, que o roteador partilhava a
constante que ia mudar. Aqui a constante partilhada é conhecida de antemão, e a
decisão de não embarcar sem a medir está escrita **antes** de haver número.

### 3.2 O que esta fase não decide

- **Não mede voz nem conteúdo.** Mede forma, como a 5V e a 5W.
- **Não afina `top_p` nem `num_predict`.** Um braço por constante custa 20
  amostras; estes dois são os que têm hipótese.
- **Não toca no `repeat_last_n`**, que fica na omissão do Ollama (64) nos três
  braços — e é declarado porque é ele que define a janela da hipótese.

---

## 4. Ameaças

### 4.1 Desligar a penalização pode trazer o ciclo de volta

É o risco central, é histórico e não hipotético, e é o que o **X3 tem veto**
para apanhar. A bateria é mecânica: fracção de linhas que repetem uma linha
anterior do mesmo poema, plágio contra o contexto, `e_verso`, truncatura,
falhas de guarda. **Se o braço P degenerar, o X3 não dispara e a hipótese morre
com a razão à vista.**

### 4.2 A mecânica fica por verificar

Não consigo ver as fronteiras de *token* do llama (§1). Se o X1 disparar, fica
provado o **efeito** e não o **mecanismo** — e a diferença importa, porque o
remédio para «a penalização pune a rima» é diferente do remédio para «a
penalização muda a amostragem de outra maneira qualquer».

### 4.3 Vinte amostras por braço

O §2.1 diz o que isso dá: **uma duplicação, e não menos**. Um efeito pequeno e
real sai como nulo, e esse nulo tem de ser lido como «não detectável aqui», não
como «não existe» — o erro que a [5U](FASE-5U-RELATORIO.md) cometeu e corrigiu.

### 4.4 Eu quero que a hipótese do §1 seja verdade

É elegante — a opção que evita um defeito a causar outro — e isso é exactamente
quando se escreve o limiar antes. Está escrito: IC a excluir zero **e** o veto do
X3 **e** a não-embarcação do §3.1.

---

## 5. Lista de verificação

```
[ ] A1  tres bracos por subclasse de `_opcoes`, asseridos antes de gerar
[ ] A2  60 amostras, bracos INTERCALADOS, voz unica, mesmas sementes
[ ] A3  desfecho continuo: densidade de rima, com o nulo de permutacao do braco
[ ] A4  X3: bateria de degeneracao + metro + os instrumentos da 5T/5U
[ ] B1  X1, X2, X3, X4 e a decisao do §3.1
[ ] C1  relatorio FASE-5X-RELATORIO.md
[ ] C2  CONTROLO.md
```

**Sessões paralelas:** verificado antes de abrir. `git add` com ficheiros
nomeados.
