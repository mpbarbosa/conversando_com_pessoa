# Fase 5E — relatório: a âncora reprova o Caeiro real, e não serve para julgar geração

Protocolo em [`FASE-5E.md`](FASE-5E.md), pré-registado em `3fc15fe` **antes de
existir qualquer pontuação**. As duas pontuações foram commitadas em `2a6e26d`
**antes de a chave ser aberta**.

---

## 1. O que se decidiu

**W1 dispara e W2 falha.** É a célula que o §4 do protocolo pré-registou como
«**o pior caso para as quatro fases**»:

> | W1 | W2 | leitura |
> |---|---|---|
> | sim | não | a âncora **não serve para julgar geração**. É o pior caso para as quatro fases |

E é legível, porque os dois portões de veto passaram com folga:

| portão | condição | medido (estimativa conjunta) | |
|---|---|---|---|
| **W4** piso de concordância | κ_lin ≥ 0,30 e exacta ≥ 50% | **κ_lin = 0,784** · exacta **88,3%** · discordância máxima 1 | **passa** |
| **W3** controlo negativo | AUC(ortónimo < Caeiro real) ≥ 0,70, p ≤ 0,05 | **0,811**, IC95% [0,690; 0,915], **p=0,0001** | **passa** |
| **W1** a âncora não premeia o real | mediana ≤ 1 e < 50% com 2 | mediana **0,5** · **3 de 20** com 2 (**15%**) | **dispara** |
| **W2** distingue autêntico de gerado | AUC(gerado < real) ≥ 0,70, p ≤ 0,05 | **0,655**, IC95% [0,488; 0,815], **p=0,112** | **falha** |

Os três avaliadores possíveis — R1, R2 e a média — concordam em todos os quatro
veredictos. **Não há leitura alternativa nesta fase.**

---

## 2. O número que decide: 3 de 20

A âncora de 3a dá a sua nota máxima a **15% dos poemas autênticos de Caeiro**.

| grupo | mediana | média | 0 | 0,5 | 1 | 2 |
|---|---|---|---|---|---|---|
| **R** Caeiro **real** | 0,5 | **0,70** | 7 | 4 | 6 | **3** |
| **O** ortónimo real | 0,0 | 0,025 | 19 | 1 | — | — |
| **G** Caeiro **gerado** | 0,0 | 0,35 | 13 | 2 | 4 | 1 |

E **sete dos vinte poemas reais de Caeiro levam 0 dos dois avaliadores** — a nota
cuja definição é «filosofa, interpreta, atribui significado oculto,
personifica». Entre eles:

| | |
|---|---|
| `poem_1108` | «Num dia excessivamente nítido… **Vi que não há Natureza, / Que Natureza não existe**… A Natureza é partes sem um todo.» |
| `poem_1112` | «Da mais alta janela da minha casa / Com um lenço branco digo adeus / Aos meus versos que partem para a humanidade» |
| `poem_1126` | «Se as coisas fossem diferentes, seriam diferentes: eis tudo… Ai de ti e de todos que levam a vida / A querer inventar a máquina de fazer felicidade!» |
| `poem_3540` | «No meu prato que mistura de Natureza! / As minhas irmãs as plantas» |

O primeiro é um dos poemas mais citados de Caeiro. A âncora reprova-o por
filosofar — e **ele filosofa**: a âncora não está a errar na aplicação, está a
errar no alvo. Foi escrita a partir da **persona** em `src/voices.py`, que diz
«não pensas sobre o que vês — vês», e isso é o **programa** de Caeiro, não a sua
obra.

### 2.1 Os quatro 2 de toda a folha, e o que o quarto é

Quatro itens em sessenta receberam 2, e **os mesmos quatro nos dois
avaliadores** — um que sabia o desenho e um que não sabia que havia desenho:

| | grupo | |
|---|---|---|
| W29 `poem_3330` | **real** | «Uma gargalhada de raparigas soa do ar da estrada.» |
| W37 `poem_3455` | **real** | «Passa uma borboleta por diante de mim» |
| W60 `poem_588` | **real** | «Copio a Natureza e não a interrogo.» |
| **W35** `B35` | **gerado** | «O vento sopra na mata sem querer.» |

