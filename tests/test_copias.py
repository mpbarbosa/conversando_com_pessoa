"""As cópias das sessões e o restauro. Passo 10 do `PRODUCAO.md`, portão **D8**.

O portão diz: «restauro num directório limpo e as sessões de antes a
aparecerem». Está no fim deste ficheiro, e é o único teste aqui que se chama
`d8`. Os outros medem as quatro decisões que o tornam verdade mais do que uma
vez — a cópia que coopera com um escritor vivo, a cópia que só tem nome de
cópia depois de passar a verificação, a rotação que nunca fica sem nenhuma, e o
restauro que recusa **antes** de tocar na base.
"""
from __future__ import annotations

import configparser
import shutil
import sqlite3
import subprocess
from pathlib import Path

import pytest

from src.web import copias
from src.web.copias import ErroDeCopia, Estado
from src.web.sessoes import VERSAO, Arquivo
from src.web.unidades import (
    NOME_COPIA,
    NOME_TEMPORIZADOR_COPIA,
    Alvo,
    copia_das_sessoes,
    escrever,
    temporizador_da_copia,
    temporizador_da_guarda,
)


@pytest.fixture
def base(tmp_path):
    """Uma base com uma sessão e duas mensagens, como um dia de uso pequeno."""
    caminho = str(tmp_path / "base" / "sessoes.db")
    a = Arquivo(caminho)
    sid = a.criar_sessao(voz="caeiro", idioma="pt", modelo="duplo",
                         rerank=False, auto=False)
    a.registar_mensagem(sid, "utilizador", "o que é a natureza?")
    a.registar_mensagem(sid, "bot", "um poema qualquer")
    return caminho


@pytest.fixture
def destino(tmp_path):
    return tmp_path / "copias"


def _copia_falsa(destino, instante, origem):
    """Uma cópia com um instante escolhido no nome, para exercitar a ordem."""
    destino.mkdir(parents=True, exist_ok=True)
    alvo = destino / f"{copias.PREFIXO}{instante}{copias.SUFIXO}"
    alvo.write_bytes(open(origem, "rb").read())
    return alvo


# --- 1. copiar ------------------------------------------------------------- #

def test_a_copia_fica_verificada_e_com_o_mesmo_conteudo(base, destino):
    alvo = copias.copiar(base, destino)
    estado = copias.verificar(alvo)
    assert estado.ok, estado.detalhe
    assert (estado.sessoes, estado.mensagens, estado.versao) == (1, 2, VERSAO)


def test_a_copia_le_o_que_o_wal_ainda_nao_fechou(base, destino):
    """**A decisão 1**, e é a razão de isto não ser um `cp`.

    A base está em WAL, logo há estado comprometido que vive no
    `sessoes.db-wal` e não no `sessoes.db`. Com uma ligação **aberta** a
    escrever, o `Connection.backup` tem de ver a transacção confirmada; um `cp`
    do ficheiro principal veria uma base mais antiga.
    """
    vivo = sqlite3.connect(base)
    try:
        vivo.execute("PRAGMA journal_mode = WAL")
        with vivo:
            vivo.execute(
                "INSERT INTO sessao (id, criada_em, voz_inicial, "
                "idioma_inicial, modelo, rerank_ligado, auto_ligado) "
                "VALUES ('nova', 'agora', 'reis', 'pt', 'duplo', 0, 0)")
        alvo = copias.copiar(base, destino)
    finally:
        vivo.close()
    assert copias.verificar(alvo).sessoes == 2, (
        "a cópia não viu a sessão que o WAL ainda tinha por fechar")


def test_sem_base_a_copia_recusa_e_di_lo(tmp_path, destino):
    with pytest.raises(ErroDeCopia) as e:
        copias.copiar(str(tmp_path / "nao-existe.db"), destino)
    assert "nada a copiar" in str(e.value)


def test_uma_copia_que_nao_passa_a_verificacao_nao_fica(base, destino,
                                                        monkeypatch):
    """**A decisão 2**: primeiro `.parcial`, verificar, e só depois o nome.

    Escrever com o nome final e verificar depois substituía a última cópia boa
    por uma má — o pior resultado possível de um programa cujo trabalho é não
    perder dados. Mede-se com a verificação forçada a falhar.
    """
    boa = copias.copiar(base, destino)
    monkeypatch.setattr(copias, "verificar",
                        lambda _: Estado(False, "fingida"))
    with pytest.raises(ErroDeCopia) as e:
        copias.copiar(base, destino)
    assert "as cópias anteriores ficam como estavam" in str(e.value)
    assert copias.listar(destino) == [boa]
    assert list(destino.glob("*.parcial")) == [], "ficou um parcial para trás"


