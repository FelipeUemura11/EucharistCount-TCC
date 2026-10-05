CREATE TABLE IF NOT EXISTS agenda_padrao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dia_semana INTEGER NOT NULL CHECK (dia_semana BETWEEN 0 AND 6),
    horario_missa TEXT NOT NULL,
    inicio_gravacao TEXT NOT NULL,
    fim_gravacao TEXT NOT NULL
);
