"use strict";
/* A página, em JavaScript sem build. Passo 5 da Fase 6.
 *
 * ## O que este ficheiro não faz, e é a regra que governa a fase (§0)
 *
 * **Não decide nada.** Em concreto, e cada uma destas foi uma tentação:
 *
 * - **não limpa o início do fluxo.** O eco da pergunta e o preâmbulo são
 *   retidos no servidor, pela `src/apresentacao.py`, que é a MESMA função que o
 *   `cli.py` chama. Uma retenção escrita aqui era uma segunda política de
 *   apresentação a divergir em silêncio da primeira — portão **I2**;
 * - **não recalcula `aprovado`.** Vem no fio, calculado pelo `serial.py` a
 *   partir da regra do domínio («veredicto limpo, sem plágio e não truncado»,
 *   corrigida na Fase 5R). Recalculá-la aqui punha uma segunda política de
 *   decisão no navegador;
 * - **não corrige combinações impossíveis.** Desactiva-as, com o motivo como
 *   legenda, a partir dos limites que o `GET /api/vozes` publica (§4.6);
 * - **não interpreta o texto.** Nada de Markdown, e nada de `innerHTML`: o
 *   verso entra no DOM por `textContent`, sempre. As quebras de linha são
 *   semânticas e o CSS trata-as com `white-space: pre-wrap` (§4.8.1).
 *
 * `tests/test_pagina.py` verifica as que são verificáveis de fora.
 */

/* Os tipos de evento do fluxo. É uma declaração deliberada e não um `switch`
 * solto: o `src/web/app.py` tem a sua (`TIPOS_DE_EVENTO`) e
 * `tests/test_pagina.py` compara as duas. Uma página que escutasse `chunk`
 * enquanto o servidor emite `fragmento` não dava erro — dava um ecrã vazio. */
const EVENTOS = ["proposta", "fragmento", "turno", "erro"];

const $ = (sel) => document.querySelector(sel);

const estado = {
  voz: "ortonimo",
  idioma: "pt",
  vozes: new Map(),       // voz -> {nomes, idiomas, idioma_unico, roteavel}
  roteador: null,         // {idiomas, acerto, custo_s, nota}
  aGerar: false,
  /* O `AbortController` da geração em curso, ou `null`. **Um por geração**, e
   * não um reutilizado: um controlador abortado fica abortado para sempre, e
   * reusá-lo fazia o `fetch` seguinte rebentar antes de sair (§2.3). */
  controlador: null,
};

/* --- arranque ----------------------------------------------------------- */

async function carregar() {
  await Promise.all([carregarVozes(), actualizarProntidao()]);
  // §4.2: a prontidão muda sem a página perguntar — o índice pode estar a
  // construir-se durante ~6,4 min. Uma sondagem de 3 s é barata porque o
  // `/api/estado` não carrega nada (é a regra do `src/web/estado.py`), e é o
  // mesmo canal que o portão I4 mantém vivo durante uma geração.
  setInterval(actualizarProntidao, 3000);
}

async function actualizarProntidao() {
  let corpo;
  try {
    corpo = await (await fetch("/api/estado")).json();
  } catch (e) {
    return;                             // o servidor caiu; a sondagem repete
  }
  const lista = $("#componentes");
  lista.replaceChildren();
  for (const c of corpo.componentes) {
    const li = document.createElement("li");
    li.append(elemento("span", "nome", c.nome));
    // Uma escolha desligada não é uma falha. O reranker é uma troca medida que
    // o utilizador pode não querer; com a mesma cruz vermelha de um Ollama em
    // baixo, a página dizia-lhe que estava alguma coisa avariada. Quem sabe
    // quais são requisitos é o servidor, e manda-o em `exigido`.
    const marca = c.pronto ? "✓" : (c.exigido ? "✗" : "○");
    li.append(elemento("span", c.pronto ? "sim" : (c.exigido ? "nao" : "escolha"),
                       marca));
    li.append(elemento("span", "detalhe", c.detalhe));
    if (c.remedio) li.append(elemento("span", "remedio", c.remedio));
    // §4.2: o custo vai declarado, para a escolha ser feita com o número à
    // frente em vez de ser uma surpresa.
    if (c.custo_s) {
      li.append(elemento("span", "custo", `~${formatar(c.custo_s)} s quando o pedires`));
    }
    lista.append(li);
  }
  // `pode_perguntar` e não `pronto`: o `pronto` é falso antes da 1.ª pergunta
  // por construção — o índice só se verifica com o corpus carregado, e o
  // corpus só se carrega ao perguntar. Governar o botão pelo `pronto` trancava
  // a única acção que resolve o que falta. Observado, e corrigido no servidor.
  $("#enviar").disabled = estado.aGerar || !corpo.pode_perguntar;
}

