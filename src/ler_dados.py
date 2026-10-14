import pandas as pd

CAMINHO = "dados/bronze/artists.csv"
df = pd.read_csv(CAMINHO)
print(df.shape)

for coluna in df.columns:
    print(f'"{coluna}"')

ESPERADAS = ["Artist Name", "Artist Type","Debut Year"]

faltando = [c for c in ESPERADAS
    if c not in df.columns]

print("Nao encontradas:", faltando)

def carregar():
    return pd.read_csv(CAMINHO)

def conferir_estrutura(df):
    print(df.shape)
    print(df.dtypes)

if __name__ == "__main__":
    conferir_estrutura(carregar())