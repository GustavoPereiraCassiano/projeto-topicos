"""Consultas SQL do painel. Só lê a Ouro; não calcula nada fora do banco."""
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import config  # noqa: E402


def conectar():
    # somente leitura: o painel nunca altera a Ouro
    return duckdb.connect(str(config.BANCO), read_only=True)


def anos():
    with conectar() as con:
        return con.execute(
            "SELECT MIN(ano), MAX(ano) FROM ouro.vw_desempenho_mandante"
        ).fetchone()


def por_estado(ano_ini, ano_fim, min_jogos):
    sql = """
        SELECT uf_id AS uf, estado, regiao,
               COUNT(*)                            AS jogos,
               COUNT(DISTINCT time_mandante_id)    AS times,
               ROUND(AVG(pontos_mandante), 3)      AS pontos_medios,
               ROUND(100.0 * AVG((resultado = 'V')::int), 1) AS vitorias_pct
        FROM ouro.vw_desempenho_mandante
        WHERE ano BETWEEN ? AND ?
        GROUP BY uf_id, estado, regiao
        HAVING COUNT(*) >= ?
        ORDER BY pontos_medios DESC
    """
    with conectar() as con:
        return con.execute(sql, [ano_ini, ano_fim, min_jogos]).df()


def por_time(uf, ano_ini, ano_fim):
    sql = """
        SELECT time_mandante_id AS time, COUNT(*) AS jogos,
               ROUND(AVG(pontos_mandante), 3) AS pontos_medios
        FROM ouro.vw_desempenho_mandante
        WHERE uf_id = ? AND ano BETWEEN ? AND ?
        GROUP BY time_mandante_id
        ORDER BY pontos_medios DESC
    """
    with conectar() as con:
        return con.execute(sql, [uf, ano_ini, ano_fim]).df()


def media_geral(ano_ini, ano_fim):
    with conectar() as con:
        return con.execute(
            "SELECT AVG(pontos_mandante) FROM ouro.vw_desempenho_mandante "
            "WHERE ano BETWEEN ? AND ?", [ano_ini, ano_fim]
        ).fetchone()[0]
