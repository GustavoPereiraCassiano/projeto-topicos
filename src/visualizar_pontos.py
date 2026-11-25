"""Conferência rápida do pontos_mandante, fora do pipeline."""
import pandas as pd

import config

df = pd.read_parquet(config.PRATA_BRASILEIRAO / "brasileirao.parquet")

print(df[["mandante", "mandante_Estado", "pontos_mandante"]].head(10))
