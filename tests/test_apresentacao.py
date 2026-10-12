"""A retenção do início do fluxo.

Mudou de `test_cli.py` no Passo 1 da [Fase 6](../docs/FASE-6.md), com a função
que exercita: `limpar_inicio` passou a ter dois consumidores — o laço do CLI e
o `POST /api/perguntar` — e os testes seguem a função, não o primeiro que a
chamou.

O comentário abaixo é o registo do defeito observado e vem **à letra** do
`test_cli.py`. O `_consumir` simula o laço de streaming; o portão **I2** da
Fase 6 acrescenta-lhe o braço da interface, e é por isso que ele vive aqui e
não dentro de um teste.
"""

# --- limpeza do início do fluxo --------------------------------------------
#
# O buffer do CLI só chamava `remover_cercas` e `remover_eco_da_pergunta`. O
# defeito foi visto no terminal: a «qual é o futuro de portugal?» o modelo
# começou por «Aqui está um poema novo, seguindo as instruções:» e essa linha
# apareceu no ecrã, embora o texto validado não a tenha — `verificar` chama
# `remover_preambulo`. O ecrã mostrava mais do que o veredicto julgara.

from src.apresentacao import limpar_inicio

PERGUNTA = "qual é o futuro de portugal?"


def _consumir(fragmentos, pergunta=PERGUNTA):
    """Simula o laço de streaming: devolve o que seria impresso."""
    buffer, saida, a_reter = "", [], True
    for f in fragmentos:
        if a_reter:
            buffer += f
            retido, a_reter = limpar_inicio(buffer, pergunta)
            if a_reter:
                buffer = retido
                continue
            buffer = ""
            saida.append(retido)
            continue
        saida.append(f)
    return "".join(saida)


def test_preambulo_observado_nao_chega_ao_ecra():
    frags = ["Aqui está um poema novo, seguindo as instruções:\n",
             "os passos ecoam\n", "silêncio envolve"]
    assert "Aqui está" not in _consumir(frags)
    assert "os passos ecoam" in _consumir(frags)


def test_eco_da_pergunta_continua_a_ser_removido():
    frags = ["Qual é o futuro de Portugal?\n", "Não sei. Olho e vejo.\n"]
    out = _consumir(frags)
    assert "Qual é o futuro" not in out
    assert "Não sei" in out


def test_preambulo_e_eco_em_linhas_separadas():
    """O caso que a retenção de uma só linha deixava passar."""
    frags = ["Aqui está o poema:\n",
             "Qual é o futuro de Portugal?\n",
             "O futuro é não haver futuro.\n"]
    out = _consumir(frags)
    assert "Aqui está" not in out
    assert "Qual é o futuro de Portugal?" not in out
    assert "O futuro é não haver futuro." in out


def test_primeiro_verso_legitimo_nao_e_comido():
    frags = ["O Tejo é mais belo que o rio da minha aldeia,\n", "mas o Tejo\n"]
    assert _consumir(frags).startswith("O Tejo é mais belo")


def test_retem_enquanto_nao_houver_linha_completa():
    texto, a_reter = limpar_inicio("sem mudança de linha ainda", PERGUNTA)
    assert a_reter
    assert texto == "sem mudança de linha ainda"
