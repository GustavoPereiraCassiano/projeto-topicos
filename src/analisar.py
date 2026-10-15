"""Analise do desempenho dos mandantes por estado (Brasileirao Serie A, 2003-2024).

Entrada : dados/prata/brasileirao/brasileirao.parquet (ou caminho passado como 1o argumento)
          dados/prata/ibge/municipios.parquet         (ou caminho passado como 2o argumento)
Saida   : resultados/*.csv, resultados/resumo.json, resultados/*.png
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PRATA_BR = Path(sys.argv[1] if len(sys.argv) > 1 else "dados/prata/brasileirao/brasileirao.parquet")
PRATA_IBGE = Path(sys.argv[2] if len(sys.argv) > 2 else "dados/prata/ibge/municipios.parquet")
SAIDA = Path("resultados")
MIN_JOGOS = 100  # abaixo disso o estado e marcado como amostra pequena

# cores (paleta de referencia da skill dataviz; azul = serie 1)
AZUL, LARANJA, CINZA, TEXTO, TEXTO2, GRADE = "#2a78d6", "#eb6834", "#b8b7b0", "#0b0b0b", "#52514e", "#e6e5e0"


# ---------- dados ----------

#LEITURA DOS DADOS DA PRATA E CRIAÇÃO DAS COLUNAS ANO E RESULTADO
def carregar():     
    df = pd.read_parquet(PRATA_BR)
    df["ano"] = pd.to_datetime(df["data"], format="%d/%m/%Y").dt.year
    df["resultado"] = df["pontos_mandante"].map({3: "V", 1: "E", 0: "D"})
    return df


#LÊ MUNICIPIOS IBGE E MONTA TABELA COM SIGLA NOME E REGIÃO DE CADA ESTADO
def mapa_uf_regiao():   
    """UF -> nome/regiao, extraido dos municipios do IBGE (camada Prata)."""
    m = pd.read_parquet(PRATA_IBGE)
    linhas = []
    for r in m["regiao-imediata"].dropna():
        uf = r["regiao-intermediaria"]["UF"]
        linhas.append((uf["sigla"], uf["nome"], uf["regiao"]["nome"]))
    return pd.DataFrame(linhas, columns=["uf", "estado", "regiao"]).drop_duplicates().set_index("uf")


# ---------- tabelas ----------

#CALCULO DE ESTATISTICAS POR ESTADO
def resumo(grupo, df):      
    g = df.groupby(grupo)
    t = g.agg(jogos=("ID", "size"), times=("mandante", "nunique"),
              pontos_medios=("pontos_mandante", "mean"), dp=("pontos_mandante", "std"))
    for r in ["V", "E", "D"]:
        t[f"{r}_%"] = g["resultado"].apply(lambda s: (s == r).mean() * 100)
    t["aproveitamento_%"] = t["pontos_medios"] / 3 * 100
    ic = 1.96 * t["dp"] / np.sqrt(t["jogos"])
    t["ic95_inf"], t["ic95_sup"] = t["pontos_medios"] - ic, t["pontos_medios"] + ic
    t["amostra_pequena"] = t["jogos"] < MIN_JOGOS
    return t.drop(columns="dp").sort_values("pontos_medios", ascending=False)

#TESTES PARA VERIFICAR SE AS DIFERENÇAS ENTRE ESTADOS IMPORTAM (V-CRAMER E KRUSKAL WALLIS)
def teste_estado(df, rotulo):      
    """Qui-quadrado (V/E/D x estado) + Kruskal-Wallis nos pontos."""
    tab = pd.crosstab(df["mandante_Estado"], df["resultado"])
    chi2, p_chi, gl, _ = stats.chi2_contingency(tab)
    n = tab.values.sum()
    v = np.sqrt(chi2 / (n * (min(tab.shape) - 1)))  
    grupos = [g["pontos_mandante"].values for _, g in df.groupby("mandante_Estado")]
    h, p_kw = stats.kruskal(*grupos)
    return {"amostra": rotulo, "estados": int(tab.shape[0]), "jogos": int(n),
            "qui2": float(chi2), "gl": int(gl), "p_qui2": float(p_chi), "cramer_v": float(v),
            "kruskal_H": float(h), "p_kruskal": float(p_kw)}

#CALCULA QUANTO DA VARIAÇÃO DOS PONTOS É EXPLICADA PELO ESTADO OU PELO TIME (O 1,6% E O 2,6%).
def variancia_explicada(df, coluna):
    """R2 e R2 ajustado dos pontos explicados por um agrupamento (estado ou time)."""
    y = df["pontos_mandante"]
    ss_tot = ((y - y.mean()) ** 2).sum()
    ss_ent = df.groupby(coluna)["pontos_mandante"].transform("mean").sub(y).pow(2).sum()
    k, n = df[coluna].nunique(), len(df)
    r2 = 1 - ss_ent / ss_tot
    return float(r2), float(1 - (1 - r2) * (n - 1) / (n - k))

#PARA CADA ESTADO COM 2 OU MAIS TIMES, TESTA SE OS TIMES DIFEREM ENTRE SI.
def teste_time_dentro_estado(df):
    """Dentro de cada estado com >=2 times, os times diferem entre si? (Kruskal)"""
    out = []
    for uf, g in df.groupby("mandante_Estado"):
        if g["mandante"].nunique() < 2:
            continue
        h, p = stats.kruskal(*[x["pontos_mandante"].values for _, x in g.groupby("mandante")])
        out.append({"estado": uf, "times": g["mandante"].nunique(), "jogos": len(g),
                    "kruskal_H": h, "p": p})
    return pd.DataFrame(out).sort_values("p")


# ---------- graficos ----------

#APARÊNCIA GRÁFICO
def estilo():
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": GRADE,
                         "axes.labelcolor": TEXTO2, "xtick.color": TEXTO2, "ytick.color": TEXTO2,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "figure.facecolor": "white", "axes.facecolor": "white"})

#GRÁFICO DE BARRAS COM A MÉDIA DE PONTOS POR ESTADO E A MARGEM DE ERRO
def graf_media(t, media_geral):
    t = t.sort_values("pontos_medios")
    fig, ax = plt.subplots(figsize=(10, 6.2))
    y = np.arange(len(t))
    cores = [CINZA if p else AZUL for p in t["amostra_pequena"]]
    ax.barh(y, t["pontos_medios"], color=cores, height=0.62)
    ax.errorbar(t["pontos_medios"], y, xerr=[t["pontos_medios"] - t["ic95_inf"], t["ic95_sup"] - t["pontos_medios"]],
                fmt="none", ecolor=TEXTO2, elinewidth=1.2, capsize=3)
    ax.axvline(media_geral, color=LARANJA, lw=1.6, ls="--")
    ax.text(media_geral, len(t) - 0.35, f" média geral {media_geral:.2f}".replace(".", ","),
            color=TEXTO2, va="bottom", ha="left", fontsize=10)
    ax.set_yticks(y)
    ax.set_yticklabels([f"{uf}  (n={n})" for uf, n in zip(t.index, t["jogos"])])
    ax.set_xlim(0, 2.2)
    ax.set_xlabel("pontos por jogo como mandante (barra = IC 95%)")
    ax.xaxis.grid(True, color=GRADE); ax.set_axisbelow(True)
    ax.set_title("Pontos médios do mandante por estado, 2003–2024", loc="left", color=TEXTO, fontsize=13, pad=22)
    ax.text(0, 1.02, "Cinza = menos de 100 jogos (amostra pequena)", transform=ax.transAxes, color=TEXTO2, fontsize=10)
    fig.tight_layout(); fig.savefig(SAIDA / "grafico_media_por_estado.png", dpi=200); plt.close(fig)

#GRÁFICO DE BARRAS EMPILHADAS COM % DE VITÓRIAS, EMPATES E DERROTAS POR ESTADO
def graf_vde(t):
    t = t.sort_values("V_%")
    fig, ax = plt.subplots(figsize=(10, 6.2))
    y = np.arange(len(t))
    esq = np.zeros(len(t))
    for col, cor, nome in [("V_%", AZUL, "Vitória"), ("E_%", CINZA, "Empate"), ("D_%", LARANJA, "Derrota")]:
        ax.barh(y, t[col], left=esq, color=cor, height=0.62, edgecolor="white", linewidth=1.5, label=nome)
        for yi, (l, w) in enumerate(zip(esq, t[col])):
            if w >= 9:
                ax.text(l + w / 2, yi, f"{w:.0f}%", ha="center", va="center",
                        color="white" if col != "E_%" else TEXTO, fontsize=9.5)
        esq += t[col].values
    ax.set_yticks(y)
    ax.set_yticklabels([f"{uf}  (n={n})" for uf, n in zip(t.index, t["jogos"])])
    ax.set_xlim(0, 100); ax.set_xlabel("% dos jogos como mandante")
    ax.legend(ncol=3, frameon=False, loc="lower left", bbox_to_anchor=(0, 1.0))
    ax.set_title("Vitórias, empates e derrotas do mandante por estado", loc="left", color=TEXTO, fontsize=13, pad=30)
    fig.tight_layout(); fig.savefig(SAIDA / "grafico_vde_por_estado.png", dpi=200); plt.close(fig)

#GRÁFICO DE PONTOS COM A MÉDIA DE CADA TIME, AGRUPADOS POR ESTADO.
def graf_times(tt, media_geral):
    tt = tt[tt["jogos"] >= MIN_JOGOS]
    ordem = tt.groupby("mandante_Estado")["pontos_medios"].apply(lambda s: np.average(s, weights=tt.loc[s.index, "jogos"])).sort_values()
    fig, ax = plt.subplots(figsize=(10, 6.2))
    pos = {uf: i for i, uf in enumerate(ordem.index)}
    for _, r in tt.iterrows():
        ax.scatter(r["pontos_medios"], pos[r["mandante_Estado"]], s=22 + r["jogos"] / 12, color=AZUL,
                   alpha=0.85, edgecolor="white", linewidth=1)
    ax.axvline(media_geral, color=LARANJA, lw=1.6, ls="--")
    ax.set_yticks(range(len(ordem))); ax.set_yticklabels(ordem.index)
    ax.set_xlabel("pontos por jogo como mandante (cada ponto = um time; tamanho = nº de jogos)")
    ax.xaxis.grid(True, color=GRADE); ax.set_axisbelow(True)
    ax.set_title("Pontos médios por time, agrupados por estado (estados com 100+ jogos)", loc="left", color=TEXTO, fontsize=13, pad=22)
    ax.text(media_geral, len(ordem) - 0.45, f" média geral {media_geral:.2f}".replace(".", ","), color=TEXTO2, fontsize=10, va="bottom")
    fig.tight_layout(); fig.savefig(SAIDA / "grafico_times_dentro_do_estado.png", dpi=200); plt.close(fig)


#CARREGA TUDO
def main():     
    SAIDA.mkdir(exist_ok=True)
    estilo()
    df = carregar()
    media_geral = float(df["pontos_mandante"].mean())

    uf = mapa_uf_regiao()
    por_estado = resumo("mandante_Estado", df)
    por_estado.insert(0, "estado", por_estado.index.map(uf["estado"]))
    por_estado.insert(1, "regiao", por_estado.index.map(uf["regiao"]))
    por_estado.round(3).to_csv(SAIDA / "tabela_por_estado.csv", index_label="uf")

    df["regiao"] = df["mandante_Estado"].map(uf["regiao"])
    por_regiao = resumo("regiao", df)
    por_regiao.round(3).to_csv(SAIDA / "tabela_por_regiao.csv", index_label="regiao")

    por_time = resumo(["mandante_Estado", "mandante"], df).reset_index()
    por_time.round(3).to_csv(SAIDA / "tabela_por_time.csv", index=False)

    grandes = df[df["mandante_Estado"].isin(por_estado.index[~por_estado["amostra_pequena"]])]
    testes = [teste_estado(df, "todos os estados"),
              teste_estado(grandes, f"estados com >= {MIN_JOGOS} jogos")]
    pd.DataFrame(testes).to_csv(SAIDA / "testes_estado.csv", index=False)

    r2_e, r2a_e = variancia_explicada(df, "mandante_Estado")
    r2_t, r2a_t = variancia_explicada(df, "mandante")
    intra = teste_time_dentro_estado(df)
    intra.to_csv(SAIDA / "testes_time_dentro_do_estado.csv", index=False)

    resumo_json = {
        "jogos": len(df), "periodo": [int(df["ano"].min()), int(df["ano"].max())],
        "times": int(df["mandante"].nunique()), "estados": int(df["mandante_Estado"].nunique()),
        "media_geral_pontos": media_geral,
        "testes": testes,
        "variancia_explicada": {"estado_r2": r2_e, "estado_r2_ajustado": r2a_e,
                                "time_r2": r2_t, "time_r2_ajustado": r2a_t},
        "times_dentro_do_estado_p<0.05": int((intra["p"] < 0.05).sum()), "estados_com_2+_times": len(intra),
    }
    (SAIDA / "resumo.json").write_text(json.dumps(resumo_json, ensure_ascii=False, indent=2))

    graf_media(por_estado, media_geral)
    graf_vde(por_estado)
    graf_times(por_time, media_geral)
    print(json.dumps(resumo_json, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
