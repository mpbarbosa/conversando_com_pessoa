# One turn, in time

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ Name         turno-sequencia                                                                │
│ Type         Sequence diagram — five lifelines, two views (the turn, and the refusals)       │
│ Project      conversando_com_pessoa                                                         │
│ Description  `POST /api/perguntar` as it happens: who holds the lock, when the 200 is gone,  │
│              which retention catches a verse before it leaves, and the fact the dataflow     │
│              projection cannot state — that the plagiarism guard runs after the fragments    │
│              of its own attempt have already gone out. Drawn from `src/web/app.py`,          │
│              `fluxo.py`, `cancelar.py`, `retencao.py`, `pipeline.py` and `estatico/app.js`.  │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

Why a sequence diagram and not another graph: [`pessoa-rag.flow.ts`](pessoa-rag.flow.ts) draws
`gerar → verificarPersona → detectarPlagio → decidir`, which is true of `src/pipeline.py` and
not of the wire. A dataflow edge is a data dependency; it has no way to say that the guard is
downstream in the *dataflow* and not downstream in *time*. That distinction is the whole I7′
finding, and it is step 23 of §1 below. The argument is in [`NOTACAO.md`](NOTACAO.md) §2.

## 1. The turn

```mermaid
sequenceDiagram
    autonumber
    participant N as navegador<br/>estatico/app.js
    participant H as POST /api/perguntar<br/>no laço de eventos
    participant E as _eventos<br/>corpo do StreamingResponse
    participant T as thread de trabalho<br/>pipeline.responder_em_fluxo
    participant O as Ollama<br/>127.0.0.1

    N->>H: fetch, com o signal de um AbortController
    H->>H: _verificar_combinacao
    H->>H: medicao_a_correr — disco, sem um await
    H->>H: trinco.locked — e nada entre isto e o acquire
    H->>H: await trinco.acquire
    H->>H: preparar_geracao, inicio_geracao = agora
    H-->>N: 200, media_type NDJSON
    Note over H,E: o 200 já saiu. Daqui para a frente<br/>nenhuma falha pode ser um estado HTTP
    H->>E: o corpo do StreamingResponse arranca, depois de o manipulador devolver

    E->>T: garantir_pipeline, em thread
    E->>T: corpo_retido, em thread — as linhas que o portão I7' protege
    Note over E,T: se o corpus não se ler, levanta, e sai um evento erro.<br/>Gerar sem saber o que retirar era publicar às cegas
    opt pedido com auto
        E->>T: rotear, em thread
        E-->>N: proposta — a voz e o que custou, antes de gerar
    end
    E->>T: reranker_para, em thread

    E->>T: em_fluxo cria a thread — nada do gerador corre no laço
    T->>T: recuperar e montar — é aqui que mora o prefill, 58 a 89% da espera
    loop cada tentativa, até 2
        T->>O: gerar_em_fluxo, system + user
        loop cada fragmento
            O-->>T: fragmento
            T-->>E: str, pela fila
            E->>E: limpar_inicio — portão I2, a mesma função que o CLI chama
            E->>E: Retentor.alimentar — portão I7', linha a linha
            E-->>N: fragmento, quando sobrou texto para mandar
        end
        O-->>T: fim da resposta
        T->>T: verificar, e depois analisar
        Note over N,T: a verificação corre AQUI, e os fragmentos desta tentativa<br/>já saíram todos. O que os conteve foi a retenção do<br/>transporte, não a guarda de plágio
        T-->>E: Turno, pela fila
        E-->>N: fragmento, o que o Retentor.esvaziar ainda tinha
        E-->>N: turno — redigido, e com retidas
        alt aprovado, ou era a última tentativa
            T->>T: return
        else rejeitado, e ainda há tentativa
            T->>T: _repetir_sem — prompt novo, sem os poemas de que copiou
            E->>E: a_reter de novo, retentor.reiniciar
            Note over N: a tentativa rejeitada não é substituída.<br/>Fica recolhida, com o motivo
        end
    end
    E->>E: finally — inicio_geracao = None, trinco.release
    Note over E,H: a libertação é no finally DESTE gerador e não no fim<br/>do manipulador: lá, o trinco ficava aberto a geração inteira
    E-->>N: fim do fluxo
```

## 2. The refusals, and giving up

