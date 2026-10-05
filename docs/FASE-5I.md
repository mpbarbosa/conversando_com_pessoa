# Fase 5I — a forma do llama: corrigir o comprimento sem gastar os 0,700

Protocolo, **pré-registado antes de existir uma amostra**. É o passo 15 da lista
«[depois da Fase 5](CONTROLO.md)», e desbloqueia — ou não — a decisão de troca
que a [Fase 5H](FASE-5H-RELATORIO.md) deixou condicionada.

**Objectivo:** decidir, por medição, se o défice de forma do `llama3.1:8b` se
corrige por instrução, **e se isso custa a poética que ele ganhou**.

---

## 1. Uma correcção ao meu próprio passo 15

O passo 15, como eu o escrevi no `CONTROLO.md`, dizia: «`num_predict` e um
pedido explícito de comprimento na `forma` são as duas coisas mais fáceis de
mexer neste projecto». **Metade disso está errado, e os dados da 5H já o diziam.**

| | |
|---|---|
| **`num_predict` não é o constrangimento** | O braço do llama teve **zero truncaturas** em 30 amostras. O modelo pára sozinho muito antes dos 220 tokens, logo subir o tecto não faz nada |
| **o pedido de comprimento já existe** | A `forma` de serviço do Caeiro **já diz** «Entre dez e vinte versos» |

O que a 5H mediu é isto:

| | dentro de 10–20 versos | abaixo de 10 | mediana |
|---|---|---|---|
| `qwen2.5:7b` | **25 de 30** | 4 | 13,5 |
| `llama3.1:8b` | **9 de 30** | **21** | 7,5 |

O qwen obedece ao pedido; o llama ignora-o. **O que falta não é o pedido — é ele
pegar**, e é por isso que esta fase tem um braço só e não dois factores.

---

## 2. A hipótese

**H5I:** o défice de forma do llama3.1 é um défice de **comprimento**, e corrige-se
tornando o requisito saliente.

E vem com uma hipótese de custo, que é a que torna isto arriscado:

**H5I-custo:** forçar comprimento num modelo que escreve curto fá-lo **encher** —
com imagem decorativa, com repetição, com volta simbólica — e isso gasta a
poética.

As duas são mensuráveis na mesma corrida, e o §5 dá a cada uma o seu portão. Se
a segunda ganhar, a resposta certa é **não** aplicar o reforço, e o relatório
di-lo-á.

---

## 3. Desenho: ablação emparelhada da cláusula de forma

Gerador: **`llama3.1:8b-instruct-q4_K_M`** nos dois braços. É o modelo cuja
forma se está a corrigir; medir isto no qwen não responderia à pergunta.

| | braço | `forma` |
|---|---|---|
| **A** | controlo | a de serviço, byte a byte |
| **B** | reforçada | a mesma com o comprimento **em primeiro lugar** e com instrução de contagem |

**10 perguntas de Caeiro × 2 braços × 3 repetições = 60 amostras, 30 pares.**

A `poetica` fica **byte a byte igual** nos dois braços. É o activo que a 5H
mediu valer +0,700, e esta fase não o pode gastar por descuido — só por
medição.

### 3.1 A regra de reescrita, e as duas cláusulas lado a lado

1. A **`poetica`** é byte a byte igual.
2. Todas as orações da `forma` de serviço **sobrevivem literalmente** em B.
3. O requisito de comprimento passa para **primeira** posição e ganha instrução
   de contagem.
4. Comprimento em caracteres entre **1,0 e 2,0** do original — crescer é
   inevitável, duplicar não.
5. `REGRAS_LINGUA`, `REGRAS_NAO_COPIAR` e `REGRAS_SAIDA` byte a byte iguais.
6. **Nenhum conteúdo poético novo.** Não é mecanizável, e é para isso que as duas
   cláusulas vão aqui inteiras:

| | |
|---|---|
| **A** (132 car.) | «Verso livre, linhas curtas, sem rima. Linguagem simples, quase seca. Poucas imagens, e nenhuma decorativa. **Entre dez e vinte versos.**» |
| **B** (216 car.) | «**O poema tem de ter entre dez e vinte versos — conta-os antes de terminares, e não entregues menos de dez.** Verso livre, linhas curtas, sem rima. Linguagem simples, quase seca. Poucas imagens, e nenhuma decorativa.» |

`verificar_personas.py` mecaniza cinco das seis regras e passou-as todas: razão
de comprimento **1,636**, `poetica` igual, as três orações preservadas, o
comprimento em primeiro em B e em último em A, e o resto do `system` igual.

### 3.2 Configuração

Igual à da 5H (§3.2 de lá): opções de serviço sem afinação por modelo,
reordenação ligada, pipeline completo, `TOP_K`=6. Semente
`20261007 + 100·r + i`, igual nos dois braços.

A persona entra por *monkeypatch* de `src.pipeline.persona`. **`src/voices.py`
não se toca.**

---

## 4. A rubrica

| # | critério | papel |
|---|---|---|
| **3b** | forma da voz | **desfecho primário.** Âncora da [Fase 5](FASE-5.md) §5.2, inalterada |
| **3a′** | poética da voz | **desfecho de não-inferioridade.** Âncora da [Fase 5F](FASE-5F.md) §2 |
| versos dentro de 10–20 | automático | **verificação de manipulação** (I0) |

