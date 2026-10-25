"""A persistência das sessões. Passo 8 da Fase 6, portão **I6**.

O esquema está em [`esquema.sql`](esquema.sql) e as entidades no §3.2 do
[plano](../../docs/FASE-6.md). Aqui estão as decisões que o plano deixou
abertas, e são cinco.

## 1. Guarda-se o que **foi ao fio**, já redigido — e não o `Turno` do domínio

`registar_turno` recebe o `dict` que o `serial.turno` produziu **depois** de
passar pelo `redigir` do [`retencao.py`](retencao.py). Não recebe o `Turno`.

A razão é o portão **I6** («a base não contém corpos de poemas») e o facto
desagradável que o portão **I7′** descobriu: numa cópia **à letra**, o verso
gerado **é** o verso de Pessoa. Partindo do fio, **o I6 herda o I7′** — o que a
base contém é um subconjunto do que o cliente já recebeu — e não há uma segunda
cópia da retenção a divergir em silêncio no dia em que uma delas mudar.

⚠️ **E o que protege a tentativa plagiada não é isto.** Medido ao escrever o
`tests/test_i6.py`: numa geração que copia à letra, o verso copiado vive no
`historico[0].texto` — **6 linhas de corpo** —, e o texto final é limpo porque
o `_repetir_sem` tirou os poemas do contexto antes da 2.ª tentativa. O que põe
aquelas 6 linhas fora do alcance do portão é o §3.2 do plano **não ter dado
coluna de texto à `tentativa_reg`**: não há o que redigir no que não se guarda,
que é a protecção mais forte que há. Há um teste a fixá-la, para a coluna não
voltar numa linha de SQL distraída.

Gravar o publicado continua a ser a decisão certa — protege o `mensagem.texto`
no caso em que as tentativas se esgotam e a última ainda copia —, mas é a
segunda linha de defesa e não a primeira. Dizê-lo ao contrário era atribuir a
este módulo um mérito que é do esquema.

## 2. Uma ligação por operação, e não uma partilhada

O servidor grava de dentro de `asyncio.to_thread`, logo de **threads
diferentes**, e uma ligação `sqlite3` não atravessa threads sem
`check_same_thread=False` — que resolve o erro e deixa a corrida. A alternativa
honesta a um trinco nosso é não partilhar: abrir, escrever, fechar. Para uma
base local de seis tabelas isso custa microssegundos, e o WAL deixa os leitores
(o `GET /api/sessoes`) entrar enquanto o escritor escreve.

## 3. `PRAGMA foreign_keys` é de ligação, não de ficheiro

É a armadilha desta biblioteca: escrito no `esquema.sql` aplicava-se à ligação
que correu o guião e a mais nenhuma, e as chaves estrangeiras ficavam
**declaradas e desligadas** — exactamente a classe de defeito do sentinela com
o caminho relativo, que ficava «silenciosamente desligado». Liga-se em cada
`abrir`, e há teste que o confirma pela ligação e não pelo ficheiro.

## 4. O caminho é relativo ao checkout, **ao contrário do sentinela**

O sentinela é absoluto e único na máquina porque é um encontro entre dois
processos em checkouts diferentes: com `data/` relativo havia dois e o mecanismo
desligava-se. Aqui a assimetria é ao contrário e é deliberada — o §5.3 do
[`PRODUCAO.md`](../../docs/PRODUCAO.md) diz que `data/sessoes.db` vive no
checkout **do serviço** e não no de trabalho. São dados **daquele** serviço, e
um ficheiro único na máquina fazia o checkout de trabalho escrever nas sessões
do público. `PESSOABOT_SESSOES` sobrepõe-se, e é o que os testes usam.

## 5. Falhar a gravar **não** mata a geração

Uma resposta de 30 s perdida porque o disco está cheio é um defeito pior do que
não ter histórico. Então quem chama protege-se e a falha fica **à vista** no
sítio onde esta casa põe as avarias: um componente do `GET /api/estado`, com o
remédio ao lado, como o Ollama em baixo (portão I3). O que não se faz é engolir
a excepção em silêncio — `ultima_falha` existe para isso, e o componente lê-a.
"""
from __future__ import annotations

import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .saude import RAIZ

#: A versão do esquema que este módulo sabe ler. Sobe quando `esquema.sql`
#: muda de forma incompatível, e aí entra um ficheiro por versão (§3.4).
VERSAO = 1

ESQUEMA = Path(__file__).resolve().parent / "esquema.sql"