async function carregarVozes() {
  const corpo = await (await fetch("/api/vozes")).json();
  estado.roteador = corpo.roteador;
  for (const v of corpo.vozes) {
    const anterior = estado.vozes.get(v.voz) || { nomes: {} };
    anterior.nomes[v.idioma] = v.nome;
    anterior.idiomas = v.idiomas;
    anterior.idioma_unico = v.idioma_unico;
    anterior.roteavel = v.roteavel;
    anterior.principal = v.principal;
    estado.vozes.set(v.voz, anterior);
  }
  desenharControlos();
  $("#rotulo-auto").textContent =
    `roteador propõe a voz (${Math.round(estado.roteador.acerto * 100)}% ` +
    `medido, ~${formatar(estado.roteador.custo_s)} s)`;
  $("#rotulo-rerank").textContent =
    `reordenar candidatos (+${corpo.reranker.ganho_ndcg5.toFixed(3)} nDCG@5, ` +
    `~${formatar(corpo.reranker.custo_s)} s; a 1.ª ~${formatar(corpo.reranker.primeira_s)} s)`;
}

/* §4.5 e §4.6: a voz é o controlo principal, e o impossível fica desactivado
 * com o motivo — nunca corrigido depois de o utilizador escolher. */
function desenharControlos() {
  const nav = $("#vozes");
  nav.replaceChildren();
  for (const [voz, v] of estado.vozes) {
    // Alexander Search não tem persona em português, logo não tem nome em
    // português — e mostrar «search» em vez do nome dele escondia de quem é a
    // voz que está desactivada, que é precisamente o que a legenda do §4.6
    // existe para explicar.
    const b = elemento("button", "voz", nomeDe(voz));
    b.type = "button";
    b.dataset.voz = voz;
    b.setAttribute("aria-pressed", String(voz === estado.voz));
    const possivel = v.idiomas.includes(estado.idioma);
    b.disabled = !possivel;
    if (!possivel) b.title = motivoDaRecusa(voz, v);
    b.addEventListener("click", () => { estado.voz = voz; desenharControlos(); });
    nav.append(b);
  }

  const caixa = $("#idiomas");
  caixa.replaceChildren();
  for (const ling of ["pt", "en"]) {
    const b = elemento("button", "", ling);
    b.type = "button";
    b.setAttribute("aria-pressed", String(ling === estado.idioma));
    const v = estado.vozes.get(estado.voz);
    const possivel = !v || v.idiomas.includes(ling);
    b.disabled = !possivel;
    if (!possivel) b.title = motivoDaRecusa(estado.voz, v);
    b.addEventListener("click", () => {
      estado.idioma = ling;
      desenharControlos();
    });
    caixa.append(b);
  }

  // O roteador só foi medido em português, logo em inglês não liga — e o
  // motivo é a legenda, não uma correcção silenciosa.
  const auto = $("#auto");
  const roteavelAgora = estado.roteador.idiomas.includes(estado.idioma);
  auto.disabled = !roteavelAgora;
  if (!roteavelAgora) {
    auto.checked = false;
    auto.title = `o roteador só foi medido em ${estado.roteador.idiomas.join(", ")}`;
  } else {
    auto.title = estado.roteador.nota;
  }
}

function motivoDaRecusa(voz, v) {
  if (!v) return "";
  if (v.idioma_unico) {
    return `${v.nomes[v.idioma_unico] || voz} escreve em ${v.idioma_unico}`;
  }
  return `esta voz só tem persona em ${v.idiomas.join(", ")}`;
}

/* --- a pergunta --------------------------------------------------------- */

$("#formulario").addEventListener("submit", (ev) => {
  ev.preventDefault();
  const texto = $("#pergunta").value.trim();
  if (!texto || estado.aGerar) return;
  $("#pergunta").value = "";
  perguntar(texto);
});

/* §2.3: cancelar. O `abort` fecha o fluxo **e** o servidor fecha o pedido ao
 * Ollama — ver `src/web/cancelar.py`. Sem a segunda metade, isto libertava o
 * ecrã e deixava a máquina a decodificar até ao `num_predict`, a competir com a
 * pergunta seguinte: a interface ficava a mentir sobre quem manda. */
