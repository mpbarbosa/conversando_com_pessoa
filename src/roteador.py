"""Roteador de voz — Fase 4, Passo A4.

## O que foi medido, e o que foi descartado

Os valores são os **publicados em 2026-10-01** e ficam como foram medidos; a
coluna da direita diz quais não são de confiança, e porquê.

| roteador | 40 perguntas | custo | contaminado? |
|---|---|---|---|
| centróide de embedding | **45%** | microssegundos | **sim → 68%** |
| vizinho mais próximo | 52,5% | 6 ms | **sim**, não remedido |
| voto@20 sobre o top-20 | 50% | 6 ms | **sim**, não remedido |
| centróide centrado (anisotropia) | 32% | microssegundos | **sim**, não remedido |
| regressão logística sobre os chunks | 42% | microssegundos | **sim → 60%** |
| BM25, voz com mais pontos no top-20 | 45% | ~20 ms | não, é lexical |
| **chamada ao qwen2.5:7b** | **72%** | **1,2 s** | não |
| chamada ao qwen2.5:3b | 42% | 0,6 s | não |

### A correcção de 2026-10-03

Cinco das oito linhas usam `idx.vectores`, que são `encode_passages` de
`Chunk.indexed_text` — e esse leva **«Autor — Título» à cabeça**
(`corpus/chunk.py:23`), enquanto as consultas são verso puro. Os centróides
carregavam o **nome do heterónimo**, e a exactidão saiu subestimada em ~23
pontos. Remedidas duas das cinco; as outras três partilham o defeito e **não
foram re-medidas**, logo os seus números não valem em nenhum sentido.

**A frase que aqui estava — «nenhum método de embedding passa dos 52,5%, o
espaço não separa estas vozes» — está refutada.** O centróide corrigido faz
**68%** em perguntas e **64%** em poemas, contra 72% do 7B. A vantagem do LLM
cai de +27 para **+4 pontos**, que a n=40 não se distinguem de zero: **o
roteador LLM não está estabelecido como melhor** que um centróide corrigido.

O que decidiria, e não foi medido: o centróide nunca correu no conjunto
adversarial (onde o 7B fez 92%) nem na ablação de indícios (72% → 70%), e um
classificador que depende de superfície lexical é o que deveria desabar aí. Ver
[`docs/fase-4/08-RELATORIO-REMEDICAO.md`](../docs/fase-4/08-RELATORIO-REMEDICAO.md).

O que **sobrevive** da leitura original: o Passo A1c continua a refutar a
hipótese do registo, porque poemas e perguntas andam juntos depois da correcção
(64% contra 68%, antes 42% contra 45%).

E isto não leva ressalva, porque não toca em `idx.vectores`: o 3B a 42% contra o
7B a 72% diz o que a tarefa é — **conhecimento**, não padrão. O 3B não sabe quem
é Ricardo Reis.

## Por que `temperature=0`

O gerador usa 0,9, medido às cegas na Fase 0 para verso. Um classificador é o
problema oposto: a mesma pergunta tem de dar sempre a mesma voz, ou o utilizador
não consegue aprender o sistema.

## O custo real: +0,5 s por pergunta, e 20 s uma vez

Os 1,2 s do Passo A2 são o caso **quente**: descartei uma chamada de
aquecimento, logo medi a 2.ª em diante. A correr o CLI em `/auto`, a primeira
pergunta roteada custou **20,0 s** — o prefill a frio dos 331 tokens deste
`SYSTEM` a 16,5 tok/s, que é a taxa de CPU que a Fase 0 mediu.

A pergunta grave era outra, e foi medida no Passo A4b: a Fase 0 resolveu os
13,63 s de prefill da persona pondo-a no `system`, que fica em cache. O roteador
tem um `system` **diferente** — se o Ollama guardasse um prefixo por slot,
alternar faria cada um invalidar o do outro, e a persona voltaria a custar 20 s
em **todas** as perguntas.

Não acontece. O Ollama 0.35 mantém os dois prefixos:

| | prefill do gerador |
|---|---|
| só o gerador, 3 perguntas | 0,72 · 0,66 · **0,57** s |
| alternado com o roteador | 0,81 · 0,67 · **0,52** s |

Custo do `/auto` do 2.º turno em diante: **+0,5 s**. Daí `aquecer()`: paga-se os
20 s quando o utilizador liga o roteador, e não na primeira pergunta que faz.

## Por que isto propõe e não decide

Um roteador a 72% manda 28% das perguntas para a voz errada. Em silêncio, isso
custa ~30 s de espera por uma resposta que não foi pedida; **com a proposta à
vista, custa uma tecla**. Daí `Proposta`, que o CLI mostra antes de gerar, e daí
a selecção explícita (`/caeiro`) continuar a ser override absoluto.

## O que os 72% valem

Medido no Passo A3, contra a ressalva de que as 40 perguntas foram escritas
**para** uma voz:

- **Ablação de indícios:** trocar 15 substantivos-assinatura (`rebanho`,
  `máquinas`, `vinho`, `o mar`) por paráfrase neutra baixa os 72% para **70%**.
  A exactidão não vinha das palavras que entregam a resposta.
- **Conjunto adversarial** (12 perguntas pré-registadas, sem voz em mente):
  **92%** de vozes aceitáveis, contra 58% de «ortónimo sempre», e 2/2 nos
  controlos. Só 67% se se exigir a voz *primária* — porque a maioria destas
  perguntas tem mais de uma resposta certa.

Os 72% medem concordância com uma etiqueta única; a tarefa real não tem etiqueta
única.
"""
from __future__ import annotations

