# Fase 0 — Medir antes de construir

Protocolo de execução da Fase 0 de [`PLANO-RAG-LOCAL.md`](PLANO-RAG-LOCAL.md).

**Propósito:** produzir evidência suficiente para decidir, com número e não com
suposição, (a) qual modelo de geração usar, (b) qual codificador de embeddings
usar, e (c) **se geração local é viável neste hardware**.

A Fase 0 tem autoridade para invalidar o resto do plano. Esse é o objetivo, não
um risco: descobrir em um dia que nenhum modelo local escreve verso aceitável em
português europeu poupa semanas de pipeline construído sobre areia.

**Nada é implementado nesta fase.** Nenhuma linha de `src/` é tocada.

---

## 0. Resumo executivo

| | |
|---|---|
| Duração | ~6–8 h de parede, das quais ~1–2 h são downloads sem supervisão |
| Entregáveis | 4 ficheiros em `docs/fase-0/`, todos versionados |
| Decisões que fecham | modelo de geração, nº de threads, codificador, viável-ou-não |
| Pré-requisito | nenhum |
| Risco de desperdício | nulo — as medições servem a qualquer caminho que o projeto tome |

Ordem de execução, com os tempos de espera já intercalados:

```
Passo 1  ambiente Python                      ~30 min
Passo 2  Ollama + download dos modelos        ~20 min + espera
Passo 3  calibrar a máquina p/ medir          ~15 min
Passo 4  benchmark de geração                 ~90 min
Passo 5  teste de voz                          ~60 min + avaliação à mão
Passo 6  benchmark de codificadores           ~90 min
Passo 7  decisão e registo                    ~45 min
```

---

## 1. Passo 1 — Ambiente Python

O `python3` do sistema é 3.14.4 e não tem wheels de torch. O alvo é 3.12,
que já está instalado em `/usr/bin/python3.12`. O `uv` também já está disponível.

```bash
cd /home/mpb/Documents/GitHub/conversando_com_pessoa
uv venv --python 3.12 .venv
source .venv/bin/activate
python --version   # deve imprimir 3.12.x
```

Instalar o torch **na variante CPU explícita**. Sem isto, o `pip` traz as
bibliotecas CUDA — cerca de 2,5 GB de ficheiros que nunca serão usados, porque
não há GPU NVIDIA nesta máquina:

```bash
uv pip install torch --index-url https://download.pytorch.org/whl/cpu
uv pip install sentence-transformers numpy requests
```

### Verificação de aceite do Passo 1

```bash
python - <<'PY'
import sys, torch, sentence_transformers as st, numpy
print("python     ", sys.version.split()[0])
print("torch      ", torch.__version__, "| cuda:", torch.cuda.is_available())
print("st         ", st.__version__)
print("numpy      ", numpy.__version__)
print("threads    ", torch.get_num_threads())
assert sys.version_info[:2] == (3, 12), "venv não é 3.12"
assert not torch.cuda.is_available(), "cuda inesperadamente disponível"
print("OK")
PY
```

`torch.cuda.is_available()` **deve** ser `False`. Se for `True`, algo está
errado no diagnóstico de hardware e todo este plano precisa ser revisto.

Registar a saída em `docs/fase-0/01-ambiente.txt`.

---

## 2. Passo 2 — Ollama e modelos

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama --version
```

> O comando acima descarrega e executa um script de instalação. É o método
> oficial do projeto, mas é prudente inspecioná-lo antes de correr:
> `curl -fsSL https://ollama.com/install.sh | less`. Alternativa sem script:
> o tarball em <https://github.com/ollama/ollama/releases>.

Modelos a descarregar. **Três**, não dois: um 7B para qualidade, um 4B para
velocidade, e um terceiro 7–8B de família diferente, porque capacidade em
português europeu varia mais entre famílias do que entre tamanhos:

```bash
ollama pull qwen2.5:7b-instruct-q4_K_M     # ~4,7 GB
ollama pull gemma2:9b-instruct-q4_K_M      # ~5,8 GB  (opcional, se houver tempo)
ollama pull llama3.1:8b-instruct-q4_K_M    # ~4,9 GB
ollama pull qwen2.5:3b-instruct-q4_K_M     # ~2,0 GB
```

Se algum nome de tag falhar, procurar o correto em <https://ollama.com/library> —
as tags mudam. Confirmar o que ficou instalado e o tamanho real em disco:

