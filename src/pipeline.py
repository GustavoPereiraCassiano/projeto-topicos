"""Ponto de entrada do pipeline: roda as etapas em ordem.

    python src/pipeline.py              # todas as etapas
    python src/pipeline.py carga        # a partir de uma etapa
"""
import logging
import shutil
import subprocess
import sys
import time
from pathlib import Path

import config

log = logging.getLogger(__name__)


def etapa_ingestao():
    import ingerir
    import ingerir_municipios

    ingerir.main()
    ingerir_municipios.main()


def etapa_transformacao():
    import transformar_brasileirao
    import transformar_municipios

    transformar_brasileirao.main()
    transformar_municipios.main()


def etapa_enriquecimento():
    import enriquecer

    enriquecer.main()


def etapa_carga():
    import carga

    carga.main()


def comando_dbt():
    """Acha o executável do dbt, mesmo com o ambiente virtual desativado."""
    achado = shutil.which("dbt")
    if achado:
        return [achado]

    pasta = Path(sys.executable).parent
    for nome in ("dbt.exe", "dbt"):
        if (pasta / nome).exists():
            return [str(pasta / nome)]

    raise FileNotFoundError(
        "dbt nao encontrado. Instale as dependencias: "
        "pip install -r requirements.txt"
    )


def rodar_dbt(*argumentos):
    # check=True: se o dbt falhar, o pipeline para em vez de seguir
    # com a Ouro quebrada.
    subprocess.run(
        [*comando_dbt(), *argumentos],
        cwd=config.PROJETO_DBT,
        check=True,
    )


def etapa_modelagem():
    import carga

    # 1. O dbt constroi a Ouro a partir da Prata que a carga copiou.
    rodar_dbt("run")
    # O run_results.json e sobrescrito pelo proximo comando dbt: le-se agora.
    execucao = carga.execucao_dbt()

    # 2. Os testes declarados no dbt. Se algum falhar, o pipeline para.
    rodar_dbt("test")
    testes = carga.resumo_testes_dbt()

    # 3. Conferencia em Python e registro de proveniencia da Ouro.
    conferencias, linhas = carga.conferir_ouro()
    carga.registrar_ouro(conferencias, linhas, execucao, testes)


def etapa_analise():
    import analisar

    analisar.main()


ETAPAS = [
    ("ingestao", etapa_ingestao),
    ("transformacao", etapa_transformacao),
    ("enriquecimento", etapa_enriquecimento),
    ("carga", etapa_carga),
    ("modelagem", etapa_modelagem),
    ("analise", etapa_analise),
]


def executar(nome, funcao):
    log.info("etapa %s: inicio", nome)
    comeco = time.perf_counter()
    try:
        funcao()
    except Exception:
        log.exception("etapa %s falhou", nome)
        raise
    duracao = time.perf_counter() - comeco
    log.info("etapa %s: fim em %.0fs", nome, duracao)


def main(a_partir_de=None):
    config.configurar_log()
    config.criar_pastas()

    nomes = [nome for nome, _ in ETAPAS]
    if a_partir_de and a_partir_de not in nomes:
        log.error("etapa desconhecida: %s", a_partir_de)
        log.error("etapas validas: %s", ", ".join(nomes))
        return 1

    comecou = a_partir_de is None
    for nome, funcao in ETAPAS:
        if nome == a_partir_de:
            comecou = True
        if not comecou:
            log.info("etapa %s: pulada", nome)
            continue
        if funcao is None:
            log.warning("etapa %s: ainda nao implementada", nome)
            continue
        executar(nome, funcao)

    log.info("pipeline concluido")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