**O único item gerado que atingiu a nota máxima da âncora é exactamente a
amostra que o §4 do relatório da Fase 5B identificou como transposição**: copia
33% dos seus versos do `poem_350`, «Mas não é indiferentemente por não se
importar comigo / E eu não exprimir desolação com isto» saiu como «Mas não é sem
querer por não amar a mata, / E eu não exprimir saudade com isto».

A 5B levantou esse confundidor como uma nota de cautela a partir de três
amostras. Esta fase mostra-o em funcionamento: **na única vez em que a geração
alcançou o critério, alcançou-o por cópia.**

---

## 3. O que a âncora é, então: um bom filtro negativo e uma má medida positiva

W3 passou com AUC de 0,811 e p=0,0001, e o ortónimo deu **19 zeros em 20**. A
âncora **não é ruído**: reconhece com fiabilidade o que não é Caeiro.

O que ela não consegue é graduar o que é. O diagnóstico, nas três medidas:

- **reconhece o não-Caeiro** — ortónimo a 0,025 de média contra 0,70 do Caeiro
  real;
- **reprova o Caeiro** — 15% de notas máximas nos poemas autênticos;
- **não separa autêntico de gerado** — AUC 0,655 com IC95% a conter 0,5.

Serve para dizer «isto não é Caeiro». Não serve para dizer «isto falha a
poética do Caeiro», que é precisamente a frase que as Fases 5 e 5B escreveram.

---

## 4. O que isto faz às quatro fases anteriores

Com cuidado, porque a tentação de generalizar aqui é grande.

**O que cai.** A leitura **absoluta** do resultado da Fase 5 — «o Caeiro gerado
**não cumpre** a poética», a partir de mediana 0,0 em 3a. Essa leitura exige que
a âncora premeie o Caeiro autêntico, e ela premeia 15% dele. Uma mediana de 0,0
no gerado é compatível com a mediana de 0,5 no real medida aqui, e a diferença
entre as duas não atinge significância (W2, p=0,112).

**O que não cai.** A Fase 5 rejeitou H — o contexto não degrada a poética — por
uma ablação **emparelhada**, onde as duas condições foram julgadas pela mesma
âncora. Um instrumento enviesado para baixo continua a servir para comparar duas
condições que ele mede do mesmo modo. **G2 mantém-se.** O mesmo vale para o G4
da Fase 5B: a saturação que a fez cair está agora explicada — a âncora dá 0 a
quase tudo, incluindo ao original — mas o veredicto «inconclusivo» não muda.

**O que fica em suspenso.** A inferência que encadeou as fases 5B a 5E: «o
Caeiro é a voz que falha, logo o défice está na persona». O Caeiro é a voz que
tira 0 nesta âncora — e o Caeiro **real** também tira. A sequência partiu de um
nível absoluto que o instrumento não suporta.

**E o que se ganha.** Três fases de instrumentação negativa valem o que custaram
se esta for a conclusão: as Fases 5 e 5B mediram **a distância entre a geração e
uma idealização da persona**, não a distância entre a geração e Pessoa. São
coisas diferentes, e a segunda é a que o projecto quer.

---

## 5. A estrutura do erro, e onde ela já tinha sido vista

A Fase 5 encontrou esta exacta estrutura no seu **juiz LLM** e mediu-a:

> «esse juiz dá 65% aos poemas gerados e **45% a Pessoa autêntico** — ordena a
> imitação 20 pontos acima do original, porque os poemas foram escritos para
> casar com a descrição que ele lê. É circular.»

E escreveu a prescrição certa: «se precisares de juiz LLM, as descrições têm de
vir de outra fonte que as personas». Depois aplicou-a ao juiz LLM e **não à sua
própria rubrica manual**, que tem a mesma origem — a persona.

A diferença de sinal é instrutiva e vale registá-la. O juiz LLM da Fase 5
**sobrevalorizava** o gerado; esta âncora **subvaloriza** o autêntico. São o
mesmo defeito visto dos dois lados: um critério derivado do tratamento mede a
proximidade ao tratamento, e não à coisa.

---

## 6. Ameaças, revisitadas — as duas principais saem desarmadas

O §6 do protocolo declarou duas ameaças e, em cada uma, **a direcção em que
empurravam**. As duas empurravam **contra** W, e W disparou de qualquer maneira:

- **Eu reconheci cerca de 18 dos 20 itens gerados**, porque li as 60 amostras na
  Fase 5B, e declarei-o no meu ficheiro de pontuação antes de a chave abrir.
  Reconhecer uma amostra como gerada empurra-a para baixo, o que **favorece** a
  conclusão antiga e dificulta W1 e W2. Além disso **R2 nunca viu nada disto** e
  deu uma mediana **mais alta** ao Caeiro real do que eu (1,0 contra 0,0), ou
  seja, W1 está mais forte no avaliador sem o viés.
- **Os poemas canónicos podem ser reconhecidos**, e o reconhecimento empurra o
  Caeiro real **para cima**, contra W1. Mesmo assim 15%.

Fica em pé:

- **Os dois avaliadores são sessões do mesmo modelo** a ler a mesma âncora, e a
  concordância de 88,3% pode ser erro correlacionado. O κ mede concordância,
  nunca correcção. É a ressalva da 5B §6.3 e é a última que sobrevive — mas
  note-se que aqui ela é a mais fraca de todas as fases: a conclusão não depende
  de um limiar fino, depende de 3 em 20.
- **n=20 por grupo**, e os IC95% são largos. O de W2 — [0,488; 0,815] — não
  exclui que a âncora separe autêntico de gerado; diz que com 20 por grupo não
  se vê.
- **Os numerais romanos saíram** dos textos (§6 do protocolo), fechando a fuga de
  cegueira que a 5D tinha. Dois dos itens reais com 2 e um com 0 eram poemas com
  numeral, logo a remoção não produziu o resultado.

---

## 7. Checklist

```
[x] A1  protocolo commitado antes de existir pontuação (3fc15fe)
[x] B1  60 itens frescos (20 R + 20 O + 20 G), nenhum dos 60 da Fase 5D
[x] B2  chave fechada; numerais romanos removidos; enquadramento de R2 verificado
[x] C1  R1 pontuou com a âncora, com razão por item, e declarou o reconhecimento
[x] C2  R2 pontuou, cego ao desenho e aos grupos
[x] C3  as duas pontuações commitadas antes de a chave abrir (2a6e26d)
[x] D1  W4 e W3 primeiro, na estimativa conjunta — **passam os dois**
[x] D2  W1 **dispara**, W2 **falha**; por avaliador em separado, sem decidir, e
        os três veredictos coincidem
[x] E1  relatório
```

---

## 8. O que isto autoriza, e o que não

**Autoriza — e é a primeira autorização positiva desde a Fase 3B — recalibrar a
âncora de 3a do Caeiro.** W1 disparou com os dois portões de veto a passar, nos
três avaliadores, e com as duas ameaças principais a empurrar em sentido
contrário. A âncora não premeia o original, e um critério que reprova Pessoa não
pode julgar quem o imita.

**Não autoriza escrever a âncora nova aqui.** Isso pede uma fase própria, com a
âncora pré-registada **antes** de ver amostras, e com a condição de aceitação que
esta fase acabou de tornar óbvia e que nenhuma das anteriores tinha:

> **A âncora nova tem de premiar o Caeiro real.** O critério de aceitação é uma
> medição no corpus — mediana ≥ 1 e uma fracção substancial de 2 nos poemas
> autênticos — e não a opinião de quem a escreve. Os 20 poemas desta folha e os
> 20 da 5D já estão seleccionados e pontuados; os restantes 24 elegíveis servem
> de conjunto retido, que é a defesa que a 5C ensinou.

**Não autoriza reabrir a Fase 5.** O G2 dela foi uma comparação emparelhada e
sobrevive (§4).

**Não autoriza concluir que o modelo escreve bom Caeiro.** W2 falhou, o que
significa que a âncora não distingue — não que não haja diferença. A média do
gerado é metade da do real (0,35 contra 0,70), e com n=20 isso não se resolve.
Medir se o gerado é pior que o original é uma pergunta que **continua aberta**, e
agora com a razão certa: faltava o instrumento, e o instrumento que havia estava
calibrado contra uma ficção.

### O que a cadeia das cinco fases deixa, em três linhas

A Fase 5B não pôde medir por saturação. A 5C falhou a construir um desfecho por
falta de corpus. A 5D construiu um com resolução e apontou a âncora. A 5E mediu
a âncora e encontrou-a a reprovar o original em 85% dos casos.

**O suspeito que estas fases andaram a perseguir — a persona do Caeiro — nunca
foi medido, porque a régua estava torta.** Endireitar a régua é o passo seguinte,
e é a primeira vez em cinco fases que se sabe exactamente o que medir e qual é a
condição de aceitação.