$("#cancelar").addEventListener("click", () => {
  if (estado.controlador) estado.controlador.abort();
});

async function perguntar(pergunta) {
  const vista = novoTurno(pergunta);
  avisar(null);
  const controlador = new AbortController();
  estado.controlador = controlador;
  trancar(true);

  let resposta;
  try {
    resposta = await fetch("/api/perguntar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        pergunta,
        voz: estado.voz,
        idioma: estado.idioma,
        rerank: $("#rerank").checked,
        auto: $("#auto").checked,
      }),
      signal: controlador.signal,
    });
  } catch (e) {
    // Um `abort` antes de a resposta chegar também cai aqui, e não é um erro do
    // servidor: é o utilizador. Dizer «o servidor não respondeu» era mentira.
    if (controlador.signal.aborted) vista.cancelado();
    else vista.falhar(`o servidor não respondeu: ${e.message}`);
    trancar(false);
    return;
  }

  if (!resposta.ok) {
    // §2.2: o 409 não é uma fila escondida. Diz quanto falta e porquê, porque
    // é a verdade do hardware — um Ollama, um encoder, um reranker.
    const d = (await resposta.json().catch(() => ({}))).detail || {};
    if (resposta.status === 409) {
      avisar(`${d.mensagem}. Falta ~${formatar(d.espera_estimada_s)} s.`);
    } else {
      avisar(d.mensagem || `o servidor recusou (${resposta.status})`);
    }
    vista.remover();
    trancar(false);
    return;
  }

  try {
    for await (const evento of linhas(resposta.body)) {
      vista.evento(evento);
    }
  } catch (e) {
    // O `abort` rebenta o leitor do corpo com `AbortError`. O que já apareceu
    // no ecrã **fica** — é verso que o modelo escreveu, e apagá-lo porque o
    // utilizador parou era destruir o que ele pode querer ler. É a mesma
    // decisão do §4.4 para a tentativa rejeitada.
    if (controlador.signal.aborted) vista.cancelado();
    else vista.falhar(`o fluxo interrompeu-se: ${e.message}`);
  } finally {
    vista.terminar();
    trancar(false);
  }
}

/* O fluxo é NDJSON: uma linha JSON por evento. Não é SSE porque o
 * `EventSource` só faz GET, e com GET a pergunta — texto que a pessoa
 * escreveu — viajava na *query string*, logo no histórico do navegador e nos
 * registos de tudo o que estivesse no caminho (§1.3). */
async function* linhas(fluxo) {
  const leitor = fluxo.getReader();
  const decodificador = new TextDecoder();
  let resto = "";
  for (;;) {
    const { value, done } = await leitor.read();
    // `stream: true` importa: um fragmento pode cortar um caractere UTF-8 ao
    // meio, e o verso é cheio de acentos.
    resto += decodificador.decode(value || new Uint8Array(), { stream: !done });
    const partes = resto.split("\n");
    resto = partes.pop();
    for (const linha of partes) {
      if (linha.trim()) yield JSON.parse(linha);
    }
    if (done) {
      if (resto.trim()) yield JSON.parse(resto);
      return;
    }
  }
}

/* --- um turno no ecrã --------------------------------------------------- */