#: Onde vive, por omissão. Ver a decisão 4.
#:
#: ⚠️ Lê-se **na construção** do `Arquivo` e não na importação do módulo, e
#: isso não é estilo: uma constante resolvida à importação fazia
#: `PESSOABOT_SESSOES` ser lido uma vez, antes de qualquer `fixture` o poder
#: pôr — e a suíte escrevia **180 KB no `data/sessoes.db` real** do checkout de
#: trabalho. Aconteceu, uma vez, e é o que o `tests/conftest.py` passou a
#: impedir.
def caminho_padrao() -> str:
    return os.environ.get("PESSOABOT_SESSOES") or str(RAIZ / "data" / "sessoes.db")


#: Mantido por compatibilidade de leitura: é o valor **à importação**, e quem
#: quer o de agora chama `caminho_padrao()`.
CAMINHO = caminho_padrao()


class ErroDeEsquema(RuntimeError):
    """A base existe e não é desta versão do esquema.

    Levanta em vez de migrar às cegas: o manifesto do índice ensinou a lição —
    «um índice velho carregado por engano não dá erro: dá respostas erradas».
    """


def agora() -> str:
    """Instante em ISO-8601, UTC, com fuso explícito.

    UTC e não hora local: a §7.4 do [`PRODUCAO.md`](../../docs/PRODUCAO.md)
    registra um portão que passou por eu ter comparado um carimbo em UTC com um
    `journalctl` em hora local. Um carimbo sem fuso é o mesmo defeito à espera.

    **Microssegundos, e isso é uma correcção.** Isto esteve escrito com
    `timespec="seconds"` e o `listar_sessoes` ordena por `criada_em`: duas
    conversas abertas no mesmo segundo ficavam com o **mesmo** carimbo, e o
    desempate era o `id` — um uuid, logo uma ordem ao acaso numa lista que
    alguém lê para reabrir a de ontem. Apanhado pelo teste da ordenação, que
    abre duas sessões seguidas; a resolução do segundo era boa de ler e
    insuficiente para o único uso que este campo tem.
    """
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def abrir(caminho: str | None = None) -> sqlite3.Connection:
    """Abre (criando se preciso), liga os pragmas e garante o esquema."""
    caminho = caminho or caminho_padrao()
    pai = Path(caminho).parent
    if caminho != ":memory:":
        pai.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(caminho)
    c.row_factory = sqlite3.Row
    # Ver a decisão 3: este é de ligação. O WAL é de ficheiro, e repeti-lo é de
    # graça; em `:memory:` o `journal_mode` não vai a WAL e não faz falta.
    c.execute("PRAGMA foreign_keys = ON")
    c.execute("PRAGMA journal_mode = WAL")
    with c:
        c.executescript(ESQUEMA.read_text(encoding="utf-8"))
        linha = c.execute("SELECT versao FROM esquema_versao").fetchone()
        if linha is None:
            c.execute("INSERT INTO esquema_versao (versao) VALUES (?)", (VERSAO,))
            versao = VERSAO
        else:
            versao = linha["versao"]
    # Fora do `with`, e isso é uma correcção e não arrumação: fechar a ligação
    # **dentro** dele fazia o `__exit__` tentar confirmar a transacção numa
    # base já fechada, e o `sqlite3.ProgrammingError` disso tapava este
    # `ErroDeEsquema`. Apanhado pelo teste da versão errada, que esperava a
    # excepção certa e recebia a outra.
    if versao != VERSAO:
        c.close()
        raise ErroDeEsquema(
            f"{caminho} tem esquema versão {versao} e este código lê a {VERSAO}")
    return c


def _bool(x: Any) -> int:
    return 1 if x else 0


