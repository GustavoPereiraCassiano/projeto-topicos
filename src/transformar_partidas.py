"""Prata da fonte primaria: partidas do Campeonato Brasileiro (Serie A).

Entrada: dados/bronze/brasileirao/partidas_*.csv (mais recente)
         dados/prata/ufs.parquet (gerado por transformar_ibge.py)
Saida:   dados/prata/partidas.parquet  (uma linha por partida)
         dados/prata/clubes.parquet    (uma linha por clube)

Pergunta norteadora: existe relacao entre o estado de origem de um time e seu
desempenho como mandante? Por isso a tabela e vista pelo lado do mandante.
"""
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

import limpeza

RAIZ = Path(__file__).resolve().parent.parent
BRONZE = RAIZ / "dados" / "bronze" / "brasileirao"
PRATA = RAIZ / "dados" / "prata"
PADRAO = "partidas_*.csv"

# --- decisoes especificas desta fonte (por isso moram aqui, nao em limpeza.py) ---
RENOMEAR = {
    "ID": "partida_id",
    "rodata": "rodada",  # a fonte grafou 'rodata'; a legenda dela diz 'Rodada'
    "mandante_Placar": "placar_mandante",
    "visitante_Placar": "placar_visitante",
    "mandante_Estado": "uf_mandante",
    "visitante_Estado": "uf_visitante",
}
ORDEM_RESULTADO = ["derrota", "empate", "vitoria"]
PADRAO_PF = r"\s*\*?\(\*?PF\)"  # sufixos '*(PF)' e '(*PF)' que a fonte cola no nome da arena
# Sinonimos de arena, ja na forma de chave_texto. So entram os casos em que
# e inequivocamente o mesmo estadio; o resto fica como a fonte escreveu.
MAPA_ARENAS = {
    "morumbis": "morumbi",
    "estadio beira-rio": "beira rio",
    "estadio serra dourada": "serra dourada",
    "estadio do governo do estado de goias (serra dourada)": "serra dourada",
    "estadio sao januario": "sao januario",
    "estadio do arruda": "arruda",
    "estadio independencia": "independencia",
    "estadio nilton santos": "engenhao",
    "olimpico engenhao": "engenhao",
    "estadio ipatingao": "ipatingao",
    "luso-brasileiro": "luso brasileiro",
    "arena fonte nova": "fonte nova",
    "itaipava arena fonte nova": "fonte nova",
}
COLUNAS_FINAIS = [
    "partida_id", "temporada", "rodada", "data", "hora",
    "mandante", "uf_mandante", "regiao_mandante",
    "visitante", "uf_visitante",
    "placar_mandante", "placar_visitante",
    "resultado_mandante", "pontos_mandante", "saldo_gols_mandante", "mesmo_estado",
    "vencedor", "vencedor_confere",
    "arena", "arena_chave", "arena_pf",
    "formacao_mandante", "formacao_visitante", "tecnico_mandante", "tecnico_visitante",
    "placar_mandante_extremo", "placar_visitante_extremo", "saldo_gols_mandante_extremo",
]


def carregar():
    arquivos = sorted(BRONZE.glob(PADRAO))
    if not arquivos:
        raise FileNotFoundError(f"nada em {BRONZE}; rode ingerir_partidas.py")
    caminho = arquivos[-1]
    df = pd.read_csv(caminho)
    print("lido:", caminho.name, df.shape)
    for coluna in df.columns:
        print(f'"{coluna}"', int(df[coluna].isna().sum()), "ausentes")
    return df, caminho


def carregar_ufs():
    caminho = PRATA / "ufs.parquet"
    if not caminho.exists():
        raise FileNotFoundError("falta dados/prata/ufs.parquet; rode transformar_ibge.py antes")
    return pd.read_parquet(caminho)


def converter_tipos(df):
    """Datas com formato declarado; numeros com coerce (e conta quantos viraram ausentes)."""
    coercoes = {}
    antes = int(df["data"].isna().sum())
    df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y", errors="coerce")
    coercoes["data"] = int(df["data"].isna().sum()) - antes
    for coluna in ["partida_id", "rodada", "placar_mandante", "placar_visitante"]:
        antes = int(df[coluna].isna().sum())
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce")
        coercoes[coluna] = int(df[coluna].isna().sum()) - antes
    print("valores que viraram ausentes na conversao:", coercoes)
    hora_invalida = int((~df["hora"].str.match(r"^\d{2}:\d{2}$", na=False)).sum())
    print("hora fora do formato HH:MM:", hora_invalida)
    return df, coercoes, hora_invalida


