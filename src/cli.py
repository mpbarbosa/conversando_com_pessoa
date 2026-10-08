"""CLI do PessoaBot.

## Decisões de interface, e de onde vêm

**Seleção de voz explícita por omissão**, com o roteador da Fase 4 em `/auto`.
A explícita é grátis e nunca erra; o roteador acerta 72% contra 25% do «ortónimo
sempre» (medido em `docs/fase-4/`) e custa **+0,5 s por pergunta** depois de
aquecido, mais ~20 s uma vez — ver `_aquecer_roteador`. Daí ser opcional, **propor em
vez de decidir**, e qualquer `/caeiro` o desligar: a 72%, uma em cada quatro
perguntas iria para a voz errada, e em silêncio isso custaria ~30 s de espera
por uma resposta que ninguém pediu.

**Streaming sempre.** A Fase 1 Passo 5 mediu ~19 s de prefill antes do primeiro
verso e ~23 s de decode. Sem streaming são 42 s de nada; com streaming são 19 s
de nada e depois verso a aparecer.

**Tempos à vista.** O prefill domina a espera (58–89%, medido na Fase 0), e
mostrar o custo de cada pergunta ensina-o ao utilizador em vez de o esconder.

**Fontes citadas.** O sistema é RAG: ver de onde veio o contexto é o mínimo.

**Reordenação por escolha**, em `/rerank`. A Fase 3B mediu +0,090 de nDCG@5 por
2,57 s, com o pool de candidatos fechado para que o número não dependa de quem
construiu o gabarito. Fica desligada por omissão porque é uma troca — 2,57 s
num total de ~30 s — e uma troca é do utilizador.
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

#: Liga e desliga o roteador. Só em português: o `SYSTEM` do roteador está em
#: português e as quatro vozes roteáveis também, logo propor em inglês seria
#: propor fora do que foi medido.
COMANDOS_AUTO = {"/auto", "/manual"}

#: Liga e desliga a reordenação por cross-encoder. O modelo tem 568M e é
#: carregado na primeira vez que se liga, não no arranque: quem não a pede não
#: paga o carregamento.
COMANDOS_RERANK = {"/rerank", "/sem-rerank"}
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
    auto: bool = typer.Option(False, "--auto",
                              help="roteador propõe a voz a cada pergunta"),
    rerank: bool = typer.Option(False, "--rerank",
                                help="reordena os candidatos (+0,090 nDCG@5, +2,6 s)"),
    verboso: bool = typer.Option(False, "--verboso", help="mostra progresso de construção"),
    grafo: bool = typer.Option(False, "--grafo",
                               help="responde pelo grafo de estado (LangGraph); "
                                    "sem streaming, imprime no fim"),
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
    typer.echo(_cinza("/auto para o roteador propor a voz "
                      "(72% de acerto, +0,5 s por pergunta)"))
    typer.echo(_cinza("/rerank para reordenar os candidatos "
                      "(+0,090 nDCG@5, +2,6 s por pergunta)"))
    typer.echo(_cinza("/sair para sair"))
    typer.echo(_cinza("uma resposta leva ~30 s em CPU; os versos aparecem à medida"))
    typer.echo()

    if auto:
        _aquecer_roteador(pipeline)
    if rerank:
        _ligar_rerank(pipeline)

    while True:
        try:
            etiqueta = (actual.value if lingua is Lang.PT
                        else f"{actual.value}/{lingua.value}")
            if auto:
                etiqueta = f"auto·{etiqueta}"
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
            # Pedir uma voz é override absoluto: desliga o roteador. Se não
            # desligasse, a pergunta seguinte desfazia a escolha em silêncio.
            desligou = auto
            auto = False
            typer.echo(_cinza(f"voz: {p.nome} ({p.idioma.value})"
                              + (" · roteador desligado" if desligou else "")))
            continue
        if linha.lower() in COMANDOS_RERANK:
            if linha.lower() == "/rerank":
                _ligar_rerank(pipeline)
            else:
                pipeline.reranker = None
                typer.echo(_cinza("reordenação desligada"))
            continue
        if linha.lower() in COMANDOS_AUTO:
            auto, lingua_antes = linha.lower() == "/auto", lingua
            if auto and lingua_antes is not Lang.PT:
                auto = False
                typer.echo(_cinza("  o roteador só foi medido em português; "
                                  "use /pt primeiro"))
            elif auto:
                typer.echo(_cinza("roteador ligado: propõe a voz e mostra-a "
                                  "antes de gerar"))
                _aquecer_roteador(pipeline)
            else:
                typer.echo(_cinza("roteador desligado"))
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

        voz_da_vez = actual
        if auto:
            voz_da_vez = _propor(pipeline, linha, actual)
        if grafo:
            _responder_pelo_grafo(pipeline, linha, voz_da_vez, lingua)
        else:
            _responder(pipeline, linha, voz_da_vez, lingua)


def _responder_pelo_grafo(pipeline: Pipeline, pergunta: str, voz: Voice,
                          idioma: Lang = Lang.PT) -> None:
    """Mesma resposta, pelo grafo de estado — e sem streaming.

    ⚠️ **A diferença é visível para quem usa:** o caminho normal imprime os
    versos à medida que chegam (~2 s para o primeiro); este espera a resposta
    inteira (~30 s de silêncio). É o preço de declarar a política como grafo em
    vez de a executar num laço de streaming, e por isso vive atrás de um flag em
    vez de substituir o caminho medido.

    O que NÃO muda: recuperação, prompt, guarda, detector de plágio e política
    de repetição são os mesmos objectos — ver `src/grafo.py` e o teste de
    paridade em `tests/test_grafo.py`.
    """
    from .grafo import PipelineGrafo
    from .pipeline import Turno

    typer.echo()
    t0 = time.perf_counter()
    try:
        turno: Turno = PipelineGrafo.de(pipeline).responder(pergunta, voz, idioma)
    except ErroDeGeracao as e:
        typer.secho(f"\n{e}", fg="red", err=True)
        return
    except KeyboardInterrupt:
        typer.echo(_cinza("\n  (interrompido)"))
        return

    typer.echo(f"{VERDE}{turno.texto}{FIM}")
    typer.echo()
    if not turno.aprovado:
        motivos = list(turno.veredicto.motivos)
        if turno.plagio.plagiou:
            motivos.append(turno.plagio.resumo())
        typer.echo(_cinza(f"  não aprovado ({'; '.join(motivos)})"))
    # `primeiro` é None de propósito: esse campo imprime «s até ao 1.º verso» e
    # aqui não há 1.º verso antes do fim. O total vai à parte, com o nome certo.
    _rodape(turno, None)
    typer.echo(_cinza(f"  {time.perf_counter() - t0:.1f} s até à resposta "
                      f"inteira (grafo, sem streaming)"))
    typer.echo()


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


def _ligar_rerank(pipeline: Pipeline) -> None:
    """Carrega o cross-encoder e liga-o ao pipeline.

    O modelo tem 568M e o carregamento é visível, logo é anunciado. Quem não
    pede a reordenação não paga nem o carregamento nem os ~2,6 s por pergunta.

    A primeira reordenação custa ~4,8 s em vez de 2,6 s, e isso **não** se
    resolve com aquecimento — tentei, e `rerank.py` tem a medição que mostra
    porque não. Anuncia-se.
    """
    if pipeline.reranker is not None:
        typer.echo(_cinza("reordenação já estava ligada"))
        return
    from .retrieval.rerank import N_RERANK, padrao

    typer.echo(_cinza("  a carregar o reranker (568M, uma vez)..."), nl=False)
    t0 = time.perf_counter()
    pipeline.reranker = padrao()
    typer.echo(_cinza(f" {time.perf_counter() - t0:.1f} s"))
    typer.echo(_cinza(f"reordenação ligada: {N_RERANK} candidatos, "
                      f"+0,090 nDCG@5 medido, ~2,6 s por pergunta"))
    # Medido a correr isto: 4,8 s na primeira e 2,5 s nas seguintes. Um
    # aquecimento não o resolve (ver `rerank.py`), logo anuncia-se.
    typer.echo(_cinza("  a primeira custa ~4,8 s; as seguintes ~2,6 s"))


def _aquecer_roteador(pipeline: Pipeline) -> None:
    """Paga o prefill a frio do roteador aqui, e não na 1.ª pergunta.

    Medido a correr o CLI: a primeira pergunta em `/auto` custou 20,0 s de
    roteamento — o prefill dos 331 tokens do `SYSTEM` a 16,5 tok/s. Do 2.º turno
    em diante são 0,5 s, porque o Ollama mantém os dois prefixos em cache
    (Passo A4b). O custo é inevitável; cair sem aviso no meio de um poema é que
    não.
    """
    from .roteador import aquecer

    typer.echo(_cinza("  a aquecer o roteador (~20 s, uma vez)..."), nl=False)
    s = aquecer(pipeline.gerador)
    typer.echo(_cinza(f" {s:.1f} s"))


def _propor(pipeline: Pipeline, pergunta: str, corrente: Voice) -> Voice:
    """Mostra a proposta do roteador e devolve a voz a usar neste turno.

    Mostra **antes** de gerar, e nomeia os comandos de override na mesma linha:
    a 72% de acerto, uma pergunta em cada quatro vai para a voz errada, e o que
    separa «custa uma tecla» de «custa 30 s» é o utilizador ver a proposta
    enquanto ela ainda não produziu nada.

    `voz is None` — Ollama em baixo, ou o modelo a divagar — mantém a voz
    corrente. Inventar uma seria pior que não propor.
    """
    from .roteador import rotear

    p = rotear(pergunta, pipeline.gerador)
    if not p.decidiu:
        typer.echo(_cinza(f"  roteador sem opinião ({p.segundos:.1f} s); "
                          f"mantenho {persona(corrente).nome}"))
        return corrente
    nome = persona(p.voz).nome
    typer.echo(_cinza(f"  voz proposta: {nome} ({p.segundos:.1f} s) · "
                      f"/caeiro /campos /reis /pessoa para fixar outra"))
    return p.voz


def _responder(pipeline: Pipeline, pergunta: str, voz: Voice,
               idioma: Lang = Lang.PT) -> None:
    from .pipeline import Turno

    typer.echo()
    t0 = time.perf_counter()
    primeiro: float | None = None
    # Streaming e validação estão em tensão: imprimir à medida significa
    # imprimir antes de poder validar. O que é removível está sempre no início —
    # o eco da pergunta (observado: a «o que vês quando olhas para uma árvore?»
    # o modelo começou com «O que vejo quando olho para uma árvore») e o
    # preâmbulo (observado: «Aqui está um poema novo, seguindo as instruções:»)
    # —, logo resolve-se retendo linhas até sobrar uma que seja verso. Custa o
    # tempo de gerar essas linhas (~2 s cada a 6 tok/s), não os 42 s de não
    # streaming.
    #
    # Retém-se **enquanto a linha limpa sair vazia**, e não só a primeira: o
    # preâmbulo e o eco podem vir em linhas separadas, e com uma só linha de
    # retenção o segundo escapava.
    buffer: list[str] = []
    a_reter = True
    try:
        for item in pipeline.responder_em_fluxo(pergunta, voz, idioma):
            if isinstance(item, str):
                if primeiro is None:
                    primeiro = time.perf_counter() - t0
                if a_reter:
                    buffer.append(item)
                    retido, a_reter = _limpar_inicio("".join(buffer), pergunta)
                    if a_reter:
                        buffer = [retido] if retido else []
                        continue
                    buffer = []
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


def _limpar_inicio(acumulado: str, pergunta: str) -> tuple[str, bool]:
    """Descasca as linhas de enquadramento do início do fluxo.

    Devolve `(texto_a_imprimir, continuar_a_reter)`. Retém enquanto não houver
    uma linha completa que sobreviva à limpeza: o preâmbulo e o eco da pergunta
    são ambos removíveis e podem vir em linhas separadas.
    """
    from .guard import (remover_cercas, remover_eco_da_pergunta,
                        remover_preambulo)
    if "\n" not in acumulado:
        return acumulado, True
    linha, resto = acumulado.split("\n", 1)
    limpa = remover_eco_da_pergunta(
        remover_preambulo(remover_cercas(linha)), pergunta)
    if not limpa.strip():
        # Linha descartada por inteiro. O resto pode já trazer outra completa,
        # logo volta-se a tentar em vez de a dar por boa.
        return _limpar_inicio(resto, pergunta) if "\n" in resto else (resto, True)
    return f"{limpa}\n{resto}", False


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
    if turno.veredicto.gramatica:
        typer.echo(_cinza(f"  construções que a persona proíbe: "
                          f"{', '.join(turno.veredicto.gramatica)}"))
    fontes = ", ".join(c.poem_id for c in turno.usados) or "nenhuma"
    typer.echo(_cinza(f"  fontes: {fontes}"))
    partes = [f"{turno.recuperacao_ms:.0f} ms recuperação"]
    # Separado da recuperação de propósito: é a parcela que o utilizador paga
    # por uma escolha e pode desligar com /sem-rerank.
    if turno.rerank_ms is not None:
        partes.append(f"{turno.rerank_ms/1000:.1f} s reordenação")
    if primeiro is not None:
        partes.append(f"{primeiro:.1f} s até ao 1.º verso")
    partes.append(turno.resposta.resumo())
    if turno.tentativas > 1:
        partes.append(f"{turno.tentativas} tentativas")
    typer.echo(_cinza("  " + " · ".join(partes)))
    typer.echo()


if __name__ == "__main__":
    app(prog_name=PROGRAMA)