```bash
ollama list
du -sh ~/.ollama/models
```

Registar em `docs/fase-0/02-modelos.txt`.

---

## 3. Passo 3 — Calibrar a máquina para medir

**Este passo é o que separa uma medição de um palpite com casas decimais.**

O Core Ultra 5 135U é um chip de 15–28 W com três tipos de núcleo. Duas coisas
contaminam qualquer benchmark feito sem cuidado.

### 3.1 Os núcleos não são iguais

Topologia medida nesta máquina:

| CPUs | Tipo | Núcleos | Máx MHz |
|---|---|---|---|
| 0–3 | **P-core** (com SMT) | 2 | 4400 |
| 4–11 | **E-core** | 8 | 3600 |
| 12–13 | **LP-E-core** | 2 | **2100** |

O llama.cpp sincroniza os threads a cada camada. Isso significa que **o thread
mais lento dita o ritmo de todos** — incluir os dois LP-E-cores de 2100 MHz na
conta pode tornar a inferência mais lenta do que usar menos threads.

Por isso o número de threads é um parâmetro **a medir**, não a assumir. O Passo 4
testa 4, 6, 8 e 10. Nunca 14.

Para garantir que os LP-E ficam fora, as corridas usam `taskset -c 0-11`.

### 3.2 A máquina acelera e desacelera

Estado observado: governor `powersave`, EPP `performance`, perfil `performance`,
na tomada, escala a 69% do máximo.

Antes de cada sessão de medição:

```bash
# na tomada, obrigatoriamente
cat /sys/class/power_supply/A*/online        # deve ser 1

# perfil de energia no máximo
powerprofilesctl set performance 2>/dev/null; powerprofilesctl get

# registar o estado, para constar no relatório
lscpu | grep -E 'scaling MHz|max MHz'
sensors 2>/dev/null | grep -iE 'package|core 0' || true
```

Regras da sessão de medição:

- **Fechar tudo o resto.** Navegador, IDE, contentores. Um Chrome com vinte abas
  consome os mesmos núcleos.
- **60 segundos de pausa** entre configurações, para o chip arrefecer.
- **Uma corrida de aquecimento descartada**, depois **3 corridas medidas**,
  reportar a **mediana**.
- Se as 3 corridas mostrarem tok/s em queda monotónica, isso **é** o sinal de
  throttling térmico. Registar o facto em vez de tirar a média e esconder.

Registar o estado inicial em `docs/fase-0/03-calibracao.txt`.

---

## 4. Passo 4 — Benchmark de geração

### 4.1 O que medir, e por que separado

O Ollama devolve, em cada resposta da API, os contadores que separam as duas
fases da inferência:

| Campo | Significado |
|---|---|
| `prompt_eval_count` / `prompt_eval_duration` | **prefill** — ler o prompt |
| `eval_count` / `eval_duration` | **decode** — escrever a resposta |
| `load_duration` | carregar o modelo (descartar após aquecimento) |

Durações vêm em **nanossegundos**.

Medir as duas separadamente não é preciosismo: o plano (§1.1) prevê que **o
prefill domine a espera**, porque o contexto RAG é 10× maior que a resposta. Se
isso se confirmar, a consequência de projeto é grande — vale mais encurtar o
contexto do que acelerar a escrita. Se não se confirmar, o plano precisa de
correção. Esta é a medição que decide.

### 4.2 Prompts de teste, construídos do corpus real

Prompts sintéticos de enchimento dariam contagens de token irrealistas: o
tokenizador parte português europeu com ortografia de época de forma diferente de
texto neutro. Os prompts saem do próprio corpus.

```bash
mkdir -p docs/fase-0
python - <<'PY'
import os, json, glob
# Monta prompts de ~500, ~1500 e ~3000 tokens a partir de poemas reais.
# Aproximação de 1,45 token/palavra (medida no corpus, ver PLANO §1.3).
poems = []
for f in sorted(glob.glob("data/pessoa_poems/*.txt")):
    t = open(f, encoding="utf-8").read()
    poems.append(t.strip())

def build(target_tokens):
    out, tok = [], 0
    for p in poems:
        n = int(len(p.split()) * 1.45)
        if tok + n > target_tokens:
            continue
        out.append(p); tok += n
        if tok >= target_tokens * 0.95:
            break
    return "\n---\n".join(out), tok

prompts = {}
for target in (500, 1500, 3000):
    body, tok = build(target)
    prompts[str(target)] = (
        "Leia os poemas abaixo e responda à pergunta em verso.\n\n"
        "Pergunta: O que é a saudade?\n\n"
        f"Poemas:\n{body}\n\nResposta em verso:"
    )
    print(f"alvo {target}: ~{tok} tokens estimados, {len(prompts[str(target)])} chars")

json.dump(prompts, open("docs/fase-0/prompts-bench.json", "w"), ensure_ascii=False, indent=1)
print("escrito docs/fase-0/prompts-bench.json")
PY
```

