
from pathlib import Path
from datetime import datetime
import json
import requests

URL = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"

PROJETO = Path(__file__).resolve().parent.parent
BRONZE = PROJETO / "dados" / "bronze" / "ibge"


def buscar():
    resposta = requests.get(URL, timeout=60)
    resposta.raise_for_status()
    return resposta


def salvar(resposta):
    BRONZE.mkdir(parents=True, exist_ok=True)

    agora = datetime.now()
    nome = agora.strftime("municipios_%Y%m%d_%H%M%S.json")
    destino = BRONZE / nome

    # Salva a resposta original da API, sem transformar os dados
    destino.write_bytes(resposta.content)

    return destino


def registrar(destino, quantidade):
    info = {
        "fonte": URL,
        "arquivo_bronze": destino.name,
        "registros": quantidade,
        "extraido_em": datetime.now().isoformat(),
    }

    caminho = BRONZE / "proveniencia.jsonl"

    with caminho.open("a", encoding="utf-8") as arquivo:
        arquivo.write(
            json.dumps(info, ensure_ascii=False) + "\n"
        )


def main():
    resposta = buscar()
    municipios = resposta.json()

    destino = salvar(resposta)
    registrar(destino, len(municipios))

    print("Municípios recebidos:", len(municipios))
    print("Arquivo salvo:", destino)
    print("Proveniência registrada!")


if __name__ == "__main__":
    main()
