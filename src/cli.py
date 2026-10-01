"""CLI do PessoaBot.

## Decisões de interface, e de onde vêm

**Seleção de voz explícita**, não automática. É grátis e nunca erra; o roteador
automático fica para a Fase 4. `/caeiro`, `/campos`, `/reis`, `/pessoa`.

**Streaming sempre.** A Fase 1 Passo 5 mediu ~19 s de prefill antes do primeiro
verso e ~23 s de decode. Sem streaming são 42 s de nada; com streaming são 19 s
de nada e depois verso a aparecer.

**Tempos à vista.** O prefill domina a espera (58–89%, medido na Fase 0), e
mostrar o custo de cada pergunta ensina-o ao utilizador em vez de o esconder.

**Fontes citadas.** O sistema é RAG: ver de onde veio o contexto é o mínimo.
"""
from __future__ import annotations

import os

# Silenciar o ruído de arranque do ecossistema Hugging Face **antes** de
# qualquer importação que o accione. O `sentence_transformers` imprime um aviso
# sobre pedidos não autenticados e uma barra de «Loading weights» que nada dizem
# a quem quer conversar com Pessoa — e o modelo vem todo do cache local, logo o
# aviso é irrelevante aqui.
#
# Nas minhas corridas de desenvolvimento filtrei isto com `grep`, o que esconde
# o problema em vez de o resolver.
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import sys
import time
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

import typer

from .corpus.models import Lang, Voice
from .generation.base import ErroDeGeracao
from .generation.ollama import OllamaGenerator
from .pipeline import Pipeline
from .voices import IDIOMA_UNICO, VOZES_COM_PERSONA, idiomas_de, persona

app = typer.Typer(add_completion=False,
                  help="Conversa em verso com Fernando Pessoa.")

#: O `--help` mostraria «python -m src.cli»; o utilizador invoca `./pessoa`.
PROGRAMA = "pessoa"

COMANDOS_VOZ = {
    "/caeiro": Voice.CAEIRO,
    "/campos": Voice.CAMPOS,
    "/reis": Voice.REIS,
    "/pessoa": Voice.ORTONIMO,
    "/ortonimo": Voice.ORTONIMO,
    # Alexander Search é um heterónimo que escrevia em inglês, com 50 poemas no
    # corpus. Durante a Fase 1 ficou inacessível porque o filtro de idioma
    # excluía o inglês por omissão.
    "/search": Voice.SEARCH,
}

COMANDOS_IDIOMA = {"/pt": Lang.PT, "/en": Lang.EN,
                   "/portugues": Lang.PT, "/ingles": Lang.EN}
SAIR = {"/sair", "/exit", "/quit", "sair"}

VERDE, CINZA, NEGRITO, FIM = "\033[32m", "\033[90m", "\033[1m", "\033[0m"


def _cinza(t: str) -> str:
    return f"{CINZA}{t}{FIM}"


def _silenciar_hf() -> None:
    """Baixa a verbosidade dos módulos HF já importados.

    As variáveis de ambiente no topo cobrem o que é lido na importação; isto
    cobre o resto, que só existe depois de os módulos serem carregados.
    """
    try:
        from transformers.utils import logging as tlog
        tlog.set_verbosity_error()
        tlog.disable_progress_bar()
    except Exception:
        pass
    try:
        from huggingface_hub.utils import logging as hlog
        hlog.set_verbosity_error()
    except Exception:
        pass


def _arrancar(modelo: str | None, verboso: bool):
    """Carrega corpus, índice, encoder e gerador, falhando com mensagem útil."""
    from .corpus.build import CAMINHO, build, load
    from .retrieval.encoder import Encoder
    from .retrieval.index import Index
    from .tokens import contador
    import os

    gen = OllamaGenerator(modelo=modelo) if modelo else OllamaGenerator()
    if not gen.disponivel():
        typer.secho(f"Ollama não responde em {gen.url_base}.", fg="red", err=True)
        typer.echo("Arrancar com: ollama serve", err=True)
        raise typer.Exit(1)
    if not gen.modelo_instalado():
        typer.secho(f"Modelo «{gen.modelo}» não instalado.", fg="red", err=True)
        typer.echo(f"Descarregar com: ollama pull {gen.modelo}", err=True)
        raise typer.Exit(1)

    if not os.path.exists(CAMINHO):
        typer.echo(_cinza("corpus.jsonl não existe; a construir (~40 s)..."))
        build(verboso=verboso)
    meta, chunks = load()

    typer.echo(_cinza("a carregar o encoder..."))
    _silenciar_hf()
    enc = Encoder()
    idx = Index.load(chunks, enc, meta["assinatura"])
    if idx is None:
        typer.echo(_cinza("índice ausente ou desactualizado; a construir (~6 min)..."))
        idx = Index.load_or_build(chunks, enc, meta["assinatura"], progresso=verboso)

    # Contador do gerador, não do encoder: o qwen conta ~17% mais tokens em
    # português, e orçamentar com o do e5 subestimaria até 46%.
    n_tok = contador("Qwen/Qwen2.5-7B-Instruct")
    return Pipeline(idx, enc, gen, n_tok), len(chunks)


