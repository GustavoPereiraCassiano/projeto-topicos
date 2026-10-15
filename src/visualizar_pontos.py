import pandas as pd

df = pd.read_parquet("dados/prata/brasileirao/brasileirao.parquet")

print(df[["mandante", "mandante_Estado", "pontos_mandante"]].head(10))