function novoTurno(pergunta) {
  const no = $("#modelo-turno").content.firstElementChild.cloneNode(true);
  no.querySelector(".pergunta").textContent = pergunta;
  no.classList.add("a-gerar");
  $("#conversa").append(no);
  no.scrollIntoView({ block: "end", behavior: "smooth" });

  const texto = no.querySelector(".resposta .texto");
  const cursor = no.querySelector(".cursor");
  const relogio = no.querySelector(".relogio");
  const fase = no.querySelector(".fase");

  const t0 = performance.now();
  let primeiro = null;
  //: O texto como chegou, sem uma única alteração. É daqui que sai o que se
  //: desenha e o que se arquiva quando uma tentativa é rejeitada — nunca do
  //: DOM, que já é uma representação e perdia as linhas em branco.
  let acumulado = "";

  /* §4.8.4: **um elemento por verso**, e é a única forma de ter indentação
   * pendente a sério.
   *
   * A tentativa anterior era um bloco só com `white-space: pre-wrap` e
   * `text-indent: -1.6em`. Não funciona, e viu-se a correr: o `text-indent`
   * aplica-se à primeira linha **do bloco**, não a cada linha visual — o
   * resultado foi o 1.º verso à margem e todos os outros recuados 1,6em, que
   * é o contrário do que se queria. Com um bloco por verso, o recuo negativo
   * cai no início de cada verso e o `padding-left` recebe a continuação de um
   * versículo de Campos que não cabe na medida.
   *
   * Só o último verso muda entre fragmentos, logo só esse é reescrito: os
   * anteriores ficam no sítio e não perdem a selecção de quem esteja a
   * copiá-los.
   */
  function desenhar() {
    const versos = acumulado.split("\n");
    while (texto.childElementCount < versos.length) {
      texto.append(elemento("div", "verso"));
    }
    while (texto.childElementCount > versos.length) {
      texto.lastElementChild.remove();
    }
    for (let i = 0; i < versos.length; i++) {
      if (texto.children[i].textContent !== versos[i]) {
        texto.children[i].textContent = versos[i];
      }
    }
    // O cursor vive no fim do último verso; fora dele, caía para uma linha
    // sozinha, porque cada verso é um bloco.
    (texto.lastElementChild || texto).append(cursor);
  }

  // §4.1: um cronómetro que CONTA, e não um indicador a rodar. Diz que o
  // sistema está vivo e ensina o custo — a mesma decisão do rodapé do CLI,
  // levada ao tempo de espera.
  fase.textContent = "a recuperar, a montar o prompt e a esperar o prefill "
    + "(58–89% da espera é ele)";
  const tique = setInterval(() => {
    relogio.textContent = `${formatar((performance.now() - t0) / 1000)} s`;
  }, 100);

  return {
    evento(e) {
      if (e.tipo === "proposta") {
        // §4.5: a proposta aparece antes de gerar. A geração arranca logo —
        // não se paga latência por uma caixa de diálogo —, e o utilizador vê
        // para onde foi. Abortar e refazer com outra voz é o passo 6.
        const p = e.proposta;
        fase.textContent = p.decidiu
          ? `voz proposta: ${nomeDe(e.voz)} (${formatar(p.segundos)} s)`
          : `o roteador não teve opinião (${formatar(p.segundos)} s); `
            + `mantenho ${nomeDe(e.voz)}`;
        return;
      }
      if (e.tipo === "fragmento") {
        if (primeiro === null) {
          primeiro = (performance.now() - t0) / 1000;
          fase.textContent = "a gerar";
        }
        // `textContent` e nunca `innerHTML`: isto é verso, não marcação.
        acumulado += e.texto;
        desenhar();
        return;
      }
      if (e.tipo === "turno") {
        if (e.turno.aprovado) {
          rodape(no, e.turno, primeiro);
          return;
        }
        // §4.4: a tentativa rejeitada NÃO é substituída. Fica no lugar,
        // recolhida, com o motivo — é a única forma de o utilizador entender
        // porque esperou 58 s em vez de 30.
        arquivarRejeitada(no, e.turno, acumulado);
        acumulado = "";
        texto.replaceChildren(cursor);
        primeiro = null;
        fase.textContent = "rejeitada; a repetir sem o poema de que copiou";
        return;
      }
      if (e.tipo === "erro") {
        this.falhar(e.mensagem);
      }
    },
    falhar(mensagem) {
      fase.textContent = "";
      no.querySelector(".rodape").hidden = false;
      no.querySelector(".notas").textContent = `✗ ${mensagem}`;
      no.querySelector(".notas").classList.add("marca");
    },
    /* O CLI imprime «(interrompido)» no `KeyboardInterrupt`. Isto é o
     * equivalente, e com o mesmo tom: diz o que aconteceu e o que custou, sem
     * pedir desculpa e sem apagar nada. */
    cancelado() {
      fase.textContent = "";
      const rodape = no.querySelector(".rodape");
      rodape.hidden = false;
      const nota = no.querySelector(".notas");
      nota.textContent = `interrompido depois de ${relogio.textContent}`;
      nota.classList.add("interrompido");
    },
    terminar() {
      clearInterval(tique);
      no.classList.remove("a-gerar");
    },
    remover() {
      clearInterval(tique);
      no.remove();
    },
  };
}

function arquivarRejeitada(no, turno, textoMostrado) {
  const det = no.querySelector(".rejeitada");
  const motivos = turno.veredicto.motivos.slice();
  if (turno.plagio.plagiou) motivos.push(turno.plagio.resumo);
  if (turno.resposta.truncada) motivos.push("truncada pelo limite de tokens");
  det.hidden = false;
  det.querySelector("summary").textContent =
    `tentativa ${turno.tentativas} rejeitada: ${motivos.join("; ")}`;
  det.querySelector(".texto-rejeitado").textContent = textoMostrado;
}

