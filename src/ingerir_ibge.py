"""Ingestao da fonte secundaria: API de Localidades do IBGE (municipios).

A API e aberta, sem chave, e devolve todos os municipios de uma vez (JSON).
Na bronze o JSON fica exatamente como veio: converter formato e transformacao.
"""
import hashlib
import json
from datetime import date, datetime
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parent.parent
BRONZE = RAIZ / "dados" / "bronze" / "ibge"

URL = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
MINIMO_ESPERADO = 5000  # o Brasil tem ~5.570 municipios; abaixo disso, veio incompleto


def buscar():
    r = requests.get(URL, timeout=60)
    r.raise_for_status()
    return r.content


def conferir(conteudo):
    dados = json.loads(conteudo)
    if not isinstance(dados, list):
        raise ValueError(f"esperava uma lista, veio {type(dados)}")
    print("municipios:", len(dados))
    print("primeiro registro:", json.dumps(dados[0], ensure_ascii=False)[:300])
    if len(dados) < MINIMO_ESPERADO:
        print(f"ATENCAO: menos de {MINIMO_ESPERADO} municipios; resposta incompleta?")
    return len(dados)


def salvar(conteudo):
    BRONZE.mkdir(parents=True, exist_ok=True)
    hoje = date.today().strftime("%Y%m%d")
    destino = BRONZE / f"municipios_{hoje}.json"
    destino.write_bytes(conteudo)
    print("salvo em:", destino)
    return destino


def registrar(destino, conteudo, registros):
    info = {
        "fonte": "IBGE - API de Localidades (municipios)",
        "url": URL,
        "arquivo_bronze": destino.name,
        "registros": registros,
        "bytes": len(conteudo),
        "sha256": hashlib.sha256(conteudo).hexdigest(),
        "extraido_em": datetime.now().isoformat(timespec="seconds"),
    }
    caminho = BRONZE / "proveniencia.jsonl"
    with caminho.open("a", encoding="utf-8") as f:
        f.write(json.dumps(info, ensure_ascii=False) + "\n")


def main():
    conteudo = buscar()
    registros = conferir(conteudo)
    destino = salvar(conteudo)
    registrar(destino, conteudo, registros)


if __name__ == "__main__":
    main()
