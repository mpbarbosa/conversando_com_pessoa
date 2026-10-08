# Fase 5V — A forma do verso: rima e metro, que nunca foram medidos

**Ataca o [passo 34](CONTROLO.md) na única causa que lhe sobra nomeada.**
Pré-registada em 2026-10-08, **antes de qualquer contagem**.

---

## 1. Porque esta, e porque agora

A [5U](FASE-5U-RELATORIO.md) deixou o passo 34 sem causa: a 5Q atribuiu o seu
AUC de 0,938–1,000 a «ortografia e **forma de verso**», e a parte ortográfica e
gramatical não aguenta o peso — **7 próclises e 1 marca ortográfica em 120
amostras**. O que fica nomeado é a **forma**, e a forma nunca foi medida:

| fase | mediu de forma | não mediu |
|---|---|---|
| [5J](FASE-5J-RELATORIO.md) · [5K](FASE-5K-RELATORIO.md) · [5M](FASE-5M-RELATORIO.md) | **comprimento** — número de versos | — |
| — | — | **metro, rima, estrutura estrófica** |

**E a forma é o que as personas pedem explicitamente.** O Reis manda «metro
regular e rima»; o Campos manda «versículo longo, de respiração ampla, muitas
vezes irregular». São instruções opostas e verificáveis.

### 1.1 E tem a propriedade que as duas fases anteriores não tinham

A 5T e a 5U morreram ambas **por falta de eventos**: a próclise aparece 7 vezes
em 120 amostras e a marca ortográfica 1 vez. **Aqui cada verso é uma
observação.** O corpus dá, por voz:

| voz | poemas reais em pt |
|---|---|
| ortónimo | **1206** |
| Campos | **320** |
| Reis | **251** |
| Caeiro | 120 |

Milhares de versos por voz. **Se esta fase falhar, não será por o chão estar
vazio** — e isso é o primeiro desenho da sequência em que posso dizer isto antes
de medir.

---

## 2. Os dois instrumentos, declarados antes de contar

### 2.1 Rima (I-R)

**Chave de rima**, do fim da última palavra de cada verso. Duas, reportadas
separadamente porque medem coisas diferentes:

- **toante** — do **último** grupo de vogais até ao fim (`separar` → `ar`,
  `tempo` → `o`). É grosseira de propósito: em português quase tudo termina em
  vogal, logo esta chave tem muita colisão por acaso.
- **consoante** — dos **dois últimos** grupos de vogais até ao fim (`separar` →
  `arar`… na forma implementada, a cadeia desde a penúltima vogal: `eternidade`
  → `ade`). Aproxima a rima a partir da sílaba tónica, que é a definição.

**«O poema rima»** = existe, dentro de uma estrofe, um par de versos cuja chave
**consoante** coincide, acima do que o acaso dá.

**E o acaso mede-se, não se estima.** Nulo empírico por **permutação**: embaralham-se
os finais de verso **entre poemas da mesma voz** e recalcula-se. Controla a taxa
de base das terminações do português, que é alta — é a lição do chão medido da
[5K](FASE-5K-RELATORIO.md), que descobriu que o nulo assintótico era conservador
por 46%.

### 2.2 Metro (I-M)

**Sílabas por verso**, por contagem de grupos de vogais — **sem elisão nem
sinalefa**, o que subconta sistematicamente. Declara-se porque **o viés é o
mesmo nos dois lados da comparação**; o que se compara é dispersão, não valor
absoluto.

**Estatística por poema:** a fracção de versos a **±1 sílaba** da mediana do
poema. Alta = metro regular (Reis), baixa = irregular (Campos).

### 2.3 O que não se mede, e porquê

**Não se mede esquema rimático** (ABAB contra AABB): exige identificar estrofes
com fiabilidade e o `stanzas` do *parse* não foi validado para isto. Fica fora, e
fora declarado.

---

## 3. Os portões de calibração, que correm **antes** de olhar para o gerado

É a lição da [5T](FASE-5T-RELATORIO.md), que é a sexta da série: **correr o
instrumento no material que ele já se sabe como é, antes de o apontar ao alvo.**
Aqui esse material são os poemas reais, e o que se sabe deles vem das personas e
não de contagem.

| | nome | dispara se | se não disparar |
|---|---|---|---|
| **V1** | **o detector de rima funciona** | nos poemas **reais**: Reis rima acima do nulo de permutação **e** Reis rima mais que Caeiro (verso livre) | o detector é **morto**. Reis é a voz que rima por definição; um detector que não o vê não vê rima |
| **V2** | **o detector de metro funciona** | nos poemas **reais**: a regularidade do **Reis** é maior que a do **Campos** | morto, pela mesma razão: são as duas vozes cujas personas pedem o contrário uma da outra |