A estimativa de 1,45 token/palavra é aproximada; o `prompt_eval_count` devolvido
pelo Ollama é a contagem **real**, e é essa que entra no relatório.

### 4.3 O script de benchmark

Guardar como `docs/fase-0/bench_geracao.py`:

```python
"""Mede prefill e decode por modelo x tamanho de prompt x nº de threads."""
import json, statistics, subprocess, sys, time
import requests

URL = "http://127.0.0.1:11434/api/generate"
PROMPTS = json.load(open("docs/fase-0/prompts-bench.json"))

MODELS = [
    "qwen2.5:3b-instruct-q4_K_M",
    "qwen2.5:7b-instruct-q4_K_M",
    "llama3.1:8b-instruct-q4_K_M",
]
THREADS = [4, 6, 8, 10]       # nunca 14: exclui os LP-E de 2100 MHz
SIZES = ["500", "1500", "3000"]
NUM_PREDICT = 200             # comprimento realista de um poema
REPS = 3
COOLDOWN = 60                 # segundos entre configuracoes

def run(model, prompt, threads):
    r = requests.post(URL, json={
        "model": model,
        "prompt": prompt,
        "stream": False,
        "keep_alive": "10m",
        "options": {
            "num_thread": threads,
            "num_predict": NUM_PREDICT,
            "temperature": 0.8,
            "top_p": 0.9,
            "seed": 42,
        },
    }, timeout=1800)
    r.raise_for_status()
    d = r.json()
    pe_n, pe_t = d.get("prompt_eval_count", 0), d.get("prompt_eval_duration", 1)
    ev_n, ev_t = d.get("eval_count", 0), d.get("eval_duration", 1)
    return {
        "prefill_tokens": pe_n,
        "prefill_s": pe_t / 1e9,
        "prefill_tps": pe_n / (pe_t / 1e9) if pe_t else 0,
        "decode_tokens": ev_n,
        "decode_s": ev_t / 1e9,
        "decode_tps": ev_n / (ev_t / 1e9) if ev_t else 0,
        "total_s": d.get("total_duration", 0) / 1e9,
        "response": d.get("response", ""),
    }

results = []
for model in MODELS:
    for threads in THREADS:
        for size in SIZES:
            prompt = PROMPTS[size]
            print(f"\n>>> {model} | threads={threads} | prompt={size}", flush=True)
            run(model, prompt, threads)              # aquecimento, descartado
            reps = []
            for i in range(REPS):
                m = run(model, prompt, threads)
                reps.append(m)
                print(f"    rep{i+1}: prefill {m['prefill_tps']:6.1f} tok/s "
                      f"({m['prefill_s']:5.1f}s, {m['prefill_tokens']} tok) | "
                      f"decode {m['decode_tps']:5.1f} tok/s | "
                      f"total {m['total_s']:6.1f}s", flush=True)
            pre = [r["prefill_tps"] for r in reps]
            dec = [r["decode_tps"] for r in reps]
            # queda monotonica entre reps = sinal de throttling termico
            drift = all(pre[i] > pre[i+1] for i in range(len(pre)-1))
            results.append({
                "model": model, "threads": threads, "prompt_size": size,
                "prefill_tokens_real": reps[0]["prefill_tokens"],
                "prefill_tps_median": statistics.median(pre),
                "decode_tps_median": statistics.median(dec),
                "prefill_s_median": statistics.median(r["prefill_s"] for r in reps),
                "total_s_median": statistics.median(r["total_s"] for r in reps),
                "throttling_suspeito": drift,
                "amostra_resposta": reps[-1]["response"][:400],
            })
            json.dump(results, open("docs/fase-0/04-bench-geracao.json", "w"),
                      ensure_ascii=False, indent=1)
            time.sleep(COOLDOWN)

print("\n=== RESUMO (mediana de 3) ===")
print(f"{'modelo':34s} {'thr':>4s} {'prompt':>7s} {'prefill':>9s} {'decode':>8s} {'total':>7s}")
for r in results:
    flag = " !throttle" if r["throttling_suspeito"] else ""
    print(f"{r['model']:34s} {r['threads']:4d} {r['prompt_size']:>7s} "
          f"{r['prefill_tps_median']:7.1f}/s {r['decode_tps_median']:6.1f}/s "
          f"{r['total_s_median']:6.1f}s{flag}")
```

