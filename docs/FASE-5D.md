# Fase 5D — a contagem de voltas: o desfecho que a âncora já define e descarta

Protocolo, **pré-registado antes de julgar**. É o passo 5 da lista «[depois da
Fase 5](CONTROLO.md)», pela segunda via — a [Fase 5C](FASE-5C-RELATORIO.md)
tentou a via lexical e fechou-a por falta de corpus.

**Objectivo:** definir e validar um desfecho contínuo para a atribuição de
sentido no Caeiro, **antes** de o aplicar a qualquer amostra gerada.

---

## 1. Porque é esta a via, depois de a lexical ter falhado

A [Fase 5B](FASE-5B-RELATORIO.md) caiu em G4 por saturação: o critério 3a tomou
3 valores em 60 amostras, 50 no mesmo. A [Fase 5C](FASE-5C-RELATORIO.md)
construiu um desfecho lexical com 8x mais resolução e **rejeitou-o**: a AUC caía
de 0,869 in-sample para **0,544** retida, porque 78 poemas limpos de Caeiro não
bastam para derivar uma lista que generalize.

O que sobra estava à vista desde o princípio, e é mais simples. A âncora de 3a,
escrita na Fase 5 e nunca tocada, diz:

> **1** — «sensorial na maior parte, com **uma** volta simbólica ou moral»
> **0** — «filosofa, interpreta, atribui significado oculto, personifica»

**A âncora conta voltas, e depois joga a contagem fora**: o 0 serve igual para
duas voltas e para dez. O desfecho que falta é a contagem que ela já faz.

Três coisas recomendam-no acima do que a 5C tentou:

1. **Não precisa de ser derivado de um corpus.** O construto vem da âncora, que
   está pré-registada desde a Fase 5. Não há lista a ajustar, logo não há como
   sobreajustar — que é exactamente o que afundou o FAS.
2. **Os poemas reais passam a ser corpo de teste e não de derivação.** É a
   diferença estrutural, e é a razão pela qual 119 poemas de Caeiro chegam aqui
   e não chegavam lá.
3. **Valida-se contra três grupos ao mesmo tempo**, numa só folha cega.

---

## 2. O desfecho: FVV, fracção de versos com volta

### 2.1 O que é uma «volta»

Um verso tem **volta** se fizer pelo menos uma destas quatro coisas, que são as
quatro que a âncora de 3a nomeia — nem mais uma:

| | tipo | o verso… |
|---|---|---|
| **A** | **significado oculto** | diz ou sugere que a coisa significa algo além de si: «sentido em cada pedra», «nas entrelinhas», «segredos dos montes» |
| **B** | **metafísica ou símbolo** | afirma sobre o ser, a verdade, a essência, o mistério, o nada, o destino: «a realidade segue as suas leis», «o não-ser» |
| **C** | **moral** | prescreve, aconselha, tira lição: «e assim deve ser», «ensina-me a sonhar» |
| **D** | **personificação ou espelho** | atribui a uma coisa acto mental, vontade ou sentimento, ou usa a natureza como espelho de sentimento: «a montanha sorri», «o riacho esquece a fonte», «praia desolada» |

**Regras de contagem, para que dois contadores cheguem ao mesmo número:**

1. A unidade é o **verso** (linha não vazia). Um verso com três voltas conta
   **uma vez**. Isto é deliberado: contar movimentos distintos dentro de um
   verso é onde dois contadores divergem, e a fracção de versos é a decisão mais
   fácil de reproduzir.
2. Uma volta **negada** não conta: «não lhes atribuo sentido», «não busco na
   natureza uma moral oculta», «não é indiferentemente por não se importar
   comigo». Negar a atribuição é a postura do Caeiro, não a sua quebra. É a
   regra que mais vai doer e está escrita antes de contar.
3. Uma volta **que a pergunta já traz** conta igual. O verso é do poema.
4. Verbos convencionais de som — «o vento sussurra», «a onda murmura» — contam
   como **D** apenas se atribuírem **intenção, destinatário ou sentimento**:
   «sussurra segredos» conta, «sussurra entre as folhas» não. Está escrito antes
   de contar porque é a fronteira mais frequente.

