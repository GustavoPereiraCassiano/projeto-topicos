"""Ingestao da fonte primaria: Brasileirao Dataset (CSV publicado no GitHub).

Baixa o arquivo exatamente como esta na fonte, grava na bronze com a data
no nome e acrescenta uma linha em proveniencia.jsonl.
"""
import hashlib
import json
from datetime import date, datetime
from io import BytesIO
from pathlib import Path

import pandas as pd
import requests

RAIZ = Path(__file__).resolve().parent.parent
BRONZE = RAIZ / "dados" / "bronze" / "brasileirao"

REPO = "adaoduque/Brasileirao_Dataset"
ARQUIVO = "campeonato-brasileiro-full.csv"
URL = f"https://raw.githubusercontent.com/{REPO}/master/{ARQUIVO}"
URL_COMMITS = f"https://api.github.com/repos/{REPO}/commits"

ESPERADAS = [
    "ID", "rodata", "data", "hora", "mandante", "visitante",
    "formacao_mandante", "formacao_visitante",
    "tecnico_mandante", "tecnico_visitante",
    "vencedor", "arena", "mandante_Placar", "visitante_Placar",
    "mandante_Estado", "visitante_Estado",
]


def baixar():
    r = requests.get(URL, timeout=60)
    r.raise_for_status()
    print("baixados:", len(r.content), "bytes")
    return r.content


def versao_da_fonte():
    """Commit mais recente que mexeu no arquivo. Responde 'qual versao da fonte'.

    Se a API do GitHub nao responder, a ingestao continua sem essa informacao.
    """
    try:
        r = requests.get(URL_COMMITS, timeout=30,
                         params={"path": ARQUIVO, "per_page": 1})
        r.raise_for_status()
        commit = r.json()[0]
        return {"commit": commit["sha"],
                "commit_data": commit["commit"]["committer"]["date"]}
    except Exception as erro:  # noqa: BLE001
        print("aviso: nao consegui o commit da fonte:", erro)
        return {"commit": None, "commit_data": None}


def conferir(conteudo):
    """Confere a estrutura sem alterar nada: so le, nao devolve o dataframe."""
    df = pd.read_csv(BytesIO(conteudo))
    faltando = [c for c in ESPERADAS if c not in df.columns]
    novas = [c for c in df.columns if c not in ESPERADAS]
    print("linhas x colunas:", df.shape)
    if faltando:
        raise ValueError(f"colunas esperadas que sumiram: {faltando}")
    if novas:
        print("ATENCAO: colunas novas na fonte:", novas)
    return len(df)


def salvar(conteudo):
    BRONZE.mkdir(parents=True, exist_ok=True)
    hoje = date.today().strftime("%Y%m%d")
    destino = BRONZE / f"partidas_{hoje}.csv"
    destino.write_bytes(conteudo)  # bytes originais, sem reler nem reescrever
    print("salvo em:", destino)
    return destino


def registrar(destino, conteudo, linhas, versao):
    info = {
        "fonte": f"github.com/{REPO}",
        "url": URL,
        "arquivo_origem": ARQUIVO,
        "arquivo_bronze": destino.name,
        "registros": linhas,
        "bytes": len(conteudo),
        "sha256": hashlib.sha256(conteudo).hexdigest(),
        "versao_fonte": versao,
        "extraido_em": datetime.now().isoformat(timespec="seconds"),
    }
    caminho = BRONZE / "proveniencia.jsonl"
    with caminho.open("a", encoding="utf-8") as f:
        f.write(json.dumps(info, ensure_ascii=False) + "\n")


def main():
    conteudo = baixar()
    linhas = conferir(conteudo)
    destino = salvar(conteudo)
    registrar(destino, conteudo, linhas, versao_da_fonte())


if __name__ == "__main__":
    main()