Correr com os LP-E-cores excluídos:

```bash
source .venv/bin/activate
taskset -c 0-11 python docs/fase-0/bench_geracao.py | tee docs/fase-0/04-bench-geracao.log
```

São 3 modelos × 4 contagens de thread × 3 tamanhos = 36 configurações, com
aquecimento, 3 repetições e 60 s de pausa. **Conte ~90 min.** Deixe correr sem
usar a máquina.

> Se `num_thread` não alterar os resultados, a opção pode ter mudado de nome na
> versão instalada do Ollama. Confirme em <https://docs.ollama.com/api> e, em
> último recurso, varie os threads por fora com `taskset -c 0-3`, `0-7`, `0-11`.

### 4.4 Aceite do Passo 4

Uma tabela com prefill tok/s, decode tok/s e tempo total por configuração, e a
melhor contagem de threads identificada por modelo. Mais: confirmação ou
refutação da previsão do plano de que o prefill domina.

---

## 5. Passo 5 — Teste de voz

**A medição mais importante da Fase 0**, e a única que não é automatizável.

Sem RAG. Sem contexto. O objetivo é isolar uma pergunta: *este modelo consegue
escrever verso em português europeu na voz de um heterónimo?* Se não conseguir
sem contexto, o RAG não o salva — RAG fornece material, não competência poética.

### 5.1 Os cinco prompts

Guardar como `docs/fase-0/prompts-voz.json`. Cada um testa uma coisa diferente:

| # | Voz | O que testa |
|---|---|---|
| 1 | Alberto Caeiro | verso livre curto, olhar sem metafísica |
| 2 | Álvaro de Campos | versículo longo, vertigem urbana |
| 3 | Ricardo Reis | ode curta, registo clássico, metro regular |
| 4 | Ortónimo | metro e rima, fragmentação do eu |
| 5 | — | **armadilha de PT-BR**: pede tratamento por *tu* e segunda pessoa |

```json
{
 "1_caeiro": "Escreve um poema curto, em português europeu, na voz de Alberto Caeiro, heterónimo de Fernando Pessoa. Caeiro olha as coisas sem lhes atribuir significado oculto: vê o que está lá. Verso livre, sem rima, sem filosofia. Tema: uma árvore ao fim da tarde. Responde apenas com o poema.",
 "2_campos": "Escreve um poema em português europeu na voz de Álvaro de Campos, heterónimo de Fernando Pessoa. Campos escreve em versículo longo, acumulativo, com vertigem e excesso. Tema: a cidade ao amanhecer e a angústia de existir. Responde apenas com o poema.",
 "3_reis": "Escreve uma ode breve em português europeu na voz de Ricardo Reis, heterónimo de Fernando Pessoa. Reis é estóico, epicurista contido, de dicção clássica e latinizante, em estrofes curtas e regulares. Tema: a brevidade da vida e a recusa de a temer. Responde apenas com o poema.",
 "4_ortonimo": "Escreve um poema em português europeu na voz de Fernando Pessoa ele mesmo. Metro regular, com rima. Tema: não saber quem se é, e fingir. Responde apenas com o poema.",
 "5_pt_pt": "Escreve um poema curto em português europeu de Portugal, não do Brasil. Trata o leitor por «tu». Tema: a saudade de algo que nunca aconteceu. Responde apenas com o poema."
}
```

### 5.2 Execução

Guardar como `docs/fase-0/teste_voz.py`:

```python
"""Gera as amostras de voz, sem RAG, e grava tudo cru em markdown."""
import json, requests, datetime

URL = "http://127.0.0.1:11434/api/generate"
PROMPTS = json.load(open("docs/fase-0/prompts-voz.json"))
MODELS = [
    "qwen2.5:3b-instruct-q4_K_M",
    "qwen2.5:7b-instruct-q4_K_M",
    "llama3.1:8b-instruct-q4_K_M",
]
BEST_THREADS = 8      # <- substituir pelo vencedor do Passo 4
N_AMOSTRAS = 2        # duas por prompt: mostra a variabilidade

out = ["# Fase 0 — teste de voz (sem RAG)",
       f"\nGerado em {datetime.date.today().isoformat()}  ",
       f"threads={BEST_THREADS}, temperature=0.9, top_p=0.9\n",
       "\n> Saídas **cruas**, sem edição nem selecção. "
       "Avaliar pela rubrica de §5.3.\n"]

for model in MODELS:
    out.append(f"\n---\n\n## {model}\n")
    for key, prompt in PROMPTS.items():
        out.append(f"\n### {key}\n")
        for i in range(N_AMOSTRAS):
            r = requests.post(URL, json={
                "model": model, "prompt": prompt, "stream": False,
                "keep_alive": "10m",
                "options": {"num_thread": BEST_THREADS, "num_predict": 300,
                            "temperature": 0.9, "top_p": 0.9, "seed": 1000 + i},
            }, timeout=1800)
            r.raise_for_status()
            d = r.json()
            secs = d.get("total_duration", 0) / 1e9
            out.append(f"\n**amostra {i+1}** ({secs:.0f}s)\n")
            out.append("```\n" + d.get("response", "").strip() + "\n```\n")
            print(f"{model} {key} #{i+1} — {secs:.0f}s", flush=True)

open("docs/fase-0/05-teste-voz.md", "w", encoding="utf-8").writelines(out)
print("escrito docs/fase-0/05-teste-voz.md")
```

```bash
taskset -c 0-11 python docs/fase-0/teste_voz.py
```

30 gerações. ~45–60 min.

### 5.3 Rubrica de avaliação — à mão, por você

A rubrica da §6.2 do plano, aplicada a cada amostra. **0 a 2 por critério,
máximo 10.**

| Critério | 0 | 1 | 2 |
|---|---|---|---|
| **É verso?** | prosa corrida | linhas quebradas mas sem ritmo | verso com quebra deliberada |
| **Português europeu?** | PT-BR claro (gerúndio, «você», léxico BR) | misturado | PT-PT consistente |
| **A voz pedida?** | genérico ou outro heterónimo | traços vagos | reconhecivelmente aquela voz |
| **Cumpre a forma?** | ignora (ex. Reis em verso livre) | parcial | respeita a forma pedida |
| **Vale como poema?** | sem sentido ou clichê de IA | passável | tem imagem própria |

Pontue **sem olhar o nome do modelo**, se conseguir. Registe os números e uma
frase de justificação por amostra em `docs/fase-0/05-avaliacao-voz.md`.

> Esta é a única parte da Fase 0 que depende de julgamento humano, e é
> deliberado. Não há métrica automática que distinga Ricardo Reis de um pastiche
> de Ricardo Reis. Você é o instrumento de medida aqui — e como só há um
> avaliador, as notas são uma leitura informada, não uma medição
> intersubjectiva. Está bom: a decisão que elas suportam é binária e grosseira.

---

## 6. Passo 6 — Benchmark de codificadores

### 6.1 O que esta medição é e não é

**Não é** uma avaliação de qualidade de recuperação. Isso exige o conjunto
dourado de 40–60 perguntas da §6.1 do plano, que é entregável da Fase 1.

**É** duas coisas mais modestas e ainda assim decisivas:

1. **Custo operacional** — tempo de carga, throughput de embedding sobre os 2083
   poemas, RAM, dimensão, tamanho do índice.
2. **Teste de fumo** — ~12 pares pergunta→poema escritos à mão, suficientes para
   apanhar um codificador catastroficamente inadequado. Era isto que teria
   apanhado o `all-MiniLM-L6-v2` monolíngue inglês no primeiro dia.

### 6.2 Os candidatos

| Modelo | Dim | Tamanho | Nota |
|---|---|---|---|
| `PORTULAN/serafim-335m-portuguese-pt-sentence-encoder-ir` | 1024 | ~1,3 GB | específico de PT, variante para recuperação |
| `intfloat/multilingual-e5-base` | 768 | ~1,1 GB | **exige prefixos** `query: ` / `passage: ` |
| `BAAI/bge-m3` | 1024 | ~2,2 GB | o mais forte, o mais pesado |
| `paraphrase-multilingual-MiniLM-L12-v2` | 384 | ~470 MB | linha de base actual no código |
| `all-MiniLM-L6-v2` | 384 | ~90 MB | **controlo negativo** — inglês, deve falhar |

