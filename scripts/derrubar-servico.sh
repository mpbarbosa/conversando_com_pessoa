#!/bin/bash
#
# derrubar-servico.sh
# -------------------
# Objectivo:    Derrubar o serviço público da saída D — a interface, o túnel e
#               a guarda do túnel — e deixá-lo derrubado, incluindo no próximo
#               arranque da máquina.
#
# Uso:          ./scripts/derrubar-servico.sh
#               ./scripts/derrubar-servico.sh --parar-so   (não desactiva)
#
# Para subir outra vez:
#               systemctl --user enable --now pessoabot.service \
#                   cloudflared.service pessoabot-tunel-guarda.timer
#
# Códigos de saída:
#   0  As três unidades estão paradas e a porta 8000 está livre.
#   1  Pelo menos uma continua a correr, ou a porta continua ocupada.
#   2  Nenhuma das unidades está instalada nesta máquina (nada a fazer).
#
# ---------------------------------------------------------------------------
# As quatro coisas que este script sabe e que um `systemctl stop` à mão não
# sabe. Todas vêm de algo medido, e estão em docs/PRODUCAO.md.
#
# 1. O TEMPORIZADOR PARA PRIMEIRO. A guarda do túnel corre de 5 em 5 minutos,
#    pergunta ao URL e **reinicia o túnel quando ele não responde** (§7.2).
#    Parar o túnel e deixar o temporizador de pé é pedir que ele volte dentro
#    de cinco minutos, sem erro nenhum a dizê-lo. É o primeiro comando, e é a
#    razão de este ficheiro existir em vez de três linhas copiadas à mão.
#
# 2. `disable --now` E NÃO `stop`. O `stop` pára agora e deixa os ligamentos
#    ao `default.target`; com `Linger=yes` — que é o que faz o serviço
#    sobreviver ao logout (portão D2) — as unidades voltavam no arranque
#    seguinte. Quem quer o serviço em baixo quer-no em baixo amanhã também.
#
# 3. O `ollama.service` NÃO É TOCADO, e é deliberado. É serviço de utilizador
#    da Fase 0, instalado sem sudo, e serve o CLI, os testes e as fases de
#    medição — nada disso tem que ver com o serviço público. Derrubá-lo aqui
#    por simetria tirava ao dono a máquina de trabalho junto com o URL.
#
# 4. A VERIFICAÇÃO NÃO PERGUNTA AO `systemctl`. Está medido o que isso vale:
#    na noite de 2026-10-19 o túnel morreu quando a máquina suspendeu e o
#    `systemctl --user is-active` respondeu `active` durante **dez horas**,
#    com `NRestarts=0`, porque o `cloudflared` não falha — insiste. «A unidade
#    está activa» deixou de ser evidência de «o serviço está acessível», e o
#    inverso vale igual. Logo confirma-se pela **porta** e pelo **processo**.

set -euo pipefail

SERVICO="pessoabot.service"
TUNEL="cloudflared.service"
TEMPORIZADOR="pessoabot-tunel-guarda.timer"
PORTA="${PESSOABOT_PORTA:-8000}"

# A ordem é a da nota 1: o temporizador antes do que ele ressuscita.
UNIDADES=("$TEMPORIZADOR" "$TUNEL" "$SERVICO")

ACCAO="disable"
if [[ "${1:-}" == "--parar-so" ]]; then
    ACCAO="stop"
    echo "==> --parar-so: as unidades voltam no próximo arranque (ver a nota 2)."
fi

# `systemctl --user` precisa de um barramento de sessão. Sem ele, todos os
# comandos abaixo falhavam com uma mensagem sobre D-Bus que não diz isto.
if ! systemctl --user show-environment > /dev/null 2>&1; then
    echo "Erro: não há barramento de utilizador acessível daqui." >&2
    echo "      Correr numa sessão do próprio utilizador, não por sudo." >&2
    exit 1
fi

# Instaladas? `disable` de uma unidade inexistente escreve para o stderr e,
# com `set -e`, levava o script abaixo antes de parar o que existe.
instaladas=()
for u in "${UNIDADES[@]}"; do
    if systemctl --user cat "$u" > /dev/null 2>&1; then
        instaladas+=("$u")
    fi
done

