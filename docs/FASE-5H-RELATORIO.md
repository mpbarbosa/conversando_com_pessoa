# Fase 5H — relatório: era o modelo, e o llama3.1 fecha 75% do fosso

Protocolo em [`FASE-5H.md`](FASE-5H.md), pré-registado em `cd5954c` **antes de
existir uma amostra**. As duas pontuações foram commitadas em `5f8e761` **antes
de a chave ser aberta**.

---

## 1. O que se decidiu

**M1 disparou, e M3 condiciona-o.** O modelo importa, e importa muito.

| leitura | mediana Q | mediana L | Δ (L−Q) | IC95% | L/Q/= | d | p | portão |
|---|---|---|---|---|---|---|---|---|
| **conjunta** | 0,50 | **1,50** | **+0,700** | **[+0,417; +0,983]** | **19 / 2 / 9** | **21** | **0,0002** | **M1** |
| R1 | 0,00 | 1,00 | +0,767 | [+0,433; +1,067] | 18 / 2 / 10 | 20 | 0,0004 | M1 |
| R2 | 1,00 | 2,00 | +0,633 | [+0,367; +0,900] | 15 / 1 / 14 | 16 | 0,0005 | M1 |

As três leituras disparam M1 por si. **M5 não dispara. M4 não dispara.**

É o primeiro resultado positivo de consequência em toda esta sequência, e o
primeiro portão de confirmação a disparar desde a Fase 3B.

---

## 2. O tamanho: 75% do fosso

A régua externa está medida e vem da [Fase 5F](FASE-5F-RELATORIO.md), com esta
mesma âncora:

| | 3a′ |
|---|---|
| Caeiro **real** | **1,604** |
| Caeiro gerado (qwen2.5:7b) | 0,675 |
| **fosso** | **0,929** |

E esta fase mede:

| | média 3a′ (conjunta) |
|---|---|
| **Q** — `qwen2.5:7b` | **0,75** |
| **L** — `llama3.1:8b` | **1,45** |

**Δ = +0,700 num fosso de 0,929: o llama3.1 fecha 75% dele.** Fica a **0,154**
do Caeiro autêntico — uma distância menor que a largura do intervalo de
confiança desta fase.

As distribuições mostram-no melhor que as médias:

| nota 3a′ (conjunta) | 0 | 0,5 | 1 | 1,5 | 2 |
|---|---|---|---|---|---|
| **Q** | 9 | 9 | 5 | 2 | 5 |
| **L** | 2 | 4 | 3 | 7 | **14** |

O qwen tem 18 das 30 amostras em 0 ou 0,5; o llama tem **14 das 30 na nota
máxima**.

**A comparação com 1,604 é entre amostras e não é um teste.** O Δ de 0,700, com
o seu intervalo, é o resultado; os 75% são uma leitura de escala e dizem-se com
essa palavra.

---

## 3. E ganhou a correr nas condições do adversário

Está no §3.2 do protocolo, escrito antes de medir, e agora conta a favor do
resultado em vez de contra:

> «As opções são as de serviço e **não se afinam por modelo**. É uma decisão com
> custo e fica declarada: o `repeat_penalty=1,1` e o `num_predict=220` foram
> escolhidos na Fase 0 **para o qwen**.»

O llama3.1 correu com `temperature`, `top_p`, `repeat_penalty` e `num_predict`
calibrados para o seu concorrente, e com um prompt cujo orçamento de tokens é
contado pelo tokenizador do encoder. **Ganhou 0,700 pontos assim.** O número é
portanto um piso e não um tecto — o que uma afinação própria daria fica por
medir, e é a razão pela qual não afinar foi a decisão certa.

E o confundidor que mataria a fase foi **verificado ausente**: a asserção do
§3.1 comparou `system` e `user` byte a byte entre braços nas 10 perguntas, e
passou. Os dois modelos receberam o mesmo prompt, carácter a carácter.

---

## 4. O que a troca custa: M3 disparou

| | qwen2.5:7b | llama3.1:8b |
|---|---|---|
| **3a′ poética** | 0,75 | **1,45** |
| **3b forma** | **1,383** | 1,200 |
| versos (mediana) | **13,5** (8–17) | 7,5 (4–15) |
| não é verso | **0** | 1 |
| critério 2 a zero | 2 | **0** |
| plágio | 1 | 1 |
| truncaturas | 1 | **0** |
| segundos (mediana) | 35,5 | **25,1** |

**M3 disparou pela forma**, e a causa é simples: a âncora de 3b pede **10 a 20
versos** e o llama escreve 7,5 de mediana, com mínimo de 4. Perde por ficar fora
do intervalo, não por escrever mal.

**Mas a evidência do custo é mais fraca que a do ganho, e isso tem de se dizer.**
O Δ3b de −0,183 tem IC95% [−0,367; −0,017] a excluir zero na conjunta, mas o
teste de sinais dá **p=0,267** (4 pares a favor de L, 9 de Q, 17 empates). O
intervalo e o binomial discordam, o que num n destes significa que o efeito em
3b está no limiar do detectável. **O ganho em 3a′ está estabelecido; o custo em
3b está indiciado.**

E o resto da troca **não** custa: o llama é 30% mais rápido, trunca menos, não
teve nenhuma amostra reprovada em português, e empata no plágio. **A latência
surpreendeu-me** — assumi ao escrever o protocolo que o 8B seria mais lento, e
foi bom que a latência estivesse no §5.1 sem portão, porque um portão meu teria
ido na direcção errada.

---

## 5. A concordância, e o que melhorou nela

| | 3a′ |
|---|---|
| κ ponderado linear | **0,548** |
| concordância exacta | **60,0%** |
| discordância máxima | 2 |
| médias | R1 0,88 · R2 1,32 |