**FVV = versos com volta ÷ versos não vazios.** Contínuo em [0, 1]. Num poema de
12 versos toma 13 valores, contra os 3 do 3a.

### 2.2 Auditabilidade, que é a defesa principal

Cada contador registra, por poema, **os índices dos versos** a que atribuiu
volta e o tipo (A–D). A contagem fica verificável contra o texto por quem não a
fez.

Não é burocracia: é a única defesa real contra a ameaça do §4. Um contador que
pontue por reconhecer o poema em vez de o ler deixa rasto — um poema que
personifica à vista com zero versos marcados é um erro visível no ficheiro.

---

## 3. A folha: três grupos, uma escala, às cegas

**60 itens**, embaralhados, com identificadores opacos `V01`–`V60`:

| grupo | n | o que é |
|---|---|---|
| **R** | 20 | poemas **reais** de Caeiro, dos 63 com 6–25 versos que **nunca** foram recuperados para as perguntas da Fase 5B |
| **O** | 20 | poemas **reais** do ortónimo em português, com 6–25 versos |
| **G** | 20 | amostras **geradas** da Fase 5B, 10 de cada braço |

Selecção por semente fixa. O intervalo de 6–25 versos é o das 60 amostras
geradas (6 a 24 observados), e mantém os três grupos comparáveis em
comprimento — o FVV é uma fracção, mas um texto longo tem mais oportunidades de
volta.

**O ortónimo é o contraste e não o Campos nem o Reis**, porque partilha os
assuntos do Caeiro — a natureza, o ser, o mistério — e atribui sentido neles. O
contraste tem de ser poética e não tópico; foi um dos erros que a 5C apanhou.

### 3.1 Os 10+10 do grupo G, e o que não se faz com eles

O grupo G é equilibrado entre os braços C e P da Fase 5B para que o braço não
confunda a comparação **entre grupos**, que é o que esta fase mede.

**O braço não é analisado nesta fase, de maneira nenhuma.** Não há portão sobre
ele, não há Δ, não há teste. Eu já li as 60 amostras da 5B e o desfecho está a
ser definido depois; qualquer número por braço aqui seria a pesca que a 5C
recusou. A 5B volta a medir-se com amostras **novas**, e só depois de este
instrumento passar.

---

## 4. A ameaça principal, que não sei remover

**Os poemas do grupo R são canónicos, e um contador pode reconhecê-los.** Quem
reconhece «O mistério das cousas, onde está ele?» sabe que é Caeiro e sabe que a
resposta esperada é zero voltas. Se isso acontecer, o portão V1 passa por
reconhecimento e não por medição, e o número não vale nada.

O que há contra isto, e é parcial:

- **A auditabilidade do §2.2.** Os índices dos versos ficam no ficheiro e
  qualquer pessoa pode verificar se a contagem corresponde ao texto.
- **O grupo G parece-se com o grupo R.** Várias amostras geradas da 5B são
  transposições de poemas reais — o §4 do relatório da 5B documenta uma com 33%
  dos versos copiados. Um contador que vá por reconhecimento vai errar nelas, e
  o erro aparece na comparação R contra G.
- **R2 não sabe que há grupos**, nem quantos, nem qual é a hipótese.

O que **não** há: nenhuma forma de apresentar Caeiro autêntico a um leitor de
Pessoa sem que ele possa ser reconhecido. Fica declarado, e o relatório tem de
repetir que V1 é condicional a isto.

---

## 5. Os portões

Estatística sem scipy: **permutação** (10000, semente 3), **AUC** por
Mann-Whitney normalizado com IC por bootstrap, e para a concordância o **ICC**
por decomposição de variâncias mais o desvio absoluto médio.

Os portões correm **por contador**, e o veredicto exige os dois (V4).

