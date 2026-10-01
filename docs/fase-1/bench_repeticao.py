"""Mede se tirar o poema copiado do contexto evita a reincidência.

Observado a correr o chatbot, à pergunta «você conhece o senhor fernando
pessoa?»: a 1.ª tentativa copiou 9/14 versos do `poem_1164` por substituição de
palavras, e a repetição — mesmo contexto, mais o REFORCO — voltou ao MESMO
poema (5/14). O utilizador interrompeu à segunda rejeição.

Desenho, à segunda tentativa. A primeira condicionava tudo a **re-observar** o
plágio na 1.ª tentativa, e isso falhou: em 3 perguntas, 0 plagiaram — incluindo
a pergunta que plagiou no terminal, com o mesmo `poem_1164` no contexto. Com
temperatura 0,9 e sem semente, o plágio é estocástico, e condicionar a medição a
um evento raro é desperdiçar gerações.

O ponto de partida é **dado pela observação**, não reproduzido: sabe-se que o
modelo copiou do `poem_1164`. Só as repetições correm, N vezes em cada política,
sobre esse mesmo ponto.

  A (antes) repetição com o MESMO contexto + REFORCO
  B (agora) repetição SEM os poemas copiados + REFORCO
"""
import json, os, sys, time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.corpus.models import Lang, Voice
from src.generation.ollama import OllamaGenerator
from src.generation.prompt import montar
from src.guard import verificar
from src.pipeline import Pipeline
from src.plagio import REFORCO, analisar
from src.retrieval.encoder import Encoder
from src.retrieval.index import Index
from src.tokens import contador
from src.voices import persona

N = 5

#: (pergunta, voz, poemas de que o modelo copiou na 1.ª tentativa).
#: O terceiro elemento vem de OBSERVAÇÃO, não de nova geração: na sessão do
#: utilizador, a esta pergunta, 9 de 14 versos vieram do `poem_1164` — um deles
#: à letra — por substituição de palavras (`Natureza`→`Silêncio`,
#: `brisa`→`luz`, `perceber`→`escutar`).
CASOS = [
    ("você conhece o senhor fernando pessoa?", Voice.CAEIRO, {"poem_1164"}),
]

print("a carregar corpus, encoder e índice...", flush=True)
from src.corpus.build import load as carregar_corpus
meta, chunks = carregar_corpus()
enc = Encoder()
idx = Index.load(chunks, enc, meta["assinatura"])
assert idx is not None, "índice ausente ou desactualizado; corre o CLI primeiro"
gen = OllamaGenerator()
assert gen.disponivel(), "ollama não responde"
# Contador do gerador, não do encoder: o qwen conta ~17% mais em português.
pipe = Pipeline(idx, enc, gen, contador("Qwen/Qwen2.5-7B-Instruct"))
print("pronto\n", flush=True)


def gerar(system, user):
    r = pipe.gerador.gerar(system, user)
    return r


def avaliar(texto, pergunta, mostrados, idioma=Lang.PT):
    v = verificar(texto, pergunta=pergunta, idioma=idioma)
    return analisar(v.texto, tuple(mostrados))


resultados = []
for pergunta, voz, copiados in CASOS:
    print("=" * 74)
    print(f">>> {pergunta}")
    print(f"    ponto de partida (observado): copiou de {', '.join(sorted(copiados))}",
          flush=True)
    recuperados, _ = pipe.recuperar(pergunta, voz)
    pA = montar(pergunta, recuperados, persona(voz), pipe.n_tokens)
    restantes = [c for c in recuperados if c.poem_id not in copiados]
    pB = montar(pergunta, restantes, persona(voz), pipe.n_tokens) if restantes else pA
    idsA = [c.poem_id for c in pA.chunks_usados]
    idsB = [c.poem_id for c in pB.chunks_usados]
    print(f"    A (antes): contexto {', '.join(idsA)}")
    print(f"    B (agora): contexto {', '.join(idsB)}", flush=True)
    if idsA == idsB:
        print("    !! os contextos são iguais: a política não muda nada aqui")

    # Contra tudo o que foi mostrado: tirar um poema do prompt não torna
    # aceitável devolvê-lo ao utilizador.
    mostrados = list(pA.chunks_usados) + [c for c in pB.chunks_usados
                                          if c not in pA.chunks_usados]

    linha = {"pergunta": pergunta, "copiados_observados": sorted(copiados),
             "contexto_a": idsA, "contexto_b": idsB, "A": [], "B": []}
    for politica, prompt in (("A", pA), ("B", pB)):
        for rep in range(N):
            t0 = time.perf_counter()
            r = gerar(prompt.system, prompt.user + REFORCO)
            a = avaliar(r.texto, pergunta, mostrados)
            poemas = sorted({x.poema for x in a.copiados})
            mesmos = sorted(set(poemas) & copiados)
            linha[politica].append({
                "plagiou": a.plagiou, "frac": round(a.fracao_copiada, 3),
                "max": round(a.max_similaridade, 3), "poemas": poemas,
                "reincidiu": bool(mesmos), "truncada": r.truncada,
                "s": round(time.perf_counter() - t0, 1),
            })
            print(f"    {politica} rep{rep+1} ({time.perf_counter()-t0:4.0f}s): "
                  f"{a.resumo():48s}"
                  f"{'  REINCIDIU em ' + ','.join(mesmos) if mesmos else ''}",
                  flush=True)
    resultados.append(linha)
    json.dump(resultados, open("docs/fase-1/09-repeticao.json", "w"),
              ensure_ascii=False, indent=1)
    print(flush=True)

print("=" * 74)
print("=== RESUMO ===")
print(f"{'política':9s} {'plagiou':>9s} {'reincidiu':>10s} {'fracção média':>14s} "
      f"{'máx média':>10s}")
for pol in ("A", "B"):
    e = [x for c in resultados for x in c[pol]]
    if not e:
        continue
    print(f"{pol:9s} {sum(x['plagiou'] for x in e):4d}/{len(e):<4d} "
          f"{sum(x['reincidiu'] for x in e):5d}/{len(e):<4d} "
          f"{sum(x['frac'] for x in e)/len(e):14.3f} "
          f"{sum(x['max'] for x in e)/len(e):10.3f}")
print("\n  A = repetição com o mesmo contexto (comportamento antigo)")
print("  B = repetição sem os poemas copiados (comportamento novo)")
json.dump(resultados, open("docs/fase-1/09-repeticao.json", "w"),
          ensure_ascii=False, indent=1)
print("\n-> docs/fase-1/09-repeticao.json")
