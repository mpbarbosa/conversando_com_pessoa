# Guião do portão D2 — «o serviço sobrevive à sessão»

O portão **D2** do [`PRODUCAO.md`](../PRODUCAO.md) §9 afirma uma coisa que
nenhum teste pode afirmar por ele: *não é um processo de terminal*. As 17 provas
do `tests/test_unidades.py` medem o que **torna** o D2 possível — caminhos
absolutos, `After` sem `Requires`, `WantedBy=default.target`, nunca o checkout
de trabalho, e o `systemd-analyze --user verify` do próprio systemd. O que falta
são **as duas metades que só o dono pode correr**: um logout e um reinício.

Esta página é o guião delas. O instrumento já existe —
`python -m src.web.instalar --verificar-d2`, em [`src/web/instalar.py`](../../src/web/instalar.py)
(`avaliar_d2`) — e julga em **tempo monótono desde o arranque**, para não haver
fuso nenhum na comparação. O que o guião acrescenta é a **ordem**, as três
recusas que protegem a medição, e a asserção que o verificador **não** faz.

---

## 0. Metade do D2 já está medida, e sem ninguém fazer nada

Lido desta máquina em **2026-10-23 13:15 (−03)**, com a casa como estava:

| | | procedência |
|---|---|---|
| arranque da máquina | **2026-10-22 12:13:01** | `uptime -s` |
| `pessoabot.service` activo desde | **2026-10-22 12:13:07** (+6 s) | `systemctl --user show -p ActiveEnterTimestamp` |
| processo do serviço | PID **3032**, 1 d 06 h de idade, do `.venv` do checkout do **serviço** | `ps -o lstart,etime,cmd` |
| `NRestarts` | **0** | `systemctl --user show -p NRestarts` |
| sessão de utilizador mais recente | **2026-10-23 12:56:32** (+59 450 s) | `loginctl show-session 156` |
| `Linger` | **yes** | `loginctl show-user` |
| veredicto do instrumento | **PASSA nas duas metades**, código de saída **0** | `--verificar-d2` |

**A metade do reinício está honestamente medida:** o serviço subiu **14 s depois
do arranque**, antes de existir sessão de utilizador nenhuma, e é exactamente
isso — e só isso — que o `enable-linger` compra. Não há aqui nada a repetir.

**A metade do logout é a que merece o acto deliberado.** O instrumento aprova-a
pelo critério certo — o serviço é 59 436 s mais velho que a sessão de onde se
pergunta, logo **não nasceu com ela** —, mas o que está medido é «o serviço não
é da idade desta sessão», e não «eu saí de uma sessão e o serviço ficou». A
diferença importa pela razão de sempre: a primeira é uma inferência sobre o que
aconteceu, a segunda é uma observação de um acto que alguém fez. É a §3.

> ✅ **E o logout foi feito, a 2026-10-23 às 23:12.** A sessão **156** foi
> terminada e o `loginctl` deixou de a conhecer — «No session '156' known» —,
> nasceu a **233** às 23:13:01, e do outro lado o **`MainPID` continua 3032**,
> com `NRestarts=0` e o mesmo `ActiveEnterTimestampMonotonic`. O processo que
> serve tem 1 d 11 h e sobreviveu à morte da sessão anterior: **a metade do
> logout deixou de ser uma inferência**. Com a §5 corrida depois dela (200, 1
> tentativa, 61,5 s, plágio zero), o **D2 está cumprido** e registado nos
> quatro sítios da §6. O que segue fica escrito para a próxima vez que o portão
> tenha de ser remedido — depois de um recuo, de uma reinstalação, ou de um
> reinício que passe por um login antes de alguém se lembrar de medir.

> ⚠️ **E esta leitura caduca.** Qualquer `python -m src.web.instalar` reinicia o
> `pessoabot` e **apaga a evidência**: o serviço passa a ser mais novo que o
> arranque e mais novo que a sessão. O verificador responde **«por medir»** nesse
> caso, e não «falha» — um portão que falhasse ali ensinava quem o lê a
> ignorá-lo. Se a tabela acima já não reproduzir, foi isso que aconteceu, e o
> remédio é a §4.

---

## 1. Antes de começar: três recusas

Nenhuma é arrumação; cada uma destrói uma medição diferente.