**Nenhum dos dois tem limiar numérico escolhido agora,** e é deliberado: o
critério é **ordenação entre vozes autênticas**, que está fixada pela poética e
não por mim. Um limiar em número seria eu a escolher o que o instrumento tem de
achar.

---

## 4. O portão de discriminação

Corre **só** nos instrumentos que passaram a calibração.

| | nome | dispara se | leitura, escrita agora |
|---|---|---|---|
| **V3** | **a forma distingue gerado de real** | por voz, o IC95 por *bootstrap* de agrupamentos da diferença (real − gerado) **exclui zero** | **a causa do AUC da 5Q tem finalmente um candidato medido**, e o passo 34 tem onde atacar |
| **V4** | **inútil** | nenhum instrumento calibra, ou o V3 não dispara em voz nenhuma | a forma **também** não explica o AUC. Então o que distingue é algo que nenhum dos meus seis instrumentos alcança, e isso é o resultado a declarar |

### 4.1 A decisão, pré-escrita

| | decisão |
|---|---|
| **V3 dispara numa voz** | fica autorizado **pré-registar uma intervenção de forma** nessa voz — e **só** nessa. A [5I](FASE-5I-RELATORIO.md) mediu saldo líquido **negativo** numa mudança de instrução, logo a intervenção é uma fase própria com o seu portão, não um remendo nesta |
| **V3 dispara no Reis** | é o caso mais informativo, porque a persona do Reis **pede** metro e rima: uma falha ali é desobediência a uma instrução explícita, e não falta de informação |
| **V4 dispara** | declara-se que **as seis vias mecânicas estão esgotadas** (ortografia, gramática, comprimento, próclise, rima, metro) e que o AUC de 0,938–1,000 da 5Q fica **sem explicação mecânica**. Nada entra em `src/` |

### 4.2 O que esta fase não decide

- **Não mede voz nem conteúdo.** Mede forma, que é uma propriedade de superfície
  — a mesma camada da 5T e da 5U.
- **Não julga nada às cegas**, porque não julga: os dois instrumentos são
  mecânicos e correm sobre texto.
- **Não corrige personas** (passo 24), nem mexe em `src/` sem o V3.
- **Não substitui o [passo 25](CONTROLO.md).** A âncora por voz mede **conteúdo**
  e esta fase mede **forma**; a 5U devolveu a urgência àquele e esta não lha tira.

---

## 5. Ameaças

### 5.1 A contagem de sílabas é crua

Sem elisão, sem sinalefa, sem tratamento de hiato. **Subconta, e subconta em
todo o lado** — nos poemas reais e nos gerados. O desfecho é **dispersão
relativa**, não o número de sílabas, e o V2 exige que a ordenação Reis > Campos
apareça. Se o viés fosse grande o bastante para apagar essa ordenação, o V2 não
dispara e o instrumento morre, que é o comportamento correcto.

### 5.2 A chave consoante não é a sílaba tónica

Aproxima-a pela penúltima vogal, o que acerta nas paroxítonas (a maioria em
português) e erra nas oxítonas e proparoxítonas. **Mesmo erro nos dois lados.**
E o nulo de permutação absorve a taxa de colisão que o erro introduz.

### 5.3 Os textos gerados são mais curtos que os poemas reais

Mediana de 10–11 versos contra 11 do corpus (medido na 5U e na 5M), logo
comparável — mas um poema com menos versos tem menos pares possíveis de rima.
**O desfecho da rima é por poema** (rima / não rima), e a comparação vai
acompanhada da distribuição de comprimentos por conjunto, para o leitor ver se
difere.

### 5.4 Eu quero que esta dispare

É a última causa nomeada, e se o V4 disparar o passo 34 fica sem via mecânica
nenhuma. O V4 tem a leitura escrita e **é um resultado**: seis instrumentos, seis
vias fechadas, e um número da 5Q que continua de pé sem explicação. Dizer isso é
mais útil que arranjar um sétimo instrumento até algum disparar.

---

## 6. Lista de verificação

```
[ ] A1  instrumentos escritos como o §2 os declara, sem olhar para dados
[ ] A2  V1 e V2: calibracao nos poemas REAIS, por voz, com nulo de permutacao
[ ] A3  V3: real contra gerado, por voz, nos conjuntos ja commitados
        (5U braco C = 60 em configuracao de producao, 5M = 180, 5Q = 48+24)
[ ] B1  portoes e a decisao do §4.1
[ ] C1  relatorio FASE-5V-RELATORIO.md
[ ] C2  CONTROLO.md
```

**Sessões paralelas:** verificado antes de abrir. `git add` com ficheiros
nomeados.
