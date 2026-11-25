"""Bronze: baixa o CSV do Brasileirão exatamente como a fonte entrega."""
from datetime import datetime
import json
import logging

import requests

import config

log = logging.getLogger(__name__)


def baixar():
    resposta = requests.get(config.URL_BRASILEIRAO, timeout=60)
    resposta.raise_for_status()
    return resposta.content


def copiar(conteudo):
    pasta = config.BRONZE_BRASILEIRAO
    pasta.mkdir(parents=True, exist_ok=True)

    # A data fica no nome: uma extração nova nunca apaga a anterior
    agora = datetime.now()
    nome = agora.strftime("brasileirao_%Y%m%d_%H%M%S.csv")
    destino = pasta / nome

    destino.write_bytes(conteudo)
    return destino


def registrar(destino):
    info = {
        "fonte": config.URL_BRASILEIRAO,
        "arquivo_bronze": destino.name,
        "extraido_em": datetime.now().isoformat(),
    }

    caminho = config.BRONZE_BRASILEIRAO / "proveniencia.jsonl"

    with caminho.open("a", encoding="utf-8") as arquivo:
        arquivo.write(json.dumps(info, ensure_ascii=False) + "\n")


def main():
    conteudo = baixar()
    destino = copiar(conteudo)
    registrar(destino)

    log.info("brasileirao: %s bytes salvos em %s", len(conteudo), destino.name)


if __name__ == "__main__":
    config.configurar_log()
    main()
