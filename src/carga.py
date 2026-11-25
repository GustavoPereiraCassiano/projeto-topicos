"""Carga: copia a Prata para o banco DuckDB e confere a camada Ouro.

A Ouro em si (dim_estado, dim_time, fato_partida e a view) é construída
pelo dbt, em brasileirao_dbt/models/. Este módulo só faz o que não é
transformação: abrir o banco, carregar os Parquet da Prata e conferir
e registrar o resultado.
"""
import json
import logging
import subprocess
from datetime import datetime

import duckdb

import config
from config import BANCO, OURO, PRATA, RAIZ

log = logging.getLogger(__name__)

PROVENIENCIA_OURO = OURO / "proveniencia.jsonl"
RESULTADOS_DBT = config.PROJETO_DBT / "target" / "run_results.json"

# Tabelas da Prata que entram no banco como estão.
# O nome da tabela no banco é a chave; o valor é o arquivo de origem.
TABELAS_PRATA = {
    "brasileirao": PRATA / "brasileirao" / "brasileirao.parquet",
    "brasileirao_enriquecido": PRATA / "brasileirao" / "brasileirao_enriquecido.parquet",
    "estados": PRATA / "ibge" / "estados.parquet",
    "municipios": PRATA / "ibge" / "municipios.parquet",
}

# Arquivos da Prata que o dbt lê (brasileirao_dbt/models/sources.yml).
ORIGENS_OURO = ["brasileirao_enriquecido.parquet", "estados.parquet"]

TABELAS_OURO = ("dim_estado", "dim_time", "fato_partida",
                "vw_desempenho_mandante")


def um_valor(con, sql):
    return con.execute(sql).fetchone()[0]


def conectar(somente_leitura=False):
    BANCO.parent.mkdir(parents=True, exist_ok=True)
    log.info("banco: %s", BANCO)
    return duckdb.connect(str(BANCO), read_only=somente_leitura)


def criar_esquemas(con):
    con.execute("CREATE SCHEMA IF NOT EXISTS prata")
    con.execute("CREATE SCHEMA IF NOT EXISTS ouro")
    log.info("esquemas prata e ouro prontos")


def carregar_prata(con):
    for tabela, caminho in TABELAS_PRATA.items():
        if not caminho.exists():
            raise FileNotFoundError(
                f"prata.{tabela}: {caminho} nao existe. "
                "Rode as etapas anteriores do pipeline."
            )
        con.execute(f"""
            CREATE OR REPLACE TABLE prata.{tabela} AS
            SELECT * FROM read_parquet('{caminho.as_posix()}')
        """)
        linhas = um_valor(con, f"SELECT COUNT(*) FROM prata.{tabela}")
        log.info("prata.%s: %s linhas", tabela, linhas)


def conferir(con):
    """Três perguntas que precisam devolver zero. Falhou, o pipeline para."""
    grao_repetido = um_valor(con, """
        SELECT COUNT(*) FROM (
            SELECT partida_id
            FROM ouro.fato_partida
            GROUP BY partida_id
            HAVING COUNT(*) > 1
        )
    """)

    orfaos = um_valor(con, """
        SELECT COUNT(*)
        FROM ouro.fato_partida f
        LEFT JOIN ouro.dim_time t ON f.time_mandante_id = t.time_id
        WHERE t.time_id IS NULL
    """)

    # A Ouro precisa ter todas as partidas da Prata, nenhuma a mais
    diferenca = um_valor(con, """
        SELECT ABS(
            (SELECT COUNT(*) FROM ouro.fato_partida)
          - (SELECT COUNT(*) FROM prata.brasileirao_enriquecido)
        )
    """)

    log.info("partidas repetidas      : %s (esperado 0)", grao_repetido)
    log.info("fatos sem time na dim   : %s (esperado 0)", orfaos)
    log.info("diferenca prata x ouro  : %s (esperado 0)", diferenca)

    if grao_repetido or orfaos or diferenca:
        raise ValueError(
            f"modelo inconsistente: {grao_repetido} repetidas, "
            f"{orfaos} orfaos, {diferenca} de diferenca"
        )

    return {
        "partidas_repetidas": grao_repetido,
        "fatos_sem_dimensao": orfaos,
        "diferenca_prata_ouro": diferenca,
    }


