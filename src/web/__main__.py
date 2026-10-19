"""`python -m src.web` — o servidor, no interface e na porta do `app.py`.

## Porque é que isto existe, e é mais do que conveniência

Até ao passo 4 do [plano do serviço público](../../docs/PRODUCAO.md) ninguém
arrancava este servidor por um comando escrito: corria-se um `uvicorn` à mão, e
o `HOST` e a `PORTA` do `app.py` **não eram lidos por ninguém** — eram duas
constantes com o valor certo e sem consumidor.

A unidade de utilizador do passo 4 precisa de um `ExecStart`. Se ele fosse
`uvicorn src.web.app:app --host 127.0.0.1 --port 8000`, o interface e a porta
passavam a existir em **dois** sítios: nas constantes e no ficheiro da unidade,
que não se testa e que ninguém lê ao mudar o `app.py`. E o que divergia era
precisamente a decisão que o portão **I7′** protege — um `--host 0.0.0.0` numa
unidade é o «copiado de um tutorial» que a Fase 6 listou como risco, e nenhum
teste deste repositório o veria.

Logo a unidade diz `python -m src.web`, e o interface vive num sítio só.

## `log_level` e `access_log`

Sem registo de acessos, de propósito: o portão **D4** do plano mede-se
**nos registos do serviço** — «de um endereço não convidado, o URL devolve o
ecrã de autenticação do fornecedor e **nunca** toca no `uvicorn`, verificado nos
registos do serviço, que não registam o pedido». Um registo de acessos é o
instrumento desse portão, logo fica ligado. É o contrário da omissão do
`uvicorn`, que é ligado também — escrito aqui para não parecer distracção.
"""
from __future__ import annotations


def main() -> None:
    import uvicorn

    from .app import HOST, PORTA
    uvicorn.run("src.web.app:app", host=HOST, port=PORTA, access_log=True)


if __name__ == "__main__":
    main()
