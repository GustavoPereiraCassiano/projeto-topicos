from pathlib import Path
from datetime import datetime
import json
import requests

URL = (
    "https://raw.githubusercontent.com/"
    "adaoduque/Brasileirao_Dataset/"
    "master/campeonato-brasileiro-full.csv"
)

# Pasta da camada Bronze
PROJETO = Path(__file__).resolve().parent.parent
BRONZE = PROJETO / "dados" / "bronze" / "brasileirao"


def baixar():
    resposta = requests.get(URL, timeout=60)
    resposta.raise_for_status()
    return resposta.content


def copiar(conteudo):
    BRONZE.mkdir(parents=True, exist_ok=True)

    agora = datetime.now()
    nome = agora.strftime("brasileirao_%Y%m%d_%H%M%S.csv")
    destino = BRONZE / nome

    destino.write_bytes(conteudo)
    return destino


def registrar(destino):
    info = {
        "fonte": URL,
        "arquivo_bronze": destino.name,
        "extraido_em": datetime.now().isoformat(),
    }

    caminho = BRONZE / "proveniencia.jsonl"

    with caminho.open("a", encoding="utf-8") as arquivo:
        arquivo.write(json.dumps(info, ensure_ascii=False) + "\n")


def main():
    conteudo = baixar()
    destino = copiar(conteudo)
    registrar(destino)

    print("Arquivo salvo:", destino)
    print("Proveniência registrada!")


if __name__ == "__main__":
    main()