/* §4.7: o rodapé, com as separações que o CLI já faz — cada uma por um motivo
 * medido, e nenhuma delas somada às outras. */
function rodape(no, turno, primeiro) {
  const pe = no.querySelector(".rodape");
  pe.hidden = false;

  const fontes = no.querySelector(".fontes");
  fontes.replaceChildren();
  if (!turno.fontes.length) {
    fontes.textContent = "sem fontes";
  } else {
    fontes.append(document.createTextNode("fontes: "));
    for (const f of turno.fontes) {
      // `recuperado` e `usado` ficam distintos: `montar` corta o contexto
      // quando o orçamento de tokens acaba, logo há poemas que a recuperação
      // trouxe e que nunca entraram no prompt. O painel do poema é o passo 9.
      const ficha = elemento("span", `ficha ${f.papel}`, f.poem_id);
      ficha.title = `${f.papel} · ${f.n_palavras} palavras`;
      fontes.append(ficha);
    }
  }

  const r = turno.resposta;
  const partes = [`${Math.round(turno.recuperacao_ms)} ms recuperação`];
  // Nunca somada à recuperação: é a parcela que se paga por uma escolha e que
  // se pode desligar.
  if (turno.rerank_ms !== null) {
    partes.push(`${formatar(turno.rerank_ms / 1000)} s reordenação`);
  }
  if (primeiro !== null) partes.push(`${formatar(primeiro)} s até ao 1.º verso`);
  // prefill e decode ficam separados: 58–89% da espera é prefill, e juntá-los
  // apagava a única coisa que explica a latência.
  partes.push(`${formatar(r.prefill_s)} s prefill (${r.prefill_tokens} tok)`);
  partes.push(`${formatar(r.decode_s)} s decode (${r.decode_tokens} tok, `
    + `${formatar(r.decode_tps)} tok/s)`);
  if (turno.tentativas > 1) partes.push(`${turno.tentativas} tentativas`);
  no.querySelector(".tempos").textContent = partes.join(" · ");

  const notas = no.querySelector(".notas");
  notas.replaceChildren();
  // A 5Q apanhou cinco respostas cortadas a meio da palavra: uma resposta
  // cortada não é uma resposta, logo tem marca própria.
  if (r.truncada) notas.append(elemento("span", "marca", "✂ truncada "));
  // §4.3: o streaming imprime antes de validar, e a guarda corrige a meio do
  // texto — onde um buffer de uma linha não chega. Não se reimprime: avisa-se.
  if (r.texto.trim() !== turno.veredicto.texto.trim()) {
    notas.append(document.createTextNode(
      "a guarda corrigiu o texto depois de ele aparecer. "));
  }
  if (turno.veredicto.suspeitas.length) {
    const palavras = turno.veredicto.suspeitas.map((s) => `«${s.palavra}»`);
    notas.append(document.createTextNode(
      `palavras que nem o corpus nem o dicionário conhecem: ${palavras.join(", ")}. `));
  }
  if (turno.veredicto.gramatica.length) {
    notas.append(document.createTextNode(
      `construções que a persona proíbe: ${turno.veredicto.gramatica.join(", ")}.`));
  }
}

/* --- utilitários -------------------------------------------------------- */

function elemento(etiqueta, classe, texto) {
  const e = document.createElement(etiqueta);
  if (classe) e.className = classe;
  if (texto !== undefined) e.textContent = texto;
  return e;
}

function nomeDe(voz) {
  const v = estado.vozes.get(voz);
  if (!v) return voz;
  return v.nomes[estado.idioma] || v.nomes.pt || Object.values(v.nomes)[0] || voz;
}

/* Vírgula decimal e uma casa, como o resto do projecto. Uma casa e não mais:
 * o `CONTROLO.md` §5 registou *throttling* térmico até 101 °C e «latências com
 * precisão menor que as casas decimais sugerem». */
function formatar(n) {
  return (n === null || n === undefined ? 0 : n).toFixed(1).replace(".", ",");
}

function trancar(aGerar) {
  estado.aGerar = aGerar;
  $("#enviar").disabled = aGerar;
  $("#pergunta").disabled = aGerar;
  // §2.3: o cancelar existe **enquanto** há o que cancelar, e não antes.
  $("#cancelar").hidden = !aGerar;
  if (!aGerar) estado.controlador = null;
}

function avisar(mensagem) {
  const p = $("#aviso");
  p.textContent = mensagem || "";
  p.hidden = !mensagem;
}

carregar();