1. **Não correr o instalador.** Nem `--ref`, nem sem argumentos, nem «só para
   confirmar». Reinicia a unidade e com ela os três instantes que o portão lê.
   Se for preciso ver o que faria, é `--ensaio`, que não toca em nada.
2. **Não reiniciar a unidade à mão.** `systemctl --user restart pessoabot` tem o
   mesmo efeito, com menos aviso.
3. **Não correr uma fase de medição.** O sentinela em
   `~/.local/state/pessoabot/.medicao-a-correr` faz o `POST /api/perguntar`
   recusar, e a pergunta real da §5 fica sem poder ser feita. Confirma-se pelo
   campo `medicao_a_correr` do `/api/health`.

E uma armadilha de ferramenta: o `--verificar-d2` importa o `src.web.app`, logo
precisa do **`python` do ambiente virtual**, não do `python3` do sistema. Com o
do sistema morre em `ModuleNotFoundError: No module named 'fastapi'`.

---

## 2. A linha de base, antes de mexer

Do checkout de trabalho:

```bash
cd ~/Documents/GitHub/conversando_com_pessoa && \
  uptime -s && \
  loginctl show-user "$USER" -p Linger && \
  systemctl --user show pessoabot.service -p ActiveEnterTimestamp -p NRestarts -p MainPID && \
  .venv/bin/python -m src.web.instalar --verificar-d2
```

Guarda a saída. É contra ela que as duas metades se leem, e é ela que diz se
alguma das três recusas da §1 foi quebrada entretanto.

---

## 3. Metade A — o logout

O acto: **terminar a sessão gráfica e voltar a entrar.** Não `reboot`, não
suspender, não trancar o ecrã — trancar não termina sessão nenhuma, e o portão
veria a mesma sessão de sempre.

1. Termina a sessão gráfica (*log out*, não *lock*).
2. Entra outra vez.
3. Abre um terminal e corre:

```bash
cd ~/Documents/GitHub/conversando_com_pessoa && .venv/bin/python -m src.web.instalar --verificar-d2
```

O que se espera, e porquê:

| metade | esperado | o que o número diz |
|---|---|---|
| sobrevive ao logout | **PASSA** | o serviço é mais velho que a sessão nova por mais de 60 s |
| sobrevive ao reinício | **PASSA** | continua a ser o mesmo serviço de +14 s — o logout não o tocou |

**Se der `FALHA` no logout**, o número a ler é o da idade: «o serviço é da idade
desta sessão» quer dizer que nasceu com o login, e a causa é o `Linger`. Com
`Linger=no` o verificador reprova as duas metades de uma vez e diz-lhe o nome:
`loginctl enable-linger`, que é metade do passo 4.

E a observação que o instrumento não faz, mas que esta metade permite fazer de
graça: **o PID não muda.** Anota-o antes e depois.

```bash
systemctl --user show pessoabot.service -p MainPID -p NRestarts
```

Um PID igual e `NRestarts=0` dos dois lados do logout é a prova directa de que
não houve morte e ressurreição nenhuma — o que o tempo monótono só consegue
dizer por inferência.

---

## 4. Metade B — o reinício, e o momento em que se mede

Esta metade **já está medida** (§0), e o guião fica escrito para a vez em que
não estiver: depois de um instalador, de um recuo, ou de um reinício qualquer
que tenha passado por um login antes de alguém se lembrar de medir.

O que a torna frágil é o **instante**: a afirmação é «o serviço subiu no
arranque, **antes de haver login nenhum**», e um login prévio não a destrói, mas
tira-lhe a leitura mais limpa. Portanto:

1. `reboot`.
2. **Antes** de entrar na sessão gráfica, vai para um terminal virtual —
   `Ctrl`+`Alt`+`F3` — e entra ali.
3. Corre:

```bash
cd ~/Documents/GitHub/conversando_com_pessoa && .venv/bin/python -m src.web.instalar --verificar-d2
```

Espera-se `PASSA` no reinício («o serviço subiu N s depois do arranque, antes de
qualquer login») e **`POR MEDIR` no logout** — e esse «por medir» está correcto:
num arranque limpo não houve logout nenhum, e o verificador recusa-se a dar por
provada uma metade com a evidência da outra. A ordem do código é essa de
propósito: pergunta-se **primeiro** se houve logout, senão um arranque limpo
dava «passa» às duas.

