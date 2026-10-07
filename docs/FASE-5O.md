# Fase 5O — O +0,700 da 5H, por um terceiro avaliador

**Passo 26**, e com ele uma verificação que ninguém pediu e que a
[5N §3](FASE-5N-RELATORIO.md) tornou necessária. Pré-registada em 2026-10-07,
antes de eu ler qualquer um dos itens novos.

---

## 1. Porque é que esta fase existe

O **+0,700** da [5H](FASE-5H-RELATORIO.md) é o número em que assenta a hipótese
de trocar o modelo de serviço. Foi medido por **R1 e R2 da mesma sessão**, e
**nunca por um avaliador de fora dela**.

A [5N §3](FASE-5N-RELATORIO.md) deu uma razão concreta para o verificar: nos
**mesmos 30 itens** do braço qwen, três leituras cegas com a **mesma** âncora
deram médias de **0,50 (R1)**, **1,00 (R2)** e **0,97 (eu)** — e o discrepante é
o R1, que **escreveu a âncora**.

O argumento de que isso não afecta a 5H é teórico: um desvio sistemático de nível
**cancela** numa diferença emparelhada. **Esta fase testa-o em vez de o assumir.**

### 1.1 E uma coisa que a 5N não viu, e muda a leitura

A discrepância entre R1 e R2 **não é uniforme**. Nos mesmos itens:

| | em 30 amostras **geradas** (qwen7b) | em 24 poemas **reais** de Caeiro |
|---|---|---|
| R1 | **0,50** | **1,50** |
| R2 | **1,00** | **1,71** |
| diferença | **2,0×** | **1,14×** |

**Nos poemas autênticos os dois avaliadores concordam; é no texto gerado que
divergem.** Faz sentido — os poemas reais são casos claros e os gerados caem na
fronteira que o passo 12 do [`CONTROLO.md`](CONTROLO.md) diz estar em aberto. E
dá o instrumento desta fase: **os poemas reais servem de régua de nível**, porque
é onde a âncora se aplica de forma estável.

---

## 2. Desenho

### 2.1 Uma folha que recupera a cegueira

O problema óbvio: eu já pontuei o braço **Q** da 5H (na [5N](FASE-5N.md), às
cegas e já commitado). Se agora pontuar o braço **L** sozinho, sei que é o L, e
sei que é o braço que a 5H diz ser melhor — viés com direcção conhecida.

A solução é misturar o L com itens que eu **nunca li** e que não são do outro
braço:

| grupo | n | o que é |
|---|---|---|
| **L** | **30** | braço llama3.1:8b da 5H, voz Caeiro — **nunca lido por mim** |
| **R** | **24** | os poemas **reais** de Caeiro retidos da [5F](FASE-5F.md), grupo R — **nunca lidos por mim** |

Verifiquei que nenhum dos 24 poemas do grupo R coincide com os poemas que
imprimi nesta sessão (ao inspeccionar `chunk`s, lacunas e contagens).

**54 itens, embaralhados, identificadores opacos `O01`–`O54`, sem o grupo.** A
chave fecha-se e não se abre antes de as pontuações estarem commitadas. Duas
amostras da mesma pergunta não ficam adjacentes.

As minhas notas do braço **Q** vêm da 5N, **já commitadas**, e não se repontuam.

### 2.2 A escala

**3a′ da [5F §2](FASE-5F.md), inalterada**, com as seis regras dos casos
difíceis. Mesma âncora que a 5H, a 5N e a 5F usaram — é o que torna as
comparações possíveis.

**3b não se pontua nesta fase.** A âncora mudou na [5L](FASE-5L.md) e os poemas
reais não têm braço nem truncatura a comparar; pontuá-lo não serviria portão
nenhum.

### 2.3 Estatística

Sem `scipy`: binomial bilateral sobre pares discordantes, IC95% por bootstrap de
10 000, AUC por contagem de pares. Reutiliza o que a 5N e a 5I já têm.

---

## 3. Portões

| | nome | dispara se | leitura, escrita agora |
|---|---|---|---|
| **O1** | **a direcção do +0,700 replica** | Δ(L − Q) nas minhas notas **> 0**, com binomial **p ≤ 0,05** e IC95% a excluir 0 | o resultado da 5H sobrevive a um avaliador de fora da sessão que o produziu. **É a verificação que importa** |
| **O2** | **a magnitude é compatível** | o meu IC95% de Δ(L − Q) **contém +0,700** | não só a direcção: o tamanho também. Se o IC excluir 0,700 por baixo, a 5H **sobrestimou** e é preciso dizê-lo |
| **O3** | **o meu nível está calibrado** | a minha média nos 24 reais cai em **[1,30; 1,90]** — o intervalo dos dois avaliadores da 5F (1,50 e 1,71) com folga de 0,20 | as minhas notas de 3a′ são comparáveis com as da sequência. Se eu pontuar acima, o Δ de **+0,400 da 5N** foi medido numa escala inflacionada e tem de ser relido |
| **O4** | **a âncora continua a premiar o original** | nos 24 reais: mediana ≥ **1** **e** ≥ **30%** com nota **2** | é a condição **X1 da 5F**, re-corrida por um terceiro avaliador. A âncora que sete fases usam só foi aceite por uma sessão |
| **O5** | **inconclusivo por potência** | pares discordantes **d < 8** em Δ(L − Q) | nada se decide. Precedente: o G4 da 5B |