@app.command()
def main(
    voz: str = typer.Option("pessoa", "--voz", "-v",
                            help="voz: caeiro, campos, reis, pessoa, search"),
    idioma: str = typer.Option("pt", "--idioma", "-i",
                               help="língua: pt ou en"),
    modelo: str = typer.Option(None, "--modelo", "-m", help="modelo do Ollama"),
    verboso: bool = typer.Option(False, "--verboso", help="mostra progresso de construção"),
) -> None:
    chave = f"/{voz.lower().lstrip('/')}"
    if chave not in COMANDOS_VOZ:
        typer.secho(f"voz desconhecida: {voz}", fg="red", err=True)
        typer.echo(f"disponíveis: {', '.join(v.value for v in VOZES_COM_PERSONA)}", err=True)
        raise typer.Exit(2)
    actual = COMANDOS_VOZ[chave]

    chave_i = f"/{idioma.lower().lstrip('/')}"
    if chave_i not in COMANDOS_IDIOMA:
        typer.secho(f"língua desconhecida: {idioma}", fg="red", err=True)
        typer.echo("disponíveis: pt, en", err=True)
        raise typer.Exit(2)
    lingua = COMANDOS_IDIOMA[chave_i]
    lingua = _ajustar_lingua(actual, lingua)

    pipeline, n_chunks = _arrancar(modelo, verboso)

    typer.echo()
    typer.secho("PessoaBot", bold=True)
    typer.echo(_cinza(f"{n_chunks} chunks · {pipeline.gerador.nome}"))
    typer.echo(_cinza("vozes: /caeiro /campos /reis /pessoa /search · língua: /pt /en"))
    typer.echo(_cinza("/sair para sair"))
    typer.echo(_cinza("uma resposta leva ~30 s em CPU; os versos aparecem à medida"))
    typer.echo()

    while True:
        try:
            etiqueta = (actual.value if lingua is Lang.PT
                        else f"{actual.value}/{lingua.value}")
            linha = input(f"{NEGRITO}você{FIM} [{etiqueta}]> ").strip()
        except (EOFError, KeyboardInterrupt):
            typer.echo("\nAdeus, como quem se despede de si mesmo.")
            return
        if not linha:
            continue
        if linha.lower() in SAIR:
            typer.echo("Adeus, como quem se despede de si mesmo.")
            return
        if linha.lower() in COMANDOS_VOZ:
            actual = COMANDOS_VOZ[linha.lower()]
            lingua = _ajustar_lingua(actual, lingua)
            p = persona(actual, lingua)
            typer.echo(_cinza(f"voz: {p.nome} ({p.idioma.value})"))
            continue
        if linha.lower() in COMANDOS_IDIOMA:
            pedida = COMANDOS_IDIOMA[linha.lower()]
            lingua = _ajustar_lingua(actual, pedida, avisar=True)
            p = persona(actual, lingua)
            typer.echo(_cinza(f"língua: {lingua.value} · voz: {p.nome}"))
            continue
        if linha.startswith("/"):
            typer.echo(_cinza(f"comando desconhecido: {linha}"))
            continue

        _responder(pipeline, linha, actual, lingua)