| | portão | condição | o que decide |
|---|---|---|---|
| **V1** | **validade discriminante** | AUC(FVV de R < FVV de O) ≥ **0,75** e permutação p ≤ 0,05 | o desfecho separa o Caeiro real do ortónimo real. Se falhar, a definição de volta não captura o construto e a fase fecha sem instrumento |
| **V2** | **o grupo gerado fica acima do real** | mediana de FVV em **G** > mediana em **R**, com permutação p ≤ 0,05 | o Caeiro gerado atribui mais sentido que o Caeiro real — a quantificação do que a Fase 5 viu como «0,0 na poética». Se **não** disparar, a premissa de todas estas fases fica em causa e isso é um resultado |
| **V3** | **resolução** | ≥ **12** valores distintos de FVV nos 60 itens, e < 40% no valor modal | o desfecho tem onde registar melhoria parcial. É o portão que o 3a não passaria: 3 valores, 83% no modal |
| **V4** | **os contadores concordam** | ICC ≥ **0,60** no FVV **e** V1 com o mesmo veredicto nos dois | sem isto, nada do resto se lê. Mesma regra do G5 da 5B |
| **V5** | **especificidade** | \|ρ(FVV, n.º de versos)\| ≤ **0,35** em ambos | o FVV não é um detector de comprimento |

**V1 e V2 são perguntas diferentes e podem dissociar-se.** V1 falha se a
definição de volta não distinguir poéticas; V2 falha se distinguir mas o Caeiro
gerado não for pior que o real. Os dois cenários têm prescrições opostas, e é por
isso que estão separados.

---

## 6. Cegueira

1. `folha.py` escreve `01-itens.md` com os 60 itens embaralhados por semente
   fixa, **versos numerados**, identificadores opacos, e nada mais. O mapa
   `id → (grupo, origem)` vai para `01-chave.json`.
2. Nenhum item adjacente pertence ao mesmo grupo mais de duas vezes seguidas, e
   nenhuma amostra gerada fica adjacente à sua companheira de pergunta.
3. As duas contagens vão para `02-contagens.json` e `02-contagens-r2.json`, e
   são **commitadas antes** de a chave abrir.
4. R2 recebe uma cópia **fora do repositório**, sem nome de fase e sem ligação
   nenhuma, como na 5B — e `folha.py` verifica que o enquadramento dela não
   nomeia fase, grupos nem hipótese.

---

## 7. O que esta fase não faz

- **Não mede H5B.** Ver o §3.1. Nenhum número por braço.
- **Não substitui o 3a.** O 3a diz se a voz se cumpre; o FVV diz quanto falta.
- **Não mede as outras vozes.** A definição de volta vem da âncora do **Caeiro**.
- **Não mede qualidade poética.** Atribuição de sentido é **uma** das coisas que
  a poética do Caeiro exige, e a forma é outro critério.
- **Não valida a contagem contra um contador humano.** Os dois contadores são
  sessões do mesmo modelo, com a ressalva da 5B §6.3: a concordância pode ser
  erro correlacionado, e o ICC mede concordância, nunca correcção.

---

## 8. O que pode autorizar

Se V1 a V5 passarem, autoriza o FVV como **desfecho primário de uma Fase 5E**,
que repete o desenho dos dois braços da 5B — a regra de reescrita, as personas e
o harness já estão escritos e verificados — com amostras **novas** e o n
dimensionado a partir do desvio do FVV medido aqui no grupo G.

Se V1 falhar, a fase fecha sem instrumento e a conclusão é que a atribuição de
sentido não é mensurável por contagem de versos com a definição do §2.1 — o que
deixa a Fase 5B definitivamente sem forma de ser medida por este caminho, e
remete para o modelo em vez do prompt.

---

## 9. Checklist

```
[ ] A1  protocolo commitado antes de existir qualquer contagem
[ ] B1  folha de 60 itens (20 R + 20 O + 20 G), embaralhada, versos numerados
[ ] B2  chave fechada; folha neutra de R2 verificada
[ ] C1  R1 conta, com índices e tipos por verso
[ ] C2  R2 conta, cego ao desenho e aos grupos
[ ] C3  as duas contagens commitadas antes de a chave abrir
[ ] D1  V1 AUC R<O com IC e permutação, por contador
[ ] D2  V2 G>R com permutação
[ ] D3  V3 resolução · V4 ICC · V5 especificidade
[ ] E1  relatório
```
