# Fase 5D — relatório: a resolução resolve-se, e o Caeiro real não cumpre a âncora

Protocolo em [`FASE-5D.md`](FASE-5D.md), pré-registado em `691cc97` **antes de
existir qualquer contagem**. As duas contagens foram commitadas em `98656db`
**antes de a chave ser aberta**.

---

## 1. O que se decidiu

**V4 falha, logo o instrumento não é aceite e, pela regra do próprio protocolo,
«sem isto, nada do resto se lê».**

| portão | R1 | R2 | |
|---|---|---|---|
| **V1** discriminante (AUC R<O ≥ 0,75) | **0,780**, p=0,0011 ✓ | **0,573**, p=0,337 ✗ | **falha** |
| **V2** gerado acima do real | med 0,442 vs 0,375, p=0,205 ✗ | med 0,332 vs 0,250, p=0,451 ✗ | **falha** |
| **V3** resolução | 38 valores, 11,7% no modal ✓ | 36 valores, 11,7% ✓ | **passa** |
| **V4** concordância | ICC=**0,671** ✓ · V1 com veredictos **diferentes** ✗ | | **falha** |
| **V5** especificidade | ρ(n.º versos)=−0,010 ✓ | +0,164 ✓ | **passa** |

Mas esta fase, ao contrário da 5C, não volta de mãos vazias. **Entrega a coisa
que a 5B precisava e devolve uma dúvida séria sobre a 5B inteira.**

---

## 2. O que fica resolvido: a resolução

Era o motivo de existirem a 5C e a 5D, e está feito:

| desfecho | valores distintos em 60 itens | no valor modal | confundidor de comprimento |
|---|---|---|---|
| **3a** (Fase 5B) | **3** | **83%** | — |
| FAS (Fase 5C) | 25 | 25% | ρ=+0,01 |
| **FVV** | **38** (R1) · 36 (R2) | **11,7%** | ρ=−0,01 / +0,16 |

**38 valores distintos contra 3, e 11,7% no modal contra 83%.** V3 e V5 passam
nos dois contadores. O problema que fez a Fase 5B cair em G4 — 22 dos 30 pares
empatados em 0–0 — não voltaria a acontecer com este desfecho.

O instrumento é rejeitado por **validade**, não por resolução. São perguntas
diferentes, e é a lição que a 5C já tinha escrito no `CONTROLO.md`.

---

## 3. O achado: o Caeiro real também não cumpre a âncora

É o resultado mais importante deste relatório e é desconfortável para o que eu
próprio escrevi nas duas fases anteriores.

**V2 pediu que o Caeiro gerado ficasse acima do Caeiro real em atribuição de
sentido. Não ficou — em nenhum dos dois contadores.**

| | R1 | R2 |
|---|---|---|
| Caeiro **real** | 0,375 | 0,250 |
| Caeiro **gerado** | 0,442 | 0,332 |
| **p** (permutação) | **0,205** | **0,451** |
| AUC(real < gerado) | 0,599 | 0,564 |

A direcção é a esperada e a diferença não chega perto de significância. E a
razão está na dispersão **interna** dos poemas reais, que é enorme:

| grupo (R1) | mín | Q1 | mediana | Q3 | máx |
|---|---|---|---|---|---|
| **R** Caeiro real | 0,000 | 0,133 | 0,375 | 0,500 | **0,700** |
| **O** ortónimo real | 0,105 | 0,455 | 0,577 | 0,714 | 0,917 |
| **G** Caeiro gerado | 0,000 | 0,357 | 0,442 | 0,562 | 0,833 |

### 3.1 Os poemas que fazem isto, e são canónicos

Os dois poemas reais de Caeiro com FVV mais alto têm **o mesmo valor nos dois
contadores**, logo não dependem da divergência do §4:

| | FVV (R1 = R2) | |
|---|---|---|
| `poem_1485`, Caeiro **VI** | **0,700** | «Pensar em Deus é desobedecer a Deus, / Porque Deus quis que o não conhecêssemos» |
| `poem_1486`, Caeiro **VII** | **0,636** | «Da minha aldeia vejo quanto da terra se pode ver do Universo…» |

E o `poem_1195` (Caeiro **XXXI**) diz de si mesmo, a 0,538:

> «Porque só sou essa coisa séria, um **intérprete da Natureza**»

