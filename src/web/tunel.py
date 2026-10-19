"""O túnel como indirecção nomeada: parar e arrancar uma unidade que **ainda
não existe nesta máquina**.

Passo 5 do [`PRODUCAO.md`](../../docs/PRODUCAO.md), portão **D3**. O passo 7 da
Fase 6 entregou um guarda de **pedido** — com o sentinela presente,
`POST /api/perguntar` devolve 409. O §3.2 (c) desse plano diz que para o
público essa é a resposta errada, e com números desta casa: o índice são
**383 s**, a Fase 5Z são ~30 min só de geração, e o enriquecimento que a Fase 4
vetou estava orçamentado em **3,2 a 7,5 horas**. Um serviço público que devolve
409 durante sete horas, nomeando «a fase e o PID» a quem perguntou por que é
que o fim do dia é melancólico, não está a ser honesto: está avariado com uma
mensagem interna. E o §3.2 (a) é pior — um pedido que chega na pausa de 60 s da
Fase 0 §3.2 **não gera nada e aquece o chip**, e o *throttling* desta máquina
foi medido até **101 °C**, pelo que a queda monotónica de tok/s passa a ter
duas causas indistinguíveis: o chip, ou um estranho.

O remédio é o **túnel cair**. O visitante recebe a página de erro do fornecedor
do túnel, que é a verdade («isto está fora de serviço»), e não consome CPU
desta máquina.

## Porque é que isto é uma indirecção, e não um `systemctl stop` em linha

**Não há túnel instalado nesta máquina** — verificado, nem `cloudflared` nem
`tailscale`, e o `PRODUCAO.md` §5.1 regista-o como «a única dependência nova
que a saída D traz». Logo o código que para o túnel tem de ser escrito **antes
de haver o que parar**, e a pergunta de desenho é como.

Chamar `systemctl --user stop` em linha dentro do `medicao()` punha o
mecanismo inteiro fora de alcance de um teste: ou os testes mexiam nas unidades
reais desta máquina (inaceitável — é o mesmo dano que o cabeçalho do
`test_sentinela.py` recusa quanto ao ficheiro), ou não verificavam nada. Daí o
`medicao()` receber um **objecto** que cumpre o `Tunel` abaixo: há uma
implementação real (`TunelSystemd`) e um duplo nos testes. Quando a unidade for
instalada — passo 4 do mesmo plano — o trabalho é **nomeá-la**, e não reescrever
este código.

## `TunelAusente` não é um remendo: é o estado desta máquina, declarado

A ausência tem de ser **explícita e sem variável**, e não um nome de unidade mal
escrito. A diferença importa porque o modo de falha desta casa é conhecido:
«não dá erro: dá respostas erradas» (o manifesto do índice, e a correcção 39 do
`CONTROLO.md` §4 sobre o caminho relativo do sentinela). Portanto:

- sem `PESSOABOT_TUNEL` definida → `TunelAusente`, que não faz nada e **diz**
  que não faz nada. É o que hoje é verdade, e uma fase corre;
- com `PESSOABOT_TUNEL` definida → `TunelSystemd`, que **verifica que a unidade
  é conhecida** (`LoadState`) antes de a parar. Um `systemctl --user stop` de
  uma unidade inexistente devolve **0** em systemd — logo, sem essa
  verificação, uma variável mal escrita dava «túnel parado» com o URL de pé.
  É o mecanismo silenciosamente desligado outra vez, e aqui com o público do
  outro lado.

## O que acontece quando **parar** falha: a fase recusa arrancar

Decisão deliberada, e o §2.4 da Fase 6 **não** a responde. Aquele sentido único
— «o servidor é que cede à medição, nunca o contrário» — fala de quem cede
entre o servidor e a fase. Aqui quem pode ceder é a **medição**, e deixar uma
fase correr com o túnel de pé é precisamente o que invalida os dados que ela
vai produzir.

A assimetria dos custos decide, e é a mesma aritmética do §3.2 (b):

- uma fase que **não arranca** custa o tempo de ler a mensagem e correr um
  comando. Repete-se;
- uma fase que arranca com o túnel de pé custa, no pior caso, as **3,2 a 7,5
  horas** do orçamento do enriquecimento — e o custo não é o tempo, é que *não
  se descobre depois*: dentro de seis meses, lendo um `01-cru.jsonl`, não há
  como saber se uma célula lenta foi térmica ou foi tráfego. É a forma exacta
  das **4 horas que o cache de KV invalidou** (correcção registada no
  `CONTROLO.md` §4, com o prefill absurdo de 25 625 tok/s): uma variável não
  controlada no instrumento, descoberta tarde.

Logo `parar()` levanta `TunelIndisponivel`, o `medicao()` **retira o sentinela
que já tinha escrito** e a fase não começa.

E a direcção inversa é deliberadamente **assimétrica**: quando **arrancar**
falha, no fim, a fase já correu e os dados são bons. Levantar ali trocava um
resultado válido por uma excepção — e pior, podia tapar a excepção do corpo da
fase. O túnel em baixo é, além disso, a direcção segura e **auto-anunciada**: o
URL responde com a página do fornecedor, o `/api/estado` continua a servir o
dono em local, e o remédio é um comando. Portanto não levanta: avisa, com o
nome da unidade e o comando.
"""
from __future__ import annotations

import os
import subprocess
import warnings
from typing import Protocol, runtime_checkable

#: A unidade do túnel, por nome. **Ausente é o estado desta máquina**, e é por
#: isso que não há valor por omissão: ver a secção do cabeçalho.
VARIAVEL = "PESSOABOT_TUNEL"

