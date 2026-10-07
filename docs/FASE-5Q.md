# Fase 5Q — Distinguir o gerado do real, nas três vozes que faltam

**Desbloqueia a decisão da troca de modelo**, que o passo 25 bloqueava. Pré-
registada em 2026-10-07, antes de eu ler qualquer item.

---

## 1. Porque é que isto substitui o passo 25

O passo 25 pedia **uma âncora 3a′ por voz**, validada contra os poemas reais
dessa voz — o percurso [5E](FASE-5E-RELATORIO.md) → [5F](FASE-5F-RELATORIO.md),
três vezes. São seis a nove fases, e a decisão da troca fica suspensa até ao fim.

**Duas fases minhas mostram que esse instrumento é mais do que o necessário.** A
[5N §3](FASE-5N-RELATORIO.md) e a [5O §2.1](FASE-5O-RELATORIO.md) mediram que **o
nível é do leitor e a diferença emparelhada é do gerador**: três avaliadores
cegos deram 0,50, 1,00 e 0,97 aos mesmos 30 itens, e o Δ de +0,700 sobreviveu
porque era um Δ. **Uma âncora absoluta é necessária para medir níveis. A decisão
da troca precisa de uma diferença.**

E há um instrumento que mede essa diferença, **já existe, e vem do corpus e não
da persona**: a **AUC(real > gerado)**. A [5F §2](FASE-5F-RELATORIO.md) deu
**0,851** para o qwen no Caeiro; a [5O §3.1](FASE-5O-RELATORIO.md) deu **0,526**
para o llama. Esta fase estende-o às três vozes que faltam.

> **E evita o erro da 5E, que o passo 25 correria o risco de repetir.** Um
> critério de conteúdo tirado da **persona** mede proximidade à **persona**, que
> é o tratamento — foi o que custou três fases de instrumentação. Aqui o critério
> é «isto é Pessoa autêntico ou não?», e a resposta certa está no **corpus**. Não
> há âncora para derivar e não há idealização para medir.

---

## 2. Desenho

### 2.1 Os 72 itens

| por voz | n | origem |
|---|---|---|
| `qwen2.5:7b` | **8** | [5M](FASE-5M-RELATORIO.md), uma repetição por pergunta |
| `llama3.1:8b` | **8** | idem, **a mesma** pergunta e repetição |
| **poemas reais** | **8** | corpus, amostrados com semente declarada |

**3 vozes × 24 = 72 itens.** Vozes: **campos**, **reis**, **ortonimo** — o Caeiro
já está medido pela 5F e pela 5O e não entra.

Os dois braços usam **a mesma pergunta e a mesma repetição**, logo o par
`(qwen, llama)` é directo; mas o desfecho **não** é emparelhado entre braços: é a
AUC de cada braço contra o **mesmo** conjunto de poemas reais da sua voz.

### 2.2 O comprimento não pode denunciar o real

Os modelos produzem, na 5M: campos 7–22 versos, reis 5–24, ortonimo 4–20. Os
poemas reais vão até 161. **Se eu amostrasse reais sem restrição, os longos
entregavam-se pelo comprimento** e a AUC mediria contagem de versos e não voz.

Logo os reais são amostrados **só de 4 a 25 versos** (`plagio._versos`),
elegíveis pelo filtro de lacuna da [5J §4.3](FASE-5J.md), `language == pt`, e
**excluindo** os poemas cujo texto eu imprimi nesta sessão. Há 174, 192 e 922
disponíveis, logo a restrição não aperta a amostragem.

**Direcção do enviesamento:** torna a tarefa **mais difícil** para mim, o que é
conservador para o Q1 e **neutro** para o Q2 — os dois braços enfrentam os mesmos
reais.

### 2.3 A escala, e porque não é binária

Por item, **1 a 4**:

| 1 | 2 | 3 | 4 |
|---|---|---|---|
| certamente **gerado** | provavelmente gerado | provavelmente **real** | certamente real |

Quatro níveis e não dois porque a AUC precisa de ordenação, e porque é o que
torna estes números comparáveis em espécie com os 0,851 da 5F e os 0,526 da 5O.

### 2.4 Cegueira

72 itens embaralhados, identificadores opacos `Q01`–`Q72`, **cada um etiquetado
com a sua voz** — preciso da voz para julgar, e a voz não revela a origem. Sem
pergunta (os reais não têm; mostrá-la em dois terços dos itens entregava o
grupo — é a lição da folha da [5O](FASE-5O.md) §2.1). Chave fechada até as
pontuações estarem commitadas.

### 2.5 Estatística

Sem `scipy`. AUC por contagem de pares com empates a meio, reutilizada da
[5K](FASE-5K-RELATORIO.md); IC95% e o Δ entre AUCs por bootstrap de 10 000,
reamostrando **os reais e os gerados** (os dois braços partilham os positivos,
logo o bootstrap reamostra-os uma vez por repetição e aplica-o aos dois).

---

## 3. Portões