A âncora de 3a, escrita na Fase 5 e usada para julgar 100 amostras ao longo de
três fases, define o 2 do Caeiro assim:

> «vê e não interpreta; **nenhuma** metafísica, símbolo, moral, nem natureza como
> espelho de sentimento»

**O Caeiro real falha isto com frequência.** Teologiza em VI, filosofa sobre o
tamanho do que vê em VII, moraliza em XXI («É preciso ser de vez em quando
infeliz»), e em XXXI chama-se intérprete da Natureza. A âncora descreve o
**programa** do Caeiro, não a sua **prática**.

### 3.2 Porque é que isto põe em dúvida a Fase 5B

A Fase 5 e a Fase 5B concluíram que o Caeiro gerado «não cumpre a poética», com
mediana **0,0** em 3a nas duas condições, e daí seguiu-se toda a cadeia: o
défice está na persona, a persona é feita de interdições, e as fases 5B, 5C e 5D
foram atrás disso.

Esta fase mede, com um desfecho que tem resolução, que **o Caeiro gerado não é
distinguível do Caeiro real na atribuição de sentido**. Se o Caeiro real fosse
julgado pela âncora de 3a, parte dele tiraria 0 também.

Isso não apaga a Fase 5B — mede outra coisa, e o §5 explica porquê — mas obriga a
registar uma possibilidade que nenhuma das fases anteriores considerou:

> O «0,0 do Caeiro» pode ser, em parte, um **artefacto da âncora**, e não uma
> falha do modelo. A âncora foi escrita a partir da **persona** em
> `src/voices.py`, e a persona é uma idealização do Caeiro. Julgar a geração por
> ela é julgá-la contra um Caeiro que não existe no corpus.

É a mesma estrutura de erro que a Fase 5 encontrou no seu juiz LLM — «as
descrições derivam das personas, logo é circular» — num sítio onde ninguém
tinha olhado: **a âncora manual tem a mesma origem**.

---

## 4. A divergência entre contadores, e o que a causou

**ICC = 0,671**, acima do piso de 0,60 que o protocolo pediu. ρ de Spearman
**+0,781**. Desvio absoluto médio de **0,143** em FVV.

E ainda assim V1 dá veredictos opostos: AUC 0,780 (p=0,001) em R1 contra 0,573
(p=0,337) em R2. **V4 falha pela segunda condição, não pelo ICC.**

A causa está numa única decisão, declarada nos dois ficheiros **antes** de a
chave abrir: a regra 2 do protocolo diz «uma volta negada não conta» e **cala-se
sobre a tautologia deflacionária**. R2 estendeu-lhe a regra e excluiu «as coisas
são só o que são» e «cada coisa só lembra o que é»; R1 contou-as como tipo B,
porque a definição de B diz «afirma sobre o ser».

Daí vêm 330 versos marcados por R1 contra 242 por R2, e a diferença concentra-se
no tipo **B** (240 contra 142).

**E o padrão tautológico é a dicção do Caeiro.** Quem o conta vê o Caeiro real
cheio de voltas; quem o exclui vê-o vazio delas. A fronteira que decide o portão
caiu exactamente entre os dois contadores — o que é o melhor argumento possível
para ter havido dois, e a demonstração de que a definição do §2.1 tem um buraco
que eu não vi ao escrevê-la.

**A lição metodológica, e é nova:** um ICC de 0,671 soa aceitável e **não basta
para estabilizar um portão com limiar**. Entre contadores que concordam a 0,78 de
ρ, a AUC oscilou 0,21 — mais do que a distância entre passar e falhar. Quem
pré-registar portões por limiar sobre juízo humano precisa de concordância
muito mais alta do que a que parece razoável, ou de portões sobre a **estimativa
conjunta** e não sobre cada avaliador.

---

## 5. O que esta fase não mediu, e cumpriu-se

**Nenhum número por braço da Fase 5B.** O grupo G foi 10 de cada braço para
equilibrar a comparação entre grupos, e o §3.1 do protocolo proibiu
explicitamente qualquer Δ por braço. Não foi calculado, não está no
`03-resultados.json`, e não está aqui.

Também não se mediu: as outras vozes, a qualidade poética (atribuição de sentido
é uma das quatro coisas que a âncora nomeia), nem a contagem contra um contador
humano — os dois contadores são sessões do mesmo modelo, com a ressalva da 5B
§6.3 de que a concordância pode ser erro correlacionado.

---

## 6. Ameaças, revisitadas