Incluir o `all-MiniLM-L6-v2` é intencional: um teste que não reprova o
codificador que sabemos estar errado não está a medir nada. É o controlo.

### 6.3 Construir o conjunto de fumo

Precisa de ~12 pares. Escolha poemas que **conhece** e escreva perguntas que
**não reutilizem as palavras do poema** — senão está a testar BM25, não embeddings.

Para encontrar candidatos por tema:

```bash
grep -ril "saudade" data/pessoa_poems/ | head -5
grep -ril "tabacaria\|cais\|navio" data/pessoa_poems/ | head -5
grep -l "^Ricardo Reis" data/pessoa_poems/*.txt | head -5
```

Três exemplos já verificados neste corpus, para arrancar:

```json
[
 {"q": "há uma voz no mar que nos fala de um lugar que não existe",
  "esperado": ["poem_100"],
  "nota": "AS ILHAS AFORTUNADAS"},
 {"q": "o amor fez-me ver melhor a natureza, não me afastou dela",
  "esperado": ["poem_1000"],
  "nota": "Caeiro, 'Quando eu não te tinha'"},
 {"q": "a chegada de um paquete ao cais desperta em mim um desejo de partir",
  "esperado": ["poem_135"],
  "nota": "Campos, ODE MARÍTIMA"}
]
```

Complete até 12 em `docs/fase-0/smoke-set.json`, cobrindo as quatro vozes
principais. **Reserve 40 min para isto** — é trabalho de leitura, e é o que dá
valor ao passo. Estes 12 pares são também a semente do conjunto dourado da
Fase 1, portanto o esforço não se perde.

### 6.4 O script

Guardar como `docs/fase-0/bench_encoders.py`:

```python
"""Custo operacional + teste de fumo de recuperação, por codificador."""
import glob, json, os, time, resource
import numpy as np
from sentence_transformers import SentenceTransformer

CANDIDATOS = [
    ("PORTULAN/serafim-335m-portuguese-pt-sentence-encoder-ir", None),
    ("intfloat/multilingual-e5-base", "e5"),
    ("BAAI/bge-m3", None),
    ("paraphrase-multilingual-MiniLM-L12-v2", None),
    ("all-MiniLM-L6-v2", None),          # controlo negativo
]
SMOKE = json.load(open("docs/fase-0/smoke-set.json"))

# corpus: id -> texto (cabecalho incluido, como no codigo actual)
ids, textos = [], []
for f in sorted(glob.glob("data/pessoa_poems/*.txt")):
    ids.append(os.path.basename(f)[:-4])
    textos.append(open(f, encoding="utf-8").read().strip())
print(f"corpus: {len(ids)} poemas")

def prep(xs, kind, modo):
    if modo == "e5":                      # e5 exige prefixos, sem eles degrada em silencio
        p = "query: " if kind == "q" else "passage: "
        return [p + x for x in xs]
    return xs

relatorio = []
for nome, modo in CANDIDATOS:
    print(f"\n>>> {nome}")
    rss0 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    t0 = time.perf_counter()
    try:
        m = SentenceTransformer(nome)
    except Exception as e:
        print(f"    FALHOU ao carregar: {e}")
        relatorio.append({"modelo": nome, "erro": str(e)[:200]})
        continue
    t_load = time.perf_counter() - t0
    dim = m.get_sentence_embedding_dimension()

    t0 = time.perf_counter()
    emb = m.encode(prep(textos, "p", modo), convert_to_numpy=True,
                   batch_size=16, show_progress_bar=True)
    t_emb = time.perf_counter() - t0
    emb = np.asarray(emb, dtype="float32")
    emb /= np.linalg.norm(emb, axis=1, keepdims=True)

    qs = [s["q"] for s in SMOKE]
    qe = m.encode(prep(qs, "q", modo), convert_to_numpy=True)
    qe = np.asarray(qe, dtype="float32")
    qe /= np.linalg.norm(qe, axis=1, keepdims=True)

    sims = qe @ emb.T
    ordem = np.argsort(-sims, axis=1)
    r1 = r5 = r10 = 0
    detalhe = []
    for i, s in enumerate(SMOKE):
        esperados = set(s["esperado"])
        top = [ids[j] for j in ordem[i][:10]]
        pos = next((k + 1 for k, t in enumerate(top) if t in esperados), None)
        r1 += pos == 1
        r5 += bool(pos and pos <= 5)
        r10 += bool(pos and pos <= 10)
        detalhe.append({"q": s["q"][:60], "posicao": pos, "top3": top[:3]})

    n = len(SMOKE)
    rss = (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss - rss0) / 1024
    linha = {
        "modelo": nome, "dim": dim,
        "load_s": round(t_load, 1),
        "embed_corpus_s": round(t_emb, 1),
        "poemas_por_s": round(len(textos) / t_emb, 1),
        "rss_delta_mb": round(rss, 0),
        "indice_mb": round(emb.nbytes / 1e6, 1),
        "smoke_r1": f"{r1}/{n}", "smoke_r5": f"{r5}/{n}", "smoke_r10": f"{r10}/{n}",
        "detalhe": detalhe,
    }
    relatorio.append(linha)
    print(f"    dim={dim} load={t_load:.1f}s embed={t_emb:.1f}s "
          f"({len(textos)/t_emb:.1f} poemas/s) indice={emb.nbytes/1e6:.1f}MB")
    print(f"    fumo: R@1={r1}/{n} R@5={r5}/{n} R@10={r10}/{n}")
    del m, emb
    json.dump(relatorio, open("docs/fase-0/06-bench-encoders.json", "w"),
              ensure_ascii=False, indent=1)

print("\n=== RESUMO ===")
print(f"{'modelo':58s} {'dim':>5s} {'emb/s':>7s} {'R@1':>6s} {'R@5':>6s}")
for r in relatorio:
    if "erro" in r:
        print(f"{r['modelo']:58s}  ERRO"); continue
    print(f"{r['modelo']:58s} {r['dim']:5d} {r['poemas_por_s']:7.1f} "
          f"{r['smoke_r1']:>6s} {r['smoke_r5']:>6s}")
```

