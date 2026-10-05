# Fase 5E — medir a âncora: a Fase 5A que faltou

Protocolo, **pré-registado antes de pontuar**. É o passo 7 da lista «[depois da
Fase 5](CONTROLO.md)», e o relatório da [Fase 5D](FASE-5D-RELATORIO.md) escreveu
que, visto de lá, «devia ter sido a Fase 5A».

**Objectivo:** decidir, por medição, se a âncora de 3a com que quatro fases
julgaram a geração premeia o **Caeiro real**.

---

## 1. Porque é que isto vem agora, e devia ter vindo primeiro

Quatro fases — 5, 5B, 5C, 5D — mediram a geração contra a âncora de 3a. A
[Fase 5D](FASE-5D-RELATORIO.md) mediu, com um desfecho que tem resolução, que o
Caeiro **gerado** não é distinguível do Caeiro **real** na atribuição de sentido
(p=0,205 e p=0,451 nos dois contadores), e que os poemas reais se espalham de
0,000 a 0,700 em FVV.

Os dois extremos altos têm o mesmo valor nos dois contadores:

| | FVV | |
|---|---|---|
| `poem_1485`, Caeiro **VI** | 0,700 | «Pensar em Deus é desobedecer a Deus» |
| `poem_1486`, Caeiro **VII** | 0,636 | «Da minha aldeia vejo quanto da terra se pode ver do Universo…» |

E a âncora de 3a define o **2** do Caeiro assim:

> «vê e não interpreta; **nenhuma** metafísica, símbolo, moral, nem natureza como
> espelho de sentimento»

A suspeita é concreta: a âncora foi escrita a partir da **persona** em
`src/voices.py`, e a persona é uma idealização. Se o Caeiro real não a cumprir,
então o «0,0 do Caeiro gerado» das Fases 5 e 5B mediu, em parte, **o
instrumento** — e não o modelo.

A Fase 5 identificou esta estrutura de erro no seu **juiz LLM** — «as descrições
dele derivam das personas, logo é circular» — e não a procurou na sua **rubrica
manual**, que tem a mesma origem. Esta fase procura-a.

**O que a 5D não autoriza, e é a razão de esta fase existir:** ninguém pontuou
os poemas reais de Caeiro **com a âncora de 3a**. O FVV é outra escala. Sem isso,
a suspeita é uma suspeita.

---

## 2. A hipótese

**W:** a âncora de 3a não premeia o Caeiro real.

Se W for verdadeira, a mediana de 3a nos poemas autênticos de Caeiro fica em
0 ou 1, e o resultado central das Fases 5 e 5B — «o Caeiro gerado falha a
poética» — passa a ser indistinguível de «a âncora reprova Caeiro».

A predição contrária é igualmente concreta: se a âncora premiar o Caeiro real
com 2 na maioria dos poemas, ela está calibrada, o «0,0» do gerado é uma falha
real da geração, e a cadeia das quatro fases mantém-se de pé.

---

## 3. Desenho: a mesma âncora, três grupos, itens novos

**60 itens**, embaralhados, identificadores opacos `W01`–`W60`, pontuados
**0, 1 ou 2** com a âncora de 3a do Caeiro, **verbatim** da
[Fase 5](FASE-5.md) §5.1 e inalterada desde que foi escrita:

| grupo | n | o que é |
|---|---|---|
| **R** | 20 | poemas reais de Caeiro, dos **43** elegíveis que a 5D **não** usou |
| **O** | 20 | poemas reais do ortónimo em português, não usados na 5D |
| **G** | 20 | amostras geradas da Fase 5B, das **40** que a 5D não usou |

**Os itens são novos de propósito.** Eu abri a chave da 5D, logo estou
desinibido para aqueles 60 itens e não posso ser avaliador deles. Com itens
frescos volto a estar cego à chave, e a 5D ganha de graça uma amostra
independente onde o seu achado pode replicar ou não.

Mesma elegibilidade da 5D: 6 a 25 versos, e os poemas de Caeiro recuperados
para as perguntas da Fase 5B ficam de fora.

### 3.1 O grupo O é o controlo negativo, e é indispensável

Sem ele, W não é falsificável de forma útil: se o Caeiro real tirar 0 e o gerado
também, isso pode significar «a âncora é apertada demais» **ou** «a âncora não
mede nada». O ortónimo distingue os dois casos — é o que a âncora de Caeiro deve
reprovar por construção.

É por isso que o portão **W3 corre primeiro** e tem poder de veto sobre os
outros.

---

## 4. Os portões, e a correcção que a 5D obriga a fazer

A 5D falhou V4 porque dois contadores com **ICC de 0,671** e ρ de 0,78 chegaram
a veredictos opostos num portão com limiar: a AUC oscilou **0,21** entre eles,
mais do que a distância entre passar e falhar. O relatório dela prescreveu a
correcção, e esta fase aplica-a:

> **Os portões correm sobre a estimativa conjunta** — a média dos dois
> avaliadores por item — e não sobre cada avaliador. Por avaliador corre-se em
> separado e **relata-se**, sem decidir.

Estatística sem scipy: permutação (10000, semente 3), AUC por Mann-Whitney
normalizado com IC por bootstrap, κ ponderado linear.