class Arquivo:
    """As sessões em disco. Uma instância por serviço; sem estado por ligação."""

    def __init__(self, caminho: str | None = None):
        self.caminho = caminho or caminho_padrao()
        #: A última excepção ao gravar, como texto, ou `None`. Lê-a o
        #: componente do `/api/estado`: ver a decisão 5.
        self.ultima_falha: str | None = None

    @contextmanager
    def _ligar(self):
        """Abre, dá a ligação dentro de uma transacção, e **fecha**.

        O `with` de uma `sqlite3.Connection` confirma ou desfaz a transacção e
        **não fecha a ligação** — é o engano fácil desta biblioteca, e deixava
        um descritor por operação até o processo morrer. Daí o `finally`.
        """
        c = abrir(self.caminho)
        try:
            with c:
                yield c
        finally:
            c.close()

    def preparar(self) -> None:
        """Cria o ficheiro e o esquema. Chamar no arranque, para a avaria
        aparecer antes da primeira pergunta e não a meio dela."""
        abrir(self.caminho).close()

    # ---- escrita -----------------------------------------------------------

    def criar_sessao(self, *, voz: str, idioma: str, modelo: str,
                     rerank: bool, auto: bool) -> str:
        """Abre uma sessão e devolve o `id` (uuid4 em hexadecimal)."""
        sid = uuid.uuid4().hex
        with self._ligar() as c:
            c.execute(
                "INSERT INTO sessao (id, criada_em, voz_inicial, "
                "idioma_inicial, modelo, rerank_ligado, auto_ligado) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (sid, agora(), voz, idioma, modelo, _bool(rerank), _bool(auto)))
        return sid

    def _proxima_ordem(self, c: sqlite3.Connection, sessao_id: str) -> int:
        linha = c.execute(
            "SELECT COALESCE(MAX(ordem), -1) + 1 AS n FROM mensagem "
            "WHERE sessao_id = ?", (sessao_id,)).fetchone()
        return int(linha["n"])

    def existe(self, sessao_id: str) -> bool:
        """A sessão existe? É o que separa «reabrir» de «abrir outra».

        Sem isto, um `sessao_id` que o cliente guardou de uma base apagada
        fazia o `INSERT` da mensagem falhar na chave estrangeira — e a falha
        aparecia como «não foi possível gravar» em vez de «essa conversa já não
        existe, abri outra».
        """
        with self._ligar() as c:
            return c.execute("SELECT 1 FROM sessao WHERE id = ?",
                             (sessao_id,)).fetchone() is not None

    def registar_mensagem(self, sessao_id: str, papel: str, texto: str) -> int:
        """Uma mensagem, e devolve o `id`. `papel` é o CHECK do esquema."""
        with self._ligar() as c:
            cur = c.execute(
                "INSERT INTO mensagem (sessao_id, ordem, papel, texto, "
                "criada_em) VALUES (?, ?, ?, ?, ?)",
                (sessao_id, self._proxima_ordem(c, sessao_id), papel, texto,
                 agora()))
            return int(cur.lastrowid)

    def registar_turno(self, sessao_id: str, turno: dict[str, Any],
                       proposta: dict[str, Any] | None = None) -> int:
        """Grava um turno **já redigido** e devolve o `turno_reg.id`.

        `turno` é o `dict` que foi ao fio — ver a decisão 1. Uma transacção
        só: um turno meio gravado é pior que nenhum, porque a `tentativa_reg`
        sem o pai é precisamente o registo que a 5Y queria e não teria.
        """
        resposta, veredicto, plagio = (turno["resposta"], turno["veredicto"],
                                       turno["plagio"])
        with self._ligar() as c:
            cur = c.execute(
                "INSERT INTO mensagem (sessao_id, ordem, papel, texto, "
                "criada_em) VALUES (?, ?, 'bot', ?, ?)",
                (sessao_id, self._proxima_ordem(c, sessao_id), turno["texto"],
                 agora()))
            mensagem_id = int(cur.lastrowid)
            cur = c.execute(
                "INSERT INTO turno_reg (mensagem_id, voz, idioma, aprovado, "
                "tentativas, recuperacao_ms, rerank_ms, prefill_s, decode_s, "
                "prefill_tokens, decode_tokens, truncada, fracao_copiada, "
                "max_similaridade, motivos, suspeitas, gramatica) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (mensagem_id, turno["voz"], turno["idioma"],
                 _bool(turno["aprovado"]), turno["tentativas"],
                 turno["recuperacao_ms"], turno["rerank_ms"],
                 resposta["prefill_s"], resposta["decode_s"],
                 resposta["prefill_tokens"], resposta["decode_tokens"],
                 _bool(resposta["truncada"]), plagio["fracao_copiada"],
                 plagio["max_similaridade"],
                 json.dumps(veredicto["motivos"], ensure_ascii=False),
                 json.dumps(veredicto["suspeitas"], ensure_ascii=False),
                 json.dumps(veredicto["gramatica"], ensure_ascii=False)))
            turno_id = int(cur.lastrowid)
            for t in turno.get("historico", ()):
                c.execute(
                    "INSERT INTO tentativa_reg (turno_id, n, veredicto_ok, "
                    "plagiou, truncada, fracao_copiada, motivos) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (turno_id, t["n"], _bool(t["veredicto"]["ok"]),
                     _bool(t["plagio"]["plagiou"]),
                     _bool(t["resposta"]["truncada"]),
                     t["plagio"]["fracao_copiada"],
                     json.dumps(t["veredicto"]["motivos"], ensure_ascii=False)))
            for ordem, f in enumerate(turno.get("fontes", ())):
                c.execute(
                    "INSERT INTO fonte (turno_id, poem_id, chunk_ix, ordem, "
                    "papel) VALUES (?, ?, ?, ?, ?)",
                    (turno_id, f["poem_id"], f["chunk_ix"], ordem, f["papel"]))
            if proposta is not None:
                c.execute(
                    "INSERT INTO proposta_reg (turno_id, voz_proposta, "
                    "voz_usada, aceite, segundos) VALUES (?, ?, ?, ?, ?)",
                    (turno_id, proposta["voz"], turno["voz"],
                     # `None` quando o roteador **não decidiu**: ali um 0
                     # lia-se como «o utilizador recusou a proposta», e o §3.5
                     # avisa que estes dados vão ser lidos como rótulos. Uma
                     # proposta que não existiu não é um rótulo nenhum.
                     None if proposta["voz"] is None
                     else _bool(proposta["voz"] == turno["voz"]),
                     proposta["segundos"]))
        return turno_id

    # ---- leitura -----------------------------------------------------------

    def listar_sessoes(self, limite: int = 50) -> list[dict[str, Any]]:
        """As sessões, da mais recente para a mais antiga.

        Traz a **primeira pergunta** de cada uma porque é o que a interface
        desenha na lista: «criada_em» sozinho não distingue duas conversas.
        """
        with self._ligar() as c:
            linhas = c.execute(
                "SELECT s.*, "
                "  (SELECT COUNT(*) FROM mensagem m WHERE m.sessao_id = s.id) "
                "    AS n_mensagens, "
                "  (SELECT m.texto FROM mensagem m WHERE m.sessao_id = s.id "
                "     AND m.papel = 'utilizador' ORDER BY m.ordem LIMIT 1) "
                "    AS primeira_pergunta "
                "FROM sessao s ORDER BY s.criada_em DESC, s.id DESC LIMIT ?",
                (limite,)).fetchall()
        return [{
            "id": r["id"],
            "criada_em": r["criada_em"],
            "voz_inicial": r["voz_inicial"],
            "idioma_inicial": r["idioma_inicial"],
            "modelo": r["modelo"],
            "rerank_ligado": bool(r["rerank_ligado"]),
            "auto_ligado": bool(r["auto_ligado"]),
            "n_mensagens": r["n_mensagens"],
            "primeira_pergunta": r["primeira_pergunta"],
        } for r in linhas]

    def ler_sessao(self, sessao_id: str) -> dict[str, Any] | None:
        """Uma sessão com as mensagens pela ordem, ou `None` se não existir.

        É esta que torna «reabrir a conversa de ontem» possível, que é o
        entregável do passo 8 — uma lista de sessões que não se abrem não é
        histórico nenhum.
        """
        with self._ligar() as c:
            s = c.execute("SELECT * FROM sessao WHERE id = ?",
                          (sessao_id,)).fetchone()
            if s is None:
                return None
            msgs = c.execute(
                "SELECT m.*, t.id AS turno_id, t.voz, t.idioma, t.aprovado, "
                "       t.tentativas, t.recuperacao_ms, t.rerank_ms, "
                "       t.prefill_s, t.decode_s, t.truncada, "
                "       t.fracao_copiada, t.motivos, t.suspeitas, t.gramatica "
                "FROM mensagem m LEFT JOIN turno_reg t ON t.mensagem_id = m.id "
                "WHERE m.sessao_id = ? ORDER BY m.ordem", (sessao_id,)
            ).fetchall()
            fontes: dict[int, list[dict[str, Any]]] = {}
            for f in c.execute(
                    "SELECT f.* FROM fonte f JOIN turno_reg t ON t.id = f.turno_id "
                    "JOIN mensagem m ON m.id = t.mensagem_id "
                    "WHERE m.sessao_id = ? ORDER BY f.ordem", (sessao_id,)):
                fontes.setdefault(f["turno_id"], []).append(
                    {"poem_id": f["poem_id"], "chunk_ix": f["chunk_ix"],
                     "papel": f["papel"]})
        mensagens = []
        for m in msgs:
            item: dict[str, Any] = {"ordem": m["ordem"], "papel": m["papel"],
                                    "texto": m["texto"],
                                    "criada_em": m["criada_em"]}
            if m["turno_id"] is not None:
                item["turno"] = {
                    "voz": m["voz"], "idioma": m["idioma"],
                    "aprovado": bool(m["aprovado"]),
                    "tentativas": m["tentativas"],
                    "recuperacao_ms": m["recuperacao_ms"],
                    "rerank_ms": m["rerank_ms"],
                    "prefill_s": m["prefill_s"], "decode_s": m["decode_s"],
                    "truncada": bool(m["truncada"]),
                    "fracao_copiada": m["fracao_copiada"],
                    "motivos": json.loads(m["motivos"]),
                    "suspeitas": json.loads(m["suspeitas"]),
                    "gramatica": json.loads(m["gramatica"]),
                    "fontes": fontes.get(m["turno_id"], []),
                }
            mensagens.append(item)
        return {
            "id": s["id"], "criada_em": s["criada_em"],
            "voz_inicial": s["voz_inicial"],
            "idioma_inicial": s["idioma_inicial"],
            "modelo": s["modelo"],
            "rerank_ligado": bool(s["rerank_ligado"]),
            "auto_ligado": bool(s["auto_ligado"]),
            "mensagens": mensagens,
        }
