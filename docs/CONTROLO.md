# Documento de controlo — PessoaBot

Estado do projecto, decisões tomadas, correcções feitas e próximos passos.
**Actualizado em 2026-10-18.**

Este é o índice-mestre. Os detalhes estão nos documentos por fase; aqui está o
que está feito, o que falta, e o que mudou de ideias pelo caminho.

---

## 1. Objectivo

Chatbot que responde **em verso**, na voz de Fernando Pessoa ou de um
heterónimo, fundamentado por RAG sobre 2083 poemas. Execução **local** nesta
máquina, com a camada de geração plugável para permitir uma fase remota depois.

> O `ROADMAP.md` descreve o objectivo **anterior** do repositório — um chatbot
> CLI com RAG e um modelo gratuito — e nesse escopo o «✅ Ready for Production»
> dele está correcto. Não o leia como se descrevesse o objectivo actual.

---

## 2. Estado por fase

| Fase | Documento | Estado |
|---|---|---|
| **0 — Medir** | [`FASE-0.md`](FASE-0.md) · [relatório](FASE-0-RELATORIO.md) | ✅ **completa**, com adenda de 3 correcções |
| **1 — Pipeline** | [`FASE-1.md`](FASE-1.md) | ✅ **completa** (9 de 9) |
| **2 — Busca híbrida** | [`FASE-2.md`](FASE-2.md) · [relatório](FASE-2-RELATORIO.md) | ✅ **negativo**: +0,004 é ruído; `apt@3` cai 95%→90% |
| **3 — Rerank** | [`FASE-3.md`](FASE-3.md) · [P1](FASE-3-PASSO-1.md) · [relatório](FASE-3-RELATORIO.md) | ✅ **inconclusivo**: sinal inverte com o gabarito; `apt@3` inalterado |
| **3B — Rerank, 2.ª tentativa** | [`FASE-3B.md`](FASE-3B.md) · [relatório](FASE-3B-RELATORIO.md) | ✅ **integrado** em `/rerank`: +0,090 nDCG@5 (16/20 perguntas, p=0,012) por 2,6 s, com o pool de candidatos **fechado** |
| **4 — Enriquecimento e roteador** | [`FASE-4.md`](FASE-4.md) · [relatório](FASE-4-RELATORIO.md) | ✅ **roteador integrado** (`/auto`, 72% · 92% com etiqueta múltipla); **enriquecimento vetado** por medição |
| **5 — A voz** | [`FASE-5.md`](FASE-5.md) · [relatório](FASE-5-RELATORIO.md) | ✅ **completa. H rejeitada** pelos dois instrumentos. O contexto não degrada a poética (4 pares contra 4); o Caeiro falha a **0,0 nas duas condições** e é identificado ao nível do Caeiro **real** — logo identificabilidade e poética divergem, e o défice está na persona |
| **5B — A persona do Caeiro** | [`FASE-5B.md`](FASE-5B.md) · [relatório](FASE-5B-RELATORIO.md) | ✅ **inconclusivo por potência (G4)**, nos dois avaliadores. O desfecho **saturou no chão**: 22 dos 30 pares empataram em 0–0, e H5B ficou **sem teste** — nem confirmada nem refutada. O que fica medido: o **0,0 do Caeiro reproduz-se a n=10**, a 60 amostras, 3 repetições por célula e um segundo avaliador cego ao desenho |
| **5C — O instrumento** | [`FASE-5C.md`](FASE-5C.md) · [relatório](FASE-5C-RELATORIO.md) | ✅ **instrumento rejeitado**: V1 e V3 falham. A AUC cai de **0,869 in-sample para 0,544 retida** — todo o sinal era sobreajustamento. O diagnóstico localiza a causa: **78 poemas limpos de Caeiro não bastam** para derivar uma lista lexical que generalize. Fecha a via lexical, e com ela o passo 4 |
| **5D — A contagem de voltas** | [`FASE-5D.md`](FASE-5D.md) · [relatório](FASE-5D-RELATORIO.md) | ✅ **instrumento não aceite (V4 falha)**, mas **a resolução resolve-se**: 38 valores distintos contra os 3 do 3a. E devolve um achado que põe em dúvida a cadeia toda — o **Caeiro real não cumpre a âncora de 3a** (`poem_1485`, «Pensar em Deus é desobedecer a Deus», dá 0,700 nos dois contadores), e o Caeiro gerado **não é distinguível** dele |
| **5E — Medir a âncora** | [`FASE-5E.md`](FASE-5E.md) · [relatório](FASE-5E-RELATORIO.md) | ✅ **W1 dispara, W2 falha** — a célula pré-registada como «o pior caso para as quatro fases». A âncora de 3a dá a nota máxima a **3 de 20** poemas **autênticos** de Caeiro, e reprova «Vi que não há Natureza» por filosofar. Com W3 e W4 a passar (AUC 0,811 · κ 0,784), e os três avaliadores a coincidir. **Autoriza recalibrar a âncora** |
| **5F — Endireitar a régua** | [`FASE-5F.md`](FASE-5F.md) · [relatório](FASE-5F-RELATORIO.md) | ✅ **os três portões passam: a âncora recalibrada é aceite**. Premeia **16 de 24** poemas autênticos retidos (67%, contra os 15% da antiga) e a discriminação **melhorou** (AUC 0,913 contra 0,811). E, sem portão, a pergunta aberta desde a Fase 5 tem resposta: **AUC(gerado < real) passa de 0,655 (p=0,112) para 0,851 (p=0,0003)** |
| **5G — A 5B remedida** | [`FASE-5G.md`](FASE-5G.md) · [relatório](FASE-5G-RELATORIO.md) | ✅ **G2 nas três leituras: H5B cai.** E a medição **correu**: `d` passou de **7** (5B) para **17**, com os mesmos n, perguntas e harness — a diferença foi a régua. IC95% do Δ em **[−0,30; +0,18]**, contra uma distância real-para-gerado de **0,93**: as interdições explicam no máximo um quinto disso |
| **5H — Trocar o modelo** | [`FASE-5H.md`](FASE-5H.md) · [relatório](FASE-5H-RELATORIO.md) | ✅ **M1 dispara nas três leituras: era o modelo.** `llama3.1:8b` dá **+0,700** sobre o `qwen2.5:7b` em 3a′ (IC95% [+0,42; +0,98], p=0,0002, 19 pares contra 2), o que fecha **75%** do fosso de 0,929 que separa o Caeiro gerado do real. **M3 condiciona**: escreve poemas demasiado curtos (7,5 versos contra 10–20 pedidos). Autoriza **investigar** a troca, não trocá-la |
| **5I — A forma do llama** | [`FASE-5I.md`](FASE-5I.md) · [relatório](FASE-5I-RELATORIO.md) | ✅ **I0 passa, I1 e I2 falham: o reforço não é autorizado.** A instrução pega (12→18 em 30 dentro de 10–20 versos) e o tecto corta (truncaturas de 2 para **6**), com saldo de **−0,150** em 3b. E levanta uma dúvida maior: só **43%** dos poemas **reais** de Caeiro cabem no intervalo que a âncora exige, contra 40% do llama e **83%** do qwen. **Dois números desta linha foram corrigidos depois:** os 43% são **39%** com uma definição de verso só (adenda `742b9f6`), e a leitura de que o llama se parece com o poeta **cai** na [5J §2.1](FASE-5J-RELATORIO.md) |
| **5J — A âncora de forma** | [`FASE-5J.md`](FASE-5J.md) · [relatório](FASE-5J-RELATORIO.md) | ✅ **J1 dispara, J2 não: a régua está torta e endireitá-la deixa-a cega.** Os intervalos de versos do 3b não descrevem o poeta, por **um** mecanismo — os **pisos** das personas: o do Campos (15) está acima da mediana real (14), o do ortónimo (12) acima da sua (9), e o **Reis é a única voz sem piso** e a única que passa (73%). Mas **não exonera o llama**, que está *mais longe* da distribuição real (KS 0,347 contra 0,288): a 5I inferiu a semelhança de **um escalar**, e 42+19 ≈ 70+0 dá a mesma fracção com distribuições diferentes. E o intervalo honesto `[4,31]`, validado a 86% em dados retidos, dá **100% aos dois modelos contra 86% do poeta** — logo a contagem de versos **sai** do 3b |
| **5K — Calibrar a forma** | [`FASE-5K.md`](FASE-5K.md) · [relatório](FASE-5K-RELATORIO.md) | ✅ **K1 dispara a n=30 e não agrupado; K2, K3 e K4 disparam.** O substituto da 5J **funciona** — AUC 0,999 e 1,000 contra **0,000** da conformidade monótona, que está *invertida* — mas **não ao n do desenho da 5H**: respeitado o agrupamento (10 perguntas × 3), o desvio do qwen **não está demonstrado** (percentil 90, potência 24%). **A n=20 é 100% nos dois.** E a régua: uma diferença entre heterónimos **reais** vale 0,149–0,317, logo o llama (0,347 do Caeiro) está **mais longe do que quaisquer dois heterónimos**, e **nenhum braço cabe no intervalo de voz nenhuma** |
| **5L — Retirar a cláusula** | [`FASE-5L.md`](FASE-5L.md) | ✅ **passo 22 feito: a contagem de versos sai do 3b.** Autorizada pela 5J, pela 5K e por uma verificação desta nota — **os quatro intervalos premeiam acima do poeta uma distribuição que não é a dele**, inclusive o do **Reis**, que está descritivamente **correcto** (73%) e é invertido pelo llama (83%). Fica a regra da **truncatura** (falha de fecho, detectável sem juízo) e saem os quatro limiares por poema. **Quebra de compatibilidade medida: a cláusula tinha sido aplicada em 68 de 69 casos aplicáveis, logo até 36% das 180 pontuações históricas de 3b mudariam** |
| **5M — A forma das 4 vozes** | [`FASE-5M.md`](FASE-5M.md) · [relatório](FASE-5M-RELATORIO.md) | ✅ **M1 e M2 disparam, M3 não — e é o M3 que muda a decisão.** A predição que a 5K registou **antes** desta corrida confirma-se: o llama vai de **0,347** no Caeiro a **0,196** no Reis. **O custo de forma da troca é só do Caeiro** (llama pior em 1 de 4; no Reis bate o qwen por 0,180). E **`reis/L` é a primeira célula de toda a sequência a reproduzir a distribuição do poeta** (0,196 contra p95 0,207). Mecanismo: **o qwen obedece à persona errada** (83% contra 39% do poeta no Caeiro) e a obediência custa-lhe fidelidade; o llama desobedece e acerta a mediana real em 3 de 4. O **M4 disparava por um desempate de 7,6×10⁻⁵** e foi corrigido |
| **5N — O `qwen2.5:3b`** | [`FASE-5N.md`](FASE-5N.md) · [relatório](FASE-5N-RELATORIO.md) | ✅ **N2 dispara, N1 não: o resultado da 5H é de família, não de capacidade.** Um salto de **+145%** de parâmetros dentro da família rende **+0,400** em 3a′ e **não é significativo** (p=0,12, d=15); o salto de **+5%** da 5H, com mudança de família, rendeu **+0,700** a p=0,0002. O 3b perde também na forma (KS 0,383 contra 0,288) e ganha só em velocidade (1,8×). **E o bónus é o achado incómodo:** nos mesmos 30 itens e com a mesma âncora, três leituras cegas dão médias de **0,50 (R1), 1,00 (R2) e 0,97 (eu)** — e a concordância **entre** sessões (κ 0,51 e 0,61) é **melhor** que dentro da mesma sessão (κ 0,46) |
| **5O — O +0,700 remedido** | [`FASE-5O.md`](FASE-5O.md) · [relatório](FASE-5O-RELATORIO.md) | ✅ **os quatro portões passam: o número da troca replica.** Δ(llama − qwen) = **+0,667** (IC95% [+0,33; +1,00], p=0,0018, **13 de 14** pares), por um avaliador de **outra sessão**, às cegas e **contra** um enviesamento declarado em sentido oposto — e o IC **contém o +0,700** da 5H. A âncora da 5F passa o X1 com um terceiro avaliador (mediana 2,0; **19/24**). E um número novo: **AUC(real > llama) = 0,526** — no 3a′ o llama **não se distingue** de Pessoa autêntico, **mas 78% da folha está no tecto**, logo é o problema da 5B ao contrário |
| **5P — A fronteira 1/2** | [`FASE-5P.md`](FASE-5P.md) · [relatório](FASE-5P-RELATORIO.md) | ✅ **P1 e P3 não disparam: o passo 28 era meu e sai.** A discordância entre os três avaliadores nos 24 poemas reais **não está no 1/2** — quatro dos sete desacordos envolvem um **0**, e nos dois poemas que eu dei como prova (`poem_3421`, `poem_3436`) **R1 e R2 deram 0 aos dois**: eu era o generoso, não a âncora a ser severa. Afrouxar não inverte conclusões (só o O3, por tautologia) mas **apaga sinal** (o p do O1 piora 6,5×) e põe os poemas reais a **100%** no tecto. **Reaponta ao passo 12** (0/1), que estava certo desde a 5G |
| **5Q — O gerado contra o real** | [`FASE-5Q.md`](FASE-5Q.md) · [relatório](FASE-5Q-RELATORIO.md) | ✅ **Q1 dispara, Q2 e Q3 não, Q4 dispara: a troca NÃO entra** (o compromisso do §4 era explícito). E o nulo esconde o achado maior: **nas três vozes que faltavam os dois modelos são trivialmente distinguíveis** de Pessoa (AUC 0,938–1,000, médias **idênticas** 1,42 e 1,42). **O gargalo é de superfície:** 32 de 48 itens gerados (**67%**) têm erro de gramática, grafia brasileira, palavra inexistente ou truncatura — e a guarda `brasileirismos` **não apanha nenhuma das 11 formas** que observei. O sucesso do Caeiro (AUC 0,526) **não generaliza** |
| **5R — O detector de superfície** | [`FASE-5R.md`](FASE-5R.md) · [relatório](FASE-5R-RELATORIO.md) | ✅ **R1 e R2 falham: o detector não entra. Entrou o passo 30.** A validação retida marcou 2,18% dos poemas da metade B, e **nove das 19 formas eram gralhas da transcrição** (`há` 698× contra `ha` 2×) — o portão contava como erro casos em que o detector estava **certo**. A razão canónica:variante separa-as da homografia real (**`avô`/`avó`, 2×**). Corrigido a 20×: falsos positivos **0,73%** (passa) e recall **17%** (falha). **Não há limiar em que os dois passem**, e a causa é o **tamanho do corpus**: `objecto` aparece **8 vezes**, logo nenhuma razão segura o autoriza. **238 testes** |
| **5S — A troca, decidida** | [`FASE-5S.md`](FASE-5S.md) · [relatório](FASE-5S-RELATORIO.md) | ✅ **S1 dispara: a troca está FEITA.** `MODELO = llama3.1:8b` em produção. Sete fases mediram a troca e **nenhuma** olhou para o que mais depende da constante: o **roteador partilha a instância de gerador** e os seus 72% foram medidos com o qwen. Medido: **68%** (27/40), duas perguntas de diferença, numa mecânica que só **propõe**. E os dois modelos são **complementares** — o llama faz **0,9 no Reis** contra 0,5 do qwen, o que torna a afinidade llama-Reis o achado confirmado por **três instrumentos independentes**. **239 testes** |
| **5T — A gramática fecha-se, e por não haver diferença** | [`FASE-5T.md`](FASE-5T.md) · [relatório](FASE-5T-RELATORIO.md) | ❌ **T1 falha em duas das três regras, e a terceira é residual.** Fecha a **segunda metade** do que a 5Q nomeou, e por razão **diferente** da 5R: não é o corpus ser pequeno, é **não haver nada a detectar** — à régua da próclise por **atracção**, o poeta está em **0,045** e os modelos em **0,052–0,062**, intervalos sobrepostos. O detector morreu **três vezes na mesma fase**, sempre no portão de segurança: 1.ª régua marca **22,6% dos poemas de Pessoa**; a correcção da quebra de linha **não muda nada** (435 → 435); a 3.ª régua baixa a 2,65% e mostra que não há sinal. **E duas das três regras da persona não descrevem o poeta**: «não uses gerúndio» quando Pessoa usa a perífrase em **101 poemas**, e «ênclise sempre» quando ele procliticiza em 51. Entrou o aviso de «você» (0,21% no corpus). **243 testes** |
| **5U — A causa atribuída é rara demais** | [`FASE-5U.md`](FASE-5U.md) · [relatório](FASE-5U-RELATORIO.md) | ❌ **U3 dispara, mas dispara no chão.** Ablação emparelhada do bloco `REGRAS_LINGUA` (120 amostras, 3 vozes, modelo único): remover a instrução **nunca piorou** a superfície — seis estimativas (3 estatísticas × 2 réguas) com o mesmo sinal —, mas **nenhuma exclui zero**, porque o braço de base tem **2 ocorrências de próclise e 1 marca ortográfica em 60 amostras**. **E é isso o achado:** a 5Q mediu AUC 0,938–1,000 e atribuiu-o a ortografia e gramática; em 120 amostras frescas há **sete** próclises e **uma** marca ortográfica. **A causa atribuída não pode carregar a detecção.** O analisador foi fixado com o diário em 2 de 120. Nada entrou em `src/` |
| **5V — O ortónimo não rima, e a persona manda-o rimar** | [`FASE-5V.md`](FASE-5V.md) · [relatório](FASE-5V-RELATORIO.md) | ✅ **V3 dispara nos dois instrumentos, e replica em dois conjuntos.** É o **primeiro instrumento mecânico da sequência a discriminar nas três vozes** — e não morreu por falta de eventos porque **cada verso é uma observação**. O achado: o ortónimo real rima a **0,7769** e o gerado a **0,2167**, que é **exactamente o seu próprio nulo de permutação** — não rima menos, **não rima nada**, apesar de a persona mandar «metro regular e **rima**». AUC **0,780** [0,724, 0,831]. **E o Reis é o controlo positivo**: manda «sem rima», e a diferença ali é +0,0325 com IC a conter zero — o instrumento não marca «gerado», marca **rima ausente onde a poética a exige**. O metro dá AUC 0,63–0,74 e revela **compressão**: a amplitude entre vozes é **0,4006** no poeta e **0,1547** no modelo. **0,780 não é 0,938**: a forma é o maior contribuinte mecânico e não fecha o número da 5Q |
| **5W — A rima não se resolve no prompt** | [`FASE-5W.md`](FASE-5W.md) · [relatório](FASE-5W-RELATORIO.md) | ❌ **W4 dispara: nada entra.** Três braços (como está · directiva · exemplo), 60 amostras, braços **intercalados**. Nenhum chegou ao 0,50 nem passou o **seu próprio nulo**, e as duas chaves concordam. **A directiva piorou nas três medidas** — 0,10 contra 0,35 do braço C —, o que replica a [5I](FASE-5I-RELATORIO.md): **duas intervenções de instrução, duas com sinal negativo**. O **exemplo** não fez dano e moveu tudo para o poeta (metro 0,665→0,708, versos 9→12, suspeitas 4→1) **menos a rima**. **E o desfecho que pré-registei era binário, que é a resolução errada:** na **densidade** o poeta rima 1 par de versos em 10 e os três braços 1 em 100 — **um factor de 10 que nenhum braço mexeu**, com n=1196 do lado real. Fecha o prompt como via para a forma; sobra descodificação ou afinação |
| **5X — A descodificação também não** · **com emenda** | [`FASE-5X.md`](FASE-5X.md) · [relatório](FASE-5X-RELATORIO.md) | ❌ **X4 dispara: nada embarca.** Três braços no ortónimo — produção, `repeat_penalty=1.0`, `temperature=0.5`. Nas **17 células com prompt limpo**, as duas intervenções sobem a densidade de rima (**1,96×** e **1,29×**) e **nenhuma exclui zero**; o fosso ao poeta fica em 10–30× em todos os recortes. **E a degeneração que justifica o `REPEAT_PENALTY` desde a Fase 0 não se reproduz no llama**: o braço P é mais limpo que produção em todas as medidas. **O §1 publicado primeiro está RETIRADO** — eu li uma diferença de prompts como chão de ruído; ver as correcções 33–35 e o [passo 42](#) |
| **5Y — Auditoria: o produto sobrevive, a célula mais citada não** | [relatório](FASE-5Y-RELATORIO.md) | **Sem protocolo**, e declarado: não há medição nova nem portão, e a pergunta nasceu dos dados. A protecção é **cobertura** — audita as **nove** fases emparelhadas. **O +0,700 da 5H sobrevive**: nas 25 células limpas dá **+0,660**, IC [+0,340, +0,960], 16 sinais contra 2, p=0,0013 — e **+0,660 é quase exactamente o +0,667 do terceiro avaliador cego da 5O**, logo a contaminação estava a inflacionar o número original. **A troca de modelo em produção está confirmada.** Mas `reis/L` da [5M](FASE-5M-RELATORIO.md) — «a única célula de toda a sequência a reproduzir a distribuição de um poeta» — **inverte**: estava dentro do nulo por 0,009 e fica fora por 0,004. **Era a única das seis que podia inverter**, e eu repeti a frase em quatro relatórios |
| **5Z — A manipulação forte, e a monotonia que não vale nada** | [`FASE-5Z.md`](FASE-5Z.md) · [relatório](FASE-5Z-RELATORIO.md) | ❌ **Z4 dispara: a mecânica fica refutada como explicação útil.** Três níveis de `repeat_penalty` no ortónimo — **1,1 · 1,0 · 0,9** —, 60 amostras, desfecho **primário na 1.ª tentativa** (passo 43: **0/20** prompts divergentes, contra **4/20** na saída final). A **monotonia** pré-registada verificou-se — 0,0075 < 0,0096 < 0,0144 — **e inverte se eu tirar uma célula de vinte**: sem `q34/r1` o braço que *premeia* repetição rima **0,8×** o de produção. Essa célula tem **quatro versos** e o par que a faz rimar é **`toque`/`que`** — a própria manipulação, contada como rima. **A 5X não replica** (1,96× → **1,28×**), e o **Z2 disparou mal operacionalizado**: a quarta vez nesta sequência, a primeira a aprovar em ruído. **O único resultado sólido é o dano**: a 0,9, linhas duplicadas **0,2353 contra 0,0031** e **metade** das amostras truncadas — o ciclo da Fase 0 reproduzido. **O `REPEAT_PENALTY` fica justificado contra 0,9 e injustificado contra 1,0** |
| **6 — Interface gráfica** | [`FASE-6.md`](FASE-6.md) | 🔶 **em curso** — planeada em detalhe em 2026-10-12, 10 passos e 8 portões, e **oito feitos: os passos 1–8** (o 6 corrigiu uma previsão do próprio plano: abortar **não** retinha o trinco — deixava a geração órfã a 985% de CPU com o trinco a dizer «livre»). O **passo 7 — sentinela, portão I8** — entrou com **duas correcções que não são da Fase 6**: vêm do [`PRODUCAO.md`](PRODUCAO.md) §4 e entraram **antes** do código. **(a)** o caminho é **absoluto** — `~/.local/state/pessoabot/.medicao-a-correr`, com `PESSOABOT_SENTINELA` a sobrepô-lo — e não o `data/.medicao-a-correr` **relativo** que o §2.4 especificou: com dois checkouts na mesma máquina há dois `data/`, e o mecanismo ficava **silenciosamente desligado**. **(b)** o I8 ganhou a asserção dos **dois checkouts** — a fase escreve de um, o servidor do outro vê-o —, e ela está **verificada por mutação**: com o caminho da especificação original falha em `assert (None is not None)`, e a asserção anterior (os dois lados concordam no caminho) **passa**. O `.gitignore` não precisou de entrada nenhuma — verificado, e não assumido: o ficheiro vive fora de qualquer checkout, logo o `git status` nunca o vê. **377 testes** (eram 353). FastAPI + página estática sem build; a interface é o **terceiro consumidor** do `Pipeline` e o portão **I1** é paridade com o CLI e o grafo, como a 5Y obrigou. O `AnthropicRemote` que o plano original punha nesta fase **sai** — muda a afirmação de «sem credenciais» do `README` e precisa de medição própria. **O passo 8 está feito** (2026-10-25): persistência em `sqlite3`, `GET /api/sessoes` e `GET /api/sessoes/{id}`, o evento `sessao` a abrir o fluxo, e o portão **I6** medido com a mutação a morder. Duas coisas que ele mudou fora da fase: o `data/sessoes.db` é **o primeiro estado deste projecto que nenhum script regenera**, logo o portão **D8** do [`PRODUCAO.md`](PRODUCAO.md) passou de condicional a **exigível** e o passo 10 de lá ficou desbloqueado; e o achado do I6 — o verso copiado à letra vive no `historico[0].texto` (**6 linhas** de corpo, medidas), e o que o põe fora do alcance do portão é a `tentativa_reg` **não ter coluna de texto**, não a retenção. **Faltam dois, e um está travado por terceiros:** o **9** (painel do poema e `GET /api/poema/{id}`, **travado** pelos termos de uso do Arquivo Pessoa, §10 do plano — e é por ele não existir que o serviço público pode publicar ids e não corpos) e o **10** (fechar). **A contagem de 377 é do momento do passo 7**; hoje a suíte está em **536** |

E uma linha que não é fase, porque não tem portão de medição a cumprir antes
de existir:

| | Documento | Estado |
|---|---|---|
| **Serviço público** | [`PRODUCAO.md`](PRODUCAO.md) · [`producao/SERVICO.md`](producao/SERVICO.md) | 🔶 **construído, e bloqueado a montante** (planeado em 2026-10-18, estado de 2026-10-23). 11 passos: **sete feitos** (1, 2, 3, 4, 5, 8 e 11), o 6 construído e medido mas travado pelo fornecedor, o 7 feito com o portão reduzido ao que é mensurável, e o 9 e o 10 condicionais. **Nada publicado** — e já não por falta de peças: o serviço corre por unidade em `127.0.0.1:8000` e o túnel está **instalado e desligado por decisão**. As duas decisões estão fechadas (§3): **sem o passo 9 da Fase 6** por direitos, e **desta máquina atrás de um túnel gratuito** (saída D). **Não se chama «produção»**: dev e prod são o mesmo computador, que é a confusão que o documento equivalente do irmão foi escrito para evitar. O **passo 7 da Fase 6 — o pré-requisito — está feito** (2026-10-18), com as duas correcções do §4 deste plano dentro: caminho absoluto e a asserção dos dois checkouts. O **passo 5 — o ajudante a parar e a arrancar o túnel — está feito** (2026-10-18), e com ele o remédio em vigor **deixa de ser o 409** e passa a ser o túnel a cair, que é o que o §3.3 pede. Três decisões de desenho, no §3.4 do plano: **(a)** o túnel entra por **indirecção** (`src/web/tunel.py`: um `Tunel` que o `medicao()` recebe, com `TunelSystemd` real e um duplo nos testes) e não como um `systemctl` em linha, porque **não há unidade para parar** — assim o passo 4 é *nomeá-la* e não reescrever isto; **(b)** a **ausência é declarada** — sem `PESSOABOT_TUNEL` há `TunelAusente`, que não faz nada e di-lo, e uma unidade **mal nomeada falha** em vez de passar, porque `systemctl --user stop` de uma unidade inexistente devolve **0** e sem verificar o `LoadState` isso dava «túnel parado» com o URL de pé (a correcção **39** outra vez, agora com o público do outro lado); **(c)** **parar que falha ⇒ a fase não arranca**, e o sentinela já escrito é retirado antes de levantar. O §2.4 da Fase 6 **não** respondia a esta — ali quem cede é o servidor, aqui quem pode ceder é a **medição** —, e decide a assimetria: uma fase que não arranca custa um comando, uma fase corrida com o túnel de pé custa até as **3,2–7,5 h** do orçamento do enriquecimento e **não se descobre depois**. A inversa é assimétrica de propósito: **arrancar que falha avisa e não levanta** (a fase já correu, os dados são bons, e levantar tapava a excepção do corpo). A **ordem** — parar depois do `escrever`, arrancar antes do `limpar` — está **verificada por mutação**: trocadas as duas chamadas caem os **três** testes da ordem e nenhum outro. E o **I4 não ganhou trabalho nenhum**: ninguém pergunta ao túnel no caminho do `/api/estado`, e há um teste que cai se alguém o fizer. **503 testes** a passar (2026-10-23; eram 403 quando esta linha nasceu). **O que mudou desde então, e vem do plano:** o passo **2** reescreveu o I7 em **I7′** e, porque a saída B não bastava, obrigou a escrever a retenção (`src/web/retencao.py`) — o corpo saía por **três outras portas**, uma delas **em fluxo**, antes de a guarda de plágio poder reprovar; o passo **3** deu o `/api/health` com o `sha` lido à importação (**D1** ✅); o passo **4** está **feito** — segundo checkout em `~/.local/share/pessoabot/servico`, `pessoabot.service` e `ollama.service` em `systemctl --user` com `enable-linger`, e o **D2 medido a 2026-10-23**: o `MainPID` **3032** atravessou um logout com `NRestarts=0`, e a unidade subiu **14 s** depois do arranque, antes de qualquer login ([guião](producao/GUIAO-D2.md)); o passo **8** fez do recuo um comando **ensaiado** a partir de uma etiqueta doente a sério (**D6** ✅); e o **11** fechou com o [`producao/SERVICO.md`](producao/SERVICO.md) escrito a partir da máquina. **O túnel está instalado:** `cloudflared` **2026.10.1** em `~/.local/cloudflared/bin`, `cloudflared.service` gerado pelo `unidades.py` e `disabled`, com o interruptor em `~/.config/pessoabot/tunel-desligado` — e o conteúdo dele é a razão. **O passo 6 está construído, medido e bloqueado a montante:** um *Protected Quick Tunnel* com `--allowed-mail` dá uma sessão autenticada de **4 segundos** ([cloudflared#1752](https://github.com/cloudflare/cloudflared/issues/1752), aberto), medida no navegador e confirmada no registo do `uvicorn` — 7 pedidos, todos `GET`, zero `POST` (§7.4). O **D4** ✅ está medido contra ele: de fora, o corpo não toca no `uvicorn`. **O que continua aberto:** o **D3** (uma fase derruba o URL e devolve-o), agora **só** por não haver túnel que sirva — e não pelo passo 4, como esta linha dizia; o **I7′** na metade que precisa do URL; o **D5** na metade que o formato das amostras não permite (§3.6, as amostras não têm instante); e o **D7** e o **D8**, condicionais aos passos 9 e 10. As três saídas estão nomeadas na §7.4 e **nenhuma é trabalho desta casa**: a correcção a montante, um domínio pago para um túnel nomeado, ou o `AnthropicRemote` em fase própria — que muda a afirmação de «sem credenciais» do `README` e pede medição contra as âncoras das 5F–5Y |

### Fase 1, passo a passo

| # | Passo | Estado | Entregável |
|---|---|---|---|
| 1 | Modelo de domínio e parsing | ✅ | `src/corpus/{models,parse}.py` · 11 testes |
| 2 | Deduplicação | ✅ | `src/corpus/dedupe.py` · 10 testes |
| 3 | Chunking | ✅ | `src/corpus/chunk.py` · `src/tokens.py` · 12 testes |
| 4 | Índice | ✅ | `src/corpus/build.py` · `src/retrieval/{encoder,index}.py` · 14 testes |
| 5 | Vozes e prompt | ✅ | `src/voices.py` · `src/generation/prompt.py` · `src/guard.py` · 29 testes |
| 6 | Gerador | ✅ | `src/generation/{base,ollama}.py` · 15 testes |
| 7 | Guarda de plágio | ✅ | `src/plagio.py` · `src/pipeline.py` · 11 testes |
| 8 | **Conjunto dourado** | ✅ | `src/avaliacao.py` · `src/retrieval/lexical.py` · `tests/test_retrieval_gold.py` · 8 testes |
| 9 | CLI | ✅ | `src/cli.py` · `pipeline.responder_em_fluxo` · 7 testes |

**237 testes a passar.** `src/main.py`, `src/model.py` e `src/retriever.py`
(280 linhas, o código antigo corrigido no início da sessão) continuam no
repositório e serão substituídos no Passo 9.

---

## 3. Decisões fechadas, e de onde vêm

Nenhuma destas é preferência: todas têm medição por trás.

| Decisão | Valor | Vem de |
|---|---|---|
| Hardware | **CPU para gerar** — a iGPU existe e é 6x no prefill, 0,55x no decode | `lscpu`; [`fase-0/07-igpu-vulkan.md`](fase-0/07-igpu-vulkan.md) |
| Threads | **10**, `taskset -c 0-11` | varredura monotónica; LP-E a 2100 MHz excluídos |
| Python | **3.12** via `uv` | 3.14 sem wheels de torch/faiss |
| Gerador | **`qwen2.5:7b-instruct-q4_K_M`** | 7,0 às cegas vs 6,5 do llama3.1:8b |
| Orçamento da parte variável | **300 tokens** | 168 tok → 33,7 s; 448 tok → 53,7 s |
| Persona no `system` | 313 tok, em cache | 13,63 s → 0,91 s da 2ª pergunta |
| `repeat_penalty` | **1,1** | resolveu a degeneração em ciclo |
| Regra anti-cópia no `system` | preventiva, em cache | mediana de versos copiados: **82% → 0%** |
| Repetição por plágio | **sem os poemas copiados** | rejeições 4/5 → 1/5; reincidência 3/5 → 0/5 |
| `LIMIAR_VERSO` de plágio | **0,72** | lacuna entre 0,70 (limpas) e 0,79 (copiam) |
| `LIMIAR_FRACAO` de plágio | **0,10** | 21% de repetição, 33,8 s de média |
| Encoder | **`intfloat/multilingual-e5-base`** | `maxlen=512` cobre 96% dos poemas inteiros |
| Lote de embedding | **8** | 1,6x mais rápido que 64, o inverso do esperado |
| Limite de chunk | **480 tokens** | 512 − 2 − 27 − 2 = 481, derivado |
| Índice | **`numpy`**, não FAISS | 2290 × 768 = **7,0 MB**; busca em 5,57 ms |
| Reranker candidato | **MiniLM-L12-H384** (~120M) | 1694 tok/s contra 90 do bge-m3 de 568M |
| LangChain | **removido** | declarado no `requirements.txt`, usado em zero linhas |
| Roteador de voz | **chamada ao qwen2.5:7b** | 72% contra 52,5% do melhor embedding; o 3b faz 42% |
| `temperature` do roteador | **0,0** | um classificador tem de ser determinista; os 0,9 são para verso |
| O roteador **propõe** | não decide | a 72%, 1 em 4 iria à voz errada; em silêncio custa 30 s, à vista custa uma tecla |
| Enriquecimento offline | **não se faz** | 88% da falta do nDCG@5 é reordenação; o enriquecimento ataca 12% por 3,2–7,5 h |
| Reranker | **`bge-reranker-v2-m3`** | +0,090 contra +0,018 do MiniLM, no pool fechado |
| Candidatos a reordenar | **8, truncados a 120 tok** | n=20 dá +0,124, mas a diferença é +0,033 com IC95% [−0,017, +0,081] |
| Reordenação ligada? | **por escolha, `/rerank`** | 2,6 s em ~30 s é uma troca, e a troca é do utilizador |
| Fronteira de profundidade | **top-20** | é até onde o gabarito está completo; mais fundo volta a pontuar não julgados |
| Comprimento do poema no **3b** | **sai da âncora por amostra** | os quatro intervalos são **invertíveis**: premeiam um braço acima do poeta ([5L §2.1](FASE-5L.md)). Mede-se ao nível do **conjunto** (passo 21) |
| Comprimento do poema, **onde se mede** | **KS ao corpus, por conjunto** | calibrado na [5K](FASE-5K-RELATORIO.md): chão p95 = 0,190 a n=30, régua 0,149–0,317 entre vozes reais |
| Truncatura no 3b | **continua a levar 0** | é falha de **fecho**, não juízo de intervalo, e lê-se de `done_reason == "length"` sem avaliador |
| **Modelo de serviço** | **`llama3.1:8b-instruct-q4_K_M`** | trocado em 2026-10-08 pela [5S](FASE-5S-RELATORIO.md). +0,667 em 3a′ replicado por um 3.º avaliador cego (5O), AUC 0,526 contra 0,851, capacidade excluída (5N), forma melhor em 3 de 4 (5M), sem diferença nas outras 3 (5Q). Custo: o roteador cai de **72% para 68%** |
| Roteador e poeta | **partilham o modelo**, deliberadamente | medido na 5S e fixado por teste. Separá-los vale 4 pontos de exactidão numa **proposta** e custa dois modelos de ~5 GB em memória |
| Colocação pronominal na guarda | **não entra** | a [5T](FASE-5T-RELATORIO.md) construiu o detector em três passagens e fechou-o: marca **2,65%** dos poemas autênticos, e à régua correcta **o poeta e os modelos procliticizam na mesma proporção**. Fixado por teste (`test_colocacao_pronominal_nao_e_verificada`) |
| «você» na guarda | **aviso, não rejeição** | 0,21% no corpus (4 de 1926) fica acima dos 0,2% do `lingua_errada`, que é o único nível a que este projecto autorizou uma rejeição. Regra pré-escrita na [5T §4.1](FASE-5T.md) |
| Remover o `REGRAS_LINGUA` | **não autorizado** | a [5U](FASE-5U-RELATORIO.md) não tem poder para o declarar decoração (7 eventos no braço de base), e mostrou que ablá-lo mexe na **saliência** do resto: o braço ablado teve 3 falhas de guarda contra 0, duas delas quebras de persona — e o `REGRAS_SAIDA`, que as proíbe, **não foi ablado** |
| Combinar rima e metro num só desfecho | **não sem validação retida** | a [5V §5](FASE-5V-RELATORIO.md) não o fez de propósito: é o movimento que produziu o pior resultado do projecto, a [5C](FASE-5C.md) a ver o AUC cair de **0,869 em amostra para 0,544** em dados retidos |
| Reforçar instruções de forma no prompt | **não** | duas tentativas, dois sinais negativos: a [5I](FASE-5I-RELATORIO.md) no comprimento e a [5W](FASE-5W-RELATORIO.md) na rima (0,10 contra 0,35). O que o W4 autoriza é **descodificação ou afinação**, não instruir melhor |
| O tokenizador do orçamento fica o do **qwen** | **sim**, com o modelo a ser llama | medido pelo `prompt_eval_count` do próprio Ollama, que é a contagem autoritativa do modelo que serve: nos mesmos 25 poemas o llama dá **135** contra **133** do qwen — razão **1,000**, máximo 1,031. Trocá-lo não compra nada e custa descarregar um tokenizador. **É a segunda coisa ligada ao `MODELO` que a 5S não olhou, e esta é benigna — mas só se sabe por estar medida** |
| `contador()` sem omissão | **obrigatório passar `ENCODER` ou `GERADOR`** | a omissão era o `ENCODER`, e orçamentar o prompt do gerador com ele subestima **17%**. O `src/` nunca caiu nisso; **nove scripts de fase caíram**. Fixado por `test_o_contador_exige_o_nome_do_tokenizador` |
| Desfechos binários para forma | **não** | a [5W §1](FASE-5W-RELATORIO.md) mediu o custo: no binário o fosso da rima lê-se como «0,84 contra 0,38» e pedia ~175 amostras por braço; na **densidade** lê-se como **10×** e não precisou de uma amostra nova. Usar **densidade** e **amplitude entre vozes** ([passo 39](#)) |
| Portões por estimativa pontual | **não: com intervalo** | **três vezes o mesmo defeito** — o `M4` da 5M a disparar num empate de 7,6×10⁻⁵, o `T2` da [5U](FASE-5U-RELATORIO.md) a disparar com **uma** ocorrência em 48, e o `X3` da [5X](FASE-5X-RELATORIO.md) a vetar em **−0,0097 num IC de ±0,13**. Passa a regra |
| **Asserir a identidade do prompt contra a fase anterior**, e não só dentro da fase | **sim** | a emenda da [5X](FASE-5X-RELATORIO.md) mediu o que custou não o fazer: eu li 0,00951 contra 0,00615 como ruído de corrida, e eram **18 de 20 prompts diferentes** por eu ter mudado o tokenizador do orçamento entre as fases. **O modelo é determinista** (2/2 textos idênticos onde o prompt coincidiu), logo não há ruído de corrida nenhum a medir |
| A análise primária de uma fase emparelhada é sobre a **primeira tentativa** | **sim**, e o `Turno` **já a guarda** | a [5Y §5](FASE-5Y-RELATORIO.md): a saída final já passou pelo `_repetir_sem`, que troca o contexto quando o modelo plagia. Só a 1.ª tentativa tem prompt idêntico entre braços **por construção**. O passo 43 pôs `Turno.historico` e `Turno.primeira` em `src/pipeline.py`; **o harness da próxima fase emparelhada registra `turno.primeira.resposta.texto` e analisa-o como desfecho primário**, deixando a saída final como secundário de produto. **A [5Z](FASE-5Z-RELATORIO.md) correu-o e verificou-o**: 1.ª tentativa **0/20** células com prompt divergente, saída final **4/20** — e na saída final os braços 1,0 e 0,9 **coincidem** (0,01262 contra 0,01264), porque o braço que mais repete é o que o sistema mais corrige |
| A afinidade llama–Reis tem **três** instrumentos | **dois** | a perna da distribuição de comprimento (`reis/L` dentro do nulo) **caiu** na [5Y §4.1](FASE-5Y-RELATORIO.md). Ficam a predição registada da 5K e o roteamento da 5S — de naturezas diferentes, logo ainda convergência, mas «a mais forte da sequência» era construída sobre a perna que caiu |
| `REPEAT_PENALTY = 1.1` | **fica**, mas a justificação **não se reproduz** | entrou na Fase 0 porque «um 8B degenerou em ciclo». Com ela desligada no `llama3.1:8b`, 20 amostras dão **zero** linhas duplicadas (contra 0,0031 de produção) e **zero** palavras suspeitas (contra 6). Não autoriza desligá-la; autoriza medi-la a sério ([5X §3.1](FASE-5X-RELATORIO.md)) |
| A chave de rima exclui pares de palavra igual | **sim, obrigatoriamente** | sem isso mede **repetição**: Caeiro, verso livre, «rimava» a **0,6417** por repetir palavras, e cai a **0,1583** — abaixo do próprio nulo — quando os pares de palavra idêntica saem ([5V §2](FASE-5V-RELATORIO.md)) |

### Números do sistema

| | |
|---|---|
| poemas | 2083 (2062 após deduplicação) |
| chunks indexados | **2290** |
| índice | 7,0 MB · busca 5,57 ms |
| recuperação | **nDCG@5 = 0,606** (denso) · **0,696** com rerank · apt@3 = 95% · oráculo@20 = **0,980** |
| conjunto dourado | **434 julgamentos**, 125 de nota 2, top-20 denso fechado — 433 das Fases 1-3B, +1 de 2026-10-19 (`q25/poem_4341`, que uma reconstrução do índice trouxe ao top-20 por um empate de um ULP; ver [`julgamentos-reconstrucao.json`](julgamentos-reconstrucao.json)) |
| corpus.jsonl | 3,0 MB · build em ~40 s |
| construção do índice | 383 s (6,4 min) |
| latência de resposta prevista | ~44 s a 500 tokens de contexto |
| roteador de voz (`/auto`) | +0,5 s por pergunta, e ~20 s uma vez a aquecer |
| reordenação (`/rerank`) | +2,6 s por pergunta, e ~4,8 s na primeira |

### O pipeline declarado como grafo (LangGraph) — 2026-10-08

**O que foi feito:** `src/grafo.py` declara a orquestração existente como um
`StateGraph` — nós `recuperar · montar · gerar · verificar · repetir`, com a
aresta condicional `verificar → repetir | END`. `PipelineGrafo.responder` tem o
mesmo contrato de `Pipeline.responder` e devolve o mesmo `Turno`. O CLI expõe-o
em `--grafo`.

**O que NÃO foi feito, e é o ponto:** nenhum componente medido mudou. O grafo
chama `Pipeline.recuperar`, `generation.prompt.montar`, `guard.verificar`,
`plagio.analisar` e `Pipeline._repetir_sem` — os mesmos objectos, pela mesma
ordem. ⇒ **os números acima continuam a valer para os dois caminhos**, e
`tests/test_grafo.py` é quem o garante: compara os dois resposta a resposta
(texto, tentativas, veredicto, poemas usados) e falha se divergirem.

**Por que o porte é natural e não decorativo:** o `for` do `pipeline.responder`
já era um grafo cíclico com arestas condicionais. A política *«se copiou e ainda
há tentativa, repetir sem os poemas de que copiou»* passou de fluxo de controlo
a objecto inspeccionável (`PipelineGrafo.diagrama()`, em Mermaid).

**Custo visível ao utilizador, e por isso fica atrás de um flag:** o caminho do
grafo **não faz streaming**. O caminho normal mostra o 1.º verso em ~2 s; o
grafo cala-se ~30 s e imprime no fim. **O caminho medido continua a ser o
omisso.**

⚠️ **Não é um agente.** O percurso é decidido por regras, não pelo modelo. Não
há ferramentas, nem escolha de caminho pelo LLM. Chamar-lhe agente seria vender
o que não há.

📌 **`draw_ascii()` precisa de `grandalf`; `draw_mermaid()` não precisa de nada**
— o diagrama é Mermaid por isso, e renderiza no README.

🔁 **E fecha um ciclo do próprio repositório:** em 2026-10-01 o `langchain` foi
**removido** do `requirements.txt` por estar declarado e usado em zero linhas.
O `langgraph` entra agora no caso oposto — importado em `src/`, exposto no CLI e
com teste que falha sem ele. A nota ficou escrita no `requirements.txt`.

### Produção — as duas decisões que **não** têm medição por trás (2026-10-18)

Esta secção abre com «nenhuma destas é preferência: todas têm medição por
trás». Estas duas são a excepção, e ficam aqui — e não escondidas noutro
sítio — porque é aqui que se procura o que foi decidido. São decisões do dono
do projecto, tomadas em 2026-10-18 sobre o plano
[`PRODUCAO.md`](PRODUCAO.md), e **nenhuma das duas é consequência de uma
medição**. Nomear isso é o que as distingue das linhas acima.

| Decisão | Valor | De onde vem |
|---|---|---|
| **O que se publica** | **saída B**: o serviço vai a público **sem o passo 9 da Fase 6** — cita `poem_1019` como **id**, e não há rota que devolva o corpo do poema. **A decisão fica; a razão que lhe dei caiu** — ver a nota ⚠️ abaixo | decisão do dono, 2026-10-18. Não é medição: era a resposta ao bloqueio de direitos do [`PRODUCAO.md`](PRODUCAO.md) §0.1. ⚠️ **E esse bloqueio estava mal localizado:** em 2026-10-19 mediu-se que o corpus está **versionado num repositório público** desde 2025-10-24 (correcção **42**), logo o passo 9 nunca foi o que retinha as transcrições. O que sustenta a saída B hoje é a correcção **40** — o varrimento do passo 2 mostrou que ela **não bastava** e obrigou à retenção —, e isso é um argumento de transporte, não de direitos |
| **Onde corre** | **saída D**: a **máquina de desenvolvimento**, atrás de um **túnel gratuito**. Fechada em 2026-10-18, depois de a opção 1 (EC2 de CPU grande) ter sido escolhida e **retirada horas depois** pela restrição de custo | decisão do dono, 2026-10-18, em dois tempos — ver a nota abaixo. Aqui **há** medição a favor, e é a única das três saídas que a tem: o hardware é **o hardware das Fases 0 a 5**, logo os 34 s por resposta e os 18 s até ao 1.º verso descrevem o que vai servir. Lido na máquina em 2026-10-18: 14 núcleos, 30 GiB, 22 disponíveis, contra os ~6–7 GiB do modelo e do encoder |

E as duas consequências que estas decisões criam, registadas por serem o que
um leitor futuro precisa de saber:

- **A saída B não implanta o sistema inteiro.** O passo 9 da Fase 6 não está
  escrito, logo não há nada a remover — mas também não se escreve enquanto A
  não fechar. O `README` passa a descrever um sistema com uma rota a menos do
  que o plano da Fase 6 prometia.
- **A saída B continua válida.** É uma decisão de direitos, não de dinheiro, e
  a restrição abaixo não a toca.

#### A restrição que reabriu «onde corre», no mesmo dia

Horas depois de escolher a opção 1, o dono acrescentou a restrição:
**«não aumente os custos atuais»**. Ela é incompatível com a decisão, e o
número está no próprio plano: um `m7i.2xlarge`/`c7i.2xlarge` em `sa-east-1` é
**~50–100× o `t3.micro`** que o repositório irmão paga. Não é um aumento
marginal a negociar — é a ordem de grandeza da opção.

Fica registado assim, e não como uma emenda silenciosa ao parágrafo acima,
porque as duas coisas aconteceram e a segunda não apaga a primeira: **a opção
1 foi escolhida com a informação que havia e foi retirada quando a restrição
apareceu.** É o mesmo hábito da §4.

O que a restrição **elimina**: qualquer EC2 novo, de qualquer tamanho —
incluindo spot, que é menos caro e não é custo zero. E elimina também
co-habitar com o irmão: o `t3.micro` dele tem 1 GiB e já está a servir
`brasileirao.mpbarbosa.com`.

O que **sobrou** para o Passo 1 decidir outra vez, e que ele decidiu no mesmo
dia (ver a nota seguinte):

| saída | custo | o que custa de outra coisa |
|---|---|---|
| **D — a máquina de desenvolvimento, atrás de um túnel gratuito** | zero em nuvem | é **o hardware que foi medido**, logo a latência é conhecida (34 s, 18 s até ao 1.º verso) e não precisa do Passo 2. Mas: a disponibilidade passa a ser a do portátil ligado, e **colide com a sequência de medição** — o sentinela do passo 7 da Fase 6 (portão **I8**) existe porque o servidor e as fases disputam o mesmo Ollama, e um URL público nessa máquina torna a disputa permanente em vez de ocasional |
| **E — geração remota** (`AnthropicRemote`) | **não é zero**: paga-se por token, mas o servidor volta a caber num `t3.micro` | muda a afirmação «sem chamada a API externa e sem credenciais» do `README`, e as latências medidas deixam de descrever o sistema. A Fase 6 §8 já a nomeou como **fase própria com medição comparada de qualidade** |
| **C — não publicar** | zero | o plano de produção fica escrito e não executado. É a única saída que respeita a restrição **e** não desfaz nenhuma afirmação medida |

Nenhuma destas três é «a opção 1 mais barata». As três mudam o produto, e é
por isso que a escolha voltou ao dono em vez de ser inferida do orçamento.

#### O que a saída D escolheu, e os dois achados que ela produziu

**Escolhida a D**, no mesmo dia. O plano foi reescrito em volta dela e a
versão que recomendava o EC2 está **retirada e não foi guardada** — o
`PRODUCAO.md` foi reescrito antes de qualquer commit, logo esse texto **não
está no histórico**. É uma perda, não uma decisão, e fica registada. Ela traz a
única vantagem que nenhuma das outras tinha — **o hardware é o que foi
medido** — e dois problemas que não se viam antes de ela ser escolhida. Os
dois estão em [`PRODUCAO.md`](PRODUCAO.md) §2 e §3, e ambos são da família
que esta casa já conhece: **o mecanismo continua a dizer «certo» depois de
deixar de proteger.**

**1. O túnel faz o portão I7 passar e tira a protecção que ele codifica.** O
I7 afirma que «o servidor não escuta noutro interface sem sinalizador
explícito». O `cloudflared` corre **nesta** máquina e liga-se **de dentro** a
`127.0.0.1:8000`: o `bind` não muda, não há sinalizador, **o portão passa
literalmente** — e o serviço está na internet. A asserção usava «escuta em
`127.0.0.1`» como medida de «não é alcançável de fora», e com um túnel as
duas deixam de ser a mesma coisa. Reescreve-se como **I7′**: o corpo do poema
não sai desta máquina, medido **de fora**.

> ✅ **Feito em 2026-10-19** (passo 2), e com um achado que esta entrada não
> previa: **reescrever o portão não bastou, porque a saída B não bastava.** O
> varrimento encontrou três outras portas por onde o corpo saía, a pior delas
> **em fluxo** — antes de a guarda de plágio poder reprovar. Ver
> [`PRODUCAO.md`](PRODUCAO.md) §2.1, as correcções #40 e #41 do §4, e a secção
> «A retenção de versos» no fim deste ficheiro.

**2. O mecanismo que devia mediar o conflito com as medições não existe.** O
sentinela é o **passo 7** da Fase 6, e a fase está no passo 6 — verificado em
2026-10-18: zero ocorrências de `medicao-a-correr` em `src/` e `tests/`. O
`src/web/app.py` já diz, em letra própria, que até lá «não correr o servidor
com uma medição a decorrer é **disciplina e não mecanismo**». Com um URL
público os clientes são estranhos que não sabem que há uma medição a correr, e
**a disciplina deixa de ter onde se aplicar** — logo o passo 7 passa a
**pré-requisito do túnel**, invertendo a ordem do plano da Fase 6.

E o sentinela, **como está especificado, resolve metade**: protege a medição
do servidor (é o que o I8 mede) e não protege (a) a medição de um pedido
público que não gera nada e **aquece o chip** na pausa de 60 s da [Fase 0
§3.2](FASE-0.md) — e o *throttling* desta máquina foi medido **até 101 °C**,
pelo que a queda monotónica de tok/s passa a ter duas causas indistinguíveis;
nem (b) o público de um **409 que dura sete horas** (o enriquecimento estava
orçamentado em 3,2–7,5 h). O remédio passa a ser **parar o túnel**, com a
**janela registada** ao lado das amostras — porque a alternativa é um
`01-cru.jsonl` em que uma célula lenta pode ser térmica ou pode ser um
estranho, e isso **não se descobre depois**. É a lição das 4 horas que o cache
de KV invalidou (§4, «defeitos nos meus próprios instrumentos»), aplicada
antes de custar quatro horas.

> ✅ **As duas metades ficaram feitas no mesmo dia**, e o parágrafo acima fica
> como foi escrito em vez de ser reescrito: é o argumento que as fez existir. O
> passo 7 da Fase 6 (o guarda de **pedido**) e o passo 5 do `PRODUCAO.md` (o
> guarda de **alcance**: o ajudante derruba o túnel) estão ambos feitos desde
> 2026-10-18 — ver a linha «Serviço público» no §2, que traz as três decisões
> de desenho do passo 5, incluindo o que acontece quando parar o túnel falha
> (**a fase não arranca**). O que fica da lista é a **janela registada**, que é
> o passo 7 do mesmo plano.

**E um defeito a corrigir antes de o código existir:** o serviço público corre
num **segundo checkout**, logo há **dois `data/`**, e o sentinela especificado
como `data/.medicao-a-correr` — caminho **relativo** — é escrito num e
verificado no outro. **Nunca é visto, o `/api/estado` diz que está tudo bem, e
o mecanismo que torna o túnel seguro está silenciosamente desligado**: passa
nos testes (um processo, um directório) e falha na máquina. Entra no passo 7
como caminho **absoluto** (`~/.local/state/pessoabot/`), e o I8 ganha a
asserção de que atravessa checkouts.

---

## 4. Correcções a afirmações minhas

Registadas porque várias eram convincentes e erradas, e porque o padrão
interessa: **a aritmética estava quase sempre certa e o modelo mental errado**.

| # | Afirmei | Realidade | Onde |
|---|---|---|---|
| 1 | O ROADMAP está errado sobre estar pronto | Está correcto **para o objectivo anterior**; eu julguei contra o novo | corrigido pelo utilizador |
| 2 | Qualidade em português do Flan-T5 não se sustenta | Afirmei sem correr o código (não havia venv nem faiss) | §correcção da 1ª avaliação |
| 3 | Prefill de 1500 tok: 8–15 s (3B), 20–45 s (7–8B) | **31 s / 84 s** — optimista 2–4x. Assumi que 14 threads AVX2 ajudariam; são 2 P-cores | `FASE-0-RELATORIO.md` §2 |
| 4 | Serafim-335m-ir é o candidato preferencial | **`maxlen=128`** — trunca ¼ dos poemas. Recomendei do artigo sem verificar | `BIBLIOGRAFIA.md` 4.1 |
| 5 | O 8B deu as únicas amostras 10/10 | **Viés**: às cegas o 7B também deu | adenda A.2 |
| 6 | A contenção de rede invalidou os tempos do e5 | Valia **5%**. Fui excessivamente cauteloso | adenda A.3 |
| 7 | `poem_17`/`poem_23` são esboços da mesma ode | **Não são**: 0,111 de similaridade, partilham só o incipit | correcção de facto |
| 8 | Há 1 par de duplicados exactos | **3 pares** + 18 grupos de variantes = 21 poemas | idem |
| 9 | `poem_12`/`poem_619` não são variantes | **São**: contenção. Diagnostiquei lendo 320 caracteres | §Passo 2 |
| 10 | A extrapolação de rerank falhou por atenção quadrática | Explicação **errada**, tirada de resultados parciais. A estimativa era optimista por 1,9x | `FASE-3-PASSO-1.md` |
| 11 | Esta máquina não tem GPU utilizável | **Tem**: Intel Arc por Vulkan. Concluí de `nvidia-smi` ausente, vi o `lspci` dizer «Intel Graphics» e não verifiquei | [`fase-0/07-igpu-vulkan.md`](fase-0/07-igpu-vulkan.md) |
| 12 | A guarda de idioma estava com o limiar alto | **Não estava**: contra o corpus, 0,12 rejeita 3 de 1906 (0,16%). O errado era o **instrumento** — media registo, não língua | secção abaixo |
| 13 | O llama3.1 reproduz a distribuição de comprimento do Caeiro «quase exactamente» | **Não reproduz**: está *mais longe* que o qwen (KS 0,347 contra 0,288; mediana 7,5 contra 11,5 do poeta). Inferi de **um escalar** — 40% contra 39% dentro do intervalo —, e eram **70+0** contra **42+19** | 5I §9.2, corrigido pela [5J §2.1](FASE-5J-RELATORIO.md) |
| 14 | A truncatura não está gravada no harness, logo precisa de heurística | **Está gravada** (`truncada`, de `done_reason == "length"`). A heurística que declarei — «última linha sem pontuação terminal» — acertou **zero**: 4 falsos positivos e 1 falso negativo em 60. Em verso livre, acabar sem ponto é **estilo** | [`FASE-5J.md`](FASE-5J.md) §4.4, corrigido a meio |
| 15 | Com `num_predict=150`, **todos** os números de comprimento desta sequência estão censurados em cima | **São 220** (`ollama.py:38`; li o 150 da tabela do docstring, desactualizada desde a Fase 1) — e com o valor certo a explicação cai: na 5H houve **1 truncatura em 60** e os modelos pararam com ~20 palavras de folga. A estreiteza das faixas é **dos modelos**. O tecto só morde **com** reforço (5I braço B: 6 em 30) | [5J §2.3](FASE-5J-RELATORIO.md), reescrito depois de publicado |
| 16 | O máximo do Caeiro real é 48 versos (5I) / **181** (adenda) | É **161** (`_versos`) e 165 (linhas não vazias). O 48 vinha de contar só o 1.º chunk; o 181 vem de **juntar** chunks, e o chunker tem `SOBREPOSICAO = 1` (`chunk.py:36`) — repete uma estrofe por fronteira, 21 linhas duplicadas no `poem_1487`. A fonte certa é o `.body` do `parse_poem` | [5J §2.2](FASE-5J-RELATORIO.md) |
| 17 | Próclise não licenciada mede português do Brasil | À 1.ª régua marcou **435 de 1926** poemas de **Pessoa** (22,6%): infinitivos («e **te amar**»), atracção à distância («Só tu, Senhor, **me dás**») e coordenação («Se eu interrogasse e **me espantasse**») são próclise **correcta**. À régua da atracção, **não há diferença** entre o poeta (0,045) e os modelos (0,052–0,062) | [5T §1](FASE-5T-RELATORIO.md) |
| 18 | «Os modelos são mais enclíticos que Pessoa» — 0,143 contra **0,318** | **Artefacto**, e cheguei a ter o intervalo de confiança a sustentá-lo. As classes que o detector marcava a mais são **mais frequentes em Pessoa**, que escreve orações longas com atractores e infinitivos encadeados. O numerador inflacionado era o dele | [5T §1.2](FASE-5T-RELATORIO.md), apanhado antes de publicar |
| 19 | «Colocação enclítica, **sempre**» descreve Pessoa | Procliticiza em **51 poemas** mesmo à régua estrita. E «não uses gerúndio» proíbe o que ele faz em **101** («Vou escrevendo os meus versos sem querer»). As duas regras estão em **produção** desde a Fase 0 | [5T §2](FASE-5T-RELATORIO.md) |
| 20 | O comentário do `verificar` dizia que ali se verificava «colocação pronominal» | **Não se verificava**, nem antes nem depois — `grep` por «proclise» em `guard.py` dava zero. Corrigido para dizer que a 5T a fechou | `src/guard.py` |
| 21 | A causa do AUC 0,938–1,000 da 5Q é «ortografia e gramática» | **Não pode ser.** Em 120 amostras frescas das três vozes há **7** próclises brasileiras e **1** marca ortográfica. Juízes cegos não separam real de gerado a 0,938–1,000 com um defeito que aparece em 7 de 60 textos. Tratei as **razões escritas pelos juízes** como achado e passei **três fases** (5R, 5T, 5U) a instrumentá-las | [5U §2](FASE-5U-RELATORIO.md) |
| 22 | A ablação da 5U mede o bloco de língua | Mede o bloco **e a estrutura do prompt**: tirar 97 *tokens* do `system` mexe na saliência do que fica. O braço ablado teve **3** falhas de guarda contra **0**, duas delas quebras de persona que o `REGRAS_SAIDA` — **não ablado** — proíbe | [5U §3](FASE-5U-RELATORIO.md) |
| 23 | Os braços da 5U estão emparelhados | Emparelhados por célula, mas **não intercalados**: as 60 do braço C correram todas antes das 60 do A. A **latência fica não interpretável** (A mais lento com menos prefill). Os desfechos de defeito não dependem de tempo | [5U §3](FASE-5U-RELATORIO.md) |
| 24 | O AUC ao poeta é um instrumento **mecânico** | **Não é.** É calculado sobre as pontuações da âncora 3a′ dadas por um avaliador **cego** (`fase-5f/analisar.py:94`, `c3a`). «Corpus-fundado» diz que o conjunto de comparação são poemas reais — o que evita o erro da 5E —, e eu li isso como «não precisa de juiz». Escrito na 5U §4 e corrigido no turno seguinte, antes de abrir qualquer fase em cima dele | [5U §4](FASE-5U-RELATORIO.md), corrigido em `docs/CONTROLO.md` |
| 38 | O colapso da 5C (AUC 0,869 → 0,544) tem duas causas prováveis nomeadas: 39 poemas e a falta de lematização | **Há uma terceira**, contada ao escrever o [`tematicos/SENTIMENTO.md`](tematicos/SENTIMENTO.md) §2.1: das 40 palavras da lista FAS, **4 são o paradigma da 2.ª pessoa** (`teu`, `tua`, `teus`, `tens`) e **11 são afecto puro**. A 2.ª pessoa é **interlocutor** — Caeiro não se dirige a um «tu», Reis dirige-se a Lídia —, logo é a ameaça de **tópico** que o protocolo declarou e nunca isolou. **Com o mesmo estatuto das outras duas: plausível, não isolada** | `docs/fase-5c/01-validacao.json` |
| 25 | A 5Q autoriza baixar a urgência do passo 25, porque «67% das amostras se entregam pela ortografia e pela gramática» | A premissa caiu com a **5U**: em 120 amostras há **7** próclises e **1** marca ortográfica. Se o andar de baixo **não** está caído, o argumento de «medir o andar de cima com o de baixo caído» não se aplica, e o passo 25 **recupera a urgência** que a 5Q lhe tirou | [5U §2](FASE-5U-RELATORIO.md) |
| 26 | «O Reis manda *metro regular e rima*» (§1 do protocolo da 5V) | **É o ortónimo.** O Reis manda «Ode breve … **sem rima**», e as odes dele são verso branco. Construí o portão de calibração V1 sobre a troca, e ele **não disparou por isso** — com o par certo (ortónimo contra Reis) dispara com folga: 0,777 contra 0,199 | [5V §1](FASE-5V-RELATORIO.md), apanhado pelo próprio portão |
| 27 | A chave de rima mede rima | Media **repetição**. Dois versos que acabam na mesma palavra dão a mesma chave, e Caeiro repete por poética e Campos faz anáfora **por instrução**. Caeiro «rimava» a 0,6417 e cai a 0,1583 — **abaixo do próprio nulo** — ao excluir os pares de palavra igual | [5V §2](FASE-5V-RELATORIO.md) |
| 28 | A chave de rima da 5V parte do penúltimo **grupo** de vogais | O regex junta `ia` num grupo só, logo `havia`→`avia` e `servia`→`ervia`, **que não casam** — e é rima de manual. A correcção parte da penúltima **vogal-letra**. Re-corri a 5V: **as conclusões não mudam, as magnitudes melhoram** (ortónimo real 0,777→0,837, gerado 0,217→0,383 contra um nulo de 0,383) | [5W §4](FASE-5W-RELATORIO.md), achado antes de os dados da 5W existirem |
| 29 | «O poema rima» é o desfecho certo para medir rima | **É a resolução errada.** Num poema de 12 versos há 66 pares e **um** acerto por acaso põe o binário em `True`, logo mistura «rima sistematicamente» com «rimou uma vez sem querer». Na densidade o fosso é de **10×** e não de 2× | [5W §1](FASE-5W-RELATORIO.md) |
| 30 | As amostras das fases de geração correram em «configuração de produção» | **O prompt não.** Nove scripts — Fases 5, 5B, 5G, 5H, 5I, 5M, 5N, 5U e 5W — chamam `contador()` **sem argumento**, o que dava o tokenizador do **encoder**, e esse subconta **17%**: correram com ~350 tokens de gerador onde o orçamento pede **300**. As comparações **dentro** de cada fase ficam intactas, porque os braços partilharam o orçamento; o que fica errado é o rótulo. Na [5W](FASE-5W-RELATORIO.md) escrevi que o braço C era idêntico a produção «byte a byte» — era verdade da **persona** e falso do **orçamento** | `src/tokens.py`, cabeçalho |
| 31 | Os IC destas fases medem a incerteza do resultado | Medem a **incerteza de amostragem dentro da célula**, não a **reprodutibilidade da célula**. A mesma configuração de produção, as mesmas 10 perguntas, 20 amostras: **0,00951** na 5W e **0,00615** na 5X. Os meus intervalos estavam certos e mediam a coisa errada — e isso atravessa a 5T, a 5U, a 5V e a 5W | [5X §1](FASE-5X-RELATORIO.md) |
| 32 | O `X3` da 5X mede dano colateral | Mede-o **sem intervalo**, logo vetou em ruído: metro **−0,0097** com IC **[−0,145, +0,116]**, quinze vezes mais largo que a estimativa. Honrei-o porque estava pré-escrito, mas o que ele veta vale o que vale | [5X §3](FASE-5X-RELATORIO.md) |
| 33 | «A mesma configuração, medida duas vezes, varia 1,54×», e daí um chão de ruído de 1,5 | **Não era a mesma configuração.** Mudei o tokenizador do orçamento entre a 5W e a 5X e **18 das 20 células receberam prompts diferentes** (4 *chunks* contra 3). **E o modelo é determinista:** nas 2 células em que o prompt coincidiu o texto é idêntico **byte a byte**, logo o remédio que prescrevi — «correr o controlo duas vezes» — devolveria resultados iguais. Premissa e remédio errados, publicados com um IC a sustentá-los | emenda da [5X](FASE-5X-RELATORIO.md), horas depois de publicar |
| 34 | «A temperatura vai para o lado errado (−36%)», logo o passo 17 fica sem direcção | **Não é robusto.** Nas **17 células com prompt idêntico entre braços** o braço T dá **1,29×**, não 0,64× — a inversão vinha das 3 células contaminadas pela repetição. E o X1 **melhora**: 1,54× passa a **1,96×** | emenda da [5X](FASE-5X-RELATORIO.md) |
| 35 | Os braços de uma fase emparelhada partilham o prompt | **Não, quando repetem números diferentes de vezes.** A repetição **re-recupera**: a guarda rejeita, o `responder` troca o contexto. Todas as células com prompt divergente são células com tentativas desiguais — 3 de 20 na 5X, 2 de 20 na 5W, **sem excepção**. É um **mediador** e não um confundidor, porque o tratamento pode causar a repetição | emenda da [5X](FASE-5X-RELATORIO.md) |
| 36 | «`reis/L` é a única célula de toda a sequência a reproduzir a distribuição de um poeta» — repetido em **quatro** relatórios | **Inverte** ao excluir as células com prompt divergente: KS 0,1956 contra p95 0,2046 (dentro por **0,009**) passa a 0,2333 contra 0,2294 (fora por 0,004). **Nunca foi robusto** — uma margem de 0,009 num KS sobre 30 amostras não suporta a frase, e era a única das seis células que podia inverter | [5Y §4](FASE-5Y-RELATORIO.md) |
| 37 | «Todas as células com prompt divergente são células com tentativas desiguais, sem excepção» (emenda da 5X) | **Falso**, e eu escrevi-o com base em **duas** fases. Com as nove: **6 células** (5 na 5U, 1 na 5B) têm tentativas **iguais** e prompts diferentes, porque os braços plagiaram poemas diferentes e removeram poemas diferentes. **Uma regularidade confirmada em duas fases é uma hipótese** — que é o que eu acabara de aprender sobre as razões dos juízes | [5Y §2](FASE-5Y-RELATORIO.md) |

| 38 | «A monotonia nos três níveis é a evidência mais forte que consigo — é o que a mecânica prediz e o que uma coincidência não prediz» ([5Z §1.1](FASE-5Z.md), pré-registo) | **Uma coincidência prediz, e previu.** A monotonia verificou-se (0,0075 < 0,0096 < 0,0144) e **inverte ao remover uma célula de vinte** — sem `q34/r1` o braço de 0,9 fica **0,8×** o de produção. Com **44 das 60** amostras a densidade **zero**, a ordenação de três médias é decidida por quais células calharam não ser zero. **Escrevi a força da predição a partir da sua forma lógica, não dos dados que a iam avaliar** | [5Z §1](FASE-5Z-RELATORIO.md) |
| 39 | O sentinela de medição vive em **`data/.medicao-a-correr`** ([FASE-6 §2.4](FASE-6.md), pré-registo do passo 7) | **Caminho relativo, e o serviço público corre num segundo checkout**, logo há **dois `data/`**: a fase escreve no seu e o servidor verifica o outro. O ficheiro nunca é visto, o `/api/estado` diz que está tudo bem, e o mecanismo que existe para tornar o túnel seguro fica **silenciosamente desligado** — a forma «não dá erro: dá respostas erradas» do manifesto do índice, desta vez **no instrumento que protege as medições**. Corrigido para absoluto **antes de o código existir**, que é a primeira vez nesta lista que isso acontece. **E o teste que o apanharia não existia:** com um processo e um directório o portão I8 passava — daí a asserção dos dois checkouts, verificada por mutação | [`PRODUCAO.md`](PRODUCAO.md) §4, achado a planear o túnel |
| 40 | A saída B torna o portão I7′ **verdadeiro por construção**: sem o passo 9 não há rota que devolva corpo de poema, logo o corpo não sai ([`PRODUCAO.md`](PRODUCAO.md) §2, escrito a planear o túnel) | **Verdade para a rota, falso para o serviço.** O varrimento falhou em **três** sítios, todos abertos de propósito pela Fase 6: os `fragmento` da tentativa plagiada (§4.4 manda-a ao fio para explicar a espera), o evento `turno` dela, e o `serial.verso_copiado` — cujo comentário dizia «o verso **gerado** [...] sem o verso original», o que é falso exactamente numa cópia à letra, em que o gerado **é** o original. Medido: 6 de 8 versos do `poem_1005` no fio. **E o achado 1 não se corrige a jusante:** a tentativa sai **em fluxo**, antes de a guarda de plágio existir para a reprovar. Eu raciocinei sobre a rota que serve corpo e não sobre **todas** as rotas que o serviço tem | [`PRODUCAO.md`](PRODUCAO.md) §2.1, achado pelo varrimento do passo 2 |
| 41 | O varrimento do I7′ mede se o corpo vai ao fio (`tests/test_i7.py`, 1.ª versão) | **Não media.** Partia a resposta por `\n` e comparava cada linha com o conjunto do corpus — e o fio é **NDJSON**, onde a mudança de linha de um verso é o par de caracteres `\n` *dentro* de uma cadeia JSON, não uma linha do corpo HTTP. Partido assim, o fio de uma geração inteira são **seis** linhas, e um verso no meio de uma delas nunca é uma linha. **Com a retenção desligada em `app.py`, as oito asserções passaram verdes.** Só a mutação o mostrou — o segundo defeito de instrumento neste mesmo portão, depois do #39. Agora varre por **subcadeia**, no texto cru *e* nas cadeias desserializadas, porque o cru não vê um verso com `"` dentro e as cadeias não vêem corpo que viaje fora de um evento válido | [`PRODUCAO.md`](PRODUCAO.md) §2.1 |
| 42 | Os 2083 ficheiros do corpus **não estão no repositório** — `README.md` §Corpus, e eu repeti-o no [`PRODUCAO.md`](PRODUCAO.md) §0.1 e §5.3 e na entrada da saída B do §3 | **Estão, e há um ano.** `git ls-files data/pessoa_poems/` dá **2083**, estão no `origin/main`, nenhuma regra de ignore os cobre e o repositório é **PÚBLICO**: **241 250 palavras**, entradas em `396cca7` (2025-10-24), o **segundo** commit deste repositório, cuja mensagem — «Major project restructure and documentation» — não as menciona. **E o repositório contradizia-se:** `data/README.md` §Origem registava «Data de entrada no repositório: 2025-10-24» e o commit, na mesma árvore em que o `README.md` dizia o contrário; o que estava certo era o `data/README.md`. O que isto derruba não é uma frase: é a função de direitos que eu dei à **saída B** (o passo 9 nunca reteve nada que um `git clone` não trouxesse) e a justificação do `bind` em `127.0.0.1` no cabeçalho do `src/web/app.py`. **Tomei a afirmação do `README` e não a verifiquei, num documento cujo assunto era o risco de publicar o corpus** — um `git ls-files \| wc -l` resolvia, e é o primeiro comando que devia ter corrido. Alcance medido no mesmo dia: 0 forks, 0 estrelas, 0 visitas, e **289 clones de 128 origens** em 14 dias, que nenhuma reescrita de histórico recupera | levantado em 2026-10-19; `README.md`, `data/README.md`, `src/web/app.py`, [`PRODUCAO.md`](PRODUCAO.md) e §3/§5 deste ficheiro corrigidos. **Decisão sobre o repositório por tomar** |
| 43 | O `.gitignore` mantém as folhas de julgamento fora do repositório público, «porque contêm os poemas INTEIROS» | **Mantém duas, por nome exacto, e a terceira passou.** As linhas excluíam `docs/fase-1/08-folha-julgamento.md` e `docs/fase-0/06b-folha-julgamento.md` — os dois nomes que existiam quando a regra foi escrita. `docs/fase-3b/01-folha-julgamento.md` **está versionada**: 9 075 palavras, 126 poemas. É o mesmo modo de falha da correcção **39** (o caminho relativo do sentinela) numa ferramenta diferente: **um nome exacto não cobre a fase seguinte, e nada avisa** — a regra continua a dizer «certo» sobre os ficheiros que nomeia enquanto deixa passar os que não nomeia. E a mesma família tem mais: os `0*-itens.md` e `0*-chave.json` das fases guardam o **contexto** dado ao modelo, que é o corpo dos poemas recuperados, e cerca de onze ficheiros versionados contêm versos à letra. Corrigido para **padrão** (`docs/**/*folha-julgamento*.md` e os dois acima), o que cobre as fases futuras e **não desversiona** o que já está no índice — desversionar é decisão de direitos, não de `.gitignore` | verificado em 2026-10-19 com `git check-ignore` sobre uma fase inventada (pega) e sobre as já seguidas (continuam seguidas) |
| 44 | O `/api/health` lê o `sha` com `git rev-parse --short HEAD` (`PRODUCAO.md` §6, pré-registo do passo 3) — e o enunciado não dizia **de onde**, nem **quando** | **Duas omissões, e as duas já tinham custado nesta casa.** *De onde:* um `git` sem `-C` segue o `cwd`, que numa unidade de utilizador é o que o `WorkingDirectory` disser — com dois checkouts, respondia **com sucesso** e com o `sha` do checkout de trabalho enquanto o serviço corria o outro. É o #39 outra vez, no instrumento seguinte. *Quando:* por pedido, dizia a verdade sobre o disco e **mentia sobre o processo** — depois de um `git checkout` o `uvicorn` continua a correr os módulos que importou, e a sonda nomeava código que não está em memória, na rota de que o recuo do passo 8 depende. Corrigido para `Path(__file__).resolve().parents[2]` e leitura **à importação**, as duas verificadas a morder | [`PRODUCAO.md`](PRODUCAO.md) §6.1 |
| 45 | «A unidade do túnel é o passo 4» ([`PRODUCAO.md`](PRODUCAO.md) §5, linha do passo 5) | **Nenhum passo do plano instalava o túnel.** A §5.1, que é a lista do passo 4, nomeia só o `pessoabot.service` e o `ollama.service`; o passo 5 escreveu o `tunel.py` para parar uma unidade que apontava para um passo que não a criava, e o passo 6 pressupõe-na. O buraco só apareceu ao tentar dar o passo 6 — e é o tipo de remissão entre passos que parece cobertura e não é | [`PRODUCAO.md`](PRODUCAO.md) §7.1 |
| 46 | O portão **D4** mede-se com `journalctl --since <marca>` e a asserção «o registo não tem o pedido» (1.ª versão da medição, minha) | **Media zero por o fuso estar errado.** A marca vinha de `date -u` e o `journalctl` lê **hora local**: a janela ficava três horas no futuro e o registo vinha vazio. Num portão cuja asserção é «não há linha», um fuso errado é um **falso sucesso** — e o D4 passou assim antes de eu verificar o instrumento com um pedido que *devia* deixar linha. Trocado por **contagem de linhas**, que não tem fuso, e a verificação de que o contador cresce passou a fazer parte do próprio portão. É o mesmo erro que eu tinha acabado de corrigir no `saude.py`, onde o `em_utc` existe precisamente porque «duas sondas a comparar fusos comparam cadeias que diferem por motivo nenhum» | [`PRODUCAO.md`](PRODUCAO.md) §7.1 |
| 47 | «Reinstalar sobre um checkout existente é mudar de referência, que é o que o recuo do passo 8 faz» (minha docstring do `instalar.clonar`) | **Não funcionava, e o dono apanhou-o a correr.** Um clone feito há duas horas não tem os commits de agora, e o `git`, não reconhecendo a referência, interpreta-a como um **caminho**: `--detach does not take a path argument '79e4dbb'` — uma mensagem que manda procurar um erro de sintaxe onde não há nenhum. Eu escrevi a frase sobre o recuo e **nunca corri o caminho do recuo**: a primeira instalação cria o checkout, logo exercita o outro ramo. Corrigido com `git fetch` antes do `checkout` e verificação de que a referência resolve; três testes novos, dois deles verificados a morder | [`PRODUCAO.md`](PRODUCAO.md) §7.1 |
| 48 | A instalação deixa o serviço a correr o código instalado (implícito em todo o `instalar.py`, e no passo 4 dado por feito) | **`systemctl --user enable --now` arranca uma unidade inactiva e não toca numa que já corra.** O checkout passou a `79e4dbb` e o processo continuou a servir `734f77a`, com os dois comandos a devolver **0**. Num recuo é o pior caso: o `git checkout` «sucede», o `systemctl` «sucede», e o código doente continua a responder. **Quem o disse foi o `/api/health`** — e só o disse porque o `sha` é lido à importação e nomeia o que está em memória (correcção 44); lido por pedido, teria respondido o do disco e o defeito ficava invisível na rota que existe para o tornar visível. Corrigido com `restart`, e a instalação passou a **conferir-se pela saúde do serviço** e a devolver 1 se divergir | [`PRODUCAO.md`](PRODUCAO.md) §7.1 |
| 49 | O URL do túnel lê-se do registo da unidade (`instalar.url_do_tunel`, 1.ª versão, minha) | **Devolvia o da execução anterior.** Lido logo a seguir ao `restart`, o registo ainda não tinha o URL novo, e o instalador imprimiu `keyboards-auburn-bean-apparent` quando o túnel a correr já era `charging-arrangements-whether-burst`. **Um URL morto com ar de bom é pior do que nenhum**: quem o recebe culpa o serviço. Corrigido para ler desde o `ActiveEnterTimestamp` que o systemd reporta, no mesmo fuso em que o `journalctl` lê — a correcção 46 outra vez, três horas depois dela. Três defeitos meus no mesmo dia, todos da forma «respondeu com sucesso e com a coisa errada» | [`PRODUCAO.md`](PRODUCAO.md) §7.1 |
| 50 | O `Restart=on-failure` da unidade do túnel cobre a queda do túnel (implícito na unidade que escrevi no passo 6) | **Não cobre nada: o `cloudflared` não falha, insiste.** Na noite de 19 para 20/10 a máquina **suspendeu** às 02:22, e ao acordar a Cloudflare já tinha largado o registo do *quick tunnel*: `Unauthorized: Tunnel not found`, **1019 tentativas em dez horas**, com `systemctl --user is-active` a responder **`active`** e `NRestarts=0` o tempo todo. O processo está vivo, logo o systemd não tem o que reiniciar, logo a unidade fica activa com o URL a dar `NXDOMAIN` no navegador do dono. **«A unidade está activa» deixou de ser evidência de «o serviço está acessível»** — é a separação do I7′ outra vez, noutro par de conceitos. O túnel durou **4 h 42 min**, e o que o matou foi a máquina dormir | [`PRODUCAO.md`](PRODUCAO.md) §7.2, observado pelo dono no navegador |
| 51 | Correr o instalador é inócuo para quem está a usar o serviço (implícito no `instalar.py` desde o passo 4) | **Trocava o URL a quem estava autenticado.** Instalar a guarda reiniciou o `cloudflared` por tabela, e o URL mudou com o dono dentro da página. Reiniciar não custa o mesmo em cada unidade: o `pessoabot` tem de reiniciar sempre, o `ollama` descarrega 4,9 GB e a pergunta seguinte paga ~50 s de prefill, e o `cloudflared` **troca o URL**. Agora só reinicia o que mudou — e o túnel só se a unidade mudar ou o URL não responder | [`PRODUCAO.md`](PRODUCAO.md) §7.3, observado pelo dono |
| 52 | A unidade da guarda, instalada com sucesso, guarda | **Não guardava.** A unidade é escrita pelo checkout de **trabalho** e corre o código do checkout do **serviço**, que está preso numa referência — e saiu a invocar `--guardar-tunel` numa referência onde a opção não existia. O `enable --now` devolveu **0**, o temporizador ficou agendado, e a primeira passagem morreu com `status=2/INVALIDARGUMENT`: uma guarda instalada com sucesso e incapaz de guardar. **A §4 não previa esta acoplagem** — a unidade pode pedir ao serviço uma capacidade que a referência servida não tem. Remédio igual ao do `conferir_sha`: corre-se a guarda uma vez em vez de acreditar no código de saída | [`PRODUCAO.md`](PRODUCAO.md) §7.3 |
| 53 | O defeito do `cloudflared` tem o sintoma de «um POST JSON de mesma origem a devolver 401» (minha leitura do [#1752](https://github.com/cloudflare/cloudflared/issues/1752), escrita na §7.1) | **O POST não é especial: a sessão morre.** Medido a 2026-10-20 com um relógio independente — a página sonda o `/api/estado` de **3 em 3 s** (`app.js:53`), e o registo do serviço tem 7 pedidos entre 09:45:32 e **09:45:36**, todos `GET`, e **nenhum** depois. A sessão autenticada durou **4 segundos**; o POST foi só a primeira coisa que o utilizador fez depois disso. Eu tinha repetido a descrição do relator, que não tinha uma sonda periódica para ver o resto | [`PRODUCAO.md`](PRODUCAO.md) §7.4 |
| 54 | O portão **D5** mede-se comparando os instantes de túnel de pé com «os instantes das amostras» ([`PRODUCAO.md`](PRODUCAO.md) §9, pré-registo do passo 7) | **As amostras não têm instante nenhum.** Os dez `01-cru.jsonl` das Fases 5B a 5Z têm `segundos`, que é uma **duração**, e nunca ninguém escreveu quando cada amostra aconteceu — verificado campo a campo. O portão pedia uma comparação entre dois conjuntos de instantes e só existe um. Dar-lhes instantes obrigava a mexer nos `gerar_amostras.py`, que esta casa não reescreve. A asserção passou a «o ficheiro das amostras só cresceu dentro da janela», que se mede hoje sem tocar em nada e apanha o modo de falha que importa — a fase ter corrido **fora** do ajudante | [`PRODUCAO.md`](PRODUCAO.md) §3.6 |
| 55 | Um `git fetch --prune origin` chega para alcançar a etiqueta de um recuo (`instalar.clonar`, correcção 47 — minha, e feita há horas) | **Não chega para a etiqueta que importa.** O `fetch` traz só as etiquetas **alcançáveis a partir dos ramos que buscou**, e a etiqueta de uma versão doente é precisamente a que pode não estar em ramo nenhum: no ensaio do D6 o commit doente foi feito num ramo apagado a seguir, de propósito, para não entrar no `main`. O recuo recusou uma etiqueta que existia no checkout de trabalho, com uma mensagem correcta sobre uma causa que não era aquela. **Só o ensaio a sério o encontrou** — e é exactamente para isso que o D6 exige um ensaio e não uma simulação | [`PRODUCAO.md`](PRODUCAO.md) §5.5 |
| 56 | Desligar o túnel pelo `tunel-desligado` mantém-no desligado (minha, ao escrever a §7.5 há duas horas) | **A guarda ressuscitou-o.** `systemctl --user restart` **arranca uma unidade desactivada** — o `disable` tira-a do arranque, **não a tranca**. A guarda, que só olhava para o URL, via o último URL do registo a não responder, concluía «morreu» e levantava o túnel outra vez, **de cinco em cinco minutos**, contra uma decisão tomada sobre uma medição. Observado a 2026-10-20: o túnel estava público em `pubmed-earn-belief-consultant` quando eu fui medir a máquina para o `SERVICO.md`, horas depois de o ter dado por fechado. **Um mecanismo automático a desfazer uma decisão de segurança** — a família inteira que este plano persegue, desta vez construída por mim no mesmo dia. A `decidir_guarda` ganhou uma quarta recusa, à frente de todas | [`PRODUCAO.md`](PRODUCAO.md) §7.6 |
| 50 | «O `test_i5_o_fluxo_cancelado_nao_deixa_o_servidor_avariado` mede que o servidor sobrevive a um cancelamento» — e, quando falhava, a sua própria mensagem: «a geração seguinte não acabou» (minha, no passo 6 da [`FASE-6.md`](FASE-6.md)) | **Quem avariava era o duplo, e o portão culpava o código medido.** O `_OllamaFalso` lia o pedido com **um `recv` só** e fechava a ligação no fim; o pedido do servidor são **3260 bytes** (209 de cabeçalhos e 3051 de corpo, o prompt com os oito chunks) e com a máquina ocupada chega em dois segmentos. Um `close()` sobre um socket com dados por ler **manda RST, não FIN**: o cliente perdia a resposta em trânsito e levantava `ChunkedEncodingError: ConnectionResetError(104)`, que o `_eventos` punha no fio como evento `erro`. Correlação perfeita nas falhas medidas: `pendentes_no_fecho=3051` em todas as que falharam e `0` em todas as que passaram. **Verificado por mutação, sob seis processos a queimar CPU:** com o `recv` único, **16 e 8 falhas em 100**; com o pedido lido até ao fim, **0 em 100**. Sem carga passava 455 vezes seguidas — e foi a máquina a ganhar um serviço e um Ollama permanentes (passo 4 do [`PRODUCAO.md`](PRODUCAO.md)) que tornou visível o que já lá estava. **E o mesmo teste afirmava uma segunda coisa que o portão não promete:** pedia outra vez sem esperar pelo trinco, quando o I5 diz «em menos de 2 s»; nessa janela — o `await tarefa` do `fluxo.py` devolve o controlo ao laço — o `POST` apanhava **409 `ocupado` em 25 de 50 corridas**, e o teste desserializava o 409 como lista de eventos e falhava a dizer a coisa errada. Corrigidos os dois: o duplo drena o pedido, o teste espera o trinco como o seu irmão já fazia, e confere o `status_code` antes dos eventos. **O portão I5 não mudou de forma** | [`tests/test_cancelar.py`](../tests/test_cancelar.py); levantado em 2026-10-19 |

### Defeitos encontrados nos meus próprios instrumentos

| Defeito | Consequência se não apanhado |
|---|---|
| **KV cache reaproveitado** entre repetições do benchmark | Prefill reportado a **25 625 tok/s**; 4 h de dados inválidos |
| Flag de throttling com `REPS=2` | «Queda monotónica» = 50% por ruído; não-informativa |
| `repeat_penalty` não definido | 8B degenerou em ciclo; atribuído ao modelo em vez do arranque |
| Avaliação de voz **não cega** | Viés específico que mudou a recomendação de modelo |
| Limpeza de título apagava 3 poemas | «Vou atirar uma bomba ao destino.» — título **é** o poema |
| Sem pausa de arrefecimento no bench de rerank | Variância de 6x na mesma configuração |
| Jaccard de n-gramas para variantes | Não separa variantes de poemas distintos |
| Fracção de stopwords tomada por teste de língua | Verso telegráfico dado por língua errada: 38 s de regeneração por uma resposta boa |
| `fracao_lingua` caindo no pt quando a língua é `?` | 4 poemas reais dados por língua errada |
| Buffer do CLI sem `remover_preambulo` | O ecrã mostrava mais do que o veredicto julgara |
| `REFORCO_EN` nunca usado no caminho do CLI | Sessão em inglês recebia o reforço em português |
| Medição condicionada a re-observar um evento estocástico | 0/3 plágios na 1.ª tentativa: zero dados |
| Dois lados de uma comparação contados por **definições diferentes** de verso | «O llama reproduz o poeta»: real por linhas não vazias, gerado por `_versos` (≥3 palavras) |
| Contagem de versos resolvida pelo **primeiro chunk** e não pelo poema | `max` publicado como 48 quando é **161**; fracções salvas por acaso (os 5 multi-chunk já estavam acima de 20) |
| Intervalo central usado para medir **dispersão** | critério por amostra a tentar medir propriedade de um conjunto: contém o poeta **ou** discrimina, nunca os dois |
| Pedido HTTP lido com **um `recv` só** num duplo de servidor | `close()` com dados por ler manda **RST**: o cliente perde a resposta em trânsito e o portão I5 acusava o servidor de avariar depois de um cancelamento (correcção **50**) |
| Portão a exigir **de imediato** o que a sua própria afirmação dá até 2 s | 409 `ocupado` desserializado como lista de eventos: o teste falhava a nomear a causa errada, e só com a máquina ocupada (correcção **50**) |
| Chave de rima a excluir **palavras iguais** e não **terminações repetidas** | `toque`/`que` contado como rima: **a célula que decide a 5Z** e, com ela, a monotonia pré-registada. Inflaciona todas as densidades publicadas desde a 5W, incluindo as do poeta, que é a régua |

---

## 5. Limitações conhecidas, não resolvidas

**As pontuações de 3b anteriores a 2026-10-06 não são comparáveis com as
posteriores.** A [Fase 5L](FASE-5L.md) retirou da âncora a contagem de versos
por poema, e essa cláusula tinha sido aplicada em **68 de 69** casos
aplicáveis: até **65 das 180** notas históricas (**36%**) estariam diferentes
sob a âncora nova. Afecta o **I1/I2 da 5I** e o **M3 da 5H**, que são leituras
de 3b. **Não afecta** nada medido em 3a′ — o M1 da 5H, a 5F, a 5G —, porque a
cláusula nunca entrou no 3a. As 180 notas **não foram repontuadas**: custaria o
mesmo que a corrida que as gerou e não serve nenhuma pergunta aberta.

| Limitação | Impacto | Estado |
|---|---|---|
| Representante de variantes é «o mais longo» | Em `poem_1000`/`poem_629` elege o que tem erro de transcrição | aceite; sem correcção barata |
| Duplicação por tradução não detectável | `poem_1794` fica no corpus | resolvida pelo filtro de idioma |
| Avaliação de voz com **um só avaliador** | Não é medição intersubjectiva | assumido |
| Throttling térmico até 101 °C | Latências com precisão menor que as casas decimais sugerem | ressalva registada |
| Qualidade do reranker em PT-PT desconhecida | Pode piorar o ranking | mede-se no Passo 2 da Fase 3 |
| ~~**Sem copiar, nem sempre é a voz pedida**~~ | **medido na Fase 5**: é verdade que nem sempre é — o Caeiro dá 0,0 de mediana em poética. Mas a explicação estava **errada**: ele quebra a interdição **sem contexto nenhum**, e a ablação dá 4 pares contra 4 | ✅ fechada, e o suspeito absolvido |
| Alguns poemas são atractores (`poem_3426`, `poem_2832`) | muito recuperados e muito copiados | pode exigir MMR na recuperação |
| **Streaming imprime antes de validar** | só o 1.º verso é retido; brasileirismos a meio só são avisados | aceite; buffer total custaria o streaming. ⚠️ **Deixou de ser só de qualidade quando o serviço passou a ser público:** o que sai antes de validar inclui **corpo de poema**, na tentativa que a guarda de plágio ia reprovar (6 de 8 versos, medido). Resolvido **para o corpo** por `src/web/retencao.py` — retenção por linha, portão I7′, [`PRODUCAO.md`](PRODUCAO.md) §2.1 —, e **não** para os brasileirismos, que continuam a sair antes de haver veredicto |
| Enviesamento de pooling | sistema novo é penalizado por construção | procedimento escrito no topo de `test_retrieval_gold.py` |
| Pool de top-5 era raso | 3 gabaritos estavam em 6.º–9.º | top-10 na próxima ronda |
| **Tabacaria em 37.º sem explicação** | hipótese do chunking testada e refutada | investigar chunk a chunk |
| Recolha do corpus não reproduzível | nenhum script no histórico | registado em `data/README.md` |
| `src/main.py` e companhia ainda no repo | Dois sistemas em paralelo | até ao Passo 9 |

### Uma ressalva à conclusão da Fase 4, encontrada na Fase 5

O Passo A1c da Fase 4 concluiu que **«o espaço do e5 não separa estas vozes»**,
dos 42–46% obtidos a rotear poemas reais. O instrumento estava handicapado:
`fase-4/bench_roteador_c.py:91–95` encoda os poemas de teste como `query` a
partir de `chunk.text` — verso puro — contra centróides construídos de
`indexed_text`, que leva **«Autor — Título»** à cabeça. O nome do heterónimo é o
indício mais discriminativo da tarefa, está no centróide e não está em consulta
nenhuma; os 42–46% saem **subestimados**.

**Remedido: o defeito valia 23 pontos em perguntas e 22 em poemas, e a afirmação
está refutada.** Com centróides de `c.text`, as perguntas vão de 45% para **68%**
e os poemas de 42% para **64%**. O espaço do e5 **separa** estas vozes.

E o **colapso no Caeiro era artefacto do nome**: nas perguntas, os erros a
apontar para o Caeiro caem de **19 para 1**, e o que sobra colapsa no ortónimo
(12), que é a classe maior — o comportamento banal que a tabela de riscos da
Fase 4 previa e que não se observou, porque o nome produzia o inverso.

**Mas a tabela de coerência sobrevive**, e é aqui que está a lição mais fina
desta correcção. Sem o nome, as quatro vozes continuam iguais entre si
(0,928–0,930 contra 0,934–0,939). A observação «as quatro vozes têm coerência
interna igual» **não** era artefacto; artefacto era o **facto que ela
explicava** — o colapso no Caeiro. Ficou uma medição correcta a explicar um
fenómeno que não existe, o que é um modo de falha diferente de «o número estava
errado», e mais difícil de apanhar: a medição resiste a toda a verificação, e é
a pergunta que ela responde que não existe.

E a decisão fica em dúvida, ao contrário do que eu escrevi aqui primeiro. O
roteador por LLM faz 72%: contra 45% eram +27 pontos, contra 68% são **+4**, e
+4 a n=40 não se distinguem de zero pelo mesmo critério que a Fase 3B usou para
preferir a configuração mais barata. O roteador não está **estabelecido** como
melhor — o que não é o mesmo que estar refutado: o LLM foi medido num conjunto
adversarial e numa ablação de indícios, e o centróide não, logo a robustez não
está comparada. **O que decidiria** está nomeado: correr o centróide `sem_nome`
nas 12 perguntas adversariais e nas 40 abladas. O 7B aguentou 72%→70% com os
substantivos-assinatura removidos, e um centróide que vive de superfície lexical
é precisamente o que deveria desabar nesse teste. A correcção vive na Fase 4;
aqui fica o ponteiro.

Para a Fase 5 o defeito era inócuo na **diferença**, e é por isso que o
Instrumento II passou a correr as duas variantes de centróide em vez de só a
contaminada — ver [`FASE-5.md`](FASE-5.md) §9.3.

---

### Sobre direitos

Fernando Pessoa morreu em 1935; obra em domínio público em Portugal e no Brasil
desde 2006. ~~**Sem impedimento legal.**~~ Mas a origem dos 2083 ficheiros não
está registada em nenhum lugar — de onde vieram, em que data, sob que licença. É
requisito de reprodutibilidade e continua pendente.

⚠️ **O «sem impedimento legal» é sobre a obra, e a questão nunca foi a obra.**
É a **transcrição**: `data/README.md` §Situação de direitos escreve-o com
cuidado — «a obra estar em domínio público não implica que uma transcrição ou
edição crítica específica o esteja», e «os ficheiros aqui vêm de uma edição
digital concreta, não de manuscritos». Esta linha resumia essa secção
apagando-lhe a distinção que ela existe para fazer, e com a procedência
pendente a frase não tinha como ser verificada em nenhum sentido.

E o que a torna mais do que imprecisa, medido em 2026-10-19: os 2083 ficheiros
estão **versionados num repositório público** desde `396cca7` (2025-10-24) —
**241 250 palavras** —, mais uma terceira folha de julgamento
(`docs/fase-3b/01-folha-julgamento.md`, 9 075 palavras) e corpos de poemas em
cerca de onze ficheiros de fases. `data/README.md` diz «para distribuir o
corpus ou publicar um serviço que o sirva, confirmar os termos do Arquivo
Pessoa primeiro», e a distribuição aconteceu há um ano. Correcções **42** e
**43** do §4; levantamento e opções feitos, **decisão por tomar**, nada
alterado no histórico nem na visibilidade.

---

## 6. Próximos passos

> As Fases 1 a 4 estão feitas. Esta secção descrevia o «imediato» como sendo o
> Passo 5 da Fase 1 e ficou para trás quatro fases seguidas; o que estava aqui
> é agora história e vive nos relatórios por fase.

### Feito — a reordenação, que a Fase 4 reabriu e a 3B decidiu

A Fase 4 mediu a folga (oráculo@20 contra o denso) e a [Fase 3B](FASE-3B-RELATORIO.md)
foi buscá-la. O que a desbloqueou não foi modelo nem máquina: foi **fechar o
pool de candidatos**, julgando os 142 poemas do top-20 do denso que faltavam.

> As três razões que dei aqui para reabrir isto estavam duas erradas, e o
> relatório da Fase 3 já o dizia: «**a latência não é o obstáculo**». A iGPU nem
> se aplica — os 6x são do backend Vulkan do Ollama e um cross-encoder corre em
> PyTorch. O obstáculo era o instrumento. Ver [`FASE-3B.md`](FASE-3B.md) §1.

Resultado: **+0,090 de nDCG@5** com 16 das 20 perguntas a melhorar (p=0,012),
por 2,6 s, em `/rerank`. Captura 24% dos 0,374 do oráculo.

### Depois, em ordem

| | Passo | Desbloqueia |
|---|---|---|
| 1 | ~~**A voz gerada é a voz pedida?**~~ — **medida**: não é, e o contexto não é a causa | ✅ [Fase 5](FASE-5-RELATORIO.md). Fecha a pergunta aberta desde a Fase 1 Passo 7 |
| 2 | Julgar as outras 20 perguntas, ou um segundo avaliador | a magnitude dos Δ, que a n=20 fica em IC95% de 0,17 de largura |
| 3 | **Fase 6** — FastAPI, Gradio, histórico, `AnthropicRemote` | — |

### Depois da Fase 5, o que ela deixou nomeado

| | passo | porquê |
|---|---|---|
| 1 | ~~**A persona do Caeiro, feita de interdições**~~ — **medida, e sem veredicto** | [Fase 5B](FASE-5B-RELATORIO.md): a ablação correu com 60 amostras e dois avaliadores, e o portão **G4** disparou nos dois. O critério 3a não tem resolução onde era preciso, logo a hipótese continua aberta — ver o passo 5 |
| 2 | ~~**Um segundo avaliador**~~ — **feito** na Fase 5B | R2 foi cego ao **desenho** e não só à condição: não soube que havia dois braços nem qual era a hipótese. κ=0,301 em 3a com 81,7% de concordância exacta, e nenhuma discordância acima de 1 ponto em 60 amostras. Ressalva: são sessões do mesmo modelo a ler as mesmas âncoras, logo pode ser **erro correlacionado** |
| 3 | **`num_predict` para Campos** | 3 truncaturas em 40, pendência já conhecida desde a Fase 4 |
| 4 | ~~A sombra lexical do Caeiro~~ — **respondido, e negativo** | [Fase 5C](FASE-5C-RELATORIO.md): a regra foi construída como o §11 pedia e **reprovou na validação retida** (AUC 0,544). Não fica pendente. Bónus: a lista vinda do **corpus** correlaciona ρ≈−0,28 com o 3a e a vinda da **persona** ρ≈0, o que dá o primeiro número ao princípio do §11 |
| 5 | ~~**Um desfecho com resolução**~~ — **resolvido na 5D**, e não é o que falta | a [Fase 5D](FASE-5D-RELATORIO.md) deu 38 valores distintos contra 3, sem confundidor de comprimento (V3 e V5 passam nos dois contadores). O instrumento é rejeitado por **validade** (V4), não por resolução — e o que o bloqueia agora é o passo 7, não a escala |
| 6 | **Medir o plágio por amostra, e não só como critério de aprovação** | ver o §4 do [relatório da 5B](FASE-5B-RELATORIO.md): as três únicas amostras que chegaram a 3a=2 tinham, as três, um poema real de Caeiro **no prompt**, e uma delas é uma transposição com 33% dos versos copiados. Onde a poética chegou ao topo, chegou por cópia |
| 7 | ~~**Pontuar os poemas REAIS de Caeiro com a âncora de 3a**~~ — **feito, e a âncora reprova-os** | [Fase 5E](FASE-5E-RELATORIO.md): 3 de 20 autênticos com a nota máxima (15%), 7 de 20 a **zero** nos dois avaliadores, e o único item **gerado** a atingir o máximo é a amostra que a 5B §4 apanhou a copiar 33% dos versos. A âncora é um bom **filtro negativo** (ortónimo a 19/20 zeros) e uma má **medida positiva** |
| 8 | ~~**A regra 2 tem de decidir sobre a tautologia deflacionária**~~ — **decidido** | a âncora da [5F](FASE-5F.md) §2.1 regra 2 fixa-o: **a tautologia deflacionária é a assinatura do Caeiro, não um defeito**. «As coisas são só o que são» conta **para** a nota máxima |
| 9 | ~~**Recalibrar a âncora de 3a do Caeiro**~~ — **feito, e aceite** | [Fase 5F](FASE-5F-RELATORIO.md): a âncora passa a medir a **direcção** do movimento e não a sua presença — o Caeiro filosofa para **fechar a porta**, o ortónimo para a abrir. Validada em **24 poemas retidos** que eu nunca li, com os três portões a passar nos três avaliadores |
| 10 | ~~**Repetir a Fase 5B com a âncora nova**~~ — **feita, e H5B cai** | [Fase 5G](FASE-5G-RELATORIO.md): G2 nas três leituras, G5 não dispara. A âncora nova entregou o que a sequência de instrumentação prometia — 17 pares discordantes contra os 7 da 5B |
| 11 | **Replicar, com portão, a separação gerado/real** | a [5F](FASE-5F-RELATORIO.md) §2 deu AUC 0,851 com p=0,0003, mas foi pré-registada **sem portão** porque a 5E tinha mostrado falta de potência a n=20. Um resultado forte onde a potência era baixa pede replicação |
| 12 | **A fronteira 0/1 da âncora** — reapontada e agora com dados | era «a fronteira 1/2» e a [5P](FASE-5P-RELATORIO.md) mostrou que o alvo é o **0/1**, que é o que o R2 tinha dito de dentro da cegueira na 5G: «quando a personificação era incidental e o fecho era deflacionário, dei **1 em vez de 0**». O defeito medido: a âncora **nova** ainda dá **0** a poemas **autênticos** de Caeiro — **4 de 24 (17%)** sob o R1 e 2 de 24 sob o R2 —, contra os 35% da antiga que a 5E criticou. **Melhorou e não está resolvido.** Os casos difíceis a escrever são `poem_2587`, `poem_3421`, `poem_3436` e `poem_3518`, e são poemas **do próprio poeta** |
| 13 | ~~**Trocar o modelo e remedir com a âncora 3a′**~~ — **feito, e era o modelo** | [Fase 5H](FASE-5H-RELATORIO.md): M1 nas três leituras, Δ=+0,700 com p=0,0002. E o llama ganhou **a correr nas condições do adversário** — `repeat_penalty` e `num_predict` foram calibrados na Fase 0 para o qwen —, logo o Δ é um **piso**. O confundidor do contexto foi verificado ausente por asserção byte a byte nas 10 perguntas |
| 14 | O terceiro braço: **negação que não nomeia** | desfaz a fusão que a [5B §2.1](FASE-5B.md) declarou e a 5G herdou — a variante afirmativa inverte a polaridade **e** deixa de nomear os referentes, e nenhuma das duas fases separou as duas coisas |
| 15 | ~~**A forma do llama3.1**~~ — **medida, e o reforço não passa** | [Fase 5I](FASE-5I-RELATORIO.md): I1 e I2 falham. E corrigiu-me a ordem — eu tinha escrito que o `num_predict` «não é o constrangimento», o que era verdade **sem** o reforço e falso **com** ele. Os dois são um par, e eu testei-os em sequência |
| 16 | **As outras três vozes com os dois modelos** — **metade feita** (forma); a outra bloqueada no passo 25 | [Fase 5M](FASE-5M-RELATORIO.md) mediu a **forma** nas 8 células e **retira a condição que o M3 da 5H pôs à troca**: o custo é **do Caeiro**, e fora dele a troca **melhora** a forma. O **conteúdo** das outras três vozes não pode ser medido com o instrumento que existe — a âncora 3a′ é do Caeiro —, logo a decisão da troca continua em aberto, agora pelo passo **25** e não por falta de corrida |
| 19 | ~~**Verificar se o intervalo de 10–20 versos da âncora de 3b é real**~~ — **feito, e não é; mas o remédio é pior** | [Fase 5J](FASE-5J-RELATORIO.md): **J1 dispara** (3 de 4 vozes, e as três falham **para baixo** — os pisos das personas estão altos demais), **J3 e J4 disparam**, e **J2 não**. O «défice de forma» do llama **não** é artefacto do instrumento: o llama está mais longe do poeta, não mais perto, e a frase da 5I §9.2 veio de uma coincidência de **um escalar**. O J4 valida `[4,31]` a 86% em dados retidos e a consequência mata-o: **100% aos dois modelos contra 86% do poeta**. A prescrição é **retirar** a contagem de versos do 3b, porque a dispersão do Caeiro (1 a 161 versos) é propriedade de **um conjunto** e não de um poema |
| 20 | **O par reforço + `num_predict`, medidos juntos** — a 5J **confirma-lhe o motivo**, e retira o segundo que eu lhe tinha dado | o §5 da [5J](FASE-5J.md) escreveu antes de medir que, se o J1 **e** o J2 disparassem, este passo ficaria sem motivo. **O J2 não disparou**: o llama escreve curto a sério (mediana 7,5 contra 11,5 do poeta). O segundo motivo que eu publiquei — um tecto a censurar a gama alta — **não existe**: são 220 e não 150, e na 5H houve 1 truncatura em 60 ([5J §2.3](FASE-5J-RELATORIO.md)). É o **reforço** que faz o tecto morder, logo os dois **têm** de ir juntos — que é o que este passo já dizia |
| 17 | **Afinar as opções por modelo** — **medida, e as duas direcções são para cima** | a [5X](FASE-5X-RELATORIO.md) correu as duas opções com hipótese no ortónimo. Nas **17 células com prompt limpo**: `repeat_penalty=1.0` dá **1,96×** a densidade de rima e `temperature=0.5` dá **1,29×** — as duas acima de produção, nenhuma a excluir zero. A leitura publicada primeiro («a temperatura vai para o lado errado») **caiu na emenda**: vinha de 3 células contaminadas pela repetição |
| 17b | **E a 5Z não replica o 1,96×** | a [5Z](FASE-5Z-RELATORIO.md) remediu `repeat_penalty=1,0` contra produção no desfecho **limpo** da 1.ª tentativa e deu **1,28×**, IC [−0,0083, +0,0116] — robusto a tirar a célula mais alta (1,29×) e a melhor contagem de sinais da fase (**7 contra 2**), mas a conter zero. **A direcção repete-se em duas fases e o tamanho não**: 1,96× era o topo de um intervalo, não uma estimativa. E o terceiro nível, `0,9`, **degenera** |
| 18 | ~~**O `qwen2.5:3b`**, instalado e nunca medido~~ — **feito: é família** | [Fase 5N](FASE-5N-RELATORIO.md): o N2 dispara. **+145%** de capacidade dentro da família qwen rendem **+0,400** em 3a′ e não passam o limiar; os **+5%** da 5H com mudança de família renderam **+0,700**. Se a capacidade fosse o motor, o salto grande teria de render mais. O N1 **não** dispara, logo a leitura é «**não se mostrou** que 145% melhorem o 3a′», não «mostrou-se que não melhoram». Vale **na família qwen, nesta gama** — o `llama3.1:3b` não está instalado |
| 21 | ~~**Um critério de forma ao nível do conjunto**~~ — **calibrado e aceite** | [Fase 5K](FASE-5K-RELATORIO.md): o KS ao corpus bate a conformidade nos dois braços (AUC 0,999 e 1,000 contra 0,000 e 0,784), com Δ a excluir 0. Tem **chão** (nulo empírico: p95 de 0,190 a n=30) e **régua** (0,149–0,317 entre vozes reais). Instrumento em [`fase-5j/analisar.py`](fase-5j/analisar.py), calibração em [`fase-5k/01-nulo.json`](fase-5k/) |
| 22 | ~~**Retirar a cláusula de comprimento da âncora de 3b**~~ — **feito** | [Fase 5L](FASE-5L.md): a [Fase 5 §5.2](FASE-5.md) está alterada nas quatro vozes, com a âncora original preservada para ler as pontuações antigas. O caso do **Reis** fechou o argumento — intervalo **correcto** e **invertido** ao mesmo tempo —, logo a correcção descritiva não salva um escalar. Nota de compatibilidade no §3 da 5L |
| 23 | **Os limiares de estrofe e de verso, que ficaram sem teste** | a 5L retirou os limiares por **poema** e deixou ficar `estrofes de 3–4 versos`, `quadras ou quintilhas`, `linhas curtas` e `versículo longo` — comprimentos de **estrofe** e de **linha**, que a 5J nunca mediu. Pela mesma lógica podem ter o mesmo defeito, e o teste é o mesmo: contar no corpus real e ver se o intervalo descreve o poeta |
| 29 | ~~**Um detector de superfície derivado do corpus**~~ — **feito, e não passa: a causa é o tamanho do corpus** | [Fase 5R](FASE-5R-RELATORIO.md): a via mecânica dá **ou** um detector seguro com **6%** de cobertura (razão 20×, 0,73% de falsos positivos) **ou** um com 33% de cobertura e **2,18%** de falsos positivos. Nenhum serve. As canónicas que faziam falta são raras — `objecto` **8×**, `ténue` **7×**, `eléctricas` **2×** — e exigir uma razão segura a uma canónica de 8 ocorrências é impossível. **O limite é de 2083 poemas, não do método.** A lista à mão fica **vetada**: das onze formas que eu vi, três estão em Pessoa |
| 30 | ~~**Rejeitar a truncatura na guarda**~~ — **feito, e está em produção** | `Turno.aprovado` passa a exigir `not resposta.truncada`, e a condição de repetição do `responder` concorda com ela. O campo vinha de `done_reason == "length"` e era **gravado e não usado**: na 5Q **cinco de 48** amostras chegaram à folha cortadas a meio da **palavra**. Custo esperado ~3 s por pergunta a 10% de ocorrência. +1 teste, **238** |
| 31–33 | ~~**O léxico externo, rejeitar desconhecidas, o detector como aviso**~~ — **a via está fechada**, verificado em 2026-10-08 | as três eram variantes da detecção ortográfica, e ela não dá: (a) o **corpus** não distingue gralha de homografia — `forca` é «tenho os nervos na **forca**», `magoa` é «inda que **magoa**, é vida», `es` é «Dar-**es**-Salaam», e eu classifiquei as três como gralhas **pela razão de frequência**, que não mede ambiguidade; (b) o **dicionário** é a norma de 2026 e **aceita** `objeto`, `eletricas`, `silencio`, `veem` — o [`src/lexico.py`](../src/lexico.py) já o documentava desde 2026-10-01. A intersecção das duas autoridades não resolve esta classe |
| 35 | ~~**Ablação da instrução de língua**~~ — **corrida, e sem poder** | a [5U](FASE-5U-RELATORIO.md) correu-a: 120 amostras, braços emparelhados por célula. Remover a instrução **nunca piorou** a superfície (seis estimativas com o mesmo sinal) e **nenhuma exclui zero**, porque o braço de base tem 2 ocorrências de próclise e 1 marca ortográfica em 60. **Fica sem resposta por falta de eventos, não por falta de corrida** — e repeti-la só vale com uma taxa de base que dê eventos. Deixa registada a hipótese da **escorva**: o bloco traz três exemplos com clítico, e o braço completo usa 54 clíticos contra 38 do ablado |
| 36 | **O AUC ao poeta nas três vozes** — **e eu descrevi-o mal** | escrevi na 5U §4 que o instrumento «é **mecânico** e corpus-fundado». **Não é mecânico**: o `fase-5f/analisar.py` calcula a AUC sobre `c3a`, que são as pontuações da âncora 3a′ dadas por um **avaliador cego** (ver a correcção 24 do §4). É corpus-**fundado** — o conjunto de comparação são poemas reais — e isso é o que evita o erro da 5E, mas a pontuação é humana. Logo este passo **depende do passo 25** (uma âncora por voz) e não é a via barata que eu lhe chamei |
| 42 | ~~**A repetição re-recupera**~~ — **auditado na [5Y](FASE-5Y-RELATORIO.md)** | contaminação medida nas nove fases: 5G 40%, 5B 23%, 5M 19%, 5H 17%, 5X 15%, 5U 12%, 5W 10%, 5I 7%, 5N 0%. **O +0,700 da 5H sobrevive** (+0,660 limpo) e com ele a troca de modelo; **`reis/L` da 5M inverte**. O que fica é o passo 43 |
| 43 | ~~**Registar as tentativas, e não só a última**~~ — **feito, e em `src/`** | `Tentativa` e `Turno.historico` em [`src/pipeline.py`](../src/pipeline.py), com `Turno.primeira` para o caso que interessa. **Sem mudança de comportamento**: o histórico é acumulado nos dois caminhos (`responder` e `responder_em_fluxo`) e o campo tem omissão `()` para não quebrar quem constrói `Turno` à mão. Quatro testes, um dos quais fixa que a 2.ª tentativa **tem** contexto diferente da 1.ª — que é o mediador que a [5Y](FASE-5Y-RELATORIO.md) mediu. **Desbloqueia o [passo 40](#)** |
| 40 | ~~**Testar a mecânica com uma manipulação forte** — `repeat_penalty = 0.9`~~ — **feito, e a mecânica não se demonstra** | [Fase 5Z](FASE-5Z-RELATORIO.md): o **Z4** dispara. Com a opção **invertida** — a premiar aquilo de que a rima é feita — a diferença a produção **contém zero** (+0,0069, IC [−0,0093, +0,0283]), vive numa célula de **quatro versos** e **inverte sem ela**, e o par que a produz é `toque`/`que`. O §4.3 do protocolo pré-escreveu a leitura: **«se a 0,9 o efeito for pequeno, a mecânica fica refutada como explicação útil»**, porque a 0,9 está empurrada na direcção favorável com toda a força disponível. **A via da descodificação fecha-se com causa**, e não por falta de potência |
| 45 | **A compressão afectiva entre vozes** — a hipótese que a análise de sentimento gesticula e que vale a pena medir | a [5V §4](FASE-5V-RELATORIO.md) mediu que o modelo **comprime a amplitude entre vozes** na **forma**: o poeta vai de 0,357 a 0,757 de regularidade métrica (amplitude **0,4006**) e o modelo de 0,517 a 0,671 (**0,1547**) — **2,6× menos**, com os erros a apontar para o **meio**. **Haverá a mesma compressão no afecto?** O desenho tem as três coisas que a 5V exigiu: um **portão de calibração** com ordenação de fonte independente — as personas declaram as posturas («Sentes tudo **em excesso**» no Campos, «estóico e epicurista **contido**» no Reis, afecto recusado no Caeiro) —, um **nulo** por permutação, e **dados que já existem** (1926 poemas e 408 amostras geradas de cinco fases). **O que NÃO vale é um léxico de sentimento**: o [`tematicos/SENTIMENTO.md`](tematicos/SENTIMENTO.md) §4 mostra que as regras 3 e 4 da âncora dependem de **negação** e **retracção**, a que um saco de palavras é cego, e o FAS da 5C é o precedente de um léxico derivado do corpus a colapsar de 0,869 para 0,544. **É o [passo 39](#) noutro eixo, e o 39 ainda não correu no eixo onde já há instrumento** — logo fica atrás dele |
| 44 | ~~**O `_RE_META` da guarda de nomes**~~ — **corrigido e em produção** | [`PASSO-44.md`](PASSO-44.md): a linguagem meta passa a ser **só o portão** dos nomes ambíguos, que é o que o comentário do próprio código já dizia que ela era. **Marcação em poemas autênticos: 1,61% → 0,93%** (31 → 18), exactamente a predição escrita, e **zero** casos sem nome de heterónimo. Os três modos de falha da Fase 0 continuam apanhados, verificados caso a caso **antes** de mexer. Três testes, um deles com o `poem_1068` **verbatim**. **Fica declarado o que não corrigi:** os 18 que sobram são Pessoa a nomear um heterónimo dentro de um poema, e distinguir «poema que nomeia» de «comentário que nomeia» não tem critério mecânico à vista |
| 41 | **Verificação de dano no Caeiro** — **já não há embarque para bloquear**, e o passo fica por mérito próprio | o `_opcoes` é **global** e o Caeiro é a única voz que funciona (AUC ao poeta **0,526**). O §3.1 da [5X](FASE-5X.md) pré-escreveu que nenhum resultado no ortónimo autoriza embarcar sem isto — e a [5Z](FASE-5Z-RELATORIO.md) retirou-lhe a urgência pelo lado mais seco: **não há mudança de opção candidata**. Fica o que o braço neutro continua a dar, nas duas fases: `rp=1,0` é **mais limpo** que produção no ortónimo (zero linhas duplicadas nas duas) e **30 s contra 38 s** por amostra. Se isso algum dia for motivo de mexer na constante, é aqui que se verifica |
| 37 | ~~**Fazer o ortónimo rimar**~~ — **tentado, e não é pelo prompt** | a [5W](FASE-5W-RELATORIO.md) correu três braços e o **W4** disparou: nenhum chegou ao 0,50 nem passou o próprio nulo, a **directiva piorou** e o **exemplo** moveu metro, comprimento e léxico para o poeta **menos a rima**. Na densidade o fosso é de **10×** e nenhum braço o mexeu. **Nada entrou em `src/`.** O que fica autorizado é a via que não passa por instruir |
| 38 | **Combinar rima e metro, com validação retida** | pode levar a forma de 0,780 para mais perto do 0,938 da 5Q. A [5C](FASE-5C.md) diz exactamente como falhar nisto: ajustou um combinador em amostra e viu o AUC cair de **0,869 para 0,544** em dados retidos. Sem validação retida, não se faz. **E herda duas coisas da [5Z](FASE-5Z-RELATORIO.md)**: a densidade de rima é **zero em 73%** das amostras, logo é uma contagem de eventos raros e não uma média a comparar; e a chave de rima conta `toque`/`que` como rima, o que **tem de ser corrigido antes** de a densidade entrar num combinador |
| 39 | **A amplitude entre vozes como desfecho próprio** | a [5V §4](FASE-5V-RELATORIO.md) mediu **0,4006** no poeta contra **0,1547** no modelo: o modelo converge para uma regularidade média em todas as vozes, e os erros apontam para o **meio** (regular de mais no Campos, irregular de mais no ortónimo) — **regressão à média, não falta de capacidade numa direcção**. É uma medida de «o modelo diferencia as vozes?» que não existia, e aplica-se a qualquer intervenção futura |
| 34 | **As outras três vozes** — **três vias fechadas, e a causa medida** | a [5Q](FASE-5Q-RELATORIO.md) mediu AUC 0,938–1,000 e atribuiu-o a «ortografia e forma». **Detecção**: fechada pela [5R](FASE-5R-RELATORIO.md)/[5T](FASE-5T-RELATORIO.md)/[5U](FASE-5U-RELATORIO.md) — 7 próclises e 1 marca em 120 amostras. **Instrução**: fechada pela [5V](FASE-5V-RELATORIO.md)/[5W](FASE-5W-RELATORIO.md) — a instrução existe, é ignorada, reforçá-la dá sinal negativo. **Descodificação**: **fechada** pela [5X](FASE-5X-RELATORIO.md)/[5Z](FASE-5Z-RELATORIO.md) — a manipulação **invertida** (`repeat_penalty=0,9`) não demonstra a mecânica e **degenera**, e o §4.3 pré-escreveu que um efeito pequeno nessa direcção a refuta como explicação útil. **A causa está medida e é a forma** (rima AUC 0,780; densidade 10–16× abaixo do poeta); o que **não** existe é via barata para a corrigir. Sobra afinação, que esta máquina não faz em CPU |
| 24 | **As personas pedem os intervalos que a 5L invalidou** — e estão em **produção** | descoberto pela verificação A3 da [5M §5.3](FASE-5M.md): `src/voices.py` manda «Entre dez e vinte versos» (:123), «Entre quinze e trinta» (:133), «No máximo doze» (:142) e «Entre doze e vinte» (:154) — **os quatro intervalos** que a [5J](FASE-5J-RELATORIO.md) mostrou não descreverem o poeta. A 5L removeu-os do **instrumento de medida** e eles ficaram na **instrução de geração**: o projecto mede sem o intervalo e continua a pedi-lo. Corrigir é uma **intervenção** e o efeito mede-se — a 5I mexeu na instrução e deu saldo líquido **negativo** —, logo pede pré-registo próprio. **A [5T §2](FASE-5T-RELATORIO.md) acrescenta-lhe um segundo item, com número:** «não uses gerúndio» proíbe uma construção que Pessoa usa em **101 poemas** («Vou escrevendo os meus versos sem querer»), e «colocação enclítica, **sempre**» é absoluta onde ele procliticiza em 51 |
| 24b | **E a 5M dá-lhe uma predição direccional** | a [5M §3.1](FASE-5M-RELATORIO.md) mediu a **obediência** à instrução errada: o qwen obedece-lhe mais do que o poeta obedece a si mesmo em **3 das 4 vozes** (Caeiro 83% contra 39%), e o llama desobedece e acerta a mediana real em 3 de 4. **Logo corrigir a persona deve beneficiar sobretudo o qwen** — registado antes de o passo 24 correr |
| 25 | **Uma âncora 3a′ por voz** — **a 5Q tirou-lhe a urgência e a 5U devolveu-lha** | a âncora por voz não ajuda enquanto **67%** das amostras se entregarem pela ortografia e pela gramática. A 5Q mostrou que a detecção é decidida pelo **defeito mais grosseiro presente**, logo medir conteúdo nas outras três vozes é medir o andar de cima com o de baixo caído. **E recupera-a com a [5U](FASE-5U-RELATORIO.md):** o argumento da 5Q era que o andar de baixo estava caído, e a 5U contou os tijolos — **7 próclises e 1 marca ortográfica em 120 amostras**. O andar de baixo **não** está caído, logo medir conteúdo nas outras três vozes volta a ser legítimo — e o [passo 36](#) depende disto |
| 26 | ~~**Um nível de referência para o 3a′**~~ — **feito, e o nível está calibrado** | [Fase 5O](FASE-5O-RELATORIO.md): nos 24 poemas **reais** retidos da 5F dou **1,792** contra 1,50 (R1) e 1,71 (R2) — dentro da faixa [1,30; 1,90] fixada antes de medir. A ordenação da 5N repete-se (eu acima do R1 nos dois conjuntos), logo o **efeito de avaliador é real e sistemático**, mas está dentro da tolerância. **A conclusão geral: o nível é do leitor, a diferença emparelhada é do gerador** |
| 27 | **Um desfecho com resolução no TECTO** — é o preço do progresso | a [5O §3.2](FASE-5O-RELATORIO.md): **42 de 54** itens levaram 2, e uma AUC de 0,526 é ambígua entre «indistinguíveis» e «a régua acabou». É o problema da [5B](FASE-5B-RELATORIO.md) **ao contrário** — ali o 3a saturava no **chão**, aqui o 3a′ satura no **topo**. A pista do que falta medir está nas caudas: o llama tem **4 zeros** e os poemas reais **zero** |
| 28 | ~~**A fronteira 1/2 está severa de mais**~~ — **retirado pela [5P](FASE-5P-RELATORIO.md): a prova era minha e estava invertida** | a inferência era «os cinco casos em que a âncora me fez descer são os cinco poemas do poeta» — **verdadeira e vazia**, porque entre 24 reais os que não levaram o máximo são por definição reais que não levaram o máximo. E os dados que a refutavam estavam commitados desde a 5F: nos dois poemas centrais, **R1 e R2 deram 0**, logo eu era o generoso. Afrouxar punha os reais a 100% no tecto |

O **Passo 1 era o que importava mais**, e a Fase 5B foi medi-lo. Voltou sem
veredicto, e a razão é instrutiva: o instrumento com que se ia medir — o
critério 3a, com as âncoras da Fase 5 — **está saturado no mínimo nesta voz**, e
uma ablação emparelhada sobre um desfecho saturado é inconclusiva por
construção. O que falta agora não é mais uma corrida; é um desfecho com
resolução no chão.

> **A lição, e é geral.** Antes de pré-registar uma ablação emparelhada,
> **verificar que o desfecho tem variância na condição de controlo**. A Fase 5
> já tinha publicado que o Caeiro dá 0,0 de mediana em 3a, e a Fase 5B desenhou
> 60 amostras sobre esse critério de qualquer maneira. Um piloto de seis
> amostras tinha mostrado a saturação em vinte minutos, por 1/10 do custo.
> Nenhuma das outras defesas do protocolo — âncoras herdadas, dois avaliadores,
> piso de potência, portão de especificidade — compensa esta falta.

> **E o corolário, da Fase 5C.** Verificar a variância **não chega**: o FAS tinha
> 8x mais resolução que o 3a e foi rejeitado de qualquer maneira, porque a
> validade é outra pergunta. Um desfecho precisa das duas, e a validade mede-se
> em dados **retidos** — a AUC do FAS caía de 0,869 para 0,544 ao passar de
> in-sample para retida. **Qualquer número de discriminação medido nos mesmos
> dados que derivaram o instrumento não é um número.**

> **E o segundo corolário, da Fase 5D.** Um **ICC de 0,671** soa aceitável e não
> basta para estabilizar um portão com limiar: entre dois contadores que
> concordam a ρ=0,78, a AUC oscilou **0,21** — mais do que a distância entre
> passar e falhar. Portões por limiar sobre juízo precisam de concordância bem
> mais alta, ou de correr sobre a estimativa **conjunta** em vez de cada
> avaliador. E a causa foi **uma** fronteira que a definição não decidiu, o que
> é o argumento para escrever as definições pelos **casos difíceis** e não pelos
> fáceis.

> **E o quinto, da Fase 5I, que custou uma segunda adenda e veio de fora.**
> **Um escalar colapsa uma distribuição.** Eu li «40% contra 39% dentro do
> intervalo» como «o llama reproduz a distribuição do poeta quase exactamente»,
> quando era **70+0** contra **43+18**: o Caeiro real erra o intervalo para os
> dois lados e o llama só para baixo. Mesma fracção, distribuições diferentes —
> e por KS o llama está **mais longe** do poeta, não mais perto. **Antes de
> chamar duas distribuições parecidas, comparar as distribuições e não uma
> fracção delas.** Foi a sessão do passo 19 que o viu.

> **E o quarto, da Fase 5I, que custou uma adenda.** Um número calculado **ad
> hoc numa sessão** não tem definição registada, e duas definições plausíveis da
> mesma coisa dão números diferentes: contar «versos» por linhas não vazias ou
> por `plagio._versos` (≥3 palavras) move a fracção do Caeiro real de 43% para
> 39%. Foi uma sessão paralela que o apanhou, não eu. **Qualquer número que
> entre num relatório tem de ter um script no repositório que o reproduza** — e
> comparações entre grupos têm de usar a mesma definição nos dois lados, o que
> parece óbvio e não foi.

> **E o terceiro, da Fase 5E, que é o mais caro de todos.** Um critério derivado
> do **tratamento** mede a proximidade ao tratamento, e não à coisa. A Fase 5
> mediu isto no seu juiz LLM — que dava 65% ao gerado e 45% a Pessoa autêntico —
> escreveu a prescrição certa («as descrições têm de vir de outra fonte que as
> personas») e aplicou-a ao juiz e **não à sua própria rubrica manual**, que tem
> a mesma origem. Quatro fases mediram a geração contra uma idealização da
> persona. **Antes de usar um critério para julgar uma imitação, pontuar o
> original com ele.** Custou três fases de instrumentação descobri-lo e é uma
> linha de protocolo.

> **E o quarto, da Fase 5J, que é sobre a forma do instrumento e não sobre
> o seu conteúdo.** Os três anteriores são sobre **validade** (5C: medir em
> dados retidos), **resolução** (5D: variância no controlo) e **origem** (5E:
> pontuar o original com o critério). Este é sobre a **forma**: **um critério
> por amostra não pode medir uma propriedade de um conjunto.** O 3b pontua
> poemas um a um, e a coisa que distingue o Caeiro em comprimento — escrever
> ora quatro versos ora cento e sessenta — não está em nenhum poema seu, está
> na obra. Daí o dilema medido da [5J](FASE-5J-RELATORIO.md) §4.3: um
> intervalo largo o bastante para conter o poeta contém trivialmente tudo o
> que os modelos fazem, e um estreito o bastante para discriminar reprova o
> poeta. **Não é uma escolha de limiar.**
>
> E um corolário sobre resumos, que custou uma frase publicada: **uma fracção
> dentro de um intervalo não identifica uma distribuição.** A 5I concluiu que
> o llama reproduzia o poeta porque 40% e 39% coincidiam; eram 70+0 contra
> 42+19. Antes de ler uma coincidência de escalares como semelhança, **olhar
> para as duas distribuições**.

> **E o quinto, da Fase 5K, que fecha a série: a escala.** Um número de
> distância sem um **chão** — quanto dá o ruído de amostragem — e sem uma
> **régua** — quanto vale uma diferença real — **não é legível**. A 5J publicou
> `KS = 0,288` e `0,347` a achar que eram legíveis. O que a calibração mudou não
> foi o número: foi passar de «0,347 é mais que 0,288» para «**0,347 é mais do
> que a distância entre o Campos e o Reis**», e para «nenhum dos dois braços
> cabe no intervalo de amostragem de voz nenhuma». Custou uma hora de
> computação.
>
> E dois corolários operacionais, os mais caros da fase: **o nulo assintótico
> era conservador por 46%** (0,278 contra os 0,190 medidos), logo medir o chão
> em vez de o estimar mudou uma decisão à tangente numa decisão com folga; e **o
> n efectivo de um desenho agrupado é o número de agrupamentos, não de
> amostras** — as 30 amostras de 10 perguntas × 3 repetições valem n≈10, e a
> essa resolução metade do resultado da fase desaparece.

> **E o sexto, da Fase 5T, que é sobre a ordem em que se olha.** Os cinco
> anteriores são sobre propriedades do instrumento — validade, resolução,
> origem, forma, escala. Este é sobre **quando** se mede: o portão de segurança
> — correr o detector no material que ele **não pode** marcar, **antes** de o
> apontar ao alvo — apanhou-me **três vezes na mesma fase**. Matou a primeira
> régua (22,6% dos poemas de Pessoa), desmentiu a correcção que eu achava que a
> salvava (435 → 435) e, à terceira, mostrou que não havia sinal nenhum (0,045
> no poeta contra 0,052–0,062 nos modelos).
>
> **Um intervalo de confiança não protege de um numerador errado.** A segunda
> passagem da 5T tinha um IC a sustentar «os modelos são mais enclíticos que
> Pessoa», e era um artefacto de o detector marcar a mais justamente nas
> construções que o poeta usa mais. O que protege é medir o instrumento no
> material que ele não pode marcar — e aqui esse material eram os **1926 poemas
> do próprio poeta**, que estavam no repositório desde o primeiro dia.

> **E o sétimo, da Fase 5U, que não é sobre instrumentos: é sobre a diferença
> entre uma causa atribuída e uma causa medida.** A [5Q](FASE-5Q-RELATORIO.md)
> produziu um número forte — AUC 0,938–1,000 — e, ao lado dele, as **razões
> escritas pelos juízes**. Tratei as razões como achado e gastei **três fases** a
> persegui-las: a 5R fechou a detecção ortográfica por tamanho de corpus, a 5T
> não achou sinal gramatical, e a 5U contou os eventos — **sete próclises e uma
> marca ortográfica em 120 amostras**. Juízes cegos não separam real de gerado a
> 0,938 com um defeito que aparece em 7 de 60 textos.
>
> **A razão que um juiz escreve é uma hipótese sobre o seu próprio processo, não
> uma medição dele.** E eu já tinha o aviso: a [5R §4](FASE-5R-RELATORIO.md)
> mostrou que **uma em três** das minhas próprias razões citava formas que estão
> em Pessoa. **O número da 5Q continua de pé; a explicação nunca esteve** — e o
> custo de as ter publicado juntas, sem separar o que foi medido do que foi
> conjecturado, foram três fases a instrumentar a conjectura.

> **E o oitavo, da Fase 5V, que não acrescenta rigor: acrescenta *onde*.** A 5T
> e a 5U usaram exactamente o mesmo método — portão de segurança no corpus,
> correcções declaradas, *bootstrap* de agrupamentos — e **morreram as duas com
> 7 eventos em 120 amostras**. A 5V usou o mesmo e chegou a uma conclusão, e a
> diferença não foi o rigor: foi que **cada verso é uma observação**.
>
> **Escolher onde medir é anterior a medir bem.** Antes de instrumentar uma
> hipótese, perguntar quantas vezes o fenómeno acontece no material que existe —
> a próclise aparece 7 vezes em 120 textos, a terminação de verso aparece
> milhares. O rigor não compensa um numerador vazio, e isso não se vê depois de
> construir o instrumento: vê-se com uma contagem de dois minutos antes.
>
> E a 5V confirmou, com dois erros meus numa fase só, o que a sexta lição já
> dizia: **o portão de calibração a correr antes do alvo apanhou os dois**.
> Troquei as instruções de duas personas e construí o portão sobre a troca; e a
> chave de rima contava **repetição**, com Caeiro a «rimar» a 0,64 por repetir
> palavras. **Nenhum dos dois se veria olhando para o alvo** — os dois
> produziriam números plausíveis sobre texto gerado.

> **E o nono, da Fase 5W, que é o par do oitavo.** Aquele dizia que escolher
> **onde** medir é anterior a medir bem. Este: **escolher com que resolução
> medir é anterior a escolher o n.**
>
> Pré-registei «o poema rima» — um binário — e isso deitou fora um factor de
> dez. No binário o ortónimo real está em 0,84 e o gerado em 0,38, e lê-se «rima
> menos»; na **densidade** — pares de versos que rimam sobre pares possíveis —
> está em 0,0997 contra 0,0095, e lê-se «rima **uma ordem de grandeza** menos».
> **São o mesmo instrumento e o mesmo texto**: a diferença é o limiar que eu pus
> em cima dele. Num poema de doze versos há 66 pares, e **um** acerto por acaso
> põe o binário em `True`.
>
> E a consequência é prática: no binário a 5W era um nulo fraco de 20 amostras
> por braço que pedia **~175**; na densidade é um resultado firme com n=1196 do
> lado que importa, e **não precisou de uma única amostra nova**. Três fases
> seguidas (5T, 5U, 5W) morreram por potência, e a causa não foi o rigor — foi
> escolher desfechos binários e de baixa frequência.

> **E o décimo, da Fase 5X — e esta eu escrevi errada primeiro, o que é o
> exemplo.** Publiquei que «a mesma configuração, medida duas vezes, varia
> 1,54×» e que o chão de ruído de uma célula de 20 amostras era um factor de
> 1,5. **Não era a mesma configuração**: entre as duas fases eu tinha mudado o
> tokenizador do orçamento, e 18 das 20 células receberam prompts diferentes.
> **E o modelo é determinista** — onde o prompt coincidiu, o texto saiu idêntico
> byte a byte —, logo o remédio que prescrevi, «correr o controlo duas vezes»,
> devolveria resultados iguais e não mediria nada. Premissa e remédio, os dois
> errados, publicados com um número bonito a sustentá-los.
>
> **A lição que sobra é a que o erro ilustra: antes de chamar duas coisas «a
> mesma configuração», comparar os prompts.** Cada fase asseria a identidade do
> prompt **dentro** de si — a 5M byte a byte, a 5W no campo `forma`, a 5X nas
> opções — e **nenhuma** a asseria **contra a fase anterior**. A variação que eu
> li como ruído era uma alteração minha de ferramentas entre corridas.
>
> E ao procurá-la apareceu uma coisa que não é ruído e é pior: **a repetição
> re-recupera.** Quando a guarda rejeita, o `responder` troca o contexto — logo
> um braço que repetiu tem prompt diferente de um que não repetiu, e **todas** as
> células com prompt divergente dentro de uma fase são células em que os braços
> repetiram números diferentes de vezes (3 de 20 na 5X, 2 de 20 na 5W, sem
> excepção). **Não é um confundidor: é um mediador**, porque o tratamento pode
> causar a repetição. Está no [passo 42](#).

> **E o décimo primeiro, da Fase 5Y.** As três anteriores são sobre o desenho —
> **onde** medir, **com que resolução**, e **verificar que «a mesma coisa» é a
> mesma coisa**. Esta é sobre o que se mede **no fim**: **o desfecho de um turno
> não é a saída do tratamento; é a saída do tratamento mais tudo o que o sistema
> fez para a corrigir.**
>
> O `_repetir_sem` é **bom produto** — foi desenhado contra um ciclo de plágio
> observado a correr, e tira do contexto os poemas de que o modelo copiou. E é
> **por ser bom produto** que estraga a medição: **quanto melhor o sistema se
> auto-corrige, menos a saída final revela do que o tratamento fez.** Contamina
> de 7% a 40% das células, fase a fase. A análise primária tem de olhar para
> **antes** da correcção, e o `Turno` não guarda isso ([passo 43](#)).
>
> E um corolário sobre a emenda que abriu a auditoria: eu escrevi «todas, sem
> excepção» a partir de **duas** fases, e com nove há **seis células** que a
> contradizem. **Uma regularidade confirmada em duas fases é uma hipótese, não
> uma regra** — que é exactamente o que eu acabara de aprender sobre as razões
> dos juízes na [5U](FASE-5U-RELATORIO.md), e repeti o erro na correcção do erro.

É agora a **Fase 5**, e a interface passa a Fase 6 — a renumeração está
declarada no topo de [`FASE-5.md`](FASE-5.md). A hipótese que vai a medição é a
que está na tabela de perguntas abertas do §5: o contexto recuperado explica e
atribui significado, e isso é o que Caeiro proíbe. Mede-se por **ablação
emparelhada** nas 20 perguntas já julgadas, com e sem contexto, às cegas, com os
portões escritos antes de existir qualquer amostra.

Em cima disso entrou, por **emenda declarada**, um segundo instrumento vindo de
uma sessão paralela que media a mesma pergunta por outro caminho: a voz gerada é
tão identificável quanto Pessoa autêntico? Essa pergunta **não se auto-calibra**
— é o controlo de poemas reais que a torna legível, e a Fase 4 A1c já mediu o
nível a bater (42–46% em poemas reais). Os juízes são mecânicos, logo esse
instrumento não tem a ameaça de avaliador único que a rubrica à mão tem. A
leitura final é a **concordância dos dois**; discordarem não decide nada.

### Pendências de limpeza

```
[ ] repetir o teste de voz do 8B com repeat_penalty (adenda A.3 só corrigiu o arranque)
[ ] repetir o bench de rerank com pausa de arrefecimento
[ ] medir num_predict=110 (poupa ~4-5s; medicao contaminada por cache)
    -> o valor actual e 220, nao 150. E a 5J §2.3 mostra que na 5H houve 1
       truncatura em 60, com ~20 palavras de folga: descer tem margem, e
       SUBIR nao alarga a forma. Subir so faz sentido COM reforco (passo 20)
[x] `contador()` sem omissao: o `nome` passa a obrigatorio, e `GERADOR` deixa
    de ser um literal no cli.py. A razao esta medida no cabecalho de tokens.py
[ ] remover src/{main,model,retriever}.py no Passo 9
[ ] remover langchain do requirements.txt
[ ] actualizar .github/copilot-instructions.md para a arquitectura nova
[ ] num_predict=220 corta o versiculo longo de Campos (visto 2x na Fase 4)
[x] remedir os centroides da Fase 4 A1c sem o nome do heteronimo: +23 pontos
[ ] correr o centroide sem_nome nas 12 adversariais e nas 40 abladas da Fase 4:
    e o que decide se o roteador LLM se mantem (68% vs 72% e so no benigno)
[ ] detector de proclise brasileira em guard.py: «Uma mao se recua» escapa a
    lista de 14 palavras. Pede medicao contra os 2083 poemas antes de entrar,
    como o lingua_errada teve (0,12 rejeita 3 de 1906) -- «se recua a mao» e
    portugues correcto, e o corpus esta cheio de inversoes. Desenho da sessao
    paralela; fase propria, pequena
[ ] variante do juiz LLM da Fase 5 com descricoes tiradas do corpus (frequencias
    de forma) em vez das personas: separa o confundidor do §9.3 da memorizacao
[ ] registar a origem dos 2083 ficheiros (reprodutibilidade, §5)
[ ] poem_224 esta indexado com mojibake e e recuperavel (visto no top-20 de q11)
[ ] um segundo avaliador para o conjunto dourado: 434 julgamentos sao todos meus
```

---

## 7. Mapa de documentos

| Documento | Conteúdo |
|---|---|
| [`PLANO-RAG-LOCAL.md`](PLANO-RAG-LOCAL.md) | arquitectura, stack, 5 fases, avaliação, riscos |
| [`PRODUCAO.md`](PRODUCAO.md) | **plano do serviço público** (2026-10-18): publicar **desta** máquina atrás de um túnel, sem o passo 9 da Fase 6. Porque é que isto **não** é «produção» e o molde do `portal_brasileirao` quase não transfere; o túnel a fazer o portão **I7 passar sem proteger**; o conflito com a sequência de medição, cujo mecanismo (**passo 7, I8**) **não existe** e resolve metade do problema quando existir; os dois `data/` que desligam o sentinela em silêncio; 11 passos e 10 portões. A versão anterior, sobre EC2, está **retirada e perdida** — reescrita antes de qualquer commit, logo não está no histórico |
| [`BIBLIOGRAFIA.md`](BIBLIOGRAFIA.md) | 23 referências verificadas, em ordem de leitura |
| [`tematicos/TOKENIZACAO.md`](tematicos/TOKENIZACAO.md) | **temático, não é fase**: os dois tokenizadores e porque não são intercambiáveis, de onde vêm o 480 e o 300, o cache de KV, e o que custou a omissão do `contador()` |
| [`tematicos/STOPWORDS.md`](tematicos/STOPWORDS.md) | **temático, não é fase**: as três listas e porque só uma remove; `guard-PT − lexical = {'mais', 'não'}`; e o limiar de língua que estava certo com o instrumento errado |
| [`tematicos/LEMATIZACAO.md`](tematicos/LEMATIZACAO.md) | **temático, não é fase**: **não houve lematização nem *stemming***, e é decisão nomeada na Fase 2 («normalizar, não lematizar»), com custo nomeado na 5C e um falso positivo em produção no `lexico.py` |
| [`tematicos/ENTIDADES.md`](tematicos/ENTIDADES.md) | **temático, não é fase**: não há NER e não faria falta; os três sinais que desambiguam `Reis`/`Campos`/`Pessoa`; o nome que vazou para os centróides e custou ~23 pontos; e a medição nova do §4 |
| [`tematicos/SENTIMENTO.md`](tematicos/SENTIMENTO.md) | **temático, não é fase**: não houve análise de sentimento e **não serviria** — o construto é sensível a negação e retracção; «polaridade» na 5B é gramatical; e **11 das 40 palavras do FAS são afecto puro, 4 são a 2.ª pessoa** |
| [`tematicos/DADOS.md`](tematicos/DADOS.md) | **temático, não é fase**: 2083 ficheiros, 3 línguas, 18:1 entre vozes; os **153 ingleses tratados como ruído** e os **7,3% que continuam inacessíveis**; o *pooling* imparcial garantido pela ordem de escrita; e a derivação de esquema dos `01-cru.jsonl` |
| [`tematicos/TRANSFERENCIA.md`](tematicos/TRANSFERENCIA.md) | **temático, não é fase**: nada foi treinado e cinco modelos pré-treinados fazem tudo; o reranker do MS MARCO a +0,018 contra +0,090, guardado como **controlo negativo**; e **família bate escala** (+145% de parâmetros dão +0,400 n.s.; +5% com outra família dão +0,700 a p=0,0002) |
| [`tematicos/AUMENTO.md`](tematicos/AUMENTO.md) | **temático, não é fase**: três sínteses, e o propósito separa-as — os nulos da 5K e da 5V funcionaram, o instrumento da 5R falhou. Mais o n efectivo: 30 amostras valem **n≈10** |
| [`tematicos/MULTITAREFA.md`](tematicos/MULTITAREFA.md) | **temático, não é fase**: o gerador e o roteador partilham a instância para tarefas **opostas** (0,9 contra 0,0), e o custo foi medido **antes** de mexer na constante — **72% → 68%**. E o mesmo padrão de «um objecto, duas tarefas» **vazou** no `Chunk` (~23 pontos) e **não vazou** no encoder |
| [`tematicos/PLAGIO.md`](tematicos/PLAGIO.md) | **temático, não é fase**: o maior efeito de produto — **82% → 0%** —, porque n-gramas não vêem a cópia por paráfrase (8-gramas a 2% com 3 de 8 versos copiados), e o mecanismo que **contaminou 7–40% das células** de cinco fases |
| [`tematicos/BUSCA.md`](tematicos/BUSCA.md) | **temático, não é fase**: **produção usa só o denso**; a Fase 2 é resultado negativo declarado (+0,004 e o `apt@3` a cair de 95% para 90%); o `k=60` não afinado de propósito; e o BM25 a sobreviver por **não** ser para buscar |
| [`tematicos/PERSONA.md`](tematicos/PERSONA.md) | **temático, não é fase**: o achado fundador («nomear produz pastiche; descrever a postura produz a voz», as duas amostras 10/10 da Fase 0) e as **três regras em produção que não descrevem o poeta** |
| [`FASE-0.md`](FASE-0.md) · [`FASE-0-RELATORIO.md`](FASE-0-RELATORIO.md) | protocolo e resultados da medição |
| [`FASE-1.md`](FASE-1.md) | 9 passos do pipeline |
| [`FASE-2.md`](FASE-2.md) | busca híbrida, BM25, ortografia histórica |
| [`FASE-3.md`](FASE-3.md) · [`FASE-3-PASSO-1.md`](FASE-3-PASSO-1.md) | rerank e latência medida |
| [`FASE-4.md`](FASE-4.md) · [`FASE-4-RELATORIO.md`](FASE-4-RELATORIO.md) | roteador de voz, e o veto ao enriquecimento |
| [`FASE-3B.md`](FASE-3B.md) · [`FASE-3B-RELATORIO.md`](FASE-3B-RELATORIO.md) | fechar o pool de candidatos, e a reordenação a entrar |
| [`FASE-5B.md`](FASE-5B.md) · [`FASE-5B-RELATORIO.md`](FASE-5B-RELATORIO.md) | a persona do Caeiro feita de interdições, e o desfecho que saturou |
| [`FASE-5C.md`](FASE-5C.md) · [`FASE-5C-RELATORIO.md`](FASE-5C-RELATORIO.md) | o desfecho lexical, e a validação retida que o reprovou |
| [`FASE-5D.md`](FASE-5D.md) · [`FASE-5D-RELATORIO.md`](FASE-5D-RELATORIO.md) | a contagem de voltas, e o Caeiro real a não cumprir a âncora |
| [`FASE-5E.md`](FASE-5E.md) · [`FASE-5E-RELATORIO.md`](FASE-5E-RELATORIO.md) | a âncora medida contra o original, e a autorização de a recalibrar |
| [`FASE-5F.md`](FASE-5F.md) · [`FASE-5F-RELATORIO.md`](FASE-5F-RELATORIO.md) | a âncora recalibrada, aceite em dados retidos — **é esta a âncora a usar** |
| [`FASE-5G.md`](FASE-5G.md) · [`FASE-5G-RELATORIO.md`](FASE-5G-RELATORIO.md) | a hipótese das interdições, finalmente medida — e rejeitada |
| [`FASE-5H.md`](FASE-5H.md) · [`FASE-5H-RELATORIO.md`](FASE-5H-RELATORIO.md) | o modelo medido, e o único positivo da cadeia |
| [`FASE-5I.md`](FASE-5I.md) · [`FASE-5I-RELATORIO.md`](FASE-5I-RELATORIO.md) | a forma do llama, e a âncora de 3b sob a mesma suspeita da 5E |
| [`FASE-5J.md`](FASE-5J.md) · [`FASE-5J-RELATORIO.md`](FASE-5J-RELATORIO.md) | a âncora de forma medida contra o poeta, e os **pisos** das personas como mecanismo único |
| [`FASE-5K.md`](FASE-5K.md) · [`FASE-5K-RELATORIO.md`](FASE-5K-RELATORIO.md) | o substituto da conformidade, calibrado com nulo empírico e régua entre vozes reais |
| [`FASE-5L.md`](FASE-5L.md) | a contagem de versos a sair do 3b, com a verificação que o autorizou — **sem relatório**, é uma alteração |
| [`FASE-5M.md`](FASE-5M.md) · [`FASE-5M-RELATORIO.md`](FASE-5M-RELATORIO.md) | a forma das quatro vozes nos dois modelos, e o custo da troca a ser só do Caeiro |
| [`FASE-5N.md`](FASE-5N.md) · [`FASE-5N-RELATORIO.md`](FASE-5N-RELATORIO.md) | o `qwen2.5:3b` da mesma família, e a dose-resposta que não aparece |
| [`FASE-5O.md`](FASE-5O.md) · [`FASE-5O-RELATORIO.md`](FASE-5O-RELATORIO.md) | o +0,700 remedido por um terceiro avaliador cego, de outra sessão |
| [`FASE-5P.md`](FASE-5P.md) · [`FASE-5P-RELATORIO.md`](FASE-5P-RELATORIO.md) | a fronteira 1/2 da âncora, e a prova que era minha e estava invertida |
| [`FASE-5Q.md`](FASE-5Q.md) · [`FASE-5Q-RELATORIO.md`](FASE-5Q-RELATORIO.md) | o gerado contra o real nas três vozes que faltavam, e o gargalo de superfície |
| [`FASE-5R.md`](FASE-5R.md) · [`FASE-5R-RELATORIO.md`](FASE-5R-RELATORIO.md) | o detector de superfície derivado do corpus, e o limite dos 2083 poemas |
| [`FASE-5S.md`](FASE-5S.md) · [`FASE-5S-RELATORIO.md`](FASE-5S-RELATORIO.md) | a troca decidida e feita, com o roteador remedido no modelo novo |
| [`FASE-5T.md`](FASE-5T.md) · [`FASE-5T-RELATORIO.md`](FASE-5T-RELATORIO.md) | a gramática fechada — e por **não haver nada a detectar**, ao contrário da 5R |
| [`FASE-5U.md`](FASE-5U.md) · [`FASE-5U-RELATORIO.md`](FASE-5U-RELATORIO.md) | a ablação do bloco de língua, e o chão de eventos que a cegou |
| [`FASE-5V.md`](FASE-5V.md) · [`FASE-5V-RELATORIO.md`](FASE-5V-RELATORIO.md) | a rima: o primeiro instrumento mecânico da sequência a discriminar as três vozes |
| [`FASE-5W.md`](FASE-5W.md) · [`FASE-5W-RELATORIO.md`](FASE-5W-RELATORIO.md) | três braços de prompt contra a rima, e a **densidade** como desfecho de resolução certa |
| [`FASE-5X.md`](FASE-5X.md) · [`FASE-5X-RELATORIO.md`](FASE-5X-RELATORIO.md) | a descodificação, **com a emenda** que retirou o §1 e nomeou o mediador da repetição |
| [`FASE-5Y-RELATORIO.md`](FASE-5Y-RELATORIO.md) | a auditoria das nove fases emparelhadas — **sem protocolo**, e declarado |
| [`FASE-5Z.md`](FASE-5Z.md) · [`FASE-5Z-RELATORIO.md`](FASE-5Z-RELATORIO.md) | a penalização **invertida**, e a monotonia que uma célula de vinte desfaz |
| [`FASE-6.md`](FASE-6.md) | a interface gráfica: pilha, entidades, portões de paridade, e a UX desenhada em volta dos 19 s de silêncio |
| `fase-0/` | 21 ficheiros de evidência e 5 scripts |
| [`fase-0/07-igpu-vulkan.md`](fase-0/07-igpu-vulkan.md) | a iGPU por Vulkan: prefill 6x, decode 0,55x — corrige a premissa «CPU-only» |
| [`fase-1/09-repeticao.md`](fase-1/09-repeticao.md) | a repetição por plágio voltava ao mesmo poema: medição das duas políticas |
| `fase-3/` | latência dos rerankers e script |
| `fase-4/` | 7 bancos de roteador, o conjunto adversarial pré-registado, e a decomposição do tecto |
| `fase-3b/` | a folha dos 142 julgamentos, o pool fechado, e a análise de significância |
| `fase-5b/` | as 60 amostras dos dois braços, as duas pontuações cegas, a variante afirmativa e a verificação da regra que a produziu |
| `fase-5c/` | o FAS, a lista derivada por log-odds, e os números da sua própria rejeição |
| `fase-5d/` | a folha dos três grupos, as duas contagens verso a verso, e os portões |
| `fase-5e/` | a folha de 60 itens frescos, as duas pontuações com a âncora, e os portões W1–W4 |
| `fase-5f/` | a folha de 64 itens com os 24 retidos, as duas pontuações, e os portões X1–X3 |
| `fase-5g/` | as 60 amostras novas dos dois braços, as duas pontuações com a âncora 3a′, e os portões G0–G5 |
| `fase-5h/` | as 60 amostras dos dois modelos, com a asserção de prompt igual, e os portões M1–M5 |
| `fase-5i/` | as 60 amostras dos dois braços de forma, e os portões I0–I4 |
| `fase-5j/` | a contagem de versos do corpus e dos dois geradores, e os portões J1–J5 |
| `fase-5k/` | o nulo empírico do KS por `n`, a régua entre vozes reais, e os portões K1–K5 |
| `fase-5l/` | a verificação dos quatro intervalos contra o poeta, que autorizou retirá-los |
| `fase-5m/` | as **180** amostras das três vozes que faltavam nos dois modelos, as medianas das personas, e os portões M1–M5 |
| `fase-5n/` | as **30** amostras do `qwen2.5:3b`, a folha cega, as pontuações e os portões N1–N4 |
| `fase-5o/` | a folha de **54** itens para o terceiro avaliador, às cegas, e os portões O1–O5 |
| `fase-5p/` | a reanálise dos três avaliadores nos 24 poemas reais, e os portões P1–P3 |
| `fase-5q/` | a folha de **48** itens, gerado contra real nas três vozes, os juízos e os portões Q1–Q4 |
| `fase-5r/` | a derivação do detector por log-odds, a validação retida, e os portões R1–R4 |
| `fase-5s/` | o banco do roteador corrido com o modelo novo (27/40), e os portões S1–S3 |
| `fase-5t/` | a próclise por **atracção** medida no corpus e nos dois modelos, e os portões T1–T4 |
| `fase-5u/` | as **120** amostras da ablação emparelhada, a sensibilidade, e os portões U1–U3 (o U4 é descritivo) |
| `fase-5v/` | a rima do poeta e do gerado verso a verso, as duas chaves, e os portões V1–V4 |
| `fase-5w/` | as 60 amostras dos três braços de prompt, a densidade de rima, e os portões W1–W4 |
| `fase-5x/` | as 60 amostras dos três braços de descodificação, a emenda das 17 células limpas, e os portões X1–X4 |
| `fase-5y/` | a auditoria das nove fases emparelhadas, célula a célula |
| `fase-5z/` | as 60 amostras dos três níveis de penalização, com a **1.ª tentativa** como primário, e os portões Z1–Z4 |

### Código

```
src/
├── tokens.py              ✅ contagem com o tokenizador real
├── corpus/
│   ├── models.py          ✅ Poem, Chunk, Voice, Lang
│   ├── parse.py           ✅ 2083/2083 parseados
│   ├── dedupe.py          ✅ exacto + variante + incipit
│   ├── chunk.py           ✅ 2290 chunks, nenhum > 512 tok
│   └── build.py           ✅ pipeline -> data/corpus.jsonl
├── retrieval/
│   ├── encoder.py         ✅ e5 com prefixos impostos pela API
│   └── index.py           ✅ numpy + manifesto
├── generation/            ⬜ vazio
└── {main,model,retriever}.py   ⚠️ código antigo, a substituir

tests/   47 testes a passar
```

### Como correr

```bash
source .venv/bin/activate
python -m pytest tests/ -q                      # 243 testes, ~2 min
ruff check .                                    # linter; ~20 ms, 0 achados
python -c "from src.corpus.build import build; build()"   # corpus.jsonl, ~40 s
```

O `ruff` cobre `src/` e `tests/`, e **não** o `docs/`: aqueles *scripts* são
artefactos de fases fechadas — o `fase-5f/analisar.py` é o registo do que a
Fase 5F calculou — e reformatá-los reescrevia o registo. O `pyproject.toml` diz
o que está desligado e porquê; os dois casos que importam são o **`E501`**, que
convidava a repartir a linha 59 do `voices.py` (é o texto do `REGRAS_LINGUA`, e
a quebra está **dentro** da *string*: reparti-la muda o prompt que a 5U mediu) e
o **`SIM905`**, que transformou as listas de *stopwords* revistas à mão em
literais de 500 caracteres numa linha.

### Correr o chatbot

```bash
./pessoa --voz caeiro
```

O `./pessoa` existe para evitar um atrito real: `source .venv/bin/activate &&
python -m src.cli` **não funciona** com `setopt correct` no zsh, porque o zsh
verifica a ortografia da linha inteira **antes** de executar qualquer parte
dela. O `python` é analisado enquanto o `PATH` é ainda o antigo, e o zsh
oferece-se para o corrigir para `python3`. Um `rehash` na mesma cadeia não
ajuda, pela mesma razão. O script invoca `.venv/bin/python` directamente, logo
não há `python` na linha de comando para corrigir.

O Ollama tem de estar a correr (`ollama serve`). A primeira execução constrói
`corpus.jsonl` (~40 s) e o índice (~6 min); depois arranca em segundos.

Também vale para os testes:

```bash
.venv/bin/python -m pytest tests/ -q
```

---

## Correcção: a obra em inglês não é contaminação

Apontado pelo proprietário do repositório em 2026-10-01.

**Pessoa escreveu obra em inglês.** Foi educado em Durban, em inglês, e os *35
Sonnets*, o *Antinous* e as *Inscriptions* são dele. **Alexander Search é um
heterónimo que escrevia em inglês**, com 50 poemas no corpus.

Eu tratei os 152 poemas ingleses como ruído a filtrar, e isso aparecia em três
lugares do código, todos agora corrigidos:

| onde | dizia | passa a |
|---|---|---|
| `dedupe.py` | a duplicação por tradução é «resolvida pelo filtro de idioma» | **não são marcados**; a `NAVAL ODE` está catalogada sob Campos e a sua autoria não está estabelecida aqui |
| `lexico.py` | o inglês «contaminaria» o vocabulário de referência | a referência é PT **porque avalia respostas em PT**, não porque o inglês seja ruído |
| `index.py` | `idioma=PT` resolve a duplicação | `idioma=PT` **porque a resposta é em português**; é preferência de consulta, não juízo sobre o corpus |

### O que fica em falta

| voz | poemas | estado |
|---|---|---|
| Alexander Search | 50 em inglês | **sem persona; o sistema não o serve** |
| Charles Robert Anon | 9 em inglês | idem |
| ortónimo em inglês | 92 (*Sonnets*, *Inscriptions*) | inacessível com `idioma=PT` |
| Campos em inglês | 2 | idem |

Servir estes exige mais que trocar um parâmetro: **todas as guardas são
específicas do português** — colocação enclítica, brasileirismos, fracção de
stopwords portuguesas, e o dicionário `pt_PT` da guarda lexical. Uma voz inglesa
precisaria de persona própria, guardas conscientes da língua e do dicionário
`en` do aspell, que está instalado.

Fica como trabalho identificado, não como defeito escondido. É a decisão de
produto mais substantiva em aberto: um PessoaBot que não fala a língua em que
Pessoa publicou os *35 Sonnets* é um PessoaBot incompleto.

### Suporte a inglês implementado

Em resposta à correcção acima. **44 testes novos**, total 164.

| camada | alteração |
|---|---|
| `voices.py` | `PERSONAS` indexado por `(Voice, Lang)`; 6 personas, 2 novas: **Alexander Search** (EN) e **ortónimo em inglês** (EN) |
| `voices.py` | `REGRAS_LINGUA`, `REGRAS_SAIDA`, `REGRAS_NAO_COPIAR` por língua |
| `guard.py` | `fracao_lingua(texto, idioma)` com stopwords EN **incluindo as arcaicas** (`thy`, `thou`, `doth`, `hath`) — sem elas um soneto à maneira de Pessoa reprovaria na língua em que foi escrito |
| `guard.py` | brasileirismos e colocação pronominal só se aplicam a PT; preâmbulos meta em EN |
| `lexico.py` | dicionário `en` do aspell + vocabulário inglês do corpus (3784 tipos) |
| `plagio.py` | `REFORCO_EN` |
| `pipeline.py` | idioma atravessa `recuperar`, `responder`, `responder_em_fluxo`, `Turno` |
| `cli.py` | `--idioma`, comandos `/pt` `/en` `/search`; voz de língua única força a sua |

#### O mesmo padrão em inglês

O dicionário moderno desconhece `giveth` e `storiless`, que Pessoa **usa**, e o
corpus salva-os — exactamente como o `acção` e o `nocturno` em português. A
palavra inventada `danceth`, produzida na primeira resposta real do Search, foi
apanhada: formada por analogia com `giveth` e `doth`, não existe no corpus nem
no dicionário.

#### O inglês **não** é mais lento

A primeira corrida mostrou prefill de 41,4 s e 52,1 s, contra 7,8–20 s em
português, e eu suspeitei da língua. **Medido: é o contrário.**

| caso | prefill a frio | a quente |
|---|---|---|
| pt Caeiro (421 tok) | 34,3 s = 14,2 tok/s | 0,7 s |
| en Search (360 tok) | 25,2 s = **16,6 tok/s** | 0,7 s |
| en ortónimo (410 tok) | 30,3 s = **15,5 tok/s** | 0,7 s |

Duas causas, nenhuma linguística: o chip estava a **82 °C** após horas de carga,
e cada pergunta em inglês era a **primeira daquela persona**, logo sem cache.

**Consequência a registar: o orçamento de 45 s assume a máquina fria.** A frio
agora dá 14–17 tok/s contra os ~21 tok/s da Fase 0, e a mesma configuração sai
do orçamento sem nada ter mudado no código. Os números do plano são de uma
máquina em repouso.


---

## As duas fases de melhoria não melhoraram, e a causa é a mesma

| fase | resultado |
|---|---|
| **2 — busca híbrida (RRF)** | **negativo**: a melhor fusão dá +0,004 de nDCG@5, ruído a n=20, e o `apt@3` cai de 95% para 90% |
| **3 — reranking (cross-encoder)** | **inconclusivo**: o sinal inverte-se com o gabarito (−0,048 no original, +0,074 no ampliado) e o `apt@3` fica a 95% nos três |

### A causa, medida

| | documentos de nota 2 no top-5, somados em 20 perguntas |
|---|---|
| denso | **40** |
| fusão | 39 |

Há **84 documentos de nota 2** no gabarito, mediana de 4 por pergunta, e o top-5
só leva cinco. Reordenar **troca respostas boas por outras respostas boas** — e
o `apt@3` constante a 95% nos dois casos é a assinatura disso.

Não é propriedade dos algoritmos: é propriedade do corpus, medida desde a Fase 0
(67% dos candidatos agrupados eram aproveitáveis).

**A recuperação densa simples parece estar no tecto do que este corpus permite a
k=5.** O caminho que resta não é melhorar o ranking — é mudar o que se mede. O
`apt@3` de 95% diz que o sistema já encontra quase sempre uma resposta apta; a
pergunta aberta desde o Passo 7 da Fase 1 continua a ser a que importa, e é
sobre **geração**: se o modelo é a voz pedida quando não copia.

> ⚠️ **As duas frases a negrito acima estão erradas, e a Fase 4 mediu-o.** O
> oráculo sobre o top-20 — o melhor que uma reordenação da lista que o índice
> **já devolve** conseguiria — dá `nDCG@5 = 0,956` contra os 0,640 do denso. Há
> **0,316 de nDCG@5, ou 88% da falta, dentro do top-20**, e 17 das 20 perguntas
> têm notas 2 abaixo da 5.ª posição. O tecto é do MiniLM, não do corpus.
>
> O erro foi de inferência: o argumento dos 84 documentos de nota 2 explica por
> que o **`apt@3`** satura a 95%, e não por que o **`nDCG@5`** fica em 0,640.
> São perguntas diferentes — «há uma nota 2 no top-3?» satura; «quantas, e em que
> ordem?» não. Ver [`FASE-4-RELATORIO.md`](FASE-4-RELATORIO.md) §2.2.

### Código mantido fora do caminho de execução

`fusion.py`, `search.py` e `rerank.py` ficam no repositório, testados, e **não
ligados ao pipeline** — não desligados por configuração, porque um componente
desligado por omissão é dívida. O que os limita é mensurável e pode mudar:
julgar as 20 perguntas restantes, agrupar a top-10, ou um orçamento de contexto
maior que 300 tokens.


---

## Correcção: «sem GPU» era incompleto

A Fase 0 concluiu **CPU-only** de `nvidia-smi` ausente. Vi o `lspci` reportar
«Intel Corporation Meteor Lake-P [Intel Graphics]» e não verifiquei. O Ollama
0.35.0 **detecta a iGPU por Vulkan e desliga-a por omissão**, com uma linha de
log que diz exactamente como a ligar:

```
msg="dropping integrated GPU; to enable, set OLLAMA_IGPU_ENABLE=1"
library=Vulkan name=Vulkan0 description="Intel(R) Graphics (MTL)"
```

Ligada, reporta `type=iGPU total="22.5 GiB" available="11.4 GiB"`.

| | CPU | iGPU | razão |
|---|---|---|---|
| prefill (421 tok, Caeiro pt) | 34,3 s · 14,2 tok/s | **5,5 s · 89,1 tok/s** | **6,28x** |
| prefill (360 tok, Search en) | 25,2 s · 16,6 tok/s | **4,9 s · 85,8 tok/s** | 5,20x |
| **decode** | 5,2–7,1 tok/s | **3,30 tok/s** (n=3) | **0,55x** |

**Nenhuma decisão fechada muda.** Para ~700 tokens de prompt e 150 de saída:
CPU a frio 74,3 s, iGPU a frio 53,3 s, **CPU a quente 25,7 s**, iGPU a quente
46,1 s. A iGPU ganha 21 s na primeira pergunta de cada voz e perde 20 s em todas
as seguintes — e com `keep_alive` de 30 min quase todas são «seguintes». A linha
«CPU-only» da §3 passa a «CPU para gerar», que é a afirmação que as medições
sustentam.

**O que isto reabre é o orçamento de contexto.** A Fase 0 rejeitou 1500 tokens
porque custavam 84 s de prefill; na iGPU custariam ~17 s. Se a Fase 4 precisar de
contexto maior — metadado enriquecido, por exemplo — a rejeição tem de ser
reavaliada, não herdada.

Dois avisos sobre esta medição: a iGPU foi medida com o pacote a 52–60 °C, mais
frio que a CPU nos seus próprios testes, o que a favorece; e nunca se testou o
desenho que ninguém considerou, **prefill na iGPU e decode na CPU**
(`llama.cpp --n-gpu-layers` parcial), que é onde os dois números apontam.

Detalhe e reprodução: [`fase-0/07-igpu-vulkan.md`](fase-0/07-igpu-vulkan.md).


---

## Correcção: a guarda de idioma media registo, não língua

Observado a correr o chatbot, à pergunta «qual é o futuro de portugal?». O
modelo respondeu isto, e a guarda rejeitou-o por «idioma improvável (fracção pt
0,077)», custando 38 s de nova geração:

> os passos ecoam / silêncio envolve / vogais cantam / pés descalços ligam terra
> ar / brotam esperanças / raízes aprofundam

É português inequívoco. O que lá não há são palavras funcionais: o registo é
telegráfico, sem artigos nem preposições.

**O meu primeiro diagnóstico — «o limiar está alto» — estava errado, e a medição
diz porquê.** Contra o corpus, 0,12 rejeita 3 de 1906 poemas portugueses
(0,16%), e um desses três é francês. Os poemas reais têm mediana 0,385 e p5
0,267. O limiar está bem posto; o instrumento é que mede a coisa errada.

### As três perguntas, em ordem de custo

| | pergunta | medida que a sustenta |
|---|---|---|
| 1 | há stopwords em abundância? | mediana 0,385 (pt) e 0,375 (en); resolve 99,8% dos casos sem subprocessos |
| 2 | outra língua pontua mais que a pedida? | pt dá 0,385 na própria e 0,048 na alheia; en 0,375 e 0,035. Em 2058 poemas, **zero** pontuam mais na língua errada |
| 3 | o dicionário reconhece o vocabulário? | **a única que não depende do registo** |

A terceira é a que separa o caso telegráfico do latim, e é a única que o faz:

| | dicionário pt | dicionário en |
|---|---|---|
| verso telegráfico (o caso observado) | **1,000** | 0,050 |
| latim (a falha da Fase 0) | **0,043** | 0,130 |
| poemas reais | p1 **0,857** | p1 **0,900** |

`MIN_FRACAO_DICIONARIO = 0,50` fica no meio dessa lacuna. A folga é deliberada:
o dicionário é pós-acordo de 1990 e rejeita 7,1% do vocabulário real de Pessoa.

**O teste relativo sozinho não bastaria**, e foi o teste que já existia que o
provou: o latim de `tests/test_guard.py` contém `se`, stopword portuguesa, logo
pontua 0,040 em pt contra 0,000 em inglês e passaria. Escrevi a versão relativa,
ela passou no meu próprio caso de latim, e reprovou no do repositório.

### Dois defeitos encontrados pelo caminho

**`fracao_lingua` caía no português quando não conhecia a língua.** `Lang.INDETERMINADO`
existe para poemas curtos demais para classificar, e `_STOPWORDS` não o cobre.
A primeira versão da correcção dava 4 poemas reais por língua errada — entre
eles «Iniguais pertencemos.» Sem autoridade sobre a língua, a guarda é agora
inerte.

**`poem_561` é francês, rotulado como português.** «Elle est si belle, / La
petite rebelle» — e é o único: medido com palavras funcionais francesas, nenhum
outro poema do corpus tem o francês a dominar (0,460 contra 0,046 de português).
A guarda sinaliza-o, e tem razão; a etiqueta do corpus é que está errada. O
teste afirma esse único positivo pelo nome, para que qualquer outro o faça
reprovar.

### E o preâmbulo que chegava ao ecrã

Na mesma resposta, o modelo começou por «Aqui está um poema novo, seguindo as
instruções:», e essa linha **foi impressa**. O `remover_preambulo` existe e a sua
regex apanha-a, mas o buffer de streaming do CLI só chamava `remover_cercas` e
`remover_eco_da_pergunta`. O texto validado não tinha o preâmbulo; o ecrã tinha.

A correcção não foi só acrescentar a chamada: a retenção passou a ser **por
linha, enquanto a linha limpa sair vazia**. Com uma só linha de retenção, um
preâmbulo seguido do eco da pergunta deixava o segundo passar.

### Sem dicionário

A guarda volta ao limiar absoluto, que é o comportamento antigo: rejeita. «Não
sei» não pode virar «está bem» — sem a ressalva, uma máquina sem `aspell`
perderia a guarda contra o latim. O preço é o falso positivo telegráfico voltar
nessas máquinas.


---

## Correcção: a repetição por plágio voltava ao mesmo poema

Observado a correr o chatbot, à pergunta «você conhece o senhor fernando
pessoa?»: a 1.ª tentativa copiou 9 de 14 versos do `poem_1164` — um deles à
letra — por substituição de palavras (`Natureza`→`Silêncio`, `brisa`→`luz`,
`perceber`→`escutar`). A repetição voltou **ao mesmo poema**: 5/14. Duas
rejeições, ~80 s, e o utilizador interrompeu.

O `REFORCO` já dizia «não reutilizes nenhum verso nem o reescrevas trocando uma
palavra», e foi ignorado duas vezes. **O contexto não mudava entre as
tentativas** — `poem_1164` continuava no prompt, e a única diferença era o
reforço e a amostragem.

A repetição passa a **tirar do contexto os poemas de que o modelo copiou**. Não é
encolher: `montar` corta pelo orçamento, logo deixar um poema de fora deixa
entrar o seguinte da recuperação — aqui, `poem_1130` em vez de `poem_1164`.

### Medido, 5 repetições por política

| | A (antes) | B (agora) |
|---|---|---|
| rejeitadas por plágio | **4/5** | **1/5** |
| reincidiu no poema proibido | **3/5** | **0/5** |
| corridas com zero versos copiados | **0/5** | **4/5** |
| fracção nas corridas que falharam | 0,08 – 0,57 | **0,89** |

**O mecanismo faz o que foi desenhado para fazer**, e a ressalva é importante:
não remove a tendência de se encostar a um poema, remove **aquele** atractor. A
falha única do B foi a mais grave das dez em fracção copiada, e veio do poema que
acabou de entrar. Com `MAX_TENTATIVAS = 2` não há ronda para tirar o segundo.

n=5, uma pergunta, uma voz — chega para a decisão, não chega para uma taxa.

### Dois defeitos encontrados pelo caminho

**`REFORCO_EN` existia e nunca era usado.** O `responder()` escolhia a língua; o
`responder_em_fluxo()` — o caminho que o CLI corre — fazia `user = p.user +
REFORCO` sem ramo nenhum. Uma sessão em inglês recebia o reforço em português.

**O primeiro desenho da medição não produziu dados.** Condicionei a comparação a
re-observar o plágio na 1.ª tentativa, e em 3 perguntas 0 plagiaram — incluindo
esta, com o mesmo poema no contexto. Com temperatura 0,9 e sem semente o plágio é
estocástico; o ponto de partida tinha de vir da observação, não de nova geração.

Número lateral dessa corrida falhada: **0 de 3 primeiras tentativas plagiaram**,
contra 1 de 1 na sessão do utilizador. O plágio é um evento, não o estado normal
destas respostas — e isto enquadra o que a correcção vale, porque ela só age
quando a primeira tentativa falha.


---

## A retenção de versos, e o que ela custa em texto real

Portão **I7′**, passo 2 do [`PRODUCAO.md`](PRODUCAO.md) (§2.1). O túnel fez o
portão I7 da Fase 6 passar sem proteger nada, e o varrimento de substituição
mostrou que a saída B — não construir o `GET /api/poema/{id}` — fechava a rota
e deixava **três outras portas** abertas. A pior sai **em fluxo**: a tentativa
que a guarda de plágio ia reprovar chega ao cliente antes de haver veredicto,
logo não há verificação a jusante que a possa apanhar.

A correcção é um filtro por linha em `src/web/retencao.py`: retém-se a linha
cujo texto normalizado está no corpus, e **retém-se a linha e não o evento** —
`aprovado: false`, o veredicto e a fracção copiada continuam a ir ao fio,
porque são eles que explicam ao utilizador porque esperou 58 s em vez de 30
(§4.4 da Fase 6).

### O limiar

Protegem-se as linhas de **4 palavras ou mais**: **29 816** das **33 236**
linhas distintas do corpus, já normalizadas (espaços colapsados, `casefold`).
Ficam **3 420** de fora — `*`, `IV`, `Agora`, `A verdade`, `Nada, nada` —, que
são numeração, rubricas de cena e fala comum: protegê-las fazia a retenção
cortar texto gerado legítimo.

### O que custa, contado nos textos que esta casa já gerou

Os dez ficheiros `01-cru.jsonl` das Fases 5B a 5Z, que é todo o texto gerado
nesta máquina que está guardado:

| | |
|---|---|
| textos gerados | **1 560** |
| linhas de 4+ palavras | **16 866** |
| linhas retidas | **20** (**0,119%**) |
| textos afectados | **12** de 1 560 (0,77%) |
| linhas distintas | **15**, de **6** poemas |
| falsos positivos | **0** |

As 15 foram inspeccionadas uma a uma, e **as 15 são versos de Pessoa** — «O
mistério das coisas, onde está ele?» e «As coisas não têm significação: têm
existência.» (`poem_3452`), «Que voz vem no som das ondas» (`poem_100`) —, e
**8 das 15 são linhas seguidas do `poem_3657` num texto só**, que é um poema
inteiro reproduzido num braço da 5Z e que nenhuma destas fases tratou como tal.

**A ressalva que importa:** isto mede o custo da retenção, não a frequência do
plágio. O plágio é um evento e não o estado normal destas respostas (ver
§Correcção sobre a repetição por plágio), e estes 16 866 versos são de fases de
medição com perguntas fixas, não de utilizadores.

### O que a retenção não é

Não é uma guarda de plágio e não a substitui: apanha a linha **igual**, e uma
linha com uma palavra trocada passa-lhe ao lado — é da `guard.py`, que a mede
por fracção. A da 5B que motivou a correcção de repetição por plágio era
precisamente por substituição (`Natureza`→`Silêncio`), e a retenção não a
teria visto. As duas têm alvos diferentes: a guarda protege a qualidade da
resposta, a retenção protege o corpus de ser publicado.

E **não garante o I7′ sozinha.** O que o garante é a cobertura: o
`tests/test_i7.py` falha se nascer uma rota que não passe pelo varrimento, e
foi assim que as três portas apareceram. A comparação em si é exacta dos dois
lados, logo um teste que a medisse seria circular — e a asserção plena do I7′ é
**de fora, contra o URL público**, que não existe até ao passo 6 sobre o
passo 4. Está registado como pendente em vez de o portão se dar por cumprido.


---

## O passo 6, e o túnel que se mediu antes de se abrir

Portão **D4** do [`PRODUCAO.md`](PRODUCAO.md) (§7.1). Três medições de
2026-10-19, contra um `cloudflared` 2026.10.1 instalado em espaço de utilizador.

### O que fecha, medido

Um *Protected Quick Tunnel* com uma lista de convidados que **ninguém pode
usar** (`ninguem@pessoabot.invalid`), e quatro pedidos de fora:

| pedido | resposta | tocou no `uvicorn`? |
|---|---|---|
| `GET /` | **302** → ecrã da Cloudflare, 46 702 bytes | não |
| `POST /api/perguntar` | **401** `Unauthorized`, 13 bytes | não |
| `GET /api/health` | **302** | não |
| `GET /api/estado` | **302** | não |

**0 linhas** novas no registo do serviço, e o instrumento verificado a morder no
mesmo instante: **+1** linha com um pedido local. Essa verificação não é zelo —
foi ela que apanhou a correcção **46**, em que a medição anterior dava zero por
o carimbo estar em UTC contra um `journalctl` em hora local.

### O que atravessa, medido

Um servidor de brincar a emitir NDJSON com pausas de 2 s (não este serviço: só
instantes), pelo URL público:

| linha | local | pelo túnel |
|---|---|---|
| 0 | 0,00 s | **0,53 s** |
| 1 | 1,99 s | **2,55 s** |
| 2 | 3,99 s | **4,67 s** |
| 3 | 5,99 s | **6,53 s** |
| 4 | 7,99 s | **8,55 s** |

**O túnel não acumula.** Os intervalos chegam como foram emitidos, com +0,53 s
de borda. Era o risco que a versão retirada do plano tinha nomeado para o nginx
— «o `proxy_buffering` a desfazer o fluxo NDJSON **sem dar erro**» —, e que
mataria os 18 s até ao 1.º verso deixando a página numa espera de 34 s em
branco.

E uma ironia com causa: a documentação do fornecedor diz que os Quick Tunnels
**não suportam SSE**. A Fase 6 recusou o SSE por privacidade — «o `EventSource`
só faz GET, e com GET a pergunta viajava na *query string*» —, e é essa decisão
que torna este serviço compatível com o único túnel gratuito que há.

### O que impede de o declarar feito

O [cloudflare/cloudflared#1752](https://github.com/cloudflare/cloudflared/issues/1752),
**aberto**: a sessão autenticada expira ~5 s depois do login, reproduzido na
versão **2026.10.1** em Ubuntu 24.04 com uma origem Python, e com o sintoma de
**um POST JSON de mesma origem a devolver 401** — que é, linha por linha, o que
esta interface faz. **Não foi verificado aqui**: verificá-lo exige completar um
login com PIN, logo um endereço real na lista e alguém a ler o correio. Fica
como o que o dono tem de medir antes de convidar alguém.


---

## O passo 6 medido até ao fim: a sessão dura quatro segundos

A 2026-10-20 o dono autenticou-se no túnel protegido com o PIN, a página
carregou, e ao perguntar recebeu «o servidor recusou (401)». O registo do
`uvicorn` deste lado:

| hora (−03) | pedido |
|---|---|
| 09:45:32 | `GET /` 200 |
| 09:45:33 | `app.js` · `estilo.css` · `/api/vozes` · `/api/estado` · `favicon.ico` |
| 09:45:36 | `GET /api/estado` 200 |
| 09:45:39 em diante | **nada** |

**7 pedidos, todos `GET`, zero `POST`.** A sonda de prontidão corre de 3 em 3
segundos, logo a ausência da sonda das 09:45:39 data a morte da sessão entre
09:45:36 e 09:45:39 — **4 segundos** depois do primeiro pedido autenticado. O
`#1752` diz «~5 s»; é a mesma coisa, medida de outro lado.

O que isto corrige na minha própria escrita está na correcção **53**: não é o
POST que falha, é a sessão que acaba.

E o que decide: **um *quick tunnel* protegido não consegue servir esta
interface.** O passo 6 está construído, testado e com o D4 medido, e não há
como entrar por ele. A recomendação da §7 do `PRODUCAO.md` — «ficar no passo
6» — foi retirada.
