# Fase 1 / Passo 7 — guarda de plágio

Medido em 2026-10-01. 24 respostas reais (4 vozes × 6 perguntas), geradas pelo
pipeline completo com `qwen2.5:7b-instruct-q4_K_M`.

---

## Veredicto

**O plágio era o modo de falha dominante, e resolve-se no prompt, não na guarda.**

| | sem regra preventiva | **com a regra no `system`** |
|---|---|---|
| mediana de versos copiados | **82%** | **0%** |
| p25 / p75 | 0% / 100% | 0% / 0% |
| máximo | 100% | 79% |
| respostas acima de 20% | 16/24 (67%) | **3/24 (12%)** |
| respostas acima de 0% | 17/24 (71%) | 5/24 (21%) |

Por voz:

| voz | sem regra | com regra |
|---|---|---|
| Caeiro | 93% | 6% |
| Ortónimo | **100%** | 0% |
| Campos | 45% | 0% |
| Reis | 43% | 0% |

---

## 1. A dimensão do problema

A primeira travessia do pipeline (Passo 6) produziu uma resposta que copiava 3
de 8 versos. Pareceu um caso isolado. **Não era:** a resposta mediana copiava
**82%** dos seus versos, e o ortónimo copiava 100% em todas as seis perguntas.

Campos e Reis copiam menos (45% e 43%), plausivelmente porque as suas formas —
versículo longo e ode clássica — estão mais longe dos poemas curtos que a
recuperação traz. Caeiro e o ortónimo escrevem em formas próximas das do
contexto, e o caminho de menor resistência é repetir.

### O que o modelo faz com o contexto

Os poemas são injectados para o modelo reconhecer o seu registo. O modelo
trata-os como material a reproduzir. Não é um defeito subtil: é o
comportamento por omissão.

## 2. O erro de enquadramento que cometi

Comecei a calibrar o **limiar** da guarda, como o plano pedia. Com mediana de
82% antes e 0% depois de um reforço corretivo, o limiar é irrelevante: qualquer
valor entre 0,2 e 0,5 produz o mesmo comportamento — regenerar em ~65% dos
casos, a ~28 s cada, o que levaria a média a ~48 s e estouraria o orçamento de
45 s.

**Estava a calibrar um parâmetro quando o problema estava a montante.** A
primeira corrida só se tornou útil porque lhe acrescentei a comparação com
reforço, que não estava no plano.

A pergunta certa era: se a instrução funciona quando é **corretiva**, funciona
quando é **preventiva**? Funciona — e no `system`, onde é prefixo em cache,
custa **zero** por pergunta.

## 3. A métrica: verso, não n-gramas

O plano especificava «maior sobreposição de n-gramas (n=8)». Medido no caso real
do Passo 6:

| métrica | valor |
|---|---|
| sobreposição de 8-gramas | **2%** |
| fracção de versos copiados | **38%** |

A cópia é por **paráfrase ao nível do verso**: troca uma palavra, encurta,
reordena.

```
Nunca sei como se pode achar um poente triste.      0,94  <- copiado
Só se for por não ser madrugada.                    0,76  <- copiado
Ambos existem; cada um seu caminho.                 0,75  <- copiado
Mas se é poente, de que será feito?                 0,52      reescrita
```

Segunda vez neste projecto que n-gramas se revelam cegos a variação lexical
pequena — a primeira foi na deduplicação (Passo 2), onde o Jaccard de 4-gramas
dava 0,457 a duas versões do mesmo poema e 0,480 a poemas distintos.

Há um teste que prova isto por contraste: calcula as duas métricas no mesmo
caso e falha se alguém voltar a n-gramas.

## 4. Os limiares, calibrados

### `LIMIAR_VERSO = 0,72`

Lacuna limpa na similaridade máxima por resposta:

| | mediana | extremo |
|---|---|---|
| respostas que copiam (5) | 0,91 | mínimo **0,79** |
| respostas limpas (19) | 0,55 | máximo **0,70** |

0,72 cai na lacuna. Nenhuma resposta limpa é apanhada por engano.

### `LIMIAR_FRACAO = 0,10`

| limiar | repete | taxa | custo médio |
|---|---|---|---|
| 0,10 | 5/24 | 21% | **33,8 s** |
| 0,20 | 3/24 | 12% | 31,5 s |
| 0,40 | 2/24 | 8% | 30,3 s |

Nos dados, 0,0 e 0,10 são equivalentes (5 de 24), logo a regra efectiva é
**«qualquer verso copiado dispara uma repetição»**.

Escolhido 0,10 e não 0,20 porque os casos entre os dois são cópias literais de
versos distintivos — «Se às vezes falo nela como num companheiro» a 0,79, «Sei
tua Maria da Graça» a 0,81 — e 33,8 s continua dentro do limite de 45 s. Ser
estrito é barato aqui.

## 5. Os casos que ainda copiam

| voz | fracção | máx | pergunta |
|---|---|---|---|
| Caeiro | 79% | 1,00 | «Vale a pena recordar?» |
| Caeiro | 46% | 1,00 | «O que é pensar?» |
| Reis | 36% | 0,91 | «A vida é breve?» |
| Ortónimo | 17% | 0,83 | «Quem és tu?» |
| Caeiro | 11% | 0,79 | «A natureza tem algum sentido?» |

Nos 3 acima de 20%, o reforço corretivo corrigiu **3 de 3** (mediana 46% → 0%).

**Observação:** `poem_3426` é a origem em dois dos casos de Caeiro. Alguns
poemas parecem ser atractores — muito recuperáveis e muito copiáveis. Vale medir
isso no conjunto dourado (Passo 8) e, se se confirmar, é argumento para
diversificação na recuperação (MMR), que não está em nenhuma fase do plano.

## 6. Desenho final

```
recuperar (top-6, filtro de voz e idioma)
  -> montar prompt: persona com REGRAS_NAO_COPIAR no system (em cache)
  -> gerar
  -> guarda de saída (preâmbulo, persona, idioma, brasileirismos)
  -> guarda de plágio
       se plagiou e há tentativas: + REFORCO no user, repetir
```

O **reforço corretivo** vive no `user` e não no `system`, de propósito:
refere-se a uma tentativa concreta, logo não pode fazer parte do prefixo
estável — e colocá-lo lá invalidaria o cache a cada pergunta.

Custo médio esperado: **1,21 gerações, ~34 s**.

## 7. A guarda de saída não produziu falsos positivos

Das 24 respostas, **24 foram aprovadas** pela guarda do Passo 5 (preâmbulo,
quebra de persona, idioma, brasileirismos). Depois da correcção dos dois níveis
de detecção de nomes, zero falsos positivos em dados reais.

## 8. O que fica por resolver

A observação do Passo 6 mantém-se e não é resolvida por nada aqui: **quando o
modelo deixa de copiar, nem sempre continua a ser a voz pedida**. Os versos
originais da amostra do Passo 6 explicavam e atribuíam significado — o que a
persona de Caeiro proíbe.

Com o plágio resolvido, essa passa a ser a pergunta aberta principal, e só o
conjunto dourado do Passo 8 e uma avaliação de voz às cegas sobre respostas
**com** RAG podem responder. A avaliação da Fase 0 foi feita sem RAG.