from dataclasses import dataclass

from .corpus.models import Voice
from .generation.base import ErroDeGeracao, Generator

#: Descreve a **postura** de cada voz, não só o nome. A Fase 0 mediu que nomear
#: o heterónimo produz pastiche e descrever a postura produz a voz; o Passo A2
#: usou o mesmo princípio para o classificar, e é este o texto medido.
SYSTEM = """És um especialista em Fernando Pessoa. Dada uma pergunta ou
sentimento de um leitor, dizes qual das quatro vozes lhe responderia melhor.

CAEIRO — vê as coisas como são e recusa dar-lhes sentido oculto. Natureza,
rebanhos, paisagem, o sol. Pensar estraga o ver. Não há metafísica nem símbolo.

CAMPOS — sente tudo em excesso e ao mesmo tempo. Cidade, máquinas, viagens,
multidões, tabacaria. Euforia e náusea, cansaço de ser tanta coisa, infância
perdida como ferida.

REIS — estóico e epicurista contido. Aceita o destino, aconselha a medida, o
gozo breve do presente, a flor que se colhe antes de murchar. Lídia, Neera,
Cloe. A morte encarada com calma clássica.

ORTONIMO (Fernando Pessoa ele mesmo) — não sabe quem é e sabe que finge. O
mistério, o sonho, a fingida dor, a distância entre pensar e ser, Portugal e o
mar como destino, a criança que foi e não reconhece.

Responde com UMA palavra: caeiro, campos, reis ou ortonimo. Nada mais."""

#: As vozes que o roteador pode propor. `search` fica de fora: escreve em
#: inglês, e propor-lhe uma pergunta em português trocaria a língua da resposta
#: sem o utilizador pedir.
ROTEAVEIS = (Voice.CAEIRO, Voice.CAMPOS, Voice.REIS, Voice.ORTONIMO)

#: 8 chega para «ortonimo» e deixa folga. O custo medido do roteador é quase
#: todo prefill (0,89 s de 1,23 s), logo encurtar a saída não o acelera muito.
MAX_TOKENS = 8

TEMPERATURA = 0.0


@dataclass(frozen=True)
class Proposta:
    """O que o roteador propõe, e o que lhe custou.

    `voz is None` quer dizer **não sei**, e o CLI responde a isso mantendo a voz
    corrente. É um estado legítimo: vale mais manter a voz do que inventar uma.
    """
    voz: Voice | None
    bruto: str
    segundos: float

    @property
    def decidiu(self) -> bool:
        return self.voz is not None


def interpretar(texto: str) -> Voice | None:
    """Lê a palavra que o modelo devolveu.

    Tolera pontuação, maiúsculas e um prefácio curto («A voz é: campos»), porque
    nas 92 chamadas medidas nos Passos A2 e A3 o modelo nunca deixou de incluir
    a palavra — mas um dia deixará, e aí o resultado é `None`, não um palpite.

    «pessoa» vale como ortónimo: é o nome que o CLI usa no comando (`/pessoa`) e
    o modelo escolhe-o às vezes.
    """
    t = texto.strip().lower()
    for v in ROTEAVEIS:
        if v.value in t:
            return v
    if "pessoa" in t or "ortónimo" in t:
        return Voice.ORTONIMO
    return None


#: Pergunta de aquecimento. Qualquer texto serve — o que se quer em cache é o
#: prefixo do `SYSTEM`, e o `user` não faz parte dele.
AQUECIMENTO = "aquecimento"


def aquecer(gerador: Generator) -> float:
    """Põe o prefixo do roteador em cache, e devolve o que isso custou.

    Existe para o custo a frio cair onde o utilizador o pediu. Sem isto, os
    ~20 s de prefill do `SYSTEM` caem na primeira pergunta que ele faz em
    `/auto`, no meio de uma espera que ele atribui ao poema.
    """
    return rotear(AQUECIMENTO, gerador).segundos


def rotear(pergunta: str, gerador: Generator) -> Proposta:
    """Propõe a voz para uma pergunta. Nunca levanta: propor é opcional.

    Se o gerador falhar — Ollama em baixo, modelo ausente — a proposta é «não
    sei». O roteador é uma conveniência, e uma conveniência não tem o direito de
    derrubar a conversa.
    """
    import time
    t0 = time.perf_counter()
    try:
        r = gerador.gerar(SYSTEM, pergunta, max_tokens=MAX_TOKENS,
                          temperatura=TEMPERATURA)
    except ErroDeGeracao:
        return Proposta(None, "", time.perf_counter() - t0)
    return Proposta(interpretar(r.texto), r.texto.strip(),
                    time.perf_counter() - t0)