| | portão | condição (na estimativa conjunta) | o que decide |
|---|---|---|---|
| **W4** | **piso de concordância** | κ ponderado linear ≥ **0,30** e concordância exacta ≥ **50%** | abaixo disto a média dos dois é ruído e **nada se lê**. Corre primeiro a par de W3 |
| **W3** | **controlo negativo** | AUC(ortónimo < Caeiro real) ≥ **0,70** e p ≤ 0,05 | a âncora mede **alguma coisa** sobre a voz do Caeiro. Se falhar, a âncora não discrimina e W1/W2 não se leem — e isso é um resultado mais grave do que W |
| **W1** | **W confirmada** | mediana de 3a no Caeiro **real** ≤ **1** *e* menos de **50%** dos poemas reais com 3a=2 | a âncora não premeia o Caeiro autêntico. O «0,0» das Fases 5 e 5B deixa de poder ser lido como falha só do modelo, e a rubrica tem de ser recalibrada antes de qualquer medição de prompt |
| **W2** | **a âncora distingue autêntico de gerado** | AUC(gerado < real) ≥ **0,70** e p ≤ 0,05 | se **passar**, a âncora é apertada mas **ordena bem**, e serve como instrumento relativo mesmo sem premiar o real. Se **falhar**, não separa o autêntico do gerado e não serve para julgar geração nenhuma |

**W1 e W2 são independentes e as quatro combinações significam coisas
diferentes**, o que é a razão de estarem separados:

| W1 | W2 | leitura |
|---|---|---|
| não | sim | a âncora está calibrada. A cadeia das quatro fases mantém-se |
| **sim** | **sim** | a âncora é **apertada mas ordena**: serve para comparar, não para dizer «falha». As Fases 5 e 5B leram um nível absoluto que a âncora não suporta |
| sim | não | a âncora não serve para julgar geração. É o pior caso para as quatro fases |
| não | não | incoerente com W3; se acontecer, o desenho está errado e diz-se isso |

---

## 5. Cegueira

1. `folha.py` escreve `01-itens.md` com os 60 itens embaralhados por semente
   fixa, identificadores opacos, e a âncora de 3a no topo. O mapa
   `id → (grupo, origem)` vai para `01-chave.json`.
2. Nunca três do mesmo grupo seguidos.
3. As duas pontuações vão para `02-pontuacoes.json` e `02-pontuacoes-r2.json`, e
   são **commitadas antes** de a chave abrir.
4. R2 recebe uma cópia fora do repositório, sem nome de fase e sem ligação
   nenhuma, e `folha.py` verifica o enquadramento por **fronteira de palavra** —
   a verificação por substring reprovou duas vezes, na 5B por «braço» dentro de
   «abraço» e na 5D por «real» dentro de «realidade».

---

## 6. Ameaças, declaradas

- **Eu já li as 60 amostras geradas da Fase 5B.** As 20 do grupo G desta folha
  são 20 dessas, e posso reconhecê-las. A direcção do viés é
  **conservadora para W**: se eu reconhecer uma amostra como gerada, tendo a
  pontuá-la baixo, o que **favorece** a conclusão antiga («o gerado falha») e
  **dificulta** W1 e W2. Declarado, e é o motivo pelo qual R2 — que nunca viu
  nada disto — vale mais aqui do que nas fases anteriores.
- **Os poemas reais são canónicos e podem ser reconhecidos.** A 5D desarmou isto
  em parte por evidência: se os contadores pontuassem por reconhecimento, o
  Caeiro real teria ficado perto de zero em FVV e não se espalhava de 0,000 a
  0,700. Mas aqui a escala é a âncora, e o viés de reconhecimento empurra o
  Caeiro real **para cima** — contra W1. Também conservador.
- **Os dois avaliadores são sessões do mesmo modelo** a ler a mesma âncora: a
  concordância pode ser erro correlacionado, e o κ mede concordância, nunca
  correcção. É a ressalva da 5B §6.3 e mantém-se.
- **As linhas de numeral romano** («XXXV», «VII») aparecem nos poemas reais e não
  nas amostras geradas. Na 5D entravam no denominador do FVV; aqui a escala é
  qualitativa, logo não há denominador — mas **são uma pista de que o item é
  autêntico**, e isso é fuga de cegueira. `folha.py` **remove-as**, e a remoção
  está declarada aqui antes de a folha existir.
- **n=20 por grupo.** Uma diferença de dois ou três itens move uma mediana numa
  escala de três níveis. Os IC vêm por bootstrap e leem-se como largos.

---

## 7. O que esta fase não faz

- **Não mede H5B.** Nenhum número por braço, outra vez.
- **Não recalibra a âncora.** Se W1 disparar, a recalibração é outra fase, com a
  âncora nova pré-registada antes de ver amostras.
- **Não mede as outras três vozes.** A âncora de 3a do Caeiro é a que está sob
  suspeita, porque é a do único caso a 0,0.
- **Não julga a Fase 5 nem a 5B como erradas.** Mede uma condição necessária para
  as lermos como elas foram escritas.

---

## 8. Checklist

```
[ ] A1  protocolo commitado antes de existir qualquer pontuação
[ ] B1  folha de 60 itens frescos (20 R + 20 O + 20 G), sem numerais romanos
[ ] B2  chave fechada; enquadramento de R2 verificado por fronteira de palavra
[ ] C1  R1 pontua 0/1/2 com a âncora, com razão por item
[ ] C2  R2 pontua, cego ao desenho e aos grupos
[ ] C3  as duas pontuações commitadas antes de a chave abrir
[ ] D1  W4 e W3 primeiro, na estimativa conjunta
[ ] D2  W1 e W2, com IC por bootstrap; por avaliador em separado, sem decidir
[ ] E1  relatório
```
