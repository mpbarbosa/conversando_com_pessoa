"""Interface de geração.

A geração está atrás de uma interface para manter a decisão local-vs-remoto
reversível. A Fase 0 concluiu que o local é viável, mas por pouco: se o
hardware mudar, ou se a qualidade medida no conjunto dourado não chegar, trocar
de backend deve ser uma linha de configuração e não uma reescrita.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Protocol, runtime_checkable


@dataclass(frozen=True)
class Resposta:
    """Texto gerado, com os tempos que o CLI mostra ao utilizador.

    Os tempos são separados de propósito: a Fase 0 mostrou que o prefill domina
    a espera (58–89% do total), e mostrá-los ensina ao utilizador o custo de
    cada pergunta.
    """
    texto: str
    prefill_s: float
    decode_s: float
    prefill_tokens: int
    decode_tokens: int
    #: `done_reason == "length"`: o modelo foi cortado pelo `num_predict`, não
    #: acabou. Observado no CLI: «e brota ao vento ímpetu» — cortado a meio.
    truncada: bool = False

    @property
    def total_s(self) -> float:
        return self.prefill_s + self.decode_s

    @property
    def decode_tps(self) -> float:
        return self.decode_tokens / self.decode_s if self.decode_s else 0.0

    def resumo(self) -> str:
        corte = " ✂ truncada" if self.truncada else ""
        return (f"{self.prefill_s:.1f}s prefill ({self.prefill_tokens} tok) · "
                f"{self.decode_s:.1f}s decode ({self.decode_tokens} tok, "
                f"{self.decode_tps:.1f} tok/s){corte}")


@runtime_checkable
class Generator(Protocol):
    @property
    def nome(self) -> str: ...

    @property
    def janela_contexto(self) -> int: ...

    def gerar(self, system: str, user: str, *, max_tokens: int = ...,
              temperatura: float | None = ...) -> Resposta:
        """Gera de uma vez. Usar só quando não há interface a mostrar o texto.

        `temperatura` sobrepõe-se à do backend. Existe para o roteador da Fase
        4, que precisa de determinismo onde o verso precisa de variedade.
        """
        ...

    def gerar_em_fluxo(self, system: str, user: str, *,
                       max_tokens: int = ...) -> Iterator[str | Resposta]:
        """Gera em fluxo: emite fragmentos de texto e, no fim, a `Resposta`.

        O último item do iterador **é** a `Resposta`, com os tempos. Quem
        consome distingue por tipo.
        """
        ...


class ErroDeGeracao(RuntimeError):
    """Falha ao gerar, com mensagem destinada ao utilizador e não ao stack."""
