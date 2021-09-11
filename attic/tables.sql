CREATE TABLE IF NOT EXISTS models (
    id              DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    name            TEXT UNIQUE,
    make            TEXT,
    color           TEXT,
    status          TEXT,
    create_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id")
);