def remover_erros_de_dominio(df):
    """Erro comprovado pelo dominio: remove e conta. Extremo legitimo so e marcado depois."""
    removidas = {}
    df, removidas["placar_mandante"] = limpeza.remover_erros(df, "placar_mandante", 0, 30)
    df, removidas["placar_visitante"] = limpeza.remover_erros(df, "placar_visitante", 0, 30)
    df, removidas["rodada"] = limpeza.remover_erros(df, "rodada", 1, 60)
    df, removidas["data"] = limpeza.remover_erros(
        df, "data", pd.Timestamp("2003-01-01"), pd.Timestamp.today())
    mesmo_clube = df["mandante"] == df["visitante"]
    removidas["mandante_igual_visitante"] = int(mesmo_clube.sum())
    print("mandante igual a visitante removidas:", removidas["mandante_igual_visitante"])
    df = df[~mesmo_clube].copy()
    for coluna in ["partida_id", "rodada", "placar_mandante", "placar_visitante"]:
        df[coluna] = df[coluna].astype("int64")
    return df, removidas


def conferir_ufs(df, ufs):
    """Toda UF da fonte primaria precisa existir no IBGE; senao a juncao perde linha."""
    validas = set(ufs["uf_sigla"])
    fora = sorted((set(df["uf_mandante"]) | set(df["uf_visitante"])) - validas)
    print("UFs que nao existem no IBGE:", fora or "nenhuma")
    return fora


def padronizar_arenas(df):
    """Rotulo original limpo em `arena`; chave comparavel em `arena_chave`; marca PF a parte."""
    antes = df["arena"].nunique()
    df["arena_pf"] = df["arena"].str.contains(PADRAO_PF, regex=True)
    sem_pf = df["arena"].str.replace(PADRAO_PF, "", regex=True)
    df["arena_chave"] = limpeza.aplicar_mapa(limpeza.chave_texto(sem_pf), MAPA_ARENAS)
    depois = df["arena_chave"].nunique()
    print(f"arenas distintas: {antes} (rotulo) -> {depois} (chave); com marca PF: {int(df['arena_pf'].sum())}")
    return df, antes, depois


def derivar_resultado(df):
    """Resultado, pontos e saldo, sempre pelo lado do mandante, a partir do placar."""
    saldo = df["placar_mandante"] - df["placar_visitante"]
    df["saldo_gols_mandante"] = saldo
    resultado = np.where(saldo > 0, "vitoria", np.where(saldo < 0, "derrota", "empate"))
    df["resultado_mandante"] = pd.Categorical(resultado, categories=ORDEM_RESULTADO, ordered=True)
    df["pontos_mandante"] = np.select([saldo > 0, saldo == 0], [3, 1], default=0)
    # a coluna `vencedor` da fonte e conferida contra o placar, nao substituida
    esperado = np.select([saldo > 0, saldo < 0], [df["mandante"], df["visitante"]], default="-")
    df["vencedor_confere"] = df["vencedor"].to_numpy() == esperado
    divergentes = df.loc[~df["vencedor_confere"], "partida_id"].tolist()
    print("vencedor diferente do placar:", len(divergentes), divergentes)
    return df, divergentes


def derivar_temporada(df):
    """Ano do campeonato. Jogos de janeiro e fevereiro pertencem a temporada anterior.

    Necessario porque a edicao de 2020 terminou em fevereiro de 2021.
    """
    df["temporada"] = (df["data"].dt.year - (df["data"].dt.month <= 2)).astype("int64")
    return df


def conferir_temporadas(df):
    """Uma temporada de pontos corridos tem n*(n-1) jogos. Lista as que fogem disso."""
    por_temporada = df.groupby("temporada").agg(jogos=("partida_id", "size"),
                                                clubes=("mandante", "nunique"))
    por_temporada["esperado"] = por_temporada["clubes"] * (por_temporada["clubes"] - 1)
    anomalas = por_temporada[por_temporada["jogos"] != por_temporada["esperado"]]
    print("temporadas:", len(por_temporada), "| fora do esperado:", len(anomalas))
    if len(anomalas):
        print(anomalas)
    return anomalas


def integrar_ufs(df, ufs):
    """Traz a regiao do mandante a partir da tabela de UFs do IBGE (chave: sigla da UF)."""
    antes = len(df)
    regiao = ufs[["uf_sigla", "regiao_nome"]].rename(
        columns={"uf_sigla": "uf_mandante", "regiao_nome": "regiao_mandante"})
    df = df.merge(regiao, on="uf_mandante", how="left", validate="m:1")
    sem_regiao = int(df["regiao_mandante"].isna().sum())
    print("linhas antes/depois da juncao:", antes, len(df), "| sem regiao:", sem_regiao)
    if len(df) != antes:
        raise ValueError("a juncao mudou o numero de linhas")
    return df, sem_regiao


