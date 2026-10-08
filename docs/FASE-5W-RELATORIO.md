# Fase 5W — relatório: a rima não se resolve no prompt, e o fosso é de uma ordem de grandeza

**Protocolo:** [`FASE-5W.md`](FASE-5W.md), pré-registado em `bea8586`.
**Analisador:** fixado em `57a4c29`, **com o diário em 5 de 60 amostras**.
**Dados:** [`fase-5w/01-cru.jsonl`](fase-5w/) (60) ·
[`02-resultados.json`](fase-5w/) · [`03-rechecagem-5v.json`](fase-5w/) ·
[`04-densidade.json`](fase-5w/)
**Produto:** **nada**. O W4 disparou e o §4.1 pré-escreveu que nesse caso nada
entra.

---

## 0. Os portões

| | braço R (directiva) | braço X (exemplo) |
|---|---|---|
| **W1** rima > 0,50, acima do nulo do braço, IC a excluir zero | ❌ **0,1000** — abaixo do próprio nulo (0,2500) e **abaixo do C** | ❌ **0,3000** — abaixo do próprio nulo (0,3500) |
| **W1′** o mesmo na chave-letra co-primária | ❌ 0,2500 (nulo 0,4000) | ❌ 0,5000 (nulo 0,5000) |
| **as duas chaves concordam?** | ✅ sim | ✅ sim |
| **W3** sem dano colateral | ❌ **não dispara**: 1 truncatura contra 0 | ✅ dispara, sem dano |
| **W2** X > R (a escorva da 5U) | — | ❌ não dispara pelo IC: [−0,05, +0,45] |
| **W4** não é alcançável pelo prompt | ✅ **DISPARA** | |

**Nenhum braço chegou perto do 0,50**, e **nenhum passou o seu próprio nulo de
permutação**. Pela decisão pré-escrita, nada entra em `src/`.

---

## 1. E o desfecho que eu pré-registei era de resolução errada

O §3 pré-registou um desfecho **binário** — «o poema rima». Num poema de doze
versos há **66 pares de versos**, e **um** par que coincida por acaso põe o
binário em `True`. Logo o binário mistura «rima sistematicamente» com «rimou uma
vez sem querer».

O desfecho certo é a **densidade**: de todos os pares de versos, quantos
partilham a chave ([`densidade.py`](fase-5w/densidade.py), posterior e
declarada).

| | densidade | razão ao poeta |
|---|---|---|
| **ortónimo real** (n=1196) | **0,0997** | — |
| braço **C** | 0,0095 | **10,5× abaixo** |
| braço **R** | 0,0046 | 21,9× abaixo |
| braço **X** | 0,0102 | 9,7× abaixo |

**O poeta rima cerca de um par de versos em dez. Os três braços, cerca de um em
cem.** O fosso é de **uma ordem de grandeza** e nenhum braço o mexeu — os três
contrastes entre braços contêm zero.

> **E é isto que dá força ao W4**, que no binário seria um nulo fraco de 20
> amostras por braço. A comparação que importa não é braço contra braço: é
> **qualquer braço contra o poeta**, e aí o n do lado real é **1196** e o fosso
> é de 10×. **Não é uma diferença à tangente que mais amostras resolveriam.**

É a lição da [5D](FASE-5D-RELATORIO.md) a repetir-se — **resolução** — e desta
vez em cima de um instrumento que eu próprio tinha construído duas fases antes.

---

## 2. A directiva piorou, e é a segunda vez

O braço **R** — «Rima alternada: em cada quadra, o segundo verso rima com o
quarto. A rima é obrigatória, não decorativa.» — ficou **abaixo do C** nas três
medidas:

| | C | **R** |
|---|---|---|
| rima (binária, consoante) | 0,3500 | **0,1000** |
| rima (binária, chave-letra) | 0,4000 | **0,2500** |
| **densidade** | 0,0095 | **0,0046** |

Nenhum contraste exclui zero com 20 amostras por braço, logo **não afirmo que a
directiva piora**. Afirmo que **não melhorou em medida nenhuma, e que o sinal é
negativo nas três** — e que isso replica a [5I](FASE-5I-RELATORIO.md), que mediu
saldo líquido **negativo** na única outra vez que este projecto reforçou uma
instrução.

**Duas intervenções de instrução, duas com sinal negativo.** Já não é um
acidente de uma fase.

---

## 3. O exemplo fez algo — só não foi rimar

O braço **X** não tem dano nenhum (W3 dispara) e mexeu **tudo na direcção do
poeta**, por quantidades que este desenho não distingue de ruído:

| | C | **X** | poeta |
|---|---|---|---|
| rima, chave-letra | 0,4000 | **0,5000** | 0,8367 |
| **metro** (regularidade) | 0,6648 | **0,7075** | **0,7572** |
| versos (mediana) | 9 | **12** | 11 |
| palavras suspeitas (total) | 4 | **1** | — |
| densidade de rima | 0,0095 | 0,0102 | 0,0997 |

E produziu, às vezes, exactamente o esquema pedido:

```
Sinto-me, como uma pedra
Que na minha estabilidade      ← 2.º
Um rio é que tem a vida.
E a minha tranquilidade        ← 4.º, rima com o 2.º
```

**O molde de terminações foi obedecido.** Mas uma quadra rimada num poema de doze
versos é densidade 0,015, e o poeta está em 0,0997.

