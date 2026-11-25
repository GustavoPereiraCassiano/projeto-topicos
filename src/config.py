"""Caminhos, parâmetros e configuração do log. Todo o projeto importa daqui."""
import logging
from pathlib import Path

# Caminho raiz do projeto, calculado a partir deste arquivo: não depende
# da pasta de onde o comando foi executado.
RAIZ = Path(__file__).resolve().parent.parent

# Diretório de dados
DADOS = RAIZ / "dados"

# Camadas
BRONZE = DADOS / "bronze"
PRATA = DADOS / "prata"
OURO = DADOS / "ouro"

# A Bronze e a Prata são organizadas por origem
BRONZE_BRASILEIRAO = BRONZE / "brasileirao"
BRONZE_IBGE = BRONZE / "ibge"
PRATA_BRASILEIRAO = PRATA / "brasileirao"
PRATA_IBGE = PRATA / "ibge"

# Banco da camada Ouro (DuckDB) e projeto dbt que a constrói
BANCO = OURO / "projeto.duckdb"
PROJETO_DBT = RAIZ / "brasileirao_dbt"

# Saídas
RESULTADOS = RAIZ / "resultados"
RELATORIOS = RAIZ / "relatorios"

# ---------------------------------------------------------- parâmetros
URL_BRASILEIRAO = (
    "https://raw.githubusercontent.com/"
    "adaoduque/Brasileirao_Dataset/"
    "master/campeonato-brasileiro-full.csv"
)
URL_MUNICIPIOS = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"

# Abaixo deste número de jogos, um estado é marcado como amostra pequena
MIN_JOGOS = 100

# ------------------------------------------------------------- logging
ARQUIVO_LOG = RAIZ / "pipeline.log"


def configurar_log(nivel=logging.INFO):
    """Log na tela e no arquivo pipeline.log, com data, nível e módulo."""
    logging.basicConfig(
        level=nivel,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(ARQUIVO_LOG, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def criar_pastas():
    for pasta in (BRONZE_BRASILEIRAO, BRONZE_IBGE, PRATA_BRASILEIRAO,
                  PRATA_IBGE, OURO, RESULTADOS, RELATORIOS):
        pasta.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    print("RAIZ:", RAIZ)
    print("BRONZE:", BRONZE)
    print("PRATA:", PRATA)
    print("OURO:", OURO)
    print("RESULTADOS:", RESULTADOS)
