"""Gerador local via Ollama.

Os parâmetros não são escolhas: vêm da Fase 0.

| parâmetro | valor | vem de |
|---|---|---|
| `num_thread` | 10 | varredura monotónica; os 2 LP-E a 2100 MHz ficam fora |
| `repeat_penalty` | 1,1 | sem ele o modelo degenerou em ciclo no prompt longo |
| `temperature` | 0,9 | usado nas amostras que pontuaram 7/10 às cegas |
| `top_p` | 0,9 | idem |
| `num_predict` | 150 | ~23 s de decode; 110 pouparia ~4–5 s (por medir) |

`repeat_penalty` a 1,1 é deliberadamente moderado: o estilo de Álvaro de Campos
**é** anafórico («Olho pró lado da barra, olho pró Indefinido, / Olho e
contenta-me ver»), e penalizar repetição combate o estilo-alvo. Valores altos
esterilizariam Campos.
"""
from __future__ import annotations

import json
from typing import Iterator

import requests

from .base import ErroDeGeracao, Resposta

URL_BASE = "http://127.0.0.1:11434"
MODELO = "qwen2.5:7b-instruct-q4_K_M"

NUM_THREAD = 10
REPEAT_PENALTY = 1.1
TEMPERATURE = 0.9
TOP_P = 0.9
#: Subido de 150 para 220: a 150 uma ode de Reis foi cortada a meio da palavra
#: («e brota ao vento ímpetu»). Custo medido: ~5,9 tok/s de decode, logo 70
#: tokens a mais são ~12 s. O orçamento tolera (ver 05-RELATORIO-ORCAMENTO.md),
#: e uma resposta cortada é pior que uma resposta lenta.
NUM_PREDICT = 220

#: Mantém o modelo e o cache de KV vivos entre perguntas. Sem isto a persona
#: voltaria a custar os 13,63 s de prefill a frio em cada pergunta.
KEEP_ALIVE = "30m"

TIMEOUT_S = 1800


class OllamaGenerator:
    def __init__(self, modelo: str = MODELO, url_base: str = URL_BASE,
                 num_thread: int = NUM_THREAD, timeout: int = TIMEOUT_S):
        self.modelo = modelo
        self.url_base = url_base.rstrip("/")
        self.num_thread = num_thread
        self.timeout = timeout

    @property
    def nome(self) -> str:
        return self.modelo

    @property
    def janela_contexto(self) -> int:
        """Janela que o Ollama reporta para o modelo carregado.

        Fixa em 4096: é o que o servidor reportou nos testes (`n_ctx_slot`).
        O orçamento de prompt é muito menor, logo isto nunca é o limite.
        """
        return 4096

    # --- plumbing -----------------------------------------------------------

    def _opcoes(self, max_tokens: int,
                temperatura: float | None = None) -> dict:
        """Opções de amostragem.

        `temperatura` existe por causa do roteador da Fase 4: um classificador
        tem de ser **determinista** — a mesma pergunta não pode dar vozes
        diferentes em duas sessões — e os 0,9 daqui foram medidos às cegas na
        Fase 0 para **verso**, que é o problema oposto.
        """
        t = TEMPERATURE if temperatura is None else temperatura
        return {
            "num_thread": self.num_thread,
            "num_predict": max_tokens,
            "temperature": t,
            "top_p": 1.0 if t == 0.0 else TOP_P,
            "repeat_penalty": REPEAT_PENALTY,
        }

    def _corpo(self, system: str, user: str, max_tokens: int, fluxo: bool,
               temperatura: float | None = None) -> dict:
        return {
            "model": self.modelo,
            "stream": fluxo,
            "keep_alive": KEEP_ALIVE,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "options": self._opcoes(max_tokens, temperatura),
        }

    @staticmethod
    def _resposta(texto: str, d: dict) -> Resposta:
        return Resposta(
            texto=texto.strip(),
            prefill_s=d.get("prompt_eval_duration", 0) / 1e9,
            decode_s=d.get("eval_duration", 0) / 1e9,
            prefill_tokens=d.get("prompt_eval_count", 0),
            decode_tokens=d.get("eval_count", 0),
            truncada=d.get("done_reason") == "length",
        )

    def _post(self, corpo: dict, fluxo: bool):
        try:
            r = requests.post(f"{self.url_base}/api/chat", json=corpo,
                              stream=fluxo, timeout=self.timeout)
        except requests.exceptions.ConnectionError as e:
            raise ErroDeGeracao(
                f"Ollama não responde em {self.url_base}. "
                f"Arrancar com «ollama serve»."
            ) from e
        except requests.exceptions.Timeout as e:
            raise ErroDeGeracao(
                f"Ollama excedeu {self.timeout}s. Em CPU uma resposta leva "
                f"~40s; este timeout sugere que o modelo não está carregado."
            ) from e

        if r.status_code == 404:
            raise ErroDeGeracao(
                f"Modelo «{self.modelo}» não encontrado. "
                f"Descarregar com «ollama pull {self.modelo}»."
            )
        if not r.ok:
            raise ErroDeGeracao(f"Ollama devolveu {r.status_code}: {r.text[:200]}")
        return r

    # --- API ----------------------------------------------------------------

    def gerar(self, system: str, user: str, *,
              max_tokens: int = NUM_PREDICT,
              temperatura: float | None = None) -> Resposta:
        r = self._post(self._corpo(system, user, max_tokens, False,
                                   temperatura), False)
        d = r.json()
        return self._resposta(d.get("message", {}).get("content", ""), d)

    def gerar_em_fluxo(self, system: str, user: str, *,
                       max_tokens: int = NUM_PREDICT) -> Iterator[str | Resposta]:
        """Emite fragmentos e, por último, a `Resposta` com os tempos.

        Os tempos só chegam na última linha do NDJSON (`done: true`), logo quem
        consome tem de iterar até ao fim para os ter.
        """
        r = self._post(self._corpo(system, user, max_tokens, True), True)
        partes: list[str] = []
        final: dict | None = None
        for linha in r.iter_lines(decode_unicode=True):
            if not linha:
                continue
            try:
                d = json.loads(linha)
            except json.JSONDecodeError:
                continue          # linha parcial: o próximo iter_lines completa
            if erro := d.get("error"):
                raise ErroDeGeracao(f"Ollama: {erro}")
            frag = d.get("message", {}).get("content", "")
            if frag:
                partes.append(frag)
                yield frag
            if d.get("done"):
                final = d
        if final is None:
            raise ErroDeGeracao("fluxo terminou sem mensagem final do Ollama")
        yield self._resposta("".join(partes), final)

    # --- diagnóstico --------------------------------------------------------

    def disponivel(self) -> bool:
        try:
            r = requests.get(f"{self.url_base}/api/version", timeout=5)
            return r.ok
        except requests.exceptions.RequestException:
            return False

    def modelo_instalado(self) -> bool:
        try:
            r = requests.get(f"{self.url_base}/api/tags", timeout=10)
            if not r.ok:
                return False
            nomes = {m.get("name", "") for m in r.json().get("models", [])}
            return self.modelo in nomes
        except requests.exceptions.RequestException:
            return False