**É a primeira fase desta sequência em que 3b é o primário e 3a′ é o travão.** A
inversão é deliberada: a 5H já estabeleceu o ganho em poética, e o que esta fase
tem de garantir é que a correcção de forma não o devolve.

---

## 5. Os portões

Primário na **estimativa conjunta** dos dois avaliadores. Teste de sinais exacto
sobre os pares discordantes, IC95% por bootstrap emparelhado, B=10000, semente 3.
Piso d ≥ 8.

| | portão | condição (conjunta, 30 pares) | o que decide |
|---|---|---|---|
| **I0** | **a manipulação pegou** | a fracção de amostras com 10–20 versos sobe de A para B | o reforço mudou o comportamento. Se **não** pegar, I1 e I2 não se leem e a conclusão é sobre a instrução, não sobre a forma |
| **I1** | **a forma melhora** | em 3b: binomial p ≤ 0,05 a favor de **B** e IC95% a excluir 0 | o reforço corrige a forma |
| **I2** | **a poética sobrevive** | em 3a′: limite **inferior** do IC95% do Δ (B−A) **acima de −0,25** | não-inferioridade. A margem é um pouco mais de **um terço** dos 0,700 que a 5H ganhou, e está fixada antes de medir |
| **I3** | **inconclusivo por potência** | d < 8 em 3b | nada se decide |
| **I4** | **os avaliadores discordam** | R1 e R2, em separado, chegam a veredictos diferentes em I1 ou I2 | publica-se e **nada se autoriza** |

**A autorização exige I1 **e** I2.** Corrigir a forma perdendo a poética não é
corrigir nada: seria desfazer o único resultado positivo desta sequência para
ganhar um critério que a 5H mostrou ser o menos sólido dos dois.

**E I2 pode falhar sozinho, o que é um resultado útil:** diria que o llama3.1
escreve curto **porque** escreve seco, que as duas coisas são a mesma, e que a
forma do Caeiro e a poética do Caeiro estão em tensão neste modelo. Nesse caso a
prescrição é deixar a forma em paz e mexer na âncora de 3b.

### 5.1 Sem portão, mas relatado

Latência, truncaturas, tentativas por plágio, brasileirismos e a distribuição de
versos, por braço. E a distância ao Caeiro real (1,604 na âncora 3a′, medido na
5F), como régua externa e **não** como teste.

---

## 6. Potência

Da 5H, o desvio-padrão das diferenças emparelhadas foi **0,674** em 3a′ e está em
`03-resultados.json` para 3b. Com 30 pares, detecta-se Δ ≥ 0,40 a ~80%.

Para **I2** a conta é outra, e é a que importa: com 30 pares e esse desvio, o
IC95% tem semi-largura de cerca de **0,25**. Isto significa que I2 só passa se o
Δ3a′ observado for **próximo de zero ou positivo** — um Δ de −0,20, por exemplo,
daria limite inferior perto de −0,45 e falharia. **A margem é apertada de
propósito**, e um I2 falhado por intervalo largo lê-se como «não se mostrou que
sobrevive», não como «mostrou-se que morre». O relatório tem de o dizer com
essas palavras.

---

## 7. Cegueira

Como na 5H: folha escrita por `folha.py` (não pelo harness), 60 amostras
embaralhadas com `I01`–`I60`, duas da mesma pergunta nunca adjacentes, chave
fechada até as duas pontuações estarem commitadas, e cópia de R2 fora do
repositório com o enquadramento verificado por **fronteira de palavra**.

**Uma ameaça nova e específica:** o comprimento do poema é **visível** e é
exactamente o que o braço manipula. Um avaliador que conte versos — e tem de
contar, para 3b — pode inferir o braço a partir do número. Não há como esconder
isto sem estragar a medição de 3b.

O que limita o dano: a inferência é imperfeita (a 5H mostra que o llama já
produzia 9 de 30 dentro do intervalo sem reforço), **3a′ é julgado pelo mesmo
avaliador na mesma passagem** e é aí que está o risco real, e R2 não sabe que há
braços nem que o comprimento é a variável.

---

## 8. O que esta fase não mede

- **O qwen.** A forma dele já cumpre (25 de 30), e o reforço nele mediria outra
  coisa.
- **`num_predict`.** Ver §1: não é o constrangimento.
- **As outras três vozes**, que é o passo 16.
- **A troca do modelo.** Esta fase informa a decisão; não a toma.

---

## 9. Checklist

```
[ ] A1  protocolo commitado antes de existir qualquer amostra
[x] A2  verificar_personas.py: as cinco regras mecanizáveis passam
[ ] A3  60 amostras, llama3.1 nos dois braços, semente base 20261007
[ ] A4  folha por folha.py com as duas âncoras; chave fechada
[ ] B1  R1 pontua 3b e 3a' às cegas, com razão por amostra
[ ] B2  R2 pontua, cego ao desenho e ao facto de o comprimento ser a variável
[ ] B3  as duas pontuações commitadas antes de a chave abrir
[ ] C1  I0 primeiro; depois I1 e I2 na conjunta; I3 e I4 verificados
[ ] D1  relatório, com a leitura de I2 do §6 qualquer que seja o resultado
```