- **O reconhecimento dos poemas canónicos** era a ameaça principal declarada no
  §4 do protocolo, e o resultado **desarma-a em parte**: se os contadores
  estivessem a pontuar por reconhecimento, o Caeiro real teria ficado perto de
  zero e V1 passaria nos dois. Em vez disso o Caeiro real espalhou-se de 0,000 a
  0,700 e V2 falhou. Isso é o padrão de quem leu os versos, não de quem
  reconheceu os autores.
- **As linhas de numeral romano** («XXXV», «VII») são versos não vazios pela
  definição, entram no denominador e não têm volta. Afectam só o grupo R, e
  **baixam-lhe** o FVV — ou seja, favorecem V1 e desfavorecem V2. Três dos cinco
  poemas reais a 0,000 são poemas com numeral. Está declarado nos dois ficheiros
  de contagem, feito antes da chave.
- **A definição de volta tem um buraco** (§4) e isso é um defeito do protocolo,
  não dos contadores.
- **O tipo B apanha a dicção filosófica do próprio Caeiro.** Declarei-o no meu
  ficheiro de contagem antes de abrir a chave, com as palavras «apliquei-o à
  letra, incluindo contra o meu interesse em V1». Foi o que aconteceu, e é
  também o que produziu o achado do §3.

---

## 7. Checklist

```
[x] A1  protocolo commitado antes de existir contagem (691cc97)
[x] B1  folha de 60 itens (20 R + 20 O + 20 G), embaralhada, versos numerados
[x] B2  chave fechada; enquadramento de R2 verificado por fronteira de palavra
[x] C1  R1 contou, com índices e tipos por verso
[x] C2  R2 contou, cego ao desenho e aos grupos
[x] C3  as duas contagens commitadas antes de a chave abrir (98656db)
[x] D1  V1 por contador, com IC por bootstrap e permutação
[x] D2  V2 por permutação — **falha nos dois**
[x] D3  V3 passa · V4 **falha** · V5 passa
[x] E1  relatório
```

---

## 8. O que isto autoriza, e o que não

**Não autoriza o FVV como desfecho.** V4 falha, e a regra do protocolo é que sem
concordância nada do resto se lê. O FVV fica em
[`fase-5d/analisar.py`](fase-5d/analisar.py) com os seus números.

**Não autoriza uma Fase 5E sobre H5B.** Pela terceira vez, falta o instrumento.

**Não autoriza concluir que a âncora de 3a está errada.** O §3 dá uma razão
séria para suspeitar dela, não uma medição dela: ninguém pontuou os poemas reais
de Caeiro **com a âncora de 3a**, que é o que faltaria para o afirmar.

**Autoriza — e isto é novo — pôr em dúvida a cadeia inteira das Fases 5, 5B, 5C
e 5D**, e com uma razão concreta: todas julgaram a geração contra uma âncora
derivada da **persona**, e a persona é uma idealização que o Caeiro real não
cumpre. A Fase 5 identificou esta estrutura de erro no seu juiz LLM e não a
procurou na sua própria rubrica.

**Autoriza a correcção de dois parâmetros de desenho**, para quem continuar:
1. A regra 2 tem de dizer o que fazer com a **tautologia deflacionária**. É a
   fronteira que move a AUC em 0,21.
2. Portões por limiar sobre juízo humano precisam de concordância bem acima de
   ICC 0,671, ou de correr sobre a estimativa **conjunta** dos avaliadores em vez
   de cada um.

### A entrada da fase seguinte, e já não é a que eu esperava

A pergunta que estas quatro fases andaram a perseguir — «porque é que o Caeiro
gerado não cumpre a poética?» — pressupõe que ele não cumpre. **Essa pressuposição
está agora medida como duvidosa**, e o passo seguinte é testá-la em vez de a
assumir:

> **Pontuar os poemas reais de Caeiro com a âncora de 3a**, às cegas, misturados
> com amostras geradas, por dois avaliadores. Se o Caeiro real tirar 0 e 1 na
> âncora com a mesma frequência que o gerado, a âncora é o problema e as Fases 5
> e 5B mediram o instrumento e não o modelo.

É barato: as 20 amostras reais já estão seleccionadas e a âncora já existe. E é a
primeira vez em quatro fases que o alvo da medição é o **próprio critério** em
vez da geração — que, visto daqui, devia ter sido a Fase 5A.
