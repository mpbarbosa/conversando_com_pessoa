# O serviço público — o que está nesta máquina

Escrito em **2026-10-20**, e **lido da máquina** enquanto se escrevia. Cada
número desta página tem procedência: ou saiu de um comando corrido aqui nesse
dia, ou de um relatório de fase deste repositório, e a coluna diz qual.

O plano que o produziu é o [`PRODUCAO.md`](../PRODUCAO.md). Esta página é o que
alguém precisa de saber para **operar** o que lá está decidido; as razões ficam
lá, e os apontadores levam-nas.

> ⚠️ **Isto não é «produção», e o nome é deliberado.** Dev e prod são o mesmo
> computador. Não há segunda máquina, não há recuo para outro disco, não há CI
> a implantar, e não há separação entre quem edita e o que está a servir. O
> repositório irmão tem um `production-environment-memory.md`; aqui esse
> ficheiro **não se escreve**, porque não há ambiente de produção para
> documentar. Chama-se **«o serviço público»** — ver a §1 do plano.

---

## 1. O estado, hoje

| | | procedência |
|---|---|---|
| o serviço responde em | `http://127.0.0.1:8000` | `curl` |
| URL público | **nenhum** | §7.5 do plano |
| etiqueta a correr | `servico-2026-10-20c` | `/api/health` |
| `sha` a correr | `aa15dd4` | `/api/health` |