def test_os_nomes_ordenam_como_o_tempo(base, destino):
    """O `ultima()` ordena por **nome**, não por `mtime`.

    Um `cp -p`, um restauro ou um `touch` mexem no `mtime` e não mexem no nome.
    Escrevem-se três cópias fora de ordem cronológica de escrita, e a mais
    recente tem de ser a do instante maior.
    """
    # Só cópias com instante escolhido: uma cópia real levava o instante de
    # **hoje** e seria sempre a mais recente, o que não media ordem nenhuma.
    _copia_falsa(destino, "20261024T000000Z", base)
    _copia_falsa(destino, "20261026T000000Z", base)
    _copia_falsa(destino, "20261025T000000Z", base)
    assert copias.ultima(destino).name == f"{copias.PREFIXO}20261026T000000Z.db"
    assert [c.name for c in copias.listar(destino)] == [
        f"{copias.PREFIXO}2026102{d}T000000Z.db" for d in (4, 5, 6)]


# --- 2. rodar -------------------------------------------------------------- #

def test_guarda_as_ultimas_e_apaga_as_mais_antigas(base, destino):
    uma = copias.copiar(base, destino)
    antigas = [_copia_falsa(destino, f"2026102{i}T000000Z", uma)
               for i in range(1, 6)]
    copias.copiar(base, destino, a_guardar=3)
    ficaram = copias.listar(destino)
    assert len(ficaram) == 3
    assert antigas[0] not in ficaram and antigas[1] not in ficaram


def test_nunca_fica_sem_nenhuma_copia(base, destino):
    """Mesmo com `a_guardar=0`: um programa de cópias que pode ficar sem
    nenhuma por causa de um argumento mal posto não é um programa de cópias."""
    copias.copiar(base, destino, a_guardar=0)
    assert len(copias.listar(destino)) == 1
    copias.copiar(base, destino, a_guardar=0)
    assert len(copias.listar(destino)) == 1


# --- 3. verificar ---------------------------------------------------------- #

def test_verificar_recusa_um_ficheiro_vazio(tmp_path):
    vazio = tmp_path / "vazio.db"
    vazio.touch()
    assert copias.verificar(vazio).ok is False
    assert "vazio" in copias.verificar(vazio).detalhe


def test_verificar_recusa_um_ficheiro_que_nao_e_sqlite(tmp_path):
    lixo = tmp_path / "lixo.db"
    lixo.write_text("não sou uma base de dados")
    assert copias.verificar(lixo).ok is False


def test_verificar_recusa_um_sqlite_sem_o_esquema_das_sessoes(tmp_path):
    """Acontece com um restauro do ficheiro errado, e abre sem queixa."""
    outro = tmp_path / "outro.db"
    with sqlite3.connect(outro) as c:
        c.execute("CREATE TABLE qualquer (x INTEGER)")
    estado = copias.verificar(outro)
    assert estado.ok is False
    assert "esquema das sessões" in estado.detalhe


def test_verificar_recusa_outra_versao_de_esquema(base, destino):
    alvo = copias.copiar(base, destino)
    with sqlite3.connect(alvo) as c:
        c.execute("UPDATE esquema_versao SET versao = 99")
    estado = copias.verificar(alvo)
    assert estado.ok is False
    assert "99" in estado.detalhe