def montar_clubes(df):
    m = df[["mandante", "uf_mandante"]].set_axis(["clube", "uf_sigla"], axis=1)
    v = df[["visitante", "uf_visitante"]].set_axis(["clube", "uf_sigla"], axis=1)
    clubes = pd.concat([m, v]).drop_duplicates().reset_index(drop=True)
    com_mais_de_uma = clubes[clubes["clube"].duplicated(keep=False)]
    if len(com_mais_de_uma):
        print("ATENCAO: clube com mais de uma UF:\n", com_mais_de_uma)
    clubes["clube_chave"] = limpeza.chave_texto(clubes["clube"])
    clubes["uf_sigla"] = clubes["uf_sigla"].astype("category")
    print("clubes:", len(clubes))
    return clubes.sort_values("clube").reset_index(drop=True)


def salvar(df, nome):
    PRATA.mkdir(parents=True, exist_ok=True)
    destino = PRATA / nome
    df.to_parquet(destino, index=False)
    print("salvo em:", destino, df.shape)
    return destino


def registrar(origem, destino, antes, depois, decisoes):
    limpeza.acrescentar_jsonl(PRATA / "proveniencia.jsonl", {
        "origem": origem.name,
        "arquivo_prata": destino.name,
        "linhas_antes": antes,
        "linhas_depois": depois,
        "decisoes": decisoes,
        "transformado_em": datetime.now().isoformat(timespec="seconds"),
    })


def main():
    df, origem = carregar()
    ufs = carregar_ufs()
    antes = len(df)
    df = df.rename(columns=RENOMEAR)

    espacos = limpeza.contar_com_espaco(df)
    print("celulas com espaco sobrando:", espacos)
    df = limpeza.tirar_espacos(df)
    df, repetidos_id = limpeza.conferir_chave(df, "partida_id")
    df, repetidos_nat = limpeza.conferir_chave(df, ["data", "mandante", "visitante"])

    df, coercoes, hora_invalida = converter_tipos(df)
    df, removidas = remover_erros_de_dominio(df)
    uf_fora = conferir_ufs(df, ufs)

    df, divergentes = derivar_resultado(df)
    df = derivar_temporada(df)
    anomalas = conferir_temporadas(df)
    df["mesmo_estado"] = df["uf_mandante"] == df["uf_visitante"]
    df, sem_regiao = integrar_ufs(df, ufs)
    df, arenas_antes, arenas_depois = padronizar_arenas(df)

    for coluna in ["placar_mandante", "placar_visitante", "saldo_gols_mandante"]:
        df = limpeza.marcar_extremos(df, coluna)
        limpeza.contar_zscore(df, coluna)
    extremos = {c: int(df[c + "_extremo"].sum())
                for c in ["placar_mandante", "placar_visitante", "saldo_gols_mandante"]}

    for coluna in ["uf_mandante", "uf_visitante", "regiao_mandante"]:
        df[coluna] = df[coluna].astype("category")
    df["data"] = df["data"].dt.normalize()

    df = df[COLUNAS_FINAIS].sort_values(["data", "partida_id"]).reset_index(drop=True)
    clubes = montar_clubes(df)
    destino = salvar(df, "partidas.parquet")
    salvar(clubes, "clubes.parquet")

    ausentes = {c: int(df[c].isna().sum())
                for c in ["formacao_mandante", "formacao_visitante", "tecnico_mandante", "tecnico_visitante"]}
    registrar(origem, destino, antes, len(df), [
        "coluna rodata renomeada para rodada; demais colunas em snake_case",
        f"celulas com espaco sobrando (pontas ou repetido) tratadas: {espacos}",
        f"partida_id repetidos: {repetidos_id}; chave natural (data, mandante, visitante) repetida: {repetidos_nat}",
        f"conversao para ausente: {coercoes}; hora fora do formato: {hora_invalida}",
        f"linhas removidas por erro de dominio: {removidas}",
        f"UFs fora do IBGE: {uf_fora or 'nenhuma'}; mandantes sem regiao apos a juncao: {sem_regiao}",
        f"vencedor divergente do placar (mantido, sinalizado em vencedor_confere): {divergentes}",
        f"temporadas com numero de jogos fora de n*(n-1): {anomalas['jogos'].to_dict() if len(anomalas) else 'nenhuma'}",
        f"arenas distintas: {arenas_antes} -> {arenas_depois} na chave; marca PF separada em arena_pf",
        f"extremos por IQR marcados (nao removidos): {extremos}",
        f"ausentes mantidos (nao coletado): {ausentes}",
    ])


if __name__ == "__main__":
    main()
