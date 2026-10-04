# Fase 5C — o instrumento que falta: um desfecho com resolução no chão do Caeiro

Protocolo, **pré-registado antes de validar**. É o passo 5 da lista «[depois da
Fase 5](CONTROLO.md)», e é **pré-requisito** de repetir a Fase 5B: aquela fase
voltou sem veredicto porque o desfecho estava saturado, e nenhuma corrida nova
resolve isso.

**Objectivo:** construir um desfecho contínuo para a poética do Caeiro, validá-lo
contra os poemas **reais**, e estimar com ele o efeito que a Fase 5B não pôde
medir — sem o decidir.

---

## 1. O que a Fase 5B deixou, e porque é que isto vem antes de medir outra vez

A [Fase 5B](FASE-5B-RELATORIO.md) correu 60 amostras, 30 pares, dois
avaliadores cegos, e caiu em **G4**. A causa está contada em números: o critério
3a tomou **3 valores distintos** em 60 amostras, **50 delas no mesmo valor**, e
**22 dos 30 pares empataram em 0–0**. Um teste de sinais sobre um desfecho
saturado é inconclusivo por construção.

A âncora de 3a não está errada — foi escrita para julgar **se** a voz se cumpre,
e responde a isso. O que ela não faz é medir **quanto** falta, e é isso que uma
intervenção no prompt precisa que se meça. A âncora de 0 vale igual para «uma
volta a mais que 1» e para «filosofa de ponta a ponta».

Esta fase constrói o instrumento que falta. **Não mede a hipótese H5B**, e o §7
diz exactamente o que pode e não pode dizer sobre ela.

---

## 2. O instrumento: FAS, fracção de versos com atribuição de sentido

**FAS(texto) = (número de versos não vazios que contêm ≥ 1 termo da lista) ÷
(número de versos não vazios).**

Contínuo em [0, 1]. Num poema de 12 versos toma 13 valores possíveis, contra os
3 de 3a.

### 2.1 A lista, e a regra que a produz

A regra é mecânica e **nunca olha para as amostras geradas**. É o princípio do
§11 do relatório da Fase 5, e é a única defesa que aqui vale:

> «o vício não é ver os resultados, é a **regra de selecção olhar para o
> contraste que é o resultado**.»

1. **Corpo de derivação:** os poemas **reais** de Caeiro, e os poemas reais
   **portugueses** de ortónimo, Campos e Reis como contraste.
2. **Tokenização:** `[a-zà-ÿ]{3,}` em minúsculas. O mínimo de 3 caracteres
   elimina fragmentos de OCR (`s`, `d`, `p`, `ra`), que o piloto encontrou no
   topo da lista.
3. **Candidatos:** palavras com ≥ **8** ocorrências no total dos dois corpos.
4. **Pontuação:** log-odds suavizado, `log( p_outros / p_caeiro )`. Positivo
   significa **depletado no Caeiro** — vocabulário que o Caeiro real evita.
5. **Lista:** as **40** palavras de log-odds mais alto. Sem filtragem à mão.

**As palavras inglesas ficam fora pela regra 1, e isso não é um detalhe.** O
piloto correu primeiro com todo o corpus não-Caeiro e as 20 primeiras palavras da
lista eram `the`, `and`, `of`, `i`, `that`, `in`, `is`, `my`, `not` — o Caeiro não
tem um poema em inglês, logo **toda** palavra inglesa é maximamente «depletada»
nele. Isso é um detector de língua a fingir-se de detector de poética, e só se
viu porque o piloto imprimiu a lista.

**Nenhuma filtragem à mão, e a razão.** Cerca de uma dúzia das 40 não é
vocabulário de atribuição (`sob`, `inda`, `somos`, `rei`, `teus`, `rua`,
`lugar`, `parece`, `claro`, `fez`, `este`, `feito`). Removê-las à mão faria da
lista uma escolha minha, e a independência entre a regra e a quantidade medida é
precisamente o que dá valor a isto. A lista vai **inteira** para o relatório, e a
face validity é relatada como contagem, não usada como filtro.

**Um filtro mecânico testado e rejeitado.** Exigir que a palavra apareça em ≥ 15
ou ≥ 30 poemas não-Caeiro distintos, para matar vocabulário concentrado num só
poema, move a AUC de 0,809 para 0,812 e troca duas palavras (`fausto`, `ave` por
`fria`, `nesta`). Não paga um parâmetro a mais, e fica registado que foi testado
sobre poemas reais, antes de haver validação.

### 2.2 Contaminação, e o que sai do corpo de derivação

Os **41** poemas de Caeiro que foram recuperados para as perguntas da Fase 5B
**saem** do corpo de derivação. Sobram **78**.

A razão é a do §4 do relatório da 5B: as três amostras que lá chegaram ao topo da
poética transpunham um poema real que estava no prompt. Derivar a lista de um
poema que uma amostra copiou tornaria a lista parcialmente ajustada ao eco. É a
mesma exclusão que o Instrumento II da Fase 5 fez, pela mesma razão.

---

## 3. Os portões de validação

Estatística sem scipy: **permutação** (10000, semente 3), **AUC** por
Mann-Whitney normalizado, e **ρ de Spearman** por Pearson sobre postos.

| | portão | condição | o que decide |
|---|---|---|---|
| **V1** | **validade discriminante** | em dados **retidos**: AUC(Caeiro real < não-Caeiro real) ≥ **0,70** e permutação p ≤ 0,05 | o instrumento distingue a voz-alvo da não-alvo em poemas que não entraram na derivação. Se falhar, FAS não serve e a fase fecha sem instrumento |
| **V3** | **validade convergente** | ρ(FAS, 3a) ≤ **−0,25** nos **dois** avaliadores, nas 60 amostras da 5B | FAS acompanha o construto que a rubrica mede. Se falhar, FAS mede **vocabulário** e não poética — e o relatório tem de o dizer com essas palavras, não chamar-lhe instrumento de poética |
| **V4** | **especificidade** | \|ρ(FAS, n.º de versos)\| ≤ **0,35** | FAS não é um detector de comprimento disfarçado. Se falhar, o confundidor fica declarado e qualquer uso futuro tem de o controlar |