if [[ ${#instaladas[@]} -eq 0 ]]; then
    echo "Nenhuma das unidades do serviço está instalada; nada a derrubar."
    echo "  (${UNIDADES[*]})"
    exit 2
fi

echo "==> A derrubar, nesta ordem: ${instaladas[*]}"
for u in "${instaladas[@]}"; do
    # Uma a uma e com `|| true`: uma unidade já parada não deve impedir as
    # outras de parar. O veredicto vem da verificação, não daqui.
    #
    # Sem `| sed` a indentar: com o cano, das três linhas `Removed ...` que o
    # systemd escreveu chegou **uma** ao ecrã (medido a 2026-10-20), e um
    # script que faz três coisas e relata uma é a versão pequena do defeito
    # que este projecto passa o tempo a apanhar. A verificação abaixo é que
    # responde, mas o relato também não deve enganar.
    systemctl --user "$ACCAO" --now "$u" || true
done

# O `--now` devolve assim que o systemd aceita, não quando o processo morre.
sleep 2

echo "==> A verificar — pela porta e pelo processo, não pelo systemctl (nota 4)."

falhou=0

for u in "${instaladas[@]}"; do
    estado="$(systemctl --user is-active "$u" 2>/dev/null || true)"
    printf '    %-34s %s\n' "$u" "${estado:-desconhecido}"
    # `activating` e `deactivating` contam como a correr: o que interessa é se
    # ainda há algo de pé, e não se o systemd já arrumou a papelada.
    case "$estado" in
        inactive|failed|"") ;;
        *) falhou=1 ;;
    esac
done

# A porta. `ss` não está em toda a parte; sem ele diz-se que não se verificou,
# em vez de se dar por verificado o que não foi.
if command -v ss > /dev/null 2>&1; then
    if ss -ltn 2>/dev/null | grep -qE "127\.0\.0\.1:${PORTA}\b"; then
        echo "    porta ${PORTA}                        AINDA OCUPADA"
        falhou=1
    else
        echo "    porta ${PORTA}                        livre"
    fi
else
    echo "    porta ${PORTA}                        NÃO VERIFICADA (sem ss)"
fi

# O processo do túnel. O padrão tem o `d` entre parênteses rectos de propósito:
# `pgrep -f` vê a linha de comando do próprio script, e um padrão que contenha
# o seu próprio texto encontra-se a si mesmo e reporta um túnel que não existe.
# `cloudflare[d]` casa com `cloudflared` e nunca consigo mesmo.
restantes="$(pgrep -c -f 'cloudflare[d] tunnel' 2>/dev/null || true)"
if [[ "${restantes:-0}" -gt 0 ]]; then
    echo "    processos de túnel                 ${restantes} AINDA A CORRER"
    falhou=1
else
    echo "    processos de túnel                 nenhum"
fi

echo "    ollama.service                     $(systemctl --user is-active ollama.service 2>/dev/null || echo 'não instalado') (intocado, nota 3)"

# E a asserção que faltava: a última linha deste script afirma que o serviço
# não volta no arranque seguinte, e isso é uma afirmação sobre os ligamentos ao
# `default.target`/`timers.target` — não sobre o estado de execução. Até
# 2026-10-20 era afirmada sem ser verificada, que é precisamente o hábito que o
# `CONTROLO.md` §4 existe para registar. Agora pergunta-se ao systemd.
if [[ "$ACCAO" == "disable" ]]; then
    for u in "${instaladas[@]}"; do
        activacao="$(systemctl --user is-enabled "$u" 2>/dev/null || true)"
        # `static` e `generated` não têm ligamento para remover, logo não
        # podem voltar por essa via: contam como desactivadas.
        case "$activacao" in
            disabled|static|generated|"") ;;
            *)
                echo "    ${u} AINDA ACTIVADA (${activacao}) — volta no arranque"
                falhou=1
                ;;
        esac
    done
fi

if [[ "$falhou" -ne 0 ]]; then
    echo ""
    echo "Algo continua de pé. Ver o que resta:" >&2
    echo "  systemctl --user status ${instaladas[*]} --no-pager" >&2
    exit 1
fi

echo ""
if [[ "$ACCAO" == "disable" ]]; then
    echo "Derrubado, e não volta no próximo arranque."
else
    echo "Parado. ⚠️  Continua activado: volta no próximo arranque."
fi
