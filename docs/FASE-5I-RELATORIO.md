# Fase 5I — relatório: a instrução pega, o tecto corta, e o saldo é zero

Protocolo em [`FASE-5I.md`](FASE-5I.md), pré-registado em `ea8965b` **antes de
existir uma amostra**. As duas pontuações foram commitadas em `0e22b72` **antes
de a chave ser aberta**.

---

## 1. O que se decidiu

**I0 passa. I1 falha. I2 falha. O reforço não é autorizado.**

| | portão | exigia | medido (conjunta, 30 pares) | |
|---|---|---|---|---|
| **I0** | a manipulação pega | fracção em 10–20 versos sobe | **12/30 → 18/30** | **passa** |
| **I1** | a forma melhora | em 3b: p ≤ 0,05 a favor de B e IC a excluir 0 | Δ=**−0,150** · IC95% [−0,417; +0,133] · 6/10/14 · p=0,455 | **falha** |
| **I2** | a poética sobrevive | limite inferior do IC de Δ3a′ **acima de −0,25** | Δ=**−0,017** · IC95% **[−0,350; +0,317]** | **falha** |

As três leituras — conjunta, R1 e R2 — chegam ao mesmo sítio. **I4 não dispara.**

A autorização exigia I1 **e** I2, e não tem nenhum dos dois. A cláusula de forma
de serviço fica como está.

**E o §9.2 levanta uma dúvida maior do que a que esta fase veio resolver:** só
**43%** dos poemas reais de Caeiro cabem no intervalo de 10–20 versos que a
âncora de 3b exige — contra 40% do llama3.1 e **83%** do qwen2.5. O «défice de
forma» pode ser o instrumento, outra vez.

---

## 2. Porque é que I1 falhou: o reforço troca «curto» por «cortado»

A instrução **funciona**. A mediana de versos sobe de 8,5 para 11,0 e a fracção
dentro do intervalo sobe de 12 para 18 em 30. O modelo obedece quando lhe dizem
com insistência.

E depois bate no tecto:

| | A (serviço) | B (reforçada) |
|---|---|---|
| versos (mediana) | 8,5 | **11,0** |
| dentro de 10–20 | 12/30 | **18/30** |
| **truncaturas** | **2** | **6** |
| segundos (mediana) | 25,7 | **40,1** |

A âncora de 3b manda dar **0 a uma amostra truncada**. O braço B ganha seis
amostras dentro do intervalo e paga com quatro truncaturas a mais, cada uma um
zero automático. **O saldo em 3b é −0,150, e é negativo.**

### 2.1 E o diagnóstico mostra que nem sem o tecto o ganho seria grande

Pós-hoc, e declarado como tal — removendo as oito amostras truncadas e
reemparelhando as 22 que sobram:

| | pares | Δ3b | pró-B / pró-A / empates |
|---|---|---|---|
| todas | 30 | −0,150 | 6 / 10 / 14 |
| **sem as truncadas** | 22 | **−0,114** | 4 / 5 / 13 |

E a fracção dentro de 10–20 **entre as que não truncaram**:

| | dentro de 10–20 |
|---|---|
| A | 11 de 28 (39%) |
| B | 12 de 24 (50%) |

**O ganho aparente de 12→18 é em boa parte feito de poemas que ficaram longos e
cortados.** Entre os que chegaram ao fim, B é modestamente melhor que A, e não o
suficiente para mover 3b. Subir o `num_predict` sozinho não resolveria isto —
melhoraria, mas o efeito de base é pequeno.

---

## 3. Porque é que I2 falhou, e o que isso **não** significa

O §6 do protocolo escreveu isto antes de medir, e cumpre-se agora:

> «um I2 falhado por intervalo largo lê-se como **não se mostrou que sobrevive**,
> não como **mostrou-se que morre**. O relatório tem de o dizer com essas
> palavras.»

É o caso, e os números são inequívocos sobre qual dos dois:

| | Δ3a′ | IC95% | pró-B / pró-A / empates |
|---|---|---|---|
| conjunta | **−0,017** | [−0,350; +0,317] | 10 / 8 / 12 |
| R1 | +0,000 | [−0,367; +0,333] | 9 / 7 / 14 |
| R2 | −0,033 | [−0,367; +0,333] | 5 / 6 / 19 |

**O efeito pontual é essencialmente zero nos três.** O que falhou foi a largura
do intervalo contra uma margem apertada de propósito: o limite inferior é −0,350
e a margem era −0,250. Com 30 pares e este desvio, I2 só passaria se o Δ fosse
claramente positivo.

**A leitura honesta: não há indício nenhum de que o reforço gaste a poética, e
esta fase não tinha potência para o estabelecer.** Quem quiser estabelecê-lo
precisa de cerca de 60 pares, e só vale a pena depois de o reforço funcionar na
forma — que é o que não acontece.

---

## 4. A correcção ao meu próprio protocolo, que a fase produziu a meio

O §1 deste protocolo abria a corrigir o meu passo 15, e dizia:

> «**`num_predict` não é o constrangimento.** O braço do llama teve zero
> truncaturas em 30 amostras.»

Era verdade **sem** o reforço, e deixou de ser verdade **com** ele. As
truncaturas triplicam, de 2 para 6, e o tempo de geração sobe 56%.

**A ordem estava ao contrário:** o `num_predict` não é irrelevante — é
irrelevante **até** a instrução pegar, e passa a ser o constrangimento **depois**.
Os dois têm de se mexer juntos ou nenhum dos dois serve, e eu testei-os em
sequência quando eram um par.

É o terceiro caso nesta sequência em que um facto medido numa fase (zero
truncaturas, 5H) é verdadeiro na condição em que foi medido e falso na condição
seguinte. Os outros dois estão na 5C (a AUC in-sample) e na 5E (a âncora
calibrada contra a persona).

---

## 5. A concordância, que foi a melhor de toda a sequência

| | 3a′ |
|---|---|
| κ ponderado linear | **0,715** |
| concordância exacta | **76,7%** |
| médias | R1 1,20 · R2 1,42 |

Contra 0,334 (5G), 0,548 (5H) e 0,620 (5F). E os dois avaliadores identificaram
**as mesmas sete truncaturas**, de forma independente e cega — numa fase em que
o comprimento é a variável manipulada, é a garantia que mais vale.

O padrão de R2 ser mais generoso mantém-se (1,42 contra 1,20), mas a diferença é
a menor de todas as fases.

---

## 6. O que mais apareceu

- **A `I47` repete a mesma estrofe verbatim antes de truncar.** É degeneração por
  repetição, modo de falha que a Fase 0 observou e que o `repeat_penalty=1,1`
  devia conter. Primeira reaparição nesta sequência, e no braço reforçado — o
  que faz sentido: forçar comprimento num modelo que quer parar é precisamente a
  condição em que a repetição aparece.
- **Duas amostras em prosa** (I17 corrida, I25 misturada), que a guarda
  `e_verso` não apanhou.
- **O braço B não plagiou nenhuma vez** (contra 1 de A) e nenhum dos dois teve
  reprovações no critério 2.
- **As medianas de 3a′ são 1,50 (A) e 1,75 (B)**, as mais altas de toda a
  sequência — consistente com a 5H, porque é o llama3.1 nos dois braços.

---

## 7. Ameaças

- **O comprimento é visível e é a variável manipulada** (§7 do protocolo).
  Declarei antes da chave que a folha tinha «dois regimes de comprimento» sem
  confiança para atribuir amostra a amostra. O que limita o dano: R2 não sabia
  que o comprimento era a variável, e o seu Δ3a′ de −0,033 é tão nulo como o
  meu.
- **Eu escrevi a cláusula reforçada e sou um dos avaliadores.** Aqui a direcção
  do viés seria **a favor** de B, e B perdeu nos dois desfechos.