```mermaid
sequenceDiagram
    autonumber
    participant N as navegador
    participant H as POST /api/perguntar
    participant S as GET /api/estado
    participant E as _eventos
    participant T as thread de trabalho
    participant O as Ollama

    N->>H: fetch
    alt combinação impossível
        H-->>N: 422 — recusa, e não corrige: a voz era a escolha de alguém
    else medição a correr
        H-->>N: 409 medicao_a_correr — o servidor cede o Ollama à fase
    else já há uma geração
        H-->>N: 409 ocupado, com espera_estimada_s
    end
    Note over H: as três são antes do trinco, e nenhuma o toma:<br/>uma recusa não tranca a porta que estava livre

    N->>S: GET /api/estado durante a geração — portão I4
    S-->>N: os componentes, e nada foi carregado para o dizer

    N->>N: clique em cancelar — controlador.abort
    N--xE: o consumidor do fluxo desaparece
    E->>E: finally do em_fluxo, e tarefa.done é falso
    E->>E: ao_desistir — cancelar_geracao, síncrono, no laço
    E->>O: socket.shutdown — acorda já o leitor bloqueado
    E->>E: resposta.close, numa thread daemon
    Note over E: e fica a marca _desistido, para o cancelamento<br/>que chega entre duas tentativas e não tem fluxo para fechar
    T--xT: o leitor acorda e a thread termina
    E->>E: await tarefa, e só então o finally
    E->>E: trinco.release
    Note over E,N: CancelledError não é Exception, logo não sai evento erro.<br/>O ecrã diz interrompido, com o que já tinha
```

## 3. What each claim rests on

Nothing here is drawn from the plan. Each row is a line of code and the test that holds it. The
step numbers are the diagrams' own `autonumber`, with the label beside them so an edit that
renumbers the diagram does not silently break the reference.

| Step | Claim | Code | Held by |
|---|---|---|---|
| §1 · 2 `_verificar_combinacao` | the impossible combination is refused, not corrected | `app.py:_verificar_combinacao` | `test_a_combinacao_impossivel_e_recusada_e_nao_corrigida` |
| §1 · 3–5 sentinel, `locked`, `acquire` | the sentinel comes first, and nothing runs between the check and the take | `app.py:perguntar` | `test_a_segunda_geracao_concorrente_recebe_409_com_a_espera` |
| §1 · 7–8 the `200`, then the body | after this a failure can only be an event, never a status | `StreamingResponse(_eventos(...))` | `test_uma_falha_na_geracao_liberta_o_trinco_e_vai_ao_fio` |
| §1 · 10 `corpo_retido` | the retained lines are read **before** a single token is generated, and failing to read them stops the turn | `Servico.corpo_retido` | `tests/test_i7.py` (8 tests) |
| §1 · 12 `proposta` | the proposal precedes the fragments, and generation does not wait on a dialog | `_eventos`, §4.5 | `test_o_auto_emite_a_proposta_antes_dos_fragmentos` |
| §1 · 19 `limpar_inicio` | the presentation retention is the CLI's own function, not a second copy of the policy | `apresentacao.limpar_inicio` | `test_i2_a_retencao_usa_a_funcao_do_cli_e_nao_uma_copia` |
| §1 · 23 `verificar, e depois analisar` | **the guard runs after the fragments of its own attempt have already gone out** — step 21 precedes it | `pipeline.py:239` vs `pipeline.py:243–244` | `tests/test_i7.py`, `src/web/retencao.py` |
| §1 · 26 `turno` | the rejected attempt reaches the wire and is not replaced on screen | `_eventos`, §4.4 | `test_i1_a_tentativa_rejeitada_vai_ao_fio_e_nao_e_substituida` |
| §1 · 29 `retentor.reiniciar` | both retentions are re-armed per attempt — the CLI does **not** do this | `buffer, a_reter = [], True` | `test_i2_o_preambulo_e_o_eco_nao_chegam_ao_fio` |
| §1 · 30 `finally` | released in the generator's `finally`, not at handler return | `app.py:543–544` | `test_o_trinco_fica_livre_depois_de_cada_geracao` |
| §2 · 5–6 `/api/estado` | the state answers mid-generation, and loads nothing to do it | `estado.py`, gate I4 | `test_i4_o_estado_responde_durante_uma_geracao` |
| §2 · 7–13 the abort | giving up stops Ollama, and does not merely free the screen | `cancelar.py:interromper` | `test_i5_depois_do_abort_o_ollama_nao_esta_a_decodificar`, `test_i5_o_trinco_fica_livre_e_a_pergunta_seguinte_arranca_em_menos_de_2s` |
| §2 · 10–12 `_desistido` | the mark catches a cancel that arrives between two attempts, with no open stream to close | `GeradorCancelavel.cancelar` | `test_cancelar_entre_duas_tentativas_apanha_a_tentativa_seguinte` |
| §2 · 15 `trinco.release` | the cancel path frees the lock too, since `CancelledError` misses the `except` | `_eventos` `finally` | `test_i5_o_fluxo_cancelado_nao_deixa_o_servidor_avariado` |

Both diagrams were rendered with Mermaid 10.9.1 before being committed, so the syntax is
checked and not assumed.

## 4. Where this should live

Here, because this folder is where analysis of this project lands. If it is adopted, its place
is next to [`docs/FASE-6.md`](../FASE-6.md) §4.4, which argues step 24 in prose three times, and
beside §2 of [`docs/PRODUCAO.md`](../PRODUCAO.md), which argues step 20. Like everything else in
this folder it is **not generated** and nothing keeps it in sync with the Python: if the event
order changes, this changes by hand.

Known omission, deliberate: `GET /api/poema/{id}` is not drawn, because it is not built —
Fase 6 passo 9 is suspended by the saída B of `PRODUCAO.md`.