def contar_ouro(con):
    return {
        tabela: um_valor(con, f"SELECT COUNT(*) FROM ouro.{tabela}")
        for tabela in TABELAS_OURO
    }


def conferir_ouro():
    con = conectar(somente_leitura=True)
    try:
        conferencias = conferir(con)
        linhas = contar_ouro(con)
    finally:
        con.close()
    return conferencias, linhas


# ---------------------------------------------------------- proveniência

def ultima_da_prata(arquivo_prata):
    """Último registro da Prata que gerou o arquivo, para ligar Ouro a Prata."""
    ultimo = None
    for pasta in (config.PRATA_BRASILEIRAO, config.PRATA_IBGE):
        caminho = pasta / "proveniencia.jsonl"
        if not caminho.exists():
            continue
        with caminho.open(encoding="utf-8") as f:
            for linha in f:
                if not linha.strip():
                    continue
                registro = json.loads(linha)
                if registro.get("arquivo_prata") == arquivo_prata or \
                        registro.get("arquivo_prata_estados") == arquivo_prata:
                    ultimo = registro
    if ultimo is None:
        return None
    origem = ultimo.get("origem") or [
        ultimo.get("origem_esquerda"), ultimo.get("origem_direita")
    ]
    return {
        "arquivo_prata": arquivo_prata,
        "origem": origem,
        "transformado_em": ultimo.get("transformado_em"),
    }


def execucao_dbt():
    if not RESULTADOS_DBT.exists():
        return None
    resultados = json.loads(RESULTADOS_DBT.read_text(encoding="utf-8"))
    comando = resultados.get("args", {}).get("which")
    if comando != "run":
        log.warning("run_results.json veio de 'dbt %s', nao de 'dbt run'",
                    comando)
        return None
    meta = resultados["metadata"]
    return {
        "versao": meta.get("dbt_version"),
        "invocation_id": meta.get("invocation_id"),
        "concluido_em": meta.get("generated_at"),
        "modelos": {
            r["unique_id"].split(".")[-1]: r["status"]
            for r in resultados.get("results", [])
        },
    }


def resumo_testes_dbt():
    """Contagem de testes por status, lida do run_results.json de 'dbt test'."""
    if not RESULTADOS_DBT.exists():
        return None
    resultados = json.loads(RESULTADOS_DBT.read_text(encoding="utf-8"))
    if resultados.get("args", {}).get("which") != "test":
        log.warning("run_results.json nao veio de 'dbt test'")
        return None
    contagem = {}
    for r in resultados.get("results", []):
        contagem[r["status"]] = contagem.get(r["status"], 0) + 1
    contagem["total"] = sum(contagem.values())
    return contagem


def versao_do_codigo():
    def git(*argumentos):
        return subprocess.run(
            ["git", *argumentos], cwd=RAIZ,
            capture_output=True, text=True, check=True,
        ).stdout.strip()

    try:
        return {
            "commit": git("rev-parse", "--short", "HEAD"),
            "alteracoes_nao_commitadas": bool(
                git("status", "--porcelain", "--", "src", "brasileirao_dbt")
            ),
        }
    except (OSError, subprocess.CalledProcessError):
        return None


def registrar_ouro(conferencias, linhas, dbt=None, testes_dbt=None):
    info = {
        "camada": "ouro",
        "banco": BANCO.name,
        "origens_prata": [ultima_da_prata(a) for a in ORIGENS_OURO],
        "dbt": dbt,
        "testes_dbt": testes_dbt,
        "codigo": versao_do_codigo(),
        "linhas": linhas,
        "conferencias": conferencias,
        "construido_em": datetime.now().isoformat(timespec="seconds"),
    }
    OURO.mkdir(parents=True, exist_ok=True)
    with PROVENIENCIA_OURO.open("a", encoding="utf-8") as f:
        f.write(json.dumps(info, ensure_ascii=False) + "\n")
    log.info("proveniencia: %s", PROVENIENCIA_OURO)
    return info


def main():
    con = conectar()
    try:
        criar_esquemas(con)
        carregar_prata(con)
    finally:
        con.close()
    log.info("carga concluida")


if __name__ == "__main__":
    config.configurar_log()
    main()