def _ajustar_lingua(voz: Voice, pedida: Lang, avisar: bool = False) -> Lang:
    """Força a língua única de uma voz que só existe numa.

    Alexander Search tem 1 poema em português entre 52: servi-lo em português
    seria servi-lo do que ele não é.
    """
    unica = IDIOMA_UNICO.get(voz)
    if unica is not None and pedida is not unica:
        if avisar:
            typer.echo(_cinza(f"  {persona(voz, unica).nome} só escreve em "
                              f"{unica.value}"))
        return unica
    if (voz, pedida) not in __import__("src.voices", fromlist=["PERSONAS"]).PERSONAS:
        disponiveis = idiomas_de(voz)
        if disponiveis and pedida not in disponiveis:
            if avisar:
                typer.echo(_cinza(f"  esta voz só tem persona em "
                                  f"{', '.join(l.value for l in disponiveis)}"))
            return disponiveis[0]
    return pedida


def _responder(pipeline: Pipeline, pergunta: str, voz: Voice,
               idioma: Lang = Lang.PT) -> None:
    from .pipeline import Turno

    typer.echo()
    t0 = time.perf_counter()
    primeiro: float | None = None
    # Streaming e validação estão em tensão: imprimir à medida significa
    # imprimir antes de poder validar. O eco da pergunta — observado: à
    # pergunta «o que vês quando olhas para uma árvore?» o modelo começou com
    # «O que vejo quando olho para uma árvore» — é sempre o primeiro verso,
    # logo resolve-se retendo só até à primeira mudança de linha. Custa o
    # tempo de gerar uma linha (~2 s a 6 tok/s), não os 42 s de não streaming.
    buffer: list[str] = []
    a_reter = True
    try:
        for item in pipeline.responder_em_fluxo(pergunta, voz, idioma):
            if isinstance(item, str):
                if primeiro is None:
                    primeiro = time.perf_counter() - t0
                if a_reter:
                    buffer.append(item)
                    if "\n" not in "".join(buffer):
                        continue
                    a_reter = False
                    from .guard import remover_eco_da_pergunta, remover_cercas
                    retido = remover_eco_da_pergunta(
                        remover_cercas("".join(buffer)), pergunta)
                    sys.stdout.write(f"{VERDE}{retido}{FIM}")
                    sys.stdout.flush()
                    continue
                sys.stdout.write(f"{VERDE}{item}{FIM}")
                sys.stdout.flush()
                continue

            turno: Turno = item
            typer.echo("\n")
            if turno.aprovado:
                _rodape(turno, primeiro)
                return
            # Não aprovado: dizer porquê antes de repetir. Esconder a repetição
            # esconderia os ~28 s que ela custa.
            motivos = list(turno.veredicto.motivos)
            if turno.plagio.plagiou:
                motivos.append(turno.plagio.resumo())
            typer.echo(_cinza(f"  rejeitado ({'; '.join(motivos)}) — a repetir"))
            typer.echo()
            primeiro = None
            t0 = time.perf_counter()
            buffer, a_reter = [], True
    except ErroDeGeracao as e:
        typer.secho(f"\n{e}", fg="red", err=True)
    except KeyboardInterrupt:
        typer.echo(_cinza("\n  (interrompido)"))


def _rodape(turno, primeiro: float | None) -> None:
    # A guarda corrige brasileirismos, e esses aparecem a meio do texto, logo
    # o buffer de uma linha não os apanha. Em vez de reimprimir, avisar.
    cru = turno.resposta.texto.strip()
    if turno.veredicto.texto.strip() != cru:
        from .voices import INTERDICOES
        trocadas = [k for k in INTERDICOES if k in cru.lower()]
        if trocadas:
            typer.echo(_cinza(f"  (corrigido: {', '.join(trocadas)})"))
    if turno.veredicto.suspeitas:
        palavras = ", ".join(f"«{x.palavra}»" for x in turno.veredicto.suspeitas)
        typer.echo(_cinza(f"  palavras que nem o corpus nem o dicionário "
                          f"conhecem: {palavras}"))
    fontes = ", ".join(c.poem_id for c in turno.usados) or "nenhuma"
    typer.echo(_cinza(f"  fontes: {fontes}"))
    partes = [f"{turno.recuperacao_ms:.0f} ms recuperação"]
    if primeiro is not None:
        partes.append(f"{primeiro:.1f} s até ao 1.º verso")
    partes.append(turno.resposta.resumo())
    if turno.tentativas > 1:
        partes.append(f"{turno.tentativas} tentativas")
    typer.echo(_cinza("  " + " · ".join(partes)))
    typer.echo()


if __name__ == "__main__":
    app(prog_name=PROGRAMA)