- **Uma voz, dez perguntas, 30 pares, um modelo.**
- **I2 falhou por potência**, e não se pode converter isso em evidência de
  ausência de dano nem de presença.

---

## 8. Checklist

```
[x] A1  protocolo commitado antes de existir amostra (ea8965b)
[x] A2  verificar_personas.py: as cinco regras mecanizáveis passam
[x] A3  60 amostras, llama3.1 nos dois braços, semente base 20261007
[x] A4  folha por folha.py; asserção de `user` igual e `system` igual fora da
        cláusula de forma, verificada nas 10 perguntas; chave fechada
[x] B1  R1 pontuou 3b e 3a' às cegas, com a ameaça do §7 declarada
[x] B2  R2 pontuou, cego ao desenho e ao facto de o comprimento ser a variável
[x] B3  as duas pontuações commitadas antes de a chave abrir (0e22b72)
[x] C1  I0 primeiro (**passa**); I1 e I2 na conjunta (**falham as duas**);
        I3 não dispara; I4 não dispara
[x] D1  a leitura de I2 do §6 aplicada: «não se mostrou que sobrevive»
```

---

## 9. O que isto autoriza, e o que não

**Não autoriza aplicar o reforço.** A `forma` de serviço fica como está, e a
variante fica em [`fase-5i/personas_5i.py`](fase-5i/personas_5i.py) medida e não
adoptada.

**Não autoriza dizer que o reforço estraga a poética.** Ver o §3: o efeito
pontual é zero nos três avaliadores, e o portão falhou por largura de intervalo.

**Não desbloqueia a decisão de troca de modelo** que a [Fase 5H](FASE-5H-RELATORIO.md)
deixou condicionada pelo M3. O custo que o M3 nomeou — o llama escrever curto —
continua lá, e esta fase mostrou que a correcção óbvia não o remove.

**Autoriza, isso sim, uma correcção ao plano:** o problema de forma do llama3.1
**não se resolve só com instrução**, e o `num_predict` tem de entrar com ela.
Está medido em que ordem, que é o que eu tinha errado.

### O que fica na mesa

1. **O par: reforço + `num_predict` mais alto**, medidos **juntos** e não em
   sequência. É a única leitura que esta fase deixa de pé, e é barata — o
   `num_predict` é uma constante em `src/generation/ollama.py`. Mas o §2.1
   avisa: entre as amostras que não truncaram, o ganho de B já é pequeno, logo
   isto pode subir a forma sem a resolver.
2. **A alternativa que esta fase torna séria — e que medi antes de a escrever.**
   O intervalo de 10–20 versos da âncora de 3b veio da **persona**, que é a mesma
   idealização que a [Fase 5E](FASE-5E-RELATORIO.md) apanhou a reprovar 85% do
   Caeiro autêntico. Ninguém tinha verificado se os poemas reais lá cabem.
   Cabem assim:

   | | dentro de 10–20 versos |
   |---|---|
   | **Caeiro real** (119 poemas) | **51 de 119 — 43%** |
   | llama3.1, braço A | 12 de 30 — 40% |
   | qwen2.5, 5H | 25 de 30 — **83%** |

   O Caeiro real tem mediana de 12 versos mas **36% dos seus poemas têm menos de
   dez**, e 25 têm mais de vinte. **O llama3.1 reproduz a distribuição do poeta
   quase exactamente; o qwen2.5 obedece à persona duas vezes mais do que o
   próprio Caeiro.**

   Se isto se confirmar num desenho próprio, então o «défice de forma» que o M3
   da 5H nomeou e que esta fase tentou corrigir **não é um défice** — é o
   instrumento a penalizar o modelo que se parece mais com o original. É o erro
   da 5E, num critério diferente, e é barato de testar: os 119 poemas estão
   contados acima.
3. As outras três vozes com os dois modelos — passo 16, intocado.
