-- Esquema do `data/sessoes.db`. Versão 1.
--
-- Seis tabelas do §3.2 do plano da Fase 6, mais a `esquema_versao` que o §3.4
-- pede. Sem Alembic: seis tabelas de um processo local migram-se com um inteiro
-- e um ficheiro por versão.
--
-- ⚠️ `PRAGMA foreign_keys` NÃO está aqui, e não é esquecimento: é um pragma de
-- **ligação** e não de ficheiro, logo escrito aqui aplicava-se à ligação que
-- correu este guião e a nenhuma outra. Quem abre a base liga-o, e há teste.
-- O `journal_mode = WAL` é o contrário — persiste no ficheiro — e está no
-- código ao lado do outro para os dois se lerem no mesmo sítio.
--
-- Os corpos dos poemas não existem em nenhuma coluna deste ficheiro: a `fonte`
-- guarda `poem_id` e `chunk_ix`. É o §3.3 do plano, é uma decisão de direitos,
-- e é o portão **I6** que a mede.

CREATE TABLE IF NOT EXISTS esquema_versao (
    versao INTEGER NOT NULL
);

-- A configuração fica na sessão porque uma resposta sem a configuração que a
-- produziu não é interpretável (§3.2). `id` é texto — um uuid4 — e não um
-- inteiro a crescer: o cliente guarda-o e um inteiro deixava adivinhar o
-- vizinho.
CREATE TABLE IF NOT EXISTS sessao (
    id             TEXT    PRIMARY KEY,
    criada_em      TEXT    NOT NULL,
    voz_inicial    TEXT    NOT NULL,
    idioma_inicial TEXT    NOT NULL,
    modelo         TEXT    NOT NULL,
    rerank_ligado  INTEGER NOT NULL,
    auto_ligado    INTEGER NOT NULL
);

-- A unidade que a interface desenha. `papel` inclui `sistema` para as linhas
-- que o CLI imprime em cinza (voz trocada, roteador ligado, rejeição).
CREATE TABLE IF NOT EXISTS mensagem (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    sessao_id TEXT    NOT NULL REFERENCES sessao(id) ON DELETE CASCADE,
    ordem     INTEGER NOT NULL,
    papel     TEXT    NOT NULL CHECK (papel IN ('utilizador', 'bot', 'sistema')),
    texto     TEXT    NOT NULL,
    criada_em TEXT    NOT NULL,
    UNIQUE (sessao_id, ordem)
);

-- O `Turno` **achatado**, porque é isto que se consulta depois. Guarda o que o
-- veredicto não reprova mas assinala (`suspeitas`, `gramatica`): a 5T mediu que
-- duas das três regras de língua não descrevem o poeta, e esse tipo de pergunta
-- só se volta a fazer se os dados ficarem.
--
-- `motivos`, `suspeitas` e `gramatica` são JSON. Três tabelas de uma coluna
-- para dados que se leem sempre inteiros e nunca se cruzam era esquema a mais;
-- o `fonte` abaixo é tabela porque tem um índice que responde a uma pergunta.
CREATE TABLE IF NOT EXISTS turno_reg (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    mensagem_id    INTEGER NOT NULL UNIQUE REFERENCES mensagem(id) ON DELETE CASCADE,
    voz            TEXT    NOT NULL,
    idioma         TEXT    NOT NULL,
    aprovado       INTEGER NOT NULL,
    tentativas     INTEGER NOT NULL,
    recuperacao_ms REAL    NOT NULL,
    rerank_ms      REAL,
    prefill_s      REAL    NOT NULL,
    decode_s       REAL    NOT NULL,
    prefill_tokens INTEGER NOT NULL,
    decode_tokens  INTEGER NOT NULL,
    truncada       INTEGER NOT NULL,
    fracao_copiada REAL    NOT NULL,
    max_similaridade REAL  NOT NULL,
    motivos        TEXT    NOT NULL,
    suspeitas      TEXT    NOT NULL,
    gramatica      TEXT    NOT NULL
);

-- A 5Y é a razão desta tabela: o `Turno` guardava só a última tentativa, e isso
-- contaminou nove fases emparelhadas (de 7% a 40% das células). Uma interface
-- que registe só a resposta final repete o erro ao nível do produto.
--
-- ⚠️ **O §3.2 do plano pede uma coluna `aprovada` aqui, e ela não existe.** O
-- domínio tem `Turno.aprovado` — «veredicto limpo, sem plágio e não truncado»,
-- uma regra que a Fase 5R corrigiu — e **não tem** `Tentativa.aprovada`.
-- Escrevê-la nesta camada era pôr uma segunda cópia da política do §0 na
-- gravação, que é precisamente o que o `serial.py` recusa fazer para o fio
-- («recalculá-la no cliente era pôr uma segunda política de decisão no
-- navegador»). Então guardam-se os **três ingredientes** e a regra fica onde
-- está. Quem quiser a coluna derivada acrescenta `Tentativa.aprovada` ao
-- domínio, com o `Turno.aprovado` a delegar nela — e isso é mexer em
-- `src/pipeline.py`, que esta fase não faz.
CREATE TABLE IF NOT EXISTS tentativa_reg (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    turno_id       INTEGER NOT NULL REFERENCES turno_reg(id) ON DELETE CASCADE,
    n              INTEGER NOT NULL,
    veredicto_ok   INTEGER NOT NULL,
    plagiou        INTEGER NOT NULL,
    truncada       INTEGER NOT NULL,
    fracao_copiada REAL    NOT NULL,
    motivos        TEXT    NOT NULL,
    UNIQUE (turno_id, n)
);

-- Ids, nunca corpos (§3.3). O `papel` separa o que foi recuperado do que entrou
-- no prompt: o `montar` corta o contexto quando o orçamento acaba, logo há
-- poemas recuperados que nunca entraram — e a diferença é informativa.
CREATE TABLE IF NOT EXISTS fonte (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    turno_id INTEGER NOT NULL REFERENCES turno_reg(id) ON DELETE CASCADE,
    poem_id  TEXT    NOT NULL,
    chunk_ix INTEGER NOT NULL,
    ordem    INTEGER NOT NULL,
    papel    TEXT    NOT NULL CHECK (papel IN ('recuperado', 'usado'))
);

-- §3.5: a entidade com o maior retorno escondido da fase. Quando o roteador
-- propõe Caeiro e quem perguntou escolhe Campos antes de gerar, isso **é** um
-- rótulo — dado por quem fez a pergunta, antes de ver a resposta, sem saber que
-- está a rotular. Com as três ressalvas do plano: não é amostra aleatória,
-- «aceite» inclui indiferença, e isto **recolhe**, não conclui.
CREATE TABLE IF NOT EXISTS proposta_reg (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    turno_id      INTEGER NOT NULL UNIQUE REFERENCES turno_reg(id) ON DELETE CASCADE,
    voz_proposta  TEXT,
    -- `aceite` é anulável de propósito: `NULL` é «o roteador não decidiu»,
    -- que não é um rótulo. Um 0 ali lia-se como recusa do utilizador, e estes
    -- dados existem para serem lidos como rótulos (§3.5).
    voz_usada     TEXT    NOT NULL,
    aceite        INTEGER,
    segundos      REAL    NOT NULL
);

-- Os dois índices do §3.4. O segundo é o que responde «que perguntas trouxeram
-- o `poem_3426`?», e sem ele essa pergunta varre a tabela toda.
CREATE INDEX IF NOT EXISTS ix_mensagem_sessao_ordem ON mensagem (sessao_id, ordem);
CREATE INDEX IF NOT EXISTS ix_fonte_poema ON fonte (poem_id);
