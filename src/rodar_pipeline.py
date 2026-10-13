"""Roda o pipeline inteiro, na ordem, a partir de qualquer pasta.

    python src/rodar_pipeline.py            # bronze + prata
    python src/rodar_pipeline.py --banco    # e carrega a prata no SQLite
Para o primeiro erro. Cada etapa continua podendo rodar sozinha.
"""
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
ETAPAS = [
    "ingerir_partidas.py",     # bronze: fonte primaria
    "ingerir_ibge.py",         # bronze: fonte secundaria
    "transformar_ibge.py",     # prata: tabela de UFs (precisa vir antes das partidas)
    "transformar_partidas.py", # prata: partidas e clubes
]


def main():
    etapas = ETAPAS + (["carregar_banco.py"] if "--banco" in sys.argv else [])
    for etapa in etapas:
        print(f"\n=== {etapa} ===")
        resultado = subprocess.run([sys.executable, str(SRC / etapa)], cwd=SRC.parent)
        if resultado.returncode != 0:
            sys.exit(f"falhou em {etapa}")
    print("\npipeline concluido")


if __name__ == "__main__":
    main()