**E o X bate o R nas duas chaves** — 0,30 contra 0,10 na consoante, 0,50 contra
0,25 na chave-letra, 0,0102 contra 0,0046 na densidade. O W2 não dispara pelo IC,
mas **as três medidas e as duas chaves concordam na direcção**. A hipótese da
escorva da [5U §1.3](FASE-5U-RELATORIO.md) fica **mais plausível e não
demonstrada** — exemplos parecem fazer mais do que directivas, e continua a não
haver potência para o afirmar.

---

## 4. Uma correcção à 5V, encontrada antes destes dados existirem

Ao testar o analisador desta fase vi que a chave consoante da 5V parte do
penúltimo **grupo** de vogais, e o regex junta `ia` num grupo só:

| palavra | chave da 5V | chave certa |
|---|---|---|
| `havia` | `avia` | `ia` |
| `servia` | `ervia` | `ia` |

**Não casam** — e `havia`/`servia` é rima de manual. Re-corri a 5V com a chave
corrigida ([`rechecar_5v.py`](fase-5w/rechecar_5v.py)) e **as conclusões não
mudam; as magnitudes melhoram:**

| voz | 5V: real / nulo / ger / nulo | corrigida: real / nulo / ger / nulo | persona |
|---|---|---|---|
| **ortónimo** | 0,777 / 0,239 / **0,217 / 0,217** | 0,837 / 0,355 / **0,383 / 0,383** | «rima» |
| Reis | 0,199 / 0,207 / 0,167 / 0,233 | 0,271 / 0,271 / 0,233 / 0,367 | «sem rima» |
| Campos | 0,459 / 0,409 / 0,200 / 0,317 | 0,547 / 0,516 / 0,383 / 0,550 | anáfora |
| Caeiro | 0,158 / 0,283 | 0,192 / 0,350 | verso livre |

**O ortónimo gerado cai outra vez exactamente no próprio nulo**, nas duas chaves.
As quatro vozes continuam a concordar com as quatro poéticas. **A 5V fica mais
forte, não mais fraca** — e nesta fase a chave corrigida entrou como
**co-primária**, com o embarque a exigir que as duas concordem. Não troquei a
chave que decide depois de ver números; acrescentei uma exigência.

---

## 5. O que isto decide

**Fecha o prompt como via para a forma.** Pela leitura pré-escrita do W4: o que
sobra é **constrangimento na descodificação ou afinação**, não instruir melhor. E
agora com dois apoios independentes:

| | |
|---|---|
| a instrução **existe** e é ignorada | 5V: gerado no próprio nulo |
| **reforçá-la** não ajuda, e o sinal é negativo | esta fase, braço R, e a [5I](FASE-5I-RELATORIO.md) antes |
| **exemplificá-la** move tudo um pouco e a rima nada | esta fase, braço X |
| o fosso é de **10×** em densidade | esta fase, com n=1196 do lado real |

**Não diz que o modelo não sabe rimar.** Diz que não rima **nesta tarefa, com
este prompt, a esta temperatura**. O braço X mostra que a estrutura pedida é
produzível — só não com densidade.

**Não fecha o AUC da 5Q.** A forma continua a dar 0,780 e o número da 5Q é
0,938–1,000 ([passo 38](CONTROLO.md), combinar com validação retida, continua
aberto).

**E dá um número que faltava a todo o projecto.** Para um desfecho **binário** a
mover-se de 0,35 para 0,50, fazem falta **~175 amostras por braço** — cinco horas
de CPU para dois braços. Com o desfecho **contínuo** da §1, a mesma pergunta cabe
em muito menos. **Três fases seguidas (5T, 5U, 5W) morreram por potência**, e a
causa não foi o rigor: foi escolher desfechos binários e de baixa frequência.

### O que fica na mesa

1. **A descodificação**, que é o que o W4 autoriza e que nunca foi tocada:
   `temperature`, `top_p`, `repeat_penalty` — e o [passo 17](CONTROLO.md) já pedia
   afinar as opções por modelo, com o Δ da 5H a ser um piso por isso mesmo.
2. **O passo 39 (amplitude entre vozes) e a densidade como desfechos padrão.**
   Ambos contínuos, ambos com o poeta como régua, ambos muito mais potentes que
   os binários que usei.
3. **O braço X, para reexame com potência.** Move quatro medidas na direcção
   certa sem dano; é o único candidato vivo, e precisa do n da §5.

> **A lição, e é a nona.** A oitava dizia que escolher **onde** medir é anterior
> a medir bem. Esta é o par dela: **escolher com que resolução medir é anterior a
> escolher o n.**
>
> Pré-registei «o poema rima» — um binário — e isso deitou fora um factor de dez.
> No binário, o poeta está em 0,84 e o gerado em 0,38, e a leitura é «rima menos».
> Na densidade, o poeta está em 0,0997 e o gerado em 0,0095, e a leitura é «rima
> **uma ordem de grandeza** menos». **São o mesmo instrumento e o mesmo texto**;
> a diferença é só o limiar que eu pus em cima dele.
>
> E a consequência é prática, não filosófica: no binário esta fase era um nulo
> fraco de 20 amostras por braço que pedia 175. Na densidade é um resultado
> firme, com n=1196 do lado que importa, e **não precisou de uma única amostra
> nova**.
