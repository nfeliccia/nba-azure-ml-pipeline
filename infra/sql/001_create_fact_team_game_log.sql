-- 001_create_fact_team_game_log.sql
-- Base table for nba_api.stats.endpoints.TeamGameLog (resultSets[0])
-- Key: (team_id, game_id) = one row per team per game

IF OBJECT_ID('dbo.fact_team_game_log', 'U') IS NOT NULL
    DROP TABLE dbo.fact_team_game_log;
GO

CREATE TABLE dbo.fact_team_game_log (
    team_id        INT            NOT NULL,
    game_id        VARCHAR(12)    NOT NULL,
    game_date      DATE           NOT NULL,
    matchup        VARCHAR(32)    NOT NULL,

    wl             CHAR(1)        NULL,
    w              SMALLINT       NOT NULL,
    l              SMALLINT       NOT NULL,
    w_pct          DECIMAL(6,5)   NULL,
    minutes        SMALLINT       NOT NULL,

    fgm            SMALLINT       NOT NULL,
    fga            SMALLINT       NOT NULL,
    fg_pct         DECIMAL(6,5)   NULL,

    fg3m           SMALLINT       NOT NULL,
    fg3a           SMALLINT       NOT NULL,
    fg3_pct        DECIMAL(6,5)   NULL,

    ftm            SMALLINT       NOT NULL,
    fta            SMALLINT       NOT NULL,
    ft_pct         DECIMAL(6,5)   NULL,

    oreb           SMALLINT       NOT NULL,
    dreb           SMALLINT       NOT NULL,
    reb            SMALLINT       NOT NULL,

    ast            SMALLINT       NOT NULL,
    stl            SMALLINT       NOT NULL,
    blk            SMALLINT       NOT NULL,
    tov            SMALLINT       NOT NULL,
    pf             SMALLINT       NOT NULL,
    pts            SMALLINT       NOT NULL,

    is_home        BIT            NOT NULL,

    season         VARCHAR(7)     NULL,
    ingested_utc   DATETIME2(0)   NOT NULL DEFAULT SYSUTCDATETIME(),

    CONSTRAINT PK_fact_team_game_log PRIMARY KEY (team_id, game_id)
);
GO

CREATE INDEX IX_fact_team_game_log_game_date ON dbo.fact_team_game_log(game_date);
GO

CREATE INDEX IX_fact_team_game_log_team_date ON dbo.fact_team_game_log(team_id, game_date);
GO