Logo as duas metades **não se medem na mesma corrida**, e o guião precisa dos
dois momentos: a §3 dá o logout, a §4 dá o reinício.

---

## 5. A asserção que o verificador não faz: o serviço **responde**

O `--verificar-d2` lê três instantes. O enunciado do portão diz mais — «deixam o
serviço de pé **e o URL a responder**» — e «de pé» pelo `systemctl` é
precisamente a palavra em que esta casa já se queimou: a §7.2 do plano registra
a máquina a suspender com o túnel morto e o `systemctl` a dizer `active`.

Como não há URL público (o túnel está desligado por decisão, §7.5 do plano), o
URL é o `127.0.0.1`. Depois de **cada** uma das duas metades:

```bash
curl -s --max-time 5 http://127.0.0.1:8000/api/health
```

Espera-se `"status":"ok"`, `"pode_perguntar":true`, e o `sha`/`etiqueta` do que
está instalado — em 2026-10-23, `aa15dd4` e `servico-2026-10-20c`. Um `sha`
diferente do esperado é a verificação do **D1** a apanhar um reinício que
aconteceu sem ninguém o pedir.

E uma pergunta real, ponta a ponta, porque o `/api/health` responde sem o modelo
ter sido carregado:

```bash
curl -N -s --max-time 180 -X POST http://127.0.0.1:8000/api/perguntar \
  -H 'Content-Type: application/json' \
  -d '{"pergunta":"o que resta de um dia que não se viveu?","voz":"ortonimo"}'
```

É um fluxo de NDJSON e leva o que o hardware medido leva — **~34 s** de geração,
mais o carregamento se o modelo tiver descarregado. Depois dela, o campo
`indice.aceito` do `/api/health` passa de `false` («em disco, ainda não
verificado contra o corpus») a verificado: é a primeira pergunta a fazer o
trabalho que o arranque não faz.

Isto é o que distingue «o processo está vivo» de «o serviço serve». As duas
metades do D2 precisam das duas.

**Ensaiado a 2026-10-23**, contra o serviço a correr, para o guião não mandar
correr comandos que ninguém tentou:

| | |
|---|---|
| `/api/health` antes | `status: ok`, `sha: aa15dd4`, `indice.aceito: **false**` |
| a pergunta | **200**, fluxo de NDJSON, **1** tentativa, `aprovado: true` |
| geração | **40,2 s** (prefill 24,3 s · 671 tok; decode 15,9 s · 110 tok a 6,9 tok/s) |
| parede, com o modelo a carregar | **62 s** |
| plágio · retidas | `fracao_copiada: 0.0`, máx. similaridade **0,556** · `retidas: 0` |
| `/api/health` depois | `indice.aceito: **true**` — «2290 chunks · intfloat/multilingual-e5-base · dim 768» |

Os 40,2 s estão dentro do que os relatórios de fase descrevem para **esta**
máquina (~34 s de mediana), e a passagem do `indice.aceito` de `false` a `true`
é a única mudança de estado que o ensaio deixou.

---

## 6. Onde se regista o resultado

O portão só passa a `✅` em quatro sítios, e a ordem é esta:

| | onde | o que muda |
|---|---|---|
| 1 | [`PRODUCAO.md`](../PRODUCAO.md) §9, linha **D2** | de `🔶 instalado, por medir` a `✅`, com a data e as duas saídas do verificador |
| 2 | [`PRODUCAO.md`](../PRODUCAO.md) §5, passo **4** | de `🔶 instalado` a `✅ feito`, e a frase «falta: as duas metades que só o dono pode correr» sai |
| 3 | [`SERVICO.md`](SERVICO.md) §1 | o estado de hoje passa a dizer que o serviço sobrevive à sessão, medido |
| 4 | [`CONTROLO.md`](../CONTROLO.md) §2, linha do **Serviço público** | o D2 deixa de estar na lista do que bloqueia |

E o que **não** se segue dele: o **D3** («o túnel obedece ao sentinela») continua
não mensurável, e não por falta deste portão — o túnel está em baixo sobre a
medição da §7.4, a sessão autenticada de **4 segundos** do *Quick Tunnel*
protegido. O D2 cumprido fecha o passo 4 e deixa o caminho público à espera de
terceiros, não de trabalho desta casa.