```bash
taskset -c 0-11 python docs/fase-0/bench_encoders.py | tee docs/fase-0/06-bench-encoders.log
```

~60–90 min, a maior parte em download e no `bge-m3`.

### 6.5 Aceite do Passo 6

- `all-MiniLM-L6-v2` tem de ficar **claramente pior** que os multilíngues. Se não
  ficar, o conjunto de fumo é mau (provavelmente as perguntas reutilizam palavras
  dos poemas) e precisa ser reescrito antes de se concluir qualquer coisa.
- Um vencedor provisório identificado, com custo operacional registado.

---

## 7. Passo 7 — Decisão

### 7.1 Orçamento de latência

Valores de referência para um chatbot de poesia. Um poeta pode demorar; um
programa que parece pendurado, não. **São juízos, não leis — ajuste-os:**

| | Alvo | Tolerável | Inutilizável |
|---|---|---|---|
| Prefill (1500 tok) | < 8 s | < 20 s | > 40 s |
| Resposta completa | < 20 s | < 45 s | > 90 s |

Com *streaming* na interface, o utilizador vê os primeiros versos durante o
decode — o que importa é o prefill, porque é a espera antes de qualquer sinal
de vida.

### 7.2 Portão de qualidade

Mediana da pontuação da rubrica (§5.3), sobre as 10 amostras do modelo:

| Mediana | Leitura | Consequência |
|---|---|---|
| **≥ 7/10** | voz local viável | seguir o plano; Fase 1 com este modelo |
| **4–6/10** | marginal | tentar 2–3 h de engenharia de prompt e reavaliar |
| **< 4/10** | inviável localmente | **parar** e ir para §7.4 |

Dois critérios eliminatórios, independentes da mediana:

- **Critério 2 (PT-PT) com 0 em mais de metade das amostras** → o modelo escreve
  em PT-BR. Prompt não corrige isto de forma fiável.
- **Critério 1 (é verso?) com 0 na maioria** → o modelo escreve prosa. Fatal.

### 7.3 Matriz de decisão

| Qualidade | Latência | Decisão |
|---|---|---|
| 7B passa | 7B tolerável | **7B local.** Seguir plano sem alteração |
| 7B passa | 7B inutilizável, 4B tolerável mas reprova qualidade | **geração remota** (§7.4), recuperação local |
| 7B e 4B passam | ambos toleráveis | **4B local**, 7B como opção de configuração |
| só 7B passa | 7B tolerável | 7B local, sem fallback leve |
| nenhum passa | — | **§7.4** |

### 7.4 Se a geração local não passar

Isto **não é falha do plano** — é o plano a funcionar. Custou um dia em vez de
três semanas.