#: Generoso de propósito. Um `systemctl --user stop` de um `cloudflared` a
#: fechar ligações pode levar segundos, e o portão **D3** dá ao URL **10 s**
#: para deixar de responder — logo o orçamento é desse lado, não deste.
TIMEOUT_S = 15.0


class TunelIndisponivel(RuntimeError):
    """Parar ou arrancar o túnel falhou.

    A levantar isto no **parar**, a fase não arranca (cabeçalho). No
    **arrancar**, o `medicao()` apanha-a e avisa: a fase já correu.
    """


@runtime_checkable
class Tunel(Protocol):
    """O que o `medicao()` precisa de saber sobre um túnel: pará-lo e arrancá-lo.

    `Protocol` e não classe base porque o duplo dos testes não deve ter de
    herdar nada para ser aceite, e porque a implementação real — um
    `systemctl` — não partilha código nenhum com ele.
    """

    #: Para a mensagem de erro e para o aviso. Com dois checkouts e duas
    #: unidades na mesma máquina, «o túnel» não diz qual.
    nome: str

    def parar(self) -> None:
        """Deixa o URL de deixar de responder. Levanta `TunelIndisponivel`."""

    def arrancar(self) -> None:
        """Devolve o URL. Levanta `TunelIndisponivel`."""


class TunelAusente:
    """Não há túnel. **O estado desta máquina em 2026-10-18**, declarado.

    Não faz nada, e é essa a resposta certa: sem `PESSOABOT_TUNEL` não há URL
    público, logo não há alcance a fechar, e uma fase tem de poder correr. O
    que isto **não** é: o caso de uma unidade mal nomeada. Essa é
    `TunelSystemd` e falha (cabeçalho).
    """

    nome = "nenhum (PESSOABOT_TUNEL não está definida)"

    def parar(self) -> None:
        return None

    def arrancar(self) -> None:
        return None


class TunelSystemd:
    """Uma unidade de utilizador: `systemctl --user stop|start <unidade>`.

    `--user` e não de sistema pela razão do `PRODUCAO.md` §5.1: a Fase 0
    instalou o Ollama «em espaço de utilizador a partir do tarball oficial, sem
    `sudo`», e «continua a não haver razão para alterar o sistema». Uma unidade
    de sistema pedia `sudo` dentro de uma fase de medição.
    """

    def __init__(self, unidade: str) -> None:
        self.nome = unidade

    def _systemctl(self, *args: str) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(["systemctl", "--user", *args],
                                  capture_output=True, text=True,
                                  timeout=TIMEOUT_S, check=False)
        except FileNotFoundError as e:  # não há systemd nesta sessão
            raise TunelIndisponivel(
                f"não há `systemctl` nesta máquina, e {self.nome} está "
                f"configurada em {VARIAVEL}") from e
        except subprocess.SubprocessError as e:
            raise TunelIndisponivel(
                f"`systemctl --user {' '.join(args)}` não respondeu em "
                f"{TIMEOUT_S:.0f} s") from e

    def _exigir_conhecida(self) -> None:
        """A unidade existe?

        Esta pergunta é o coração da secção «não é um remendo» do cabeçalho:
        `systemctl --user stop` de uma unidade **inexistente** devolve 0.
        Sem esta verificação, uma variável mal escrita dava «túnel parado» com
        o URL de pé — e o público do outro lado a aquecer o chip.
        """
        r = self._systemctl("show", "-p", "LoadState", "--value", self.nome)
        estado = r.stdout.strip()
        if estado != "loaded":
            raise TunelIndisponivel(
                f"a unidade {self.nome} não está instalada nesta máquina "
                f"(LoadState={estado or 'desconhecido'!s}); "
                f"{VARIAVEL} nomeia uma unidade que não existe")

    def parar(self) -> None:
        self._exigir_conhecida()
        r = self._systemctl("stop", self.nome)
        if r.returncode != 0:
            raise TunelIndisponivel(
                f"`systemctl --user stop {self.nome}` devolveu "
                f"{r.returncode}: {r.stderr.strip() or 'sem mensagem'}")

    def arrancar(self) -> None:
        self._exigir_conhecida()
        r = self._systemctl("start", self.nome)
        if r.returncode != 0:
            raise TunelIndisponivel(
                f"`systemctl --user start {self.nome}` devolveu "
                f"{r.returncode}: {r.stderr.strip() or 'sem mensagem'}")


def desta_maquina() -> Tunel:
    """O túnel desta máquina, lido **a cada chamada** e não à importação.

    A cada chamada pela razão que o `sentinela.caminho()` já dá: uma constante
    fixada na importação tornava a variável inútil num processo de vida longa,
    e impedia um teste de a definir.
    """
    unidade = (os.environ.get(VARIAVEL) or "").strip()
    return TunelSystemd(unidade) if unidade else TunelAusente()


def avisar_que_nao_voltou(tunel: Tunel, erro: Exception) -> None:
    """O túnel não voltou, e a fase já correu. Avisa em vez de levantar.

    Separado em função própria para o teste poder apanhá-lo: um aviso que
    ninguém verifica é a mesma coisa que não avisar.
    """
    warnings.warn(
        f"a medição terminou e o túnel {tunel.nome} NÃO voltou: {erro}. "
        f"O URL está em baixo — o servidor local continua a responder. "
        f"Remédio: systemctl --user start {tunel.nome}",
        RuntimeWarning, stacklevel=3)
