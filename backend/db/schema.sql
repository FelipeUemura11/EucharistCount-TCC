-- =============================================================================
-- Eucharist Count — esqueleto do banco de dados (SQLite)
-- =============================================================================
--
-- Este arquivo define a estrutura relacional que vai sustentar o backend
-- FastAPI ainda a ser construído. Ele parte de tres premissas do projeto:
--
--   1. NENHUMA imagem, video ou dado biometrico e armazenado (LGPD). So
--      persistimos numeros: contagens, horarios e estimativas agregadas.
--   2. A contagem de hoje ("olhometro") e um caso particular deste modelo:
--      as tabelas de estimativa/comunhao ja preveem o registro manual que
--      voces fazem hoje, e o motor de visao computacional (quando plugado)
--      so passa a preencher as mesmas colunas de forma automatica.
--   3. O documento do TCC descreve um fluxo de "human-in-the-loop": o
--      ministro pode corrigir a estimativa sugerida. Por isso guardamos o
--      valor calculado E o valor ajustado, separadamente — o historico
--      corrigido e o que vai alimentar o futuro modelo de regressao.
--
-- Convencoes:
--   - Nomes de tabelas/colunas em portugues, como o resto do codigo do motor.
--   - Datas/horarios como TEXT em formato ISO-8601 (YYYY-MM-DD, HH:MM,
--     YYYY-MM-DDTHH:MM:SS), que e o formato nativo de comparacao do SQLite.
--   - Toda tabela "de fato" (celebracao, sessao) tem timestamps de auditoria.
-- =============================================================================

PRAGMA foreign_keys = ON;

-- -----------------------------------------------------------------------------
-- 1. paroquia
-- -----------------------------------------------------------------------------
-- Configuracao de identidade da paroquia (nome/logo exibidos no menu lateral).
-- Tabela de linha unica: o app sempre le/atualiza o registro id = 1.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS paroquia (
    id              INTEGER PRIMARY KEY CHECK (id = 1),
    nome            TEXT NOT NULL,
    cidade          TEXT,
    logotipo_path   TEXT,
    atualizado_em   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now'))
);

-- -----------------------------------------------------------------------------
-- 2. horario_padrao
-- -----------------------------------------------------------------------------
-- Agenda semanal padrao (tela "Configuracoes"). Cada linha e uma missa fixa
-- de um dia da semana, com a janela de gravacao/monitoramento associada.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS horario_padrao (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    dia_semana                  INTEGER NOT NULL CHECK (dia_semana BETWEEN 0 AND 6), -- 0=domingo ... 6=sabado
    horario_missa               TEXT NOT NULL,   -- 'HH:MM'
    horario_inicio_gravacao     TEXT NOT NULL,   -- 'HH:MM'
    horario_fim_gravacao        TEXT NOT NULL,   -- 'HH:MM'
    ativo                       INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1)),
    criado_em                   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now')),
    atualizado_em               TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_horario_padrao_dia ON horario_padrao(dia_semana);

-- -----------------------------------------------------------------------------
-- 3. celebracao
-- -----------------------------------------------------------------------------
-- Uma data concreta com missa: gerada a partir da agenda padrao OU cadastrada
-- avulsamente (celebracao especial, ex.: Natal). "origem" registra qual dos
-- dois casos e este, espelhando CelebrationMassSchedule.source no frontend.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS celebracao (
    id                              INTEGER PRIMARY KEY AUTOINCREMENT,
    horario_padrao_id               INTEGER REFERENCES horario_padrao(id) ON DELETE SET NULL,
    titulo                          TEXT NOT NULL,           -- ex.: 'Missa Dominical', 'Celebracao de Natal'
    tipo                            TEXT NOT NULL DEFAULT 'comum',  -- 'comum', 'especial', 'natal', 'pascoa', ... (celebration_type)
    data                            TEXT NOT NULL,           -- 'YYYY-MM-DD'
    horario_missa                   TEXT NOT NULL,           -- 'HH:MM'
    horario_inicio_monitoramento    TEXT,                    -- 'HH:MM' (pode ser desconhecido em registros so manuais)
    horario_fim_monitoramento       TEXT,                    -- 'HH:MM'
    origem                          TEXT NOT NULL DEFAULT 'global' CHECK (origem IN ('global', 'personalizada')),
    capacidade                      INTEGER,                 -- lotacao maxima do espaco, se conhecida
    pessoas_esperadas               INTEGER,                 -- estimativa previa (planejamento)
    status                          TEXT NOT NULL DEFAULT 'agendada'
                                        CHECK (status IN ('agendada', 'em_andamento', 'finalizada', 'cancelada')),
    criado_em                       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now')),
    atualizado_em                   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now')),
    UNIQUE (data, horario_missa)
);

