"""Contagem de tokens com o tokenizador real.

Dois tokenizadores importam neste projecto e **não** são intercambiáveis:

- o do **encoder** (`e5`), que define o limite de chunk (maxlen=512)
- o do **gerador**, que define o orçamento de prompt (`ORCAMENTO_USER = 300`)

Medido no corpus: o e5 dá mediana de 1,469 tokens por palavra (a estimativa de
1,45 usada no planeamento estava certa).

## Por que é que `contador()` não tem omissão

Tinha, e era o `ENCODER` — e isso é uma armadilha, porque **orçamentar o prompt
do gerador com o tokenizador do encoder subestima**. Remedido em 2026-10-08, nos
mesmos 25 poemas:

| tokenizador | mediana | razão ao e5 |
|---|---|---|
| e5 | 111 | 1,000 |
| gerador | 133 | **1,167** |

São os 17% que o [`generation/prompt.py`](generation/prompt.py) já publicava. O
`src/` nunca caiu nisso — as duas chamadas sempre passaram o nome —, mas **nove
scripts de fase caíram**, e com eles as amostras das Fases 5, 5B, 5G, 5H, 5I,
5M, 5N, 5U e 5W: correram com ~350 tokens de gerador onde o orçamento pede 300.
As comparações **dentro** de cada fase ficam intactas (os braços partilharam o
orçamento); o que fica errado é chamar-lhes «configuração de produção».

A omissão saiu para que o erro passe a ser impossível de cometer em silêncio.
"""
from __future__ import annotations

from collections.abc import Callable
from functools import lru_cache

ENCODER = "intfloat/multilingual-e5-base"

#: O tokenizador do **gerador**, para orçamentar o prompt.
#:
#: **Continua a ser o do qwen depois de a Fase 5S trocar o modelo para o
#: `llama3.1:8b`, e isso foi verificado e não corrigido.** Medido em 2026-10-08
#: pelo `prompt_eval_count` do próprio Ollama, que é a contagem autoritativa do
#: modelo que serve: nos mesmos 25 poemas o llama dá mediana **135** contra
#: **133** do qwen — razão de **1,000**, máximo de 1,031. O orçamento derivado
#: com o qwen descreve o llama dentro de 3%, logo trocá-lo não compraria nada e
#: custaria uma descarga de tokenizador novo.
#:
#: É a segunda coisa ligada ao `MODELO` que a 5S não olhou (a primeira foi o
#: roteador, que ela encontrou). Esta é benigna — mas só se sabe por estar medida.
GERADOR = "Qwen/Qwen2.5-7B-Instruct"


@lru_cache(maxsize=4)
def _tokenizador(nome: str):
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(nome)


def contador(nome: str) -> Callable[[str], int]:
    """Devolve uma função que conta tokens, sem tokens especiais.

    `nome` é **obrigatório** de propósito: ver o cabeçalho do módulo. Use
    `ENCODER` para o que diz respeito a *chunks* e `GERADOR` para o que diz
    respeito ao prompt.
    """
    tok = _tokenizador(nome)

    def conta(texto: str) -> int:
        return len(tok(texto, add_special_tokens=False).input_ids)

    return conta
