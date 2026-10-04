"""Corrige o critério 2: o piso de 0,50 era do dicionário, não das stopwords."""
import json, os, sys
sys.path.insert(0, "/home/mpb/Documents/GitHub/conversando_com_pessoa")
from src.corpus.models import Lang
from src.guard import brasileirismos, fracao_lingua, lingua_errada, _fracao_reconhecida

D = "/home/mpb/Documents/GitHub/conversando_com_pessoa/docs/fase-5"
chave = {x["id"]: x for x in json.load(open(f"{D}/01-chave.json"))["chave"]}
am = json.load(open(f"{D}/01-amostras.json"))

print("aspell disponível?", _fracao_reconhecida("uma árvore é uma árvore", Lang.PT))
for a in am["amostras"]:
    cru = chave[a["id"]]["texto_cru"]
    limpo = chave[a["id"]]["texto"]
    br = brasileirismos(cru)
    errada = lingua_errada(limpo, Lang.PT)
    dic = _fracao_reconhecida(limpo, Lang.PT)
    if errada or len(br) >= 2 or (dic is not None and dic < 0.50):
        c2 = 0
    elif len(br) == 1:
        c2 = 1
    else:
        c2 = 2
    a["c2_pt_corrigido"] = c2
    a["c2_pt_errado_piso050"] = a.pop("c2_pt")
    a["lingua_errada"] = errada
    a["fracao_dicionario"] = None if dic is None else round(dic, 3)
    a["c2_pt"] = c2

am["_meta"]["correccao_c2"] = (
    "O PISO_LINGUA=0,50 do harness era o MIN_FRACAO_DICIONARIO, que se aplica a "
    "`_fracao_reconhecida` (dicionário) e não a `fracao_lingua` (stopwords), cujo "
    "piso real é 0,12 em `lingua_errada`. Com o piso errado, 38 de 40 amostras "
    "falhavam. Valores antigos preservados em `c2_pt_errado_piso050`.")
json.dump(am, open(f"{D}/01-amostras.json", "w"), ensure_ascii=False, indent=1)

import statistics as st
v = [a["c2_pt"] for a in am["amostras"]]
o = [a["c2_pt_errado_piso050"] for a in am["amostras"]]
print(f"c2 corrigido: mediana {st.median(v)}  2s={v.count(2)} 1s={v.count(1)} 0s={v.count(0)}")
print(f"c2 com o piso errado: mediana {st.median(o)}  2s={o.count(2)} 1s={o.count(1)} 0s={o.count(0)}")
print("língua errada em:", [a["id"] for a in am["amostras"] if a["lingua_errada"]])
