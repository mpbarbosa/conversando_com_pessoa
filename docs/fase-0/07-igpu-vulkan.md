# Correcção à premissa de hardware: existe uma iGPU utilizável

Medido em 2026-10-01, depois de as Fases 0 a 3 estarem concluídas.

---

## O que estava errado

A Fase 0 concluiu **«CPU-only, sem GPU»** a partir de `nvidia-smi` ausente. Vi o
`lspci` reportar «Intel Corporation Meteor Lake-P [Intel Graphics]» e tratei-o
como irrelevante, porque assumi que inferência em gráficos integrados não era
caminho. **Não verifiquei.**

O Ollama 0.35.0 detecta-a por Vulkan e **desliga-a por omissão**:

```
dropping integrated GPU; to enable, set OLLAMA_IGPU_ENABLE=1
  library=Vulkan name=Vulkan0 description="Intel(R) Graphics (MTL)"
```

Com `OLLAMA_IGPU_ENABLE=1`:

```
inference compute library=Vulkan type=iGPU total="22.5 GiB" available="11.4 GiB"
vram-based default context total_vram="22.5 GiB" default_num_ctx=4096
```

22,5 GiB de memória partilhada, mais que suficiente para o modelo de 4,7 GB.

---

## A medição

`qwen2.5:7b-instruct-q4_K_M`, `threads=10`, prefill a frio forçado com nonce no
início do prompt de sistema, mediana de repetições. **A máquina estava mais fria
nesta medição (52–60 °C) do que nas medições de CPU de hoje**, o que favorece a
iGPU — e ela perde mesmo assim no decode.

### Prefill: a iGPU ganha por 5 a 6 vezes

| persona | tokens | CPU | iGPU | razão |
|---|---|---|---|---|
| pt Caeiro | 421 | 34,3 s = 14,2 tok/s | **5,5 s = 89,1 tok/s** | **6,28x** |
| en Search | 360 | 25,2 s = 16,6 tok/s | **4,9 s = 85,8 tok/s** | **5,20x** |

### Decode: a iGPU perde por quase metade

| | tok/s |
|---|---|
| CPU (medido hoje, várias corridas) | 5,2 – 7,1 |
| **iGPU** (mediana de 3, intervalo 3,24–3,35) | **3,30** |

Razão: **0,55x**.

É o padrão esperado quando se olha para ele: o prefill é compute-bound e
paralelo, onde a GPU brilha; o decode é sequencial e limitado por **largura de
banda de memória**, que uma iGPU **partilha com a CPU** e ainda paga transferência
por cima.

---

## A conclusão depende de qual pergunta é

Para uma resposta típica — ~700 tokens de prompt, ~150 de saída:

| | prefill | decode | total |
|---|---|---|---|
| CPU, **1.ª pergunta** da voz | 49,3 s | 25,0 s | **74,3 s** |
| iGPU, **1.ª pergunta** da voz | **7,9 s** | 45,4 s | **53,3 s** ✅ |
| CPU, **seguintes** | 0,7 s | 25,0 s | **25,7 s** ✅ |
| iGPU, **seguintes** | 0,7 s | 45,4 s | 46,1 s |

**A iGPU ganha 21 s na primeira pergunta de cada voz e perde 20 s em todas as
outras.**

Como o `keep_alive` mantém o prefixo em cache e a persona é prefixo estável, a
esmagadora maioria das perguntas numa conversa é «seguinte». **A CPU é a escolha
certa para esta carga** — e é por isso que o Ollama desliga a iGPU por omissão.

---

## O que isto corrige, e o que não

**Corrige a premissa.** A conclusão certa não é «sem GPU»: é «**com uma iGPU que
acelera o prefill 6x e trava o decode para metade**». Isso atravessa quatro fases
de documentação e está agora referenciado nelas.

**Não corrige nenhuma decisão de arquitectura.** O orçamento de 300 tokens, os
~30 s por resposta e a rejeição do contexto de 1500 tokens continuam válidos,
porque na carga real o decode domina e a iGPU piora-o.

**Mas reabre uma porta que eu tinha fechado.** A Fase 0 rejeitou o contexto de
1500 tokens por causa dos 84 s de prefill. Na iGPU seriam **~17 s**. Se o
contexto voltar a ser o constrangimento — por exemplo se a pergunta aberta sobre
a voz exigir mais poemas no prompt — a iGPU torna-o viável: o **contexto deixa de
custar quase nada, e é a saída que fica caro**.

Há aqui um desenho que nenhuma fase considerou: **prefill na iGPU, decode na
CPU**. O Ollama não o oferece, mas o `llama.cpp` tem controlo por camada
(`--n-gpu-layers`) e a repartição é mensurável. Não foi tentado.

---

## Como reproduzir

```bash
OLLAMA_IGPU_ENABLE=1 ~/.local/ollama/bin/ollama serve &
```

O log confirma com `type=iGPU` na linha `inference compute`. Sem a variável, a
mesma linha diz `id=cpu library=cpu`.
