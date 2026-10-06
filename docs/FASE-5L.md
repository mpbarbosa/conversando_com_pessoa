# Fase 5L — Retirar a cláusula de comprimento do 3b

**Passo 22** da tabela do [`CONTROLO.md`](CONTROLO.md) §6. Escrita em 2026-10-06.

**Reprodutível:** os dois quadros do §2 saem de
[`fase-5l/verificar.py`](fase-5l/verificar.py) → `01-verificacao.json`. Têm
script porque a 5I publicou um número calculado na sessão **sem script** e isso
custou duas adendas ([5J §2.1](FASE-5J.md)).

**Não é uma fase de medição: é uma alteração de instrumento.** A autorização vem
de duas fases pré-registadas ([5J](FASE-5J-RELATORIO.md) e
[5K](FASE-5K-RELATORIO.md)) e de duas verificações aritméticas feitas aqui, que
declaro como feitas **antes** de escrever e sem portão — ver o §2.

O entregável é a âncora nova em [`FASE-5.md`](FASE-5.md) §5.2, e esta é a nota de
autorização e de compatibilidade que a `CONTROLO.md` pediu.

---

## 1. O que se retira, e de onde vem a autorização

| voz | retira-se | fica |
|---|---|---|
| **Caeiro** | `10–20 versos` · `ou fora do intervalo` · `longo` (em «longo e ornamentado») | verso livre, linhas curtas, sem rima, pouca imagem, ornamento |
| **Campos** | `15–30 versos` | versículo longo, respiração ampla, enumeração, anáfora, truncatura |
| **Reis** | `≤12 versos` · `>12 versos` | ode breve, estrofes de 3–4 versos, sem rima, sintaxe latinizante, latim |
| **Ortónimo** | `12–20 versos` | metro regular, rima, quadras ou quintilhas |

**O que não se retira**, e porquê:

- **`linhas curtas` (Caeiro) e `versículo longo` (Campos)** são comprimento de
  **verso**, não de **poema**. A 5J mediu o número de versos por poema e não o
  comprimento de cada verso. Ficam, **não testados**.
- **`estrofes de 3–4 versos` (Reis) e `quadras ou quintilhas` (Ortónimo)** são
  comprimento de **estrofe**. Mesma razão. Ficam, **não testados**.
- **A truncatura leva 0.** Uma amostra truncada está **incompleta** — é uma falha
  de fecho e não um juízo de intervalo —, e a [5J §2.3](FASE-5J-RELATORIO.md)
  mostrou que é detectável sem juízo, pelo campo `truncada`
  (`done_reason == "length"`). Fica, e passa a ser **a única regra mecânica de
  comprimento no 3b**, justificada por outro motivo.
- **`ode breve` (Reis)** é um resíduo de comprimento, agora **sem número**.
  Declaro-o em vez de o esconder: o que sai é o **limiar contado**, não a noção
  de brevidade, e a noção não foi medida.

### 1.1 A autorização, por voz

| voz | o que está medido | onde |
|---|---|---|
| **Caeiro** | intervalo descritivamente falso (39% dos reais lá cabem) **e** detector **invertido** (AUC = 0,000) | [5J §1](FASE-5J-RELATORIO.md) · [5K §3](FASE-5K-RELATORIO.md), **pré-registados** |
| **Campos** | descritivamente falso, decisivo nas quatro sensibilidades (32%, Wilson sup. 0,38) | [5J §1.2](FASE-5J-RELATORIO.md), **pré-registado** |
| **Ortónimo** | idem (25%, Wilson sup. 0,28) | idem |
| **Reis** | intervalo **correcto** (73%) **e invertível de qualquer maneira** | §2.1 **desta** nota, medido depois |

---

## 2. As duas verificações feitas aqui, declaradas como posteriores

### 2.1 Os quatro intervalos são invertíveis — inclusive o do Reis

A 5J e a 5K autorizavam retirar três dos quatro. **O do Reis passou o J1** (73%
dos poemas reais de Reis cabem em `≤12`), logo retirá-lo só pelo argumento geral
da [5J §4.3](FASE-5J-RELATORIO.md) seria fazer o que critiquei nas outras fases:
mudar um instrumento sem medir aquela célula.

Medi. Aplicando **cada** intervalo ao poeta real e aos dois braços da 5H:

| intervalo de | poeta real | llama3.1 | qwen2.5 | inverte? |
|---|---|---|---|---|
| caeiro `10–20` | 39% | 30% | **83%** | **sim** — qwen |
| campos `15–30` | 32% | 7% | **47%** | **sim** — qwen |
| **reis `≤12`** | **73%** | **83%** | 47% | **sim** — llama |
| ortonimo `12–20` | 25% | 17% | **70%** | **sim** — qwen |

**Os quatro intervalos premeiam, acima do próprio poeta, uma distribuição que não
é a dele.** E não é por essas distribuições serem plausíveis para aquela voz: a
[5K §2.2](FASE-5K-RELATORIO.md) mostrou que **nenhum dos dois braços cabe no
intervalo de amostragem de voz nenhuma** — o llama falha o nulo do Reis a 0,216
contra um p95 de 0,204.

**O caso do Reis é o mais fino da sequência inteira, e é o que fecha o
argumento:** um intervalo pode estar **descritivamente correcto** e ser, ainda
assim, um detector **invertido**. A correcção descritiva não salva um escalar.

> **Porque é que isto vale como autorização apesar de medido depois.** É
> aritmética sobre dados que já existiam, sem grau de liberdade inferencial: duas
> fracções e uma comparação, sem limiar escolhido, sem modelo, sem amostragem.
> `83% > 73%` não tem outra leitura. Não é um teste de hipótese e não o apresento
> como tal — se dependesse de um limiar ou de um intervalo de confiança, precisava
> de pré-registo e eu teria de o fazer noutra fase.

### 2.2 A cláusula era vinculativa, logo a quebra de compatibilidade é grande

Cruzando as 180 pontuações históricas de 3b que têm texto e condição
recuperáveis (fases 5G, 5H, 5I) contra o intervalo da sua voz:

| | 3b = 0 | 3b = 1 | 3b = 2 |
|---|---|---|---|
| **fora** do intervalo | 3 | **65** | **1** |
| **dentro** do intervalo | 7 | 65 | 39 |

**Dos 69 itens fora do intervalo, 68 ficaram em ≤1.** A cláusula não era
decorativa: foi aplicada quase sem excepção — e a excepção única (um 2 fora do
intervalo) é um avaliador a sobrepor-se à âncora.

**Consequência:** até **65 das 180** pontuações (**36%**) podem mudar de 1 para 2
ao retirar a cláusula, porque estavam fora do intervalo e com o tecto no 1. É um
**limite superior**: um item podia estar em 1 por razão qualitativa também, e
isso só se sabe repontuando.

Os sete `3b = 0` **dentro** do intervalo são sobretudo truncaturas — a 5I teve
oito —, que é a regra que **fica**.

---

## 3. A nota de compatibilidade

> **As pontuações de 3b anteriores a 2026-10-06 não são comparáveis com as
> posteriores.** A âncora mudou numa cláusula que foi aplicada em 68 de 69 casos
> aplicáveis (§2.2), logo até 36% das notas históricas estariam diferentes sob a
> âncora nova.

Em concreto:

- **Não comparar** um Δ de 3b medido antes com um medido depois. Isto afecta o
  **I1/I2 da 5I** (saldo de −0,150 em 3b) e o **M3 da 5H**, que são leituras de
  3b com a cláusula dentro.
- **O que não é afectado:** tudo o que é medido em **3a′** — o M1 da 5H
  (Δ = +0,700), a 5F, a 5G. A cláusula de comprimento nunca entrou no 3a.
- **O comprimento do poema continua a ser medido**, mas ao nível do **conjunto** e
  não da amostra: é o critério do **passo 21**, calibrado na
  [5K](FASE-5K-RELATORIO.md), com o nulo por voz em
  [`fase-5k/01-nulo.json`](fase-5k/) como referência de leitura. **Não se perdeu
  um critério; mudou-se a unidade de medida.**

---

## 4. O que esta nota não faz

- **Não repontua nada.** As 180 pontuações históricas ficam como estão, com a
  ressalva do §3. Repontuá-las custaria o mesmo que a corrida que as gerou e não
  serviria nenhuma pergunta aberta.
- **Não toca nos critérios qualitativos** do 3b, nem no 3a′, nem no 4, nem no 5.
- **Não valida o que fica.** Os limiares de **estrofe** (`3–4 versos`, `quadras ou
  quintilhas`) e de **verso** (`linhas curtas`, `versículo longo`) ficam **não
  testados**, e pela mesma lógica da 5J podem ter o mesmo defeito. Está nomeado
  como passo novo em vez de ser assumido como são.
- **Não decide o passo 16**, que continua a precisar de 20 perguntas por célula
  e de ~4 h de geração.