R2 continua mais generoso — terceira fase seguida — mas o κ subiu de **0,334**
(5G) para **0,548**, e a **forma** das duas distribuições passou a ser a mesma:
na 5G o meu modo estava em 0 e o dele em 2; aqui os dois têm o modo em 2.

A explicação mais provável é a que a chave confirma: **esta folha tinha dois
registos genuinamente diferentes**, e um sinal forte é mais fácil de concordar
sobre do que um sinal ausente. Declarei antes de abrir a chave que sentira «dois
registos distintos na folha, um mais curto e mais seco», sem saber de que braço
era. Era o llama.

Isso é também a prova mais directa contra a ameaça do §7.1 — eu podia reconhecer
o braço pelo estilo —, e não a desfaz: **R2 nunca viu amostra de nenhum dos dois
modelos e mediu Δ=+0,633 com p=0,0005.** O efeito não depende do meu
reconhecimento.

---

## 6. Ameaças

- **Eu podia reconhecer o braço pelo estilo** (§7.1), e declarei-o antes de
  pontuar, incluindo a impressão que tive. A defesa é R2, que não podia, e que
  mediu o mesmo. A direcção do viés era imprevisível porque eu não tinha
  preferência declarada entre os modelos — e continuo a não ter, porque o §4
  mostra que a troca tem custo.
- **Opções não afinadas por modelo** (§3.2). Favorece o qwen, logo o Δ é um piso.
- **Uma voz, dez perguntas, 30 pares, uma âncora.** H5H confirma-se para o
  Caeiro, nestas perguntas, com este instrumento.
- **A âncora 3a′ foi escrita por mim** (Fase 5F) e eu sou um dos avaliadores.
  Aqui há uma defesa que a 5G não tinha: o efeito é grande e R2, que não a
  escreveu, reproduz-o com p<0,001.
- **Três artefactos de formato** que a guarda não apanhou: H57 começa com
  «Pergunta:», H25 tem um «---» solto, H17 tem linha de título. E **H41 repete
  «Uma árvore é uma árvore; um poente é um poente» verbatim da persona**, o que
  viola o `REGRAS_SAIDA`. Declarados antes da chave; pesaram em 3b e não em 3a′.
  São defeitos de guarda, e a sua distribuição por braço fica no
  `03-resultados.json`.

---

## 7. Checklist

```
[x] A1  protocolo commitado antes de existir amostra (cd5954c)
[x] A2  asserção de prompt byte a byte igual entre braços — **passou nas 10**
[x] A3  60 amostras, semente base 20261006, em blocos por modelo
[x] A4  folha escrita por folha.py com a âncora 3a′; chave fechada
[x] B1  R1 pontuou 3a' e 3b às cegas, com razão e a ameaça do §7.1 declarada
[x] B2  R2 pontuou, cego ao desenho e à existência de dois modelos
[x] B3  as duas pontuações commitadas antes de a chave abrir (5f8e761)
[x] C1  sinais e bootstrap na conjunta; **M1** nas três leituras, **M3**
        condiciona, M4 e M5 não disparam
[x] D1  potência do §6 repetida; latência relatada, e corrigiu a minha suposição
```

---

## 8. O que isto autoriza, e o que não

**Autoriza investigar a troca do modelo de serviço — e só isso.** Está escrito no
§5 do protocolo, antes de se saber o resultado, e cumpre-se agora que o
resultado é favorável: trocar o gerador é uma decisão de produto com custos que
60 amostras numa voz não medem — memória, as guardas de língua calibradas na
Fase 0 para o qwen, o roteador da Fase 4, e as outras três vozes.

**Com o custo nomeado, que é o que o M3 serve para obrigar:** o llama escreve
poemas **demasiado curtos** para a âncora de forma do Caeiro — 7,5 versos de
mediana contra 10–20 pedidos. Qualquer investigação da troca começa aí, e começa
barata: `num_predict` e uma instrução de comprimento na `forma` são as duas
coisas mais fáceis de mexer em todo este projecto.

**Não autoriza trocar.** Não autoriza nada sobre as outras três vozes. E não
autoriza ler os 75% como um teste — é uma leitura de escala contra um número
medido noutra amostra.

**Fecha a cadeia de eliminação**, e com um positivo depois de quatro negativos:

| suspeito | veredicto |
|---|---|
| o contexto recuperado | eliminado — Fase 5, G2 |
| o chão ser real | eliminado — Fase 5E |
| a forma interdictiva da persona | eliminado — Fase 5G, G2, IC95% [−0,30; +0,18] |
| **o modelo** | **confirmado — Fase 5H, M1, Δ=+0,700, p=0,0002** |

Sobra, por eliminação, o **conteúdo** da persona — e o que esta fase mostra é
que ele explica no máximo os 0,154 que o llama ainda deixa em cima da mesa, se
explicar alguma coisa.

### O que fica na mesa, em ordem

1. **A forma do llama**: `num_predict` e um pedido explícito de 10–20 versos,
   medido com a mesma âncora. É o passo que custa menos e desbloqueia a decisão
   de troca.
2. **As outras três vozes com os dois modelos.** O Caeiro era o caso extremo; o
   Reis já dava 2,0 na âncora antiga. Se o llama piorar o Reis, a troca deixa de
   ser óbvia.
3. **Afinar as opções por modelo**, e remedir. O Δ de 0,700 é um piso.
4. **O `qwen2.5:3b`**, instalado e nunca medido: diria se isto é capacidade ou
   família.
5. Apertar a âncora na fronteira 1/2 — passo 12 — continua aberto, e o κ de
   0,548 é melhor que o de 0,334 da 5G mas não é bom.