| | nome | dispara se | leitura, escrita agora |
|---|---|---|---|
| **Q1** | **o instrumento tem resolução** | AUC(real > gerado) **pooled nos dois braços** > **0,65** | eu distingo real de gerado nestas vozes. **Se não disparar, nada mais se lê** — como na [5B](FASE-5B-RELATORIO.md), um desfecho sem separação não decide nada |
| **Q2** | **o llama está mais perto do poeta** | AUC(real > llama) **<** AUC(real > qwen), pooled, com IC95% do Δ a **excluir 0** | **a troca melhora o conteúdo nas três vozes**, e entra no `src/` nesta fase (§4) |
| **Q3** | **e está nas três, não numa** | o Q2 na direcção do llama em **≥2 das 3** vozes | a melhoria é geral. Se for numa só, a troca é **por voz** e não global — ver §3.2 |
| **Q4** | **inconclusivo** | o IC95% do Δ do Q2 **inclui 0** | «não se mostrou», e a prescrição é acrescentar as repetições que sobram da 5M (há 3 por pergunta; esta fase usa 1) em vez de decidir |

### 3.1 O desfecho que me obrigaria a dizer o contrário

**Se o Q2 disparar na direcção do qwen**, a conclusão é que o llama ganha no
Caeiro e **perde** nas outras três, e a prescrição é **não trocar globalmente** —
e considerar modelo **por voz**, que a arquitectura suporta. Escrevo-o antes de
medir porque é o desfecho que contraria sete fases de trabalho meu e seria o mais
tentador de explicar.

### 3.2 O que esta fase não faz

- **Não mede «qualidade poética»**, mede **indistinguibilidade do original**. São
  coisas diferentes e esta é a que o corpus consegue arbitrar sem âncora.
- **Não substitui o passo 25 para todos os fins.** Uma âncora por voz continua a
  ser o que faz falta para medir **progresso** numa voz ao longo do tempo. O que
  esta fase substitui é o passo 25 **como bloqueio da decisão de troca**.
- **Não mede forma.** A [5M](FASE-5M-RELATORIO.md) já a mediu nas quatro vozes.
- **Não tem segundo avaliador.** Como a 5N e a 5O.

---

## 4. O compromisso, escrito antes de medir

**Se o Q1 e o Q2 dispararem a favor do llama, a troca do modelo de serviço entra
no `src/` nesta mesma fase**, no mesmo commit que o relatório ou no seguinte.
Não fica como passo seguinte.

A razão de o escrever: `src/` não é tocado desde 2026-10-03 e houve **59 commits**
desde então, todos em `docs/`. O programa de medição destacou-se do produto, e uma
fase que mede e adia seria mais uma volta disso.

**Se o Q4 disparar**, nada entra — e a prescrição é a do §3 (mais repetições),
não «decidir com o que há».

---

## 5. Ameaças

### 5.1 Vou querer equilibrar as respostas

Sei que um terço dos itens é real, porque escrevi o desenho. Numa tarefa de
detecção isso convida a **equilibrar** — a dizer «real» cerca de 24 vezes
independentemente do que leia. A defesa é fraca e declaro-a: pontuo **sem contar**
quantos reais já marquei, e reporto a **distribuição** das minhas respostas no
relatório, para que o desequilíbrio (ou a sua ausência suspeita) fique visível.

### 5.2 Reconheço Pessoa por qualidade, e isso é o instrumento e não um defeito

É o que o Q1 mede. Se a tarefa for fácil, o instrumento discrimina; o problema
seria o contrário. Mas há um caso que **confunde**: posso reconhecer um poema
**específico** por já o ter lido alguma vez, em vez de o reconhecer como Pessoa
pela voz. Não tenho como excluir isso para os 2083 poemas; excluo os que
imprimi **nesta sessão** e declaro o resto.

### 5.3 O ortónimo é um alvo largo

1055 poemas, de toda a vida e em dois idiomas. A [5M §5.2](FASE-5M.md) já avisava
que é a voz menos coerente. Uma AUC baixa no ortónimo pode significar «o modelo
acertou» ou «o alvo é largo demais para errar». Fica declarado antes de medir, e é
a razão de o Q3 pedir 2 de 3 e não 3 de 3.

### 5.4 Uma repetição por pergunta

A 5M tem 3. Uso 1 (semente declarada) para manter a folha em 72 itens. Perde-se
potência e o §3 Q4 diz o que fazer se faltar: acrescentar as outras duas, que já
estão geradas e commitadas.

---

## 6. Lista de verificação

```
[x] A1  folha Q01-Q72 embaralhada, etiquetada com a voz, chave fechada
[x] B1  72 juizos as cegas -> 02-juizos.json, commitados antes da chave
[x] B2  Q1 DISPARA (AUC 0,988) · Q2 NAO (medias identicas) · Q3 NAO (1 de 3)
        · Q4 DISPARA
[x] B3  distribuicao: 32/13/3/24. Chamei real a 27 de 72, havendo 24 reais
[x] C1  portoes -> 03-resultados.json
[x] C2  o Q2 NAO disparou e o Q4 disparou -> **nada entra no src/**, como o
        §4 pre-escreveu
[x] C3  relatorio FASE-5Q-RELATORIO.md
[x] C4  CONTROLO.md: fase, passo 25 sem urgencia, passos 29 e 30 novos
```

**Duas correccoes, no §1 e no §4 do relatorio.** A fuga editorial que declarei ao
commitar os juizos era **imaterial** (a AUC sem esses 4 itens e identica a tres
decimais). E a prescricao que o §4 deu para o Q4 — «acrescentar as repeticoes
que sobram» — **esta errada**: supunha falta de potencia, e o que ha e falta de
**resolucao**, com as medias identicas e as AUCs encostadas ao limite da escala.

**Sessões paralelas:** verificado antes de abrir. `git add` com ficheiros
nomeados.
