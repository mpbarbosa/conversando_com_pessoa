"""Fase 1 / Passo 7 - calibracao do limiar de plagio.

Duas perguntas, uma corrida:

1. **Qual a distribuicao de fraccao copiada** em respostas reais? O limiar tem
   de sair dos dados: um limiar apertado com cópia generalizada significa
   regenerar quase sempre, a ~28s por tentativa.

2. **O reforco no prompt reduz a cópia?** Se nao reduzir, a logica de repeticao
   e inutil e precisa-se de outra estrategia.
"""
import json, os, sys, time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from transformers import AutoTokenizer

from src.corpus.build import load
from src.corpus.models import Voice
from src.generation.ollama import OllamaGenerator
from src.generation.prompt import montar
from src.guard import verificar
from src.plagio import REFORCO, analisar
from src.retrieval.encoder import Encoder
from src.retrieval.index import Index
from src.voices import persona

PERGUNTAS = {
    Voice.CAEIRO: ["Porque é que o fim do dia parece triste?",
                   "O que vês quando olhas para uma árvore?",
                   "A natureza tem algum sentido?",
                   "O que é pensar?", "Vale a pena recordar?",
                   "O que sentes ao ver o rio?"],
    Voice.CAMPOS: ["O que é a angústia de existir?",
                   "O que sentes na cidade ao amanhecer?",
                   "Porque é que queres partir?",
                   "O que é não ser nada?", "O que é o cansaço?",
                   "O que é a vertigem?"],
    Voice.REIS: ["A vida é breve?", "Devo temer a morte?",
                 "O que é a medida?", "O que é o destino?",
                 "Devo gozar o presente?", "O que são os deuses?"],
    Voice.ORTONIMO: ["Quem és tu?", "O que é fingir?",
                     "O que é o mistério?", "Onde foi a tua infância?",
                     "O que é sentir?", "O que é a saudade?"],
}

gen = OllamaGenerator()
if not gen.disponivel():
    print("Ollama em baixo"); sys.exit(1)

meta, chunks = load()
enc = Encoder()
idx = Index.load(chunks, enc, meta["assinatura"])
assert idx is not None, "indice recusado"
tq = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct")
n_tok = lambda t: len(tq(t, add_special_tokens=False).input_ids)

resultados = []
for voz, perguntas in PERGUNTAS.items():
    p_voz = persona(voz)
    print(f"\n{'='*74}\n### {voz.value}", flush=True)
    for q in perguntas:
        qv = enc.encode_queries([q])[0]
        recuperados = [c for c, _ in idx.search(qv, top_k=6, voz=voz)]
        p = montar(q, recuperados, p_voz, n_tok)

        r1 = gen.gerar(p.system, p.user)
        v1 = verificar(r1.texto)
        a1 = analisar(v1.texto, p.chunks_usados)

        linha = {
            "voz": voz.value, "pergunta": q,
            "n_contexto": len(p.chunks_usados),
            "tok_user": p.tokens_user,
            "t1_fracao": round(a1.fracao_copiada, 3),
            "t1_max_sim": a1.max_similaridade,
            "t1_n_versos": a1.n_versos,
            "t1_copiados": [[c.verso, c.similaridade, c.poema] for c in a1.copiados],
            "t1_guarda_ok": bool(v1),
            "t1_guarda_motivos": list(v1.motivos),
            "t1_texto": v1.texto,
            "t1_total_s": round(r1.total_s, 1),
        }
        print(f"  {q[:38]:40s} {a1.n_versos:2d}v  copiados {len(a1.copiados):2d} "
              f"({a1.fracao_copiada:5.0%})  max {a1.max_similaridade:.2f}  "
              f"{r1.total_s:5.1f}s", flush=True)

        # --- 2a tentativa com reforco, quando a 1a copiou muito ---
        if a1.fracao_copiada > 0.2:
            r2 = gen.gerar(p.system, p.user + REFORCO)
            v2 = verificar(r2.texto)
            a2 = analisar(v2.texto, p.chunks_usados)
            linha.update({
                "t2_fracao": round(a2.fracao_copiada, 3),
                "t2_max_sim": a2.max_similaridade,
                "t2_n_versos": a2.n_versos,
                "t2_texto": v2.texto,
                "t2_total_s": round(r2.total_s, 1),
            })
            delta = a2.fracao_copiada - a1.fracao_copiada
            print(f"    {'-> com reforço':40s} {a2.n_versos:2d}v  "
                  f"copiados {len(a2.copiados):2d} ({a2.fracao_copiada:5.0%})  "
                  f"max {a2.max_similaridade:.2f}  delta {delta:+.0%}", flush=True)

        resultados.append(linha)
        json.dump(resultados, open("docs/fase-1/07b-plagio-preventivo.json", "w"),
                  ensure_ascii=False, indent=1)

# --- distribuicao ---
import statistics as st
f1 = [r["t1_fracao"] for r in resultados]
print(f"\n\n{'='*74}\n=== DISTRIBUICAO DA FRACCAO COPIADA (1a tentativa, n={len(f1)}) ===")
print(f"  minimo {min(f1):.0%}  p25 {sorted(f1)[len(f1)//4]:.0%}  "
      f"mediana {st.median(f1):.0%}  p75 {sorted(f1)[3*len(f1)//4]:.0%}  "
      f"maximo {max(f1):.0%}")
for lim in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5):
    n = sum(1 for x in f1 if x > lim)
    print(f"  acima de {lim:.0%}: {n:2d}/{len(f1)} ({100*n/len(f1):3.0f}%) "
          f"-> regeneraria {n} vez(es)")

print(f"\n=== POR VOZ ===")
for voz in PERGUNTAS:
    xs = [r["t1_fracao"] for r in resultados if r["voz"] == voz.value]
    if xs:
        print(f"  {voz.value:10s} mediana {st.median(xs):5.0%}  "
              f"max {max(xs):5.0%}  n={len(xs)}")

com_reforco = [r for r in resultados if "t2_fracao" in r]
if com_reforco:
    print(f"\n=== EFEITO DO REFORCO (n={len(com_reforco)}) ===")
    antes = [r["t1_fracao"] for r in com_reforco]
    depois = [r["t2_fracao"] for r in com_reforco]
    print(f"  antes:  mediana {st.median(antes):.0%}  max {max(antes):.0%}")
    print(f"  depois: mediana {st.median(depois):.0%}  max {max(depois):.0%}")
    melhorou = sum(1 for a, b in zip(antes, depois) if b < a)
    print(f"  melhorou em {melhorou}/{len(com_reforco)}  "
          f"piorou em {sum(1 for a,b in zip(antes,depois) if b > a)}")