CREATE INDEX IF NOT EXISTS idx_celebracao_data ON celebracao(data);
CREATE INDEX IF NOT EXISTS idx_celebracao_status ON celebracao(status);

CREATE TRIGGER IF NOT EXISTS trg_celebracao_atualizado_em
AFTER UPDATE ON celebracao
FOR EACH ROW
BEGIN
    UPDATE celebracao SET atualizado_em = strftime('%Y-%m-%dT%H:%M:%S', 'now') WHERE id = OLD.id;
END;

-- -----------------------------------------------------------------------------
-- 4. sessao_monitoramento
-- -----------------------------------------------------------------------------
-- A EXECUCAO real da contagem para uma celebracao (o que de fato aconteceu,
-- em oposicao ao que estava agendado em `celebracao`). Existe como tabela
-- separada porque uma celebracao pode ter o monitoramento reiniciado (queda
-- de energia, travamento da maquina etc.) — cada tentativa e uma sessao.
--
-- Hoje, sem camera, o "olhometro" preenche esta tabela manualmente pela
-- interface (uma sessao por celebracao, com os totais digitados ao final).
-- Quando o motor de visao entrar em producao, ele passa a escrever aqui
-- pelo mesmo caminho — nenhuma tabela nova sera necessaria.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sessao_monitoramento (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    celebracao_id           INTEGER NOT NULL REFERENCES celebracao(id) ON DELETE CASCADE,
    origem_contagem         TEXT NOT NULL DEFAULT 'manual' CHECK (origem_contagem IN ('manual', 'visao_computacional')),
    iniciado_em             TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now')),
    finalizado_em           TEXT,
    status                  TEXT NOT NULL DEFAULT 'em_andamento'
                                CHECK (status IN ('em_andamento', 'concluida', 'interrompida')),
    total_entradas          INTEGER NOT NULL DEFAULT 0,
    total_saidas            INTEGER NOT NULL DEFAULT 0,
    ocupacao_maxima         INTEGER NOT NULL DEFAULT 0,   -- pico de ocupacao durante a sessao
    ocupacao_final          INTEGER NOT NULL DEFAULT 0,   -- contagem OFICIAL de pessoas (hoje: olhometro / "people" da planilha)
    contagem_sistema        INTEGER,                       -- contagem AUTOMATICA do YOLO/ByteTrack para a mesma sessao
                                                            -- (NULL enquanto a camera nao roda; uma vez preenchida, compara-se
                                                            -- contra ocupacao_final para medir a acuracia do modelo de visao)
    parametros_contagem     TEXT,                          -- JSON: copia do config.json usado (auditoria/reproducibilidade)
    observacoes             TEXT,                          -- nota livre sobre o dia (ex.: "chuva forte", "microfone com falha")
    criado_em               TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_sessao_celebracao ON sessao_monitoramento(celebracao_id);
CREATE INDEX IF NOT EXISTS idx_sessao_status ON sessao_monitoramento(status);

-- -----------------------------------------------------------------------------
-- 5. instantaneo_ocupacao
-- -----------------------------------------------------------------------------
-- Serie temporal de ocupacao dentro de uma sessao — e o que alimenta o
-- grafico do Dashboard (occupancyData). No motor automatizado, o
-- APScheduler grava uma linha aqui a cada N segundos/minutos; no modo
-- manual, cada leitura do "olhometro" tambem pode virar uma linha aqui.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS instantaneo_ocupacao (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    sessao_id               INTEGER NOT NULL REFERENCES sessao_monitoramento(id) ON DELETE CASCADE,
    registrado_em           TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now')),
    ocupacao_atual          INTEGER NOT NULL,
    entradas_acumuladas     INTEGER NOT NULL,
    saidas_acumuladas       INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_instantaneo_sessao_tempo ON instantaneo_ocupacao(sessao_id, registrado_em);

-- -----------------------------------------------------------------------------
-- 6. configuracao_estimativa
-- -----------------------------------------------------------------------------
-- Parametros usados para converter ocupacao em estimativa de comunhao e
-- hostias. Hoje e um coeficiente fixo (conforme o TCC descreve como
-- primeira etapa); no futuro, "metodo" passa a 'regressao' sem quebrar o
-- restante do schema. Gravar como historico (append-only) permite saber
-- qual coeficiente estava em vigor quando cada sessao antiga foi calculada.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS configuracao_estimativa (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    metodo                  TEXT NOT NULL DEFAULT 'coeficiente_fixo'
                                CHECK (metodo IN ('coeficiente_fixo', 'regressao')),
    coeficiente_comunhao    REAL NOT NULL,   -- fracao media dos presentes que costuma comungar (fallback mesmo em modo regressao)
    margem_hostias          REAL NOT NULL DEFAULT 0.10, -- folga aplicada sobre a estimativa, ex.: 0.10 = +10%
    modelo_path             TEXT,             -- caminho do artefato do modelo (.joblib), quando metodo = 'regressao'
    vigente_desde           TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now')),
    observacoes             TEXT
);

-- -----------------------------------------------------------------------------
-- 7. estimativa_comunhao
-- -----------------------------------------------------------------------------
-- Uma linha por sessao, com tres "fontes" de valor que convivem de proposito:
--
--   - comungantes_reais / hostias_reais: o que foi de fato OBSERVADO e
--     contado a olho pela equipe (a coluna 'communed' da planilha do
--     colega de voces). Hoje, na fase manual, essa e a UNICA coluna
--     preenchida — nao ha calculo nenhum ainda, so contagem humana.
--   - estimativa_calculada / hostias_calculadas: o que o SISTEMA preve
--     (coeficiente fixo hoje, regressao no futuro). Fica NULL enquanto
--     esse modulo nao existir.
--   - estimativa_ajustada / hostias_ajustadas: uma correcao humana feita
--     EM CIMA do valor calculado pelo sistema (human-in-the-loop, ja em
--     producao). So faz sentido quando ja existe uma estimativa calculada
--     para corrigir — diferente de comungantes_reais, que existe mesmo
--     sem nenhum calculo.
--
-- Com as tres, da para comparar real x calculado (acuracia do modelo) e
-- real x ajustado (o quanto a correcao humana ainda e necessaria) assim
-- que o modulo de estimativa entrar em producao.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS estimativa_comunhao (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    sessao_id                   INTEGER NOT NULL UNIQUE REFERENCES sessao_monitoramento(id) ON DELETE CASCADE,
    configuracao_estimativa_id  INTEGER REFERENCES configuracao_estimativa(id),
    comungantes_reais           INTEGER,   -- contagem manual real (ground truth), ex.: 'communed' da planilha
    hostias_reais               INTEGER,   -- hostias efetivamente consagradas/usadas, se registrado
    coeficiente_utilizado       REAL,      -- coeficiente vigente no momento do calculo (NULL se ainda nao calculado)
    estimativa_calculada        INTEGER,   -- comungantes estimados pelo coeficiente/modelo
    hostias_calculadas          INTEGER,   -- sugestao automatica da IA (estimativa + margem), ex.: 'hosts_consecrated'
    estimativa_ajustada         INTEGER,   -- correcao manual do ministro sobre a estimativa calculada
    hostias_ajustadas           INTEGER,
    ajustado_por                TEXT,
    ajustado_em                 TEXT,
    observacoes                 TEXT
);

-- -----------------------------------------------------------------------------
-- 8. evento_sistema
-- -----------------------------------------------------------------------------
-- Log leve de saude/operacao (camera, modelo, reconexoes, erros). Alimenta
-- a secao "Saude do sistema" das Configuracoes com dados reais em vez de
-- valores fixos na tela. Opcional para o MVP manual, mas ja deixa o campo
-- pronto para quando a camera entrar em producao.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS evento_sistema (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    sessao_id       INTEGER REFERENCES sessao_monitoramento(id) ON DELETE SET NULL,
    componente      TEXT NOT NULL,   -- ex.: 'camera', 'modelo_yolo', 'api', 'banco'
    nivel           TEXT NOT NULL CHECK (nivel IN ('info', 'aviso', 'erro')),
    mensagem        TEXT NOT NULL,
    registrado_em   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_evento_sistema_tempo ON evento_sistema(registrado_em);

-- -----------------------------------------------------------------------------
-- 9. vw_historico — view de conveniencia para a tela "Historico"
-- -----------------------------------------------------------------------------
-- Junta celebracao + sessao (a mais recente concluida) + estimativa em uma
-- unica consulta, ja no formato das colunas da tabela do frontend
-- (HistoryRecord): data, celebracao, horario, total de pessoas, estimativa,
-- hostias sugeridas, entradas e saidas.
-- -----------------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS vw_historico AS
SELECT
    c.id                                    AS celebracao_id,
    c.data                                  AS data,
    c.titulo                                AS celebracao,
    c.horario_missa                         AS horario_missa,
    s.id                                    AS sessao_id,
    s.ocupacao_final                        AS total_pessoas,
    COALESCE(e.estimativa_ajustada, e.estimativa_calculada, e.comungantes_reais) AS estimativa_comunhao,
    COALESCE(e.hostias_ajustadas, e.hostias_calculadas, e.hostias_reais)         AS hostias_sugeridas,
    s.total_entradas                        AS entradas,
    s.total_saidas                          AS saidas
FROM celebracao c
JOIN sessao_monitoramento s ON s.celebracao_id = c.id AND s.status = 'concluida'
LEFT JOIN estimativa_comunhao e ON e.sessao_id = s.id
WHERE c.status = 'finalizada';
