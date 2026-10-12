"""Limpeza do início do fluxo, partilhada por quem o mostra.

## Porque é que isto não vive no `cli.py`

Viveu, até ao Passo 1 da [Fase 6](../docs/FASE-6.md). Mudou de casa porque
passou a ter **dois** consumidores: o laço de streaming do CLI e o
`POST /api/perguntar` da interface gráfica.

Não é arrumação. O defeito que esta função corrige foi **observado**, e repete-se
em qualquer coisa que imprima fragmentos à medida que chegam:

- à pergunta «o que vês quando olhas para uma árvore?», o modelo começou por
  «O que vejo quando olho para uma árvore» — o eco da pergunta;
- à «qual é o futuro de portugal?», começou por «Aqui está um poema novo,
  seguindo as instruções:» — o preâmbulo.

As duas linhas apareciam no ecrã **embora o texto validado não as tenha**:
`verificar` chama `remover_preambulo`, logo o veredicto já as tinha deitado
fora. O ecrã mostrava mais do que o veredicto julgara.

Numa interface gráfica é pior que no terminal: o texto aparece e depois salta
para trás. Uma segunda implementação da retenção — num `app.js`, por exemplo —
seria uma segunda política de apresentação a divergir em silêncio da primeira, e
é precisamente o que o portão **I2** da Fase 6 existe para impedir.

⚠️ O que isto **não** resolve continua registado no `CONTROLO.md` §5: o
streaming imprime antes de validar. Só o início é retido; a guarda corrige
brasileirismos a meio do texto e um buffer de uma linha não os apanha. Quem
mostra, **avisa** no rodapé.
"""
from __future__ import annotations

from .guard import remover_cercas, remover_eco_da_pergunta, remover_preambulo


def limpar_inicio(acumulado: str, pergunta: str) -> tuple[str, bool]:
    """Descasca as linhas de enquadramento do início do fluxo.

    Devolve `(texto_a_imprimir, continuar_a_reter)`. Retém enquanto não houver
    uma linha completa que sobreviva à limpeza: o preâmbulo e o eco da pergunta
    são ambos removíveis e podem vir em linhas separadas.
    """
    if "\n" not in acumulado:
        return acumulado, True
    linha, resto = acumulado.split("\n", 1)
    limpa = remover_eco_da_pergunta(
        remover_preambulo(remover_cercas(linha)), pergunta)
    if not limpa.strip():
        # Linha descartada por inteiro. O resto pode já trazer outra completa,
        # logo volta-se a tentar em vez de a dar por boa.
        return limpar_inicio(resto, pergunta) if "\n" in resto else (resto, True)
    return f"{limpa}\n{resto}", False