def test_verificar_recusa_um_ficheiro_truncado(base, destino):
    """Tamanho plausível, e `integrity_check` a dizer que não.

    É o caso que distingue verificar de olhar para o tamanho — e o que um `cp`
    a meio de uma escrita produz.
    """
    alvo = copias.copiar(base, destino)
    bruto = alvo.read_bytes()
    alvo.write_bytes(bruto[:len(bruto) // 2])
    assert copias.verificar(alvo).ok is False


# --- 4. restaurar ---------------------------------------------------------- #

def test_restaurar_recusa_uma_copia_ma_sem_tocar_na_base(base, tmp_path):
    """**A decisão 4**: verificar antes, nunca depois.

    A asserção é sobre os **bytes** da base, não sobre a excepção: um restauro
    que levanta depois de ter mexido no original não é melhor que um que não
    levanta.
    """
    antes = open(base, "rb").read()
    ma = tmp_path / "ma.db"
    ma.write_text("não sou uma base")
    with pytest.raises(ErroDeCopia):
        copias.restaurar(ma, base)
    assert open(base, "rb").read() == antes
    assert not (tmp_path / "base" / "sessoes.db.substituido").exists()


def test_restaurar_guarda_a_base_anterior(base, destino):
    alvo = copias.copiar(base, destino)
    a = Arquivo(base)
    a.criar_sessao(voz="reis", idioma="pt", modelo="duplo", rerank=False,
                   auto=False)
    assert len(a.listar_sessoes()) == 2
    copias.restaurar(alvo, base)
    assert len(Arquivo(base).listar_sessoes()) == 1, "a cópia não entrou"
    anterior = str(base) + ".substituido"
    assert copias.verificar(anterior).sessoes == 2, (
        "a base anterior não ficou guardada, e um restauro do ficheiro errado "
        "deixava de ter volta")


def test_restaurar_apaga_os_sidecars_do_wal(base, destino):
    """Um WAL antigo ao lado de uma base nova é a mistura de dois estados.

    A asserção é sobre o **conteúdo** e não sobre a ausência do ficheiro: o
    SQLite cria um `-wal` e um `-shm` novos assim que alguém abre a base
    restaurada, e exigir que não existam era medir o passo seguinte em vez
    deste. O que não pode sobreviver são os **bytes antigos**.
    """
    alvo = copias.copiar(base, destino)
    for lado in ("-wal", "-shm"):
        Path(str(base) + lado).write_bytes(b"velho")
    copias.restaurar(alvo, base)
    for lado in ("-wal", "-shm"):
        p = Path(str(base) + lado)
        assert not p.exists() or b"velho" not in p.read_bytes(), (
            f"o {lado} do original sobreviveu ao restauro")


def test_restaurar_nao_consome_a_copia(base, destino):
    """Uma cópia continua a ser cópia depois de servir: sem isto, a segunda
    tentativa de restauro já não tem rede."""
    alvo = copias.copiar(base, destino)
    copias.restaurar(alvo, base)
    assert copias.verificar(alvo).ok is True


# --- 5. o portão ----------------------------------------------------------- #

def test_d8_a_copia_restaura_num_directorio_limpo(base, destino, tmp_path):
    """**O portão D8**, no enunciado em que ele está escrito.

    «Restauro num directório limpo e as sessões de antes a aparecerem» — logo o
    destino é um sítio onde não há base nenhuma, nem `-wal`, nem pasta. É o caso
    de um disco novo, que é aquele para que uma cópia existe.

    E a asserção é sobre o **conteúdo**, não sobre a existência do ficheiro: as
    sessões, as mensagens pela ordem, e o texto da pergunta que alguém fez.
    """
    antes = Arquivo(base).listar_sessoes()
    assert antes and antes[0]["primeira_pergunta"] == "o que é a natureza?"
    alvo = copias.copiar(base, destino)

    limpo = tmp_path / "disco-novo" / "data" / "sessoes.db"
    assert not limpo.parent.exists(), "o directório não estava limpo"
    estado = copias.restaurar(alvo, str(limpo))

    assert estado.ok, estado.detalhe
    depois = Arquivo(str(limpo)).listar_sessoes()
    assert len(depois) == len(antes)
    assert depois[0]["primeira_pergunta"] == "o que é a natureza?"
    sessao = Arquivo(str(limpo)).ler_sessao(depois[0]["id"])
    assert [m["papel"] for m in sessao["mensagens"]] == ["utilizador", "bot"]
    assert sessao["mensagens"][0]["texto"] == "o que é a natureza?"


def test_d8_morde_se_a_copia_estiver_vazia(base, destino, tmp_path):
    """**O instrumento.** Uma base restaurada sem as sessões tem de reprovar.

    Sem isto, o teste acima podia estar verde por comparar um zero com um zero.
    Restaura-se uma cópia de uma base **vazia** e exige-se que a contagem não
    bata com a de antes — é o que o portão afirma, e é o que falharia se o
    `restaurar` escrevesse um ficheiro válido e sem conteúdo.
    """
    vazia = Arquivo(str(tmp_path / "vazia" / "sessoes.db"))
    vazia.preparar()
    copia_vazia = copias.copiar(vazia.caminho, destino)
    limpo = tmp_path / "disco-novo" / "sessoes.db"
    estado = copias.restaurar(copia_vazia, str(limpo))
    assert estado.ok, "uma base vazia é válida: o que não é é suficiente"
    assert estado.sessoes == 0
    assert len(Arquivo(base).listar_sessoes()) == 1
    assert estado.sessoes != len(Arquivo(base).listar_sessoes()), (
        "o instrumento do D8 não distingue uma cópia com sessões de uma vazia")


# --- 6. as unidades -------------------------------------------------------- #
#
# Contrato próprio, e é por isso que estão num dicionário próprio: o
# `test_unidades.py` varre os `GERADORES` a exigir `Type=exec` e
# `WantedBy=default.target`, que é o que o portão D2 afirma dos **serviços de
# arranque**. Uma `oneshot` disparada por temporizador cumpre o contrário dos
# dois, e afrouxar o D2 para a acomodar era trocar um portão por comodidade.

def _ini(texto: str) -> configparser.ConfigParser:
    c = configparser.ConfigParser()
    c.optionxform = str
    c.read_string(texto)
    return c


@pytest.fixture
def alvo(tmp_path):
    """Um alvo cujo `python` existe: o `systemd-analyze` lê o `ExecStart`."""
    checkout = tmp_path / "servico"
    (checkout / ".venv" / "bin").mkdir(parents=True)
    py = checkout / ".venv" / "bin" / "python"
    py.write_text("#!/bin/sh\n")
    py.chmod(0o755)
    for nome in ("ollama", "cloudflared"):
        b = tmp_path / nome
        b.write_text("#!/bin/sh\n")
        b.chmod(0o755)
    return Alvo(checkout=checkout, python=py, ollama=tmp_path / "ollama",
                cloudflared=tmp_path / "cloudflared")


def test_a_copia_e_oneshot_e_nao_fica_a_correr(alvo):
    s = _ini(copia_das_sessoes(alvo))["Service"]
    assert s["Type"] == "oneshot"
    assert "Restart" not in s, (
        "uma cópia que se reinicia em falha copia em ciclo; quem decide a "
        "cadência é o temporizador")


def test_o_execstart_da_copia_e_absoluto_e_nao_depende_do_path(alvo):
    """A lição da Fase 0 outra vez: o `PATH` de uma unidade não é o do dono."""
    exec_start = _ini(copia_das_sessoes(alvo))["Service"]["ExecStart"]
    assert exec_start.split()[0] == str(alvo.python)
    assert exec_start.endswith("-m src.web.instalar --copiar")


def test_a_copia_nao_entra_no_default_target(alvo):
    """Entrar ali fazia a cópia correr a cada arranque **e** por temporizador,
    e um `oneshot` em `default.target` atrasa o arranque de quem espera por
    ele."""
    assert "Install" not in _ini(copia_das_sessoes(alvo))


def test_o_temporizador_da_copia_e_diario_e_recupera_o_que_faltou(alvo):
    """`Persistent=true`, ao contrário do temporizador da guarda.

    A razão do outro é a rede: a passagem «que faltou» corre no instante em que
    a máquina acorda, e uma guarda que pergunta a um URL sem rede não serve. Uma
    cópia lê um ficheiro local — a passagem que faltou é a que interessa.
    """
    t = _ini(temporizador_da_copia(alvo))
    assert t["Timer"]["OnUnitActiveSec"] == "1d"
    assert t["Timer"]["Persistent"] == "true"
    assert t["Timer"]["Unit"] == NOME_COPIA
    assert t["Install"]["WantedBy"] == "timers.target", (
        "sem isto o `linger` não o apanha e o temporizador corre hoje e não "
        "volta amanhã"
    )


def test_a_guarda_do_tunel_continua_sem_persistent(alvo):
    """O contraste, fixado: se alguém «harmonizar» os dois temporizadores,
    isto falha e manda ler as duas razões."""
    assert "Persistent" not in _ini(temporizador_da_guarda(alvo))["Timer"]


@pytest.mark.skipif(shutil.which("systemd-analyze") is None,
                    reason="sem systemd-analyze nesta máquina")
def test_o_systemd_aceita_a_copia_e_o_temporizador(alvo, tmp_path):
    """Um `configparser` diz que é um INI; só o systemd diz que é uma unidade."""
    d = tmp_path / "u"
    escrever(alvo, d, convidados=None)
    for nome in (NOME_COPIA, NOME_TEMPORIZADOR_COPIA):
        r = subprocess.run(("systemd-analyze", "--user", "verify",
                            str(d / nome)), capture_output=True, text=True)
        meus = [ln for ln in r.stderr.splitlines() if ln.startswith(nome)]
        assert not meus, meus