### 3.1 O O2 é o portão desconfortável, e está escrito antes de medir

O O1 testa a **direcção** e o O2 a **magnitude**. **É possível o O1 disparar e o
O2 não** — direcção certa, tamanho menor —, e nesse caso a conclusão é que a
**troca de modelo continua indicada mas o efeito publicado é grande demais**.
Escrevo-o agora porque é o desfecho que me custaria mais admitir depois.

### 3.2 O que esta fase não pode concluir

- **Não repete a 5H.** Reutiliza as amostras dela; o que é novo é o **avaliador**.
  Logo não testa a geração, testa a **leitura**.
- **Não mede o conteúdo das outras vozes** — continua a ser o passo 25.
- **Não produz um AUC comparável ao 0,851 da 5F.** O 5F contrastou real contra
  **qwen**; aqui o contraste é real contra **llama**. Reporto-o como **número
  novo** e não como replicação.
- **Não tem segundo avaliador.** Como a 5N, tem um. A diferença é que aqui o
  objecto **é** o efeito de avaliador, logo a limitação é a própria matéria.

---

## 4. Ameaças

### 4.1 O efeito de contexto, que é a principal

As minhas notas do braço Q foram dadas numa folha cujo **fundo** era o
`qwen2.5:3b` — um modelo pior. As do braço L vão ser dadas numa folha cujo fundo
são **poemas autênticos de Pessoa**. Se o fundo mexe na minha régua, mexe para
**cima**, e eu pontuarei o L mais **baixo** do que pontuei o Q.

**Direcção: enviesa o Δ(L − Q) para baixo.** Logo um Δ **positivo e
significativo** é robusto — medido contra o vento —, e um Δ nulo é ambíguo entre
«o efeito não existe» e «o contexto comeu-o». Está escrito antes de medir, e é a
razão pela qual o O1 é o portão principal e não o O2.

### 4.2 Vou reconhecer os poemas reais

Pessoa autêntico distingue-se de um 8B por qualidade, e eu vou dar por isso. Isso
**não** enviesa o Δ(L − Q), porque o braço Q não está nesta folha e os dois
grupos desta folha nunca se comparam entre si num portão emparelhado. Enviesa o
**O4** e o AUC do §3.2, que passam a ter a ressalva de não serem cegos quanto a
real-contra-gerado. O **O3** é menos afectado: a questão lá é o meu **nível
absoluto** nos reais, e saber que são reais não me diz que nota a âncora manda
dar.

### 4.3 Comparo notas dadas em folhas diferentes

O Δ(L − Q) junta notas de duas folhas, em dois momentos. É o ponto fraco do
desenho e não há como o remover sem repontuar o Q — o que destruiria a cegueira
que ele tem. Fica declarado, e o §4.1 diz a direcção do erro que isso introduz.

### 4.4 Já li o relatório da 5H e sei que diz +0,700

Não há como desfazer. É exactamente por isso que o O2 está escrito com um
critério numérico **antes** de eu ver os números, e que o §3.1 nomeia o desfecho
incómodo.

---

## 5. Lista de verificação

```
[x] A1  folha O01-O54 embaralhada, sem pergunta, chave fechada
[x] B1  54 pontuadas as cegas -> 02-pontuacoes.json, commitadas antes da chave
[x] B2  O1 DISPARA (+0,667, p=0,0018, 13 de 14) · O2 DISPARA (o IC contem 0,700)
[x] B3  O3 DISPARA: 1,792 nos reais, contra 1,50 (R1) e 1,71 (R2)
[x] B4  O4 DISPARA: mediana 2,0 e 19/24 (79%) · AUC(real > llama) = 0,526
[x] C1  portoes -> 03-resultados.json
[x] C2  relatorio FASE-5O-RELATORIO.md
[x] C3  CONTROLO.md: fase, passo 26, o +0,700 replicado, e o tecto
```

**Uma correccao a uma afirmacao minha, no §4 do relatorio:** o §2.3 da 5N dizia
que o `H01` «nao entra nesta fase» e entrava nesta, que e a seguinte — e o item
`O42` desta folha. Reconheci-o a pontuar e dei-lhe 0, contra a direccao do meu
vies. **Uma declaracao de contaminacao tem de dizer o que o item e, nao em que
fase nao vai entrar.**

**Sessões paralelas:** verificado antes de abrir. `git add` com ficheiros
nomeados.