**V1 exige retenção, e é o ponto metodológico desta fase.** Os 78 poemas limpos
de Caeiro partem-se **ao meio** por semente fixa (39/39), e os não-Caeiro
também; a lista deriva-se **só** da metade de derivação e a AUC mede-se **só** na
metade retida. A AUC de 0,809 do piloto é in-sample e está inflacionada — a
lista foi derivada dos mesmos poemas que depois separou. O número que conta é o
retido, e ainda não existe.

### 3.1 O que **não** é portão, e porquê

**A resolução não é portão, porque já é conhecida.** O piloto mediu FAS nas 60
amostras da 5B **agrupadas, sem separar os braços** — a pergunta era variância,
não efeito — e deu **18 valores distintos**, mediana 0,062, IQR [0,000; 0,154],
máximo 0,429, com 28 das 60 a zero. Contra os 3 valores de 3a e 50 das 60 no
mesmo valor, é 6x mais resolução e 47% de chão em vez de 83%.

Pré-registar como portão uma coisa que já sei que passa seria teatro. Fica como
**propriedade medida e declarada**, com a nota de que foi medida cegamente ao
braço mas **não** cegamente a mim: eu já li as 60 amostras.

---

## 4. Ameaças, declaradas

- **Eu li as 60 amostras geradas antes de desenhar este instrumento.** É a
  ameaça principal e não a sei remover. A defesa é estrutural e não temporal: a
  regra de selecção da lista olha **só** para poemas reais, e não poderia ser
  ajustada ao contraste entre braços nem que eu quisesse, porque não vê as
  amostras. Mas a escolha de *FAS* como forma do desfecho é minha, e eu já vi o
  material.
- **Por isso o §7 proíbe que esta fase decida H5B.** A aplicação aos 30 pares
  existentes é explicitamente exploratória.
- **FAS é lexical, e a poética não é.** Um poema pode atribuir sentido sem usar
  nenhuma das 40 palavras («as coisas falam-me do que não dizem») e pode usá-las
  sem atribuir nada («não há mistério nenhum»). V3 mede se isto importa na
  prática; não o resolve.
- **A lista não é lematizada.** `sonhar` está na lista e `sonho`, `sonhos`,
  `sonhava` não, salvo se entrarem por mérito próprio. Sem lematizador garantido
  no ambiente, as formas de superfície são o que há, e isto reduz a
  sensibilidade — nunca infla.
- **O contraste é «não-Caeiro PT», que mistura três poéticas.** Parte do sinal
  pode ser tópico (Campos e a cidade, Reis e Lídia) e não atribuição de sentido.
  O relatório reporta, sem portão, a variante com o contraste limitado ao
  **ortónimo**, que partilha os assuntos do Caeiro e atribui sentido neles.
- **Os 78 poemas limpos são poucos**, e metade deles são 39. A AUC retida vem com
  intervalo por bootstrap, e um intervalo largo lê-se como intervalo largo.

---

## 5. Checklist

```
[ ] A1  protocolo commitado antes de existir qualquer número de validação
[ ] B1  partição 39/39 dos Caeiro limpos e do contraste, por semente fixa
[ ] B2  lista derivada SÓ da metade de derivação; publicada inteira
[ ] C1  V1: AUC retida com IC por bootstrap, e permutação
[ ] C2  V3: ρ de Spearman contra 3a de R1 e de R2
[ ] C3  V4: ρ contra o número de versos
[ ] D1  variante de contraste só-ortónimo, sem portão
[ ] E1  exploratório: Δ FAS emparelhado nos 30 pares da 5B, d, e o n implicado
[ ] F1  relatório
```

---

## 6. O que esta fase não faz

- **Não mede H5B.** Ver o §7.
- **Não toca em `src/voices.py`.**
- **Não substitui 3a.** Se V1, V3 e V4 passarem, FAS passa a **acompanhar** a
  rubrica como desfecho contínuo, e a rubrica continua a dizer se a voz se
  cumpre. São perguntas diferentes.
- **Não mede as outras vozes.** A lista é derivada contra o Caeiro, e aplicá-la
  ao Campos mediria o quanto o Campos não é Caeiro, o que não interessa a
  ninguém.
- **Não valida FAS como medida de qualidade poética.** Mede atribuição de
  sentido, que é **uma** das quatro coisas que a âncora de 3a nomeia.

---

## 7. O que esta fase pode autorizar, e o que está proibida de concluir

**Pode autorizar** o uso de FAS como desfecho primário de uma **Fase 5D**, que
repetiria o desenho da 5B — os dois braços, a regra de reescrita e o harness já
estão escritos e verificados — com amostras **novas** e o n que o §E1 indicar.

**Está proibida de concluir qualquer coisa sobre H5B.** Os 30 pares da 5B já
existem, eu já os li, e o desfecho foi escolhido depois. O Δ que sair do passo
E1 é uma **estimativa de efeito para dimensionar a 5D**, e o relatório
apresenta-o com essas palavras ou não o apresenta. Se eu achar, ao ver esse
número, que ele parece decidir algo, a resposta certa é a 5D — não uma
reinterpretação deste protocolo.

É a mesma regra que a Fase 5B aplicou ao único intervalo que lhe excluiu o zero,
e aplicou-a contra o seu próprio interesse.