A arquitectura sobrevive quase intacta, porque a geração está atrás de uma
interface (`Generator`, §3.3 do plano). O que muda:

- Toda a recuperação continua local: parsing, chunking, índice, BM25, rerank.
  É a maior parte do trabalho e do valor.
- A geração passa a `AnthropicRemote`. Custo estimado no plano (§8): **~0,018
  USD por pergunta** com RAG — cerca de 1,8 USD por cem perguntas.
- As Fases 1 a 4 ficam **inalteradas**. Só a Fase 5 sobe na ordem.
- Fica ainda a opção de voltar ao local mais tarde, com outro modelo ou outro
  hardware, sem reescrever nada.

Registe a decisão e a evidência que a sustenta. Uma decisão sem o rasto do
porquê é indistinguível de um palpite, três meses depois.

---

## 8. Entregáveis

Todos versionados em `docs/fase-0/`:

| Ficheiro | Conteúdo |
|---|---|
| `01-ambiente.txt` | versões, confirmação de que não há CUDA |
| `02-modelos.txt` | `ollama list`, tamanhos em disco |
| `03-calibracao.txt` | estado térmico e de energia da sessão |
| `04-bench-geracao.json` + `.log` | prefill/decode por modelo × threads × prompt |
| `05-teste-voz.md` | **30 saídas cruas**, sem edição |
| `05-avaliacao-voz.md` | rubrica preenchida à mão, com justificações |
| `06-bench-encoders.json` + `.log` | custo operacional e teste de fumo |
| `smoke-set.json` | os 12 pares — semente do conjunto dourado da Fase 1 |
| `RELATORIO.md` | **a decisão**, com as tabelas e o raciocínio |

Os três scripts (`bench_geracao.py`, `teste_voz.py`, `bench_encoders.py`) também
ficam versionados: a Fase 0 será repetida quando mudar de modelo ou de máquina.

### Nota sobre o que se compromete

As saídas cruas em `05-teste-voz.md` vão incluir tentativas falhadas, PT-BR
acidental e versos maus. **Comprometa-as assim mesmo.** É o registo de por que a
decisão foi tomada, e um `05-teste-voz.md` curado não serve para nada.

---

## 9. Riscos da própria Fase 0

| Risco | Sinal | Resposta |
|---|---|---|
| Medições contaminadas por throttling | tok/s em queda monotónica entre repetições | é o que a flag `throttling_suspeito` apanha; aumentar a pausa para 120 s e repetir a configuração afectada |
| Tags de modelo inexistentes no Ollama | `ollama pull` falha | procurar o nome actual em <https://ollama.com/library> |
| `num_thread` sem efeito | tok/s idêntico para 4 e 10 threads | variar por fora com `taskset -c 0-3` / `0-7` / `0-11` |
| Conjunto de fumo mau | controlo negativo não reprova | reescrever as perguntas sem reutilizar palavras dos poemas |
| Um só avaliador no teste de voz | — | limitação assumida (§5.3); a decisão que suporta é grosseira |
| Avaliar o próprio trabalho com viés | tendência a aprovar o modelo que se quer usar | pontuar sem ver o nome do modelo |
| `bge-m3` não cabe em memória | OOM | correr sozinho, com os outros descarregados |

---

## 10. Checklist

```
[ ] 1  venv 3.12 criado, torch CPU, cuda=False confirmado
[ ] 2  Ollama instalado, 3 modelos descarregados, tamanhos registados
[ ] 3  máquina na tomada, perfil performance, estado registado
[ ] 4  prompts-bench.json gerado do corpus real
[ ] 5  bench de geração corrido (36 configs), melhor nº de threads identificado
[ ] 6  prefill vs decode: previsão do plano confirmada ou refutada
[ ] 7  smoke-set.json com 12 pares escritos à mão
[ ] 8  teste de voz corrido, 30 amostras cruas comprometidas
[ ] 9  rubrica preenchida à mão, sem olhar o nome do modelo
[ ] 10 bench de encoders corrido, controlo negativo reprovado como esperado
[ ] 11 RELATORIO.md escrito com a decisão e a evidência
[ ] 12 PLANO-RAG-LOCAL.md actualizado onde a medição contrariou a estimativa
```

O item 12 é o que fecha o ciclo: a §1.1 do plano tem estimativas de tok/s
derivadas da largura de banda de memória, declaradas como estimativas. Depois da
Fase 0 passam a ser medições — ou são corrigidas.
