"""Bronze: baixa a lista de municípios da API de Localidades do IBGE."""
from datetime import datetime
import json
import logging

import requests

import config

log = logging.getLogger(__name__)


def buscar():
    resposta = requests.get(config.URL_MUNICIPIOS, timeout=60)
    resposta.raise_for_status()
    return resposta


def salvar(resposta):
    pasta = config.BRONZE_IBGE
    pasta.mkdir(parents=True, exist_ok=True)

    agora = datetime.now()
    nome = agora.strftime("municipios_%Y%m%d_%H%M%S.json")
    destino = pasta / nome

    # Salva a resposta original da API, sem transformar os dados
    destino.write_bytes(resposta.content)

    return destino


def registrar(destino, quantidade):
    info = {
        "fonte": config.URL_MUNICIPIOS,
        "arquivo_bronze": destino.name,
        "registros": quantidade,
        "extraido_em": datetime.now().isoformat(),
    }

    caminho = config.BRONZE_IBGE / "proveniencia.jsonl"

    with caminho.open("a", encoding="utf-8") as arquivo:
        arquivo.write(
            json.dumps(info, ensure_ascii=False) + "\n"
        )


def main():
    resposta = buscar()
    municipios = resposta.json()

    destino = salvar(resposta)
    registrar(destino, len(municipios))

    log.info("municipios: %s registros salvos em %s",
             len(municipios), destino.name)


if __name__ == "__main__":
    config.configurar_log()
    main()