**Por que é que não há URL público.** O túnel está desligado por decisão do
dono, sobre uma medição: um *Quick Tunnel* protegido com `--allowed-mail` **não
consegue servir esta interface**, porque a sessão autenticada dura **4
segundos** ([`#1752`](https://github.com/cloudflare/cloudflared/issues/1752),
aberto). Está medido na §7.4 do plano. A razão está escrita em
`~/.config/pessoabot/tunel-desligado`, e é esse ficheiro que impede qualquer
reinstalação de o reabrir.

---

## 2. As peças, e onde vivem

| peça | caminho | nota |
|---|---|---|
| checkout do **serviço** | `~/.local/share/pessoabot/servico` | referência destacada numa etiqueta; **5,7 GB**, dos quais o `.venv` é quase tudo |
| checkout de **trabalho** | `~/Documents/GitHub/conversando_com_pessoa` | onde se edita, corre o `pytest` e correm as fases |
| Ollama | `~/.local/ollama/bin/ollama` | **fora do `PATH`**, decisão da Fase 0: sem `sudo`, sem serviço de sistema. Versão **0.35.0** |
| `cloudflared` | `~/.local/cloudflared/bin/cloudflared` | mesma disciplina. Versão **2026.10.1** |
| sentinela de medição | `~/.local/state/pessoabot/.medicao-a-correr` | **absoluto e único na máquina**: com dois checkouts há dois `data/`, e um caminho relativo desligava o mecanismo em silêncio |
| lista de convidados | `~/.config/pessoabot/convidados` | fica **nesta máquina**; não existe em conta de fornecedor nenhum |
| interruptor do túnel | `~/.config/pessoabot/tunel-desligado` | existindo, não há túnel, e o conteúdo é a razão |
| unidades | `~/.config/systemd/user/` | geradas por `src/web/unidades.py`, nunca escritas à mão |

**Os dois checkouts não são arrumação.** O serviço público não pode servir o
checkout onde se edita: um `git switch` a meio de uma fase ficava no ar sob um
URL. Partilham o que é caro e imutável — o Ollama, o modelo de 4,9 GB e o cache
do Hugging Face (11 GB) —, e o serviço tem `.venv`, `data/` e referência
próprios.

---

## 3. As unidades

| unidade | estado hoje | o que faz |
|---|---|---|
| `ollama.service` | `enabled · active` | o Ollama, com `OLLAMA_KEEP_ALIVE=24h` |
| `pessoabot.service` | `enabled · active` | `python -m src.web` no checkout do serviço |
| `cloudflared.service` | **`disabled · inactive`** | o túnel. Ver §1 |
| `pessoabot-tunel-guarda.timer` | **`disabled · inactive`** | perguntava ao URL de 5 em 5 min |

`Linger=yes`, logo tudo isto sobrevive a fechar a sessão gráfica.

**Três decisões que as unidades codificam**, e que não se devem desfazer sem ler
a §5.4 do plano:

- **`ExecStart` absoluto.** O `PATH` de uma unidade não é o do dono, e o Ollama
  está fora dele de propósito.
- **`After=` e nunca `Requires=`.** O `/api/estado` reporta «Ollama em baixo»
  com o remédio em vez de o processo morrer, e o portão **I3** mede-o. Com
  `Requires=`, um Ollama caído levava com ele a página que sabia explicar a
  avaria.
- **O interface e a porta não estão na unidade.** Vêm do `HOST`/`PORTA` do
  `app.py`, por `python -m src.web`. Um `--host 0.0.0.0` numa unidade é o
  «copiado de um tutorial» que a Fase 6 listou como risco, e nenhum teste o
  veria — há um a proibi-lo no ficheiro.

---

## 4. Os comandos

| o que | comando |
|---|---|
| instalar ou actualizar | `python -m src.web.instalar` |
| ver o que faria | `python -m src.web.instalar --ensaio` |
| **recuar** para uma etiqueta | `python -m src.web.instalar --recuar servico-AAAA-MM-DDx` |
| o túnel está vivo? | `python -m src.web.instalar --verificar-tunel` |
| o túnel fecha estranhos? | `python -m src.web.instalar --verificar-d4 <url>` |
| de que código é o processo? | `curl -s localhost:8000/api/health` |

Todos correm do **checkout de trabalho**, e o instalador **recusa-se** a
instalar sobre ele.

**O instalador verifica-se pelo serviço, não pelo seu próprio código de saída.**
Compara o `sha` do `/api/health` com o do checkout e devolve 1 se divergirem —
porque `systemctl` a responder 0 não é evidência de nada: já houve uma
instalação que trocou o checkout e deixou o processo antigo a servir (§7.1).

---

## 5. Recuar

O recuo é um comando, e **foi ensaiado** de uma etiqueta deliberadamente doente
para a anterior (portão **D6**, §5.5 do plano). A ordem não é invertível:

1. `git fetch --prune --tags` — **com `--tags`**, senão a etiqueta de uma versão
   doente, que pode não estar em ramo nenhum, não chega;
2. `git checkout --detach <etiqueta>`;
3. `pip install`, porque as dependências podem ter mudado entre etiquetas;
4. **verificar o manifesto do índice, e recusar se divergir** — antes do
   reinício, nunca depois: o manifesto devolve `None` em vez de reconstruir em
   silêncio, e um serviço reiniciado com o índice errado cobra **383 s** de CPU
   saturado à primeira pergunta;
5. reiniciar, e conferir pelo `/api/health`.

---

## 6. Antes de correr uma fase de medição

**O servidor está sempre de pé, e usa o mesmo Ollama — que tem um slot só.**
Até ao passo 4, «não correr o servidor com uma medição a decorrer» era
disciplina; com uma unidade activada e `Linger=yes` **não há onde aplicar
disciplina**. O único mecanismo é o sentinela:

```python
from src.web.sentinela import medicao
with medicao("5Z", amostras=Path("docs/fase-5z/01-cru.jsonl")):
    ...
```

O ajudante escreve o sentinela (e o servidor passa a recusar perguntas com
409), derruba o túnel se houver, e escreve `00-janela.json` ao lado das
amostras — na abertura e no fecho. Uma fase que corra **sem** isto partilha o
Ollama com o serviço, e as latências medidas deixam de descrever o caminho que
o utilizador corre.

⚠️ **A janela não mede o que o portão D5 dizia que media.** O D5 pedia que os
instantes de túnel de pé não se sobrepusessem «aos instantes das amostras», e
as amostras **não têm instante nenhum** — têm `segundos`, que é uma duração. O
que a janela mede é que **o ficheiro das amostras só cresceu dentro dela**. Ver
a §3.6 do plano.

---

## 7. O hardware, e o que ele dá

| | | procedência |
|---|---|---|
| núcleos | **14** | `nproc` |
| RAM | **30 GiB**, 17 disponíveis | `free -g` |
| disco livre em `/home` | **102 GB** de 441 | `df -h` |
| sistema | Ubuntu 26.04.1 LTS, kernel 7.0.0-38, systemd 259 | `/etc/os-release`, `uname -r` |
| Python | 3.12.3 | `python -V` |
| uma resposta | **~34 s**, ~18 s até ao 1.º verso, 14–17 tok/s | Fases 0 a 5, **nesta máquina** |
| a 1.ª pergunta de cada arranque | **+~23 s** de encoder e índice | medido a 2026-10-20 (65 s de parede contra 42,1 s de geração) |
| tecto | **~105 respostas/hora** | 3600 / 34, um trinco, uma geração de cada vez |
| *throttling* térmico | até **101 °C** | Fase 0 |

**A vantagem desta montagem é uma só, e é real:** o hardware é o hardware
medido. Os números das Fases 0 a 5 descrevem **este** computador, logo não há
nada a remedir num servidor desconhecido.

---

## 8. O que não existe, e porquê

| | |
|---|---|
| **URL público** | a sessão autenticada dura 4 s (§7.4). Um túnel **sem** autenticação funcionaria, e é o que a §7 recusa |
| **URL estável** | um *Quick Tunnel* muda de nome em cada arranque **e não sobrevive a uma suspensão** — medido: 4 h 42 min, e a máquina dormiu às 02:22. Precisaria de um domínio, que é dinheiro |
| **`GET /api/poema/{id}`** | saída B: a rota **não existe enquanto houver túnel**. E o portão **I7′** mostrou que isso não bastava — havia três outras portas por onde o corpo saía, e a correcção é a `src/web/retencao.py` |
| **cópias de `data/sessoes.db`** | o passo 8 da Fase 6 não existe, logo o ficheiro também não. Hoje **nenhum** estado precisa de cópia: o corpus está versionado, e o `corpus.jsonl` e o índice reconstroem-se |
| **limite de pedidos** | passo 9 do plano, e só faz sentido se alguma vez houver público |
| **`docs/producao/production-environment-memory.md`** | não há ambiente de produção para documentar |

---

## 9. Se alguma coisa estiver errada

| sintoma | o que perguntar primeiro |
|---|---|
| a página não abre | `systemctl --user status pessoabot.service`, e depois `curl localhost:8000/api/health` |
| responde mas está lenta | `/api/estado`: o encoder carrega na 1.ª pergunta, e o reranker e o roteador são escolhas com custo escrito |
| diz «Ollama em baixo» | `systemctl --user status ollama.service`. **Não** é avaria do serviço: foi desenhado para o dizer com o remédio |
| recusa perguntas com 409 | há uma medição a correr. O `/api/estado` nomeia a fase e o PID; um sentinela esquecido diagnostica-se pelo PID |
| o `sha` não é o que instalei | o processo não foi substituído. `systemctl --user restart pessoabot.service` |

⚠️ **E a regra que esta casa aprendeu três vezes num dia: não se acredita no
código de saída de um comando — pergunta-se ao serviço.** O `systemctl` já
disse `active` com o URL morto durante dez horas, o `enable --now` já devolveu
0 sem substituir o processo, e o `enable` já devolveu 0 com uma guarda incapaz
de guardar. As correcções **48**, **50** e **52** do `CONTROLO.md` §4 são as
três.
