# Desempenho dos times no Brasileirão (Série A) por estado, 2003–2024

Projeto final de Tópicos Especiais em Programação (ECOX14, UNIFEI).
Autor: Gustavo Pereira Cassiano.

**Pergunta de pesquisa:** existe relação entre o estado de origem de um time e seu desempenho como mandante no Campeonato Brasileiro (Série A)?

## Como rodar (um comando, a partir da raiz)

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
python src/pipeline.py
```

O pipeline executa, em ordem: ingestão → transformação → enriquecimento → carga → modelagem (dbt run + dbt test) → análise. O log vai para o console e para `pipeline.log`.

Para retomar a partir de uma etapa (sem baixar os dados de novo):

```bash
python src/pipeline.py transformacao   # ou: enriquecimento, carga, modelagem, analise
```

Painel (depois do pipeline):

```bash
streamlit run dashboard/painel.py
```

Documentação do modelo (opcional): `cd brasileirao_dbt && dbt docs generate --profiles-dir . && dbt docs serve --profiles-dir .`

## Fontes

| Fonte | Formato | Uso |
|---|---|---|
| Brasileirão (GitHub, base de jogos da Série A) | CSV | jogos, placares, times e estado do mandante |
| API de Localidades do IBGE | JSON | estados e regiões (via municípios) |

## Arquitetura (medalhão)

| Camada | Onde | Conteúdo |
|---|---|---|
| Bronze | `dados/bronze/` | arquivos como a fonte entrega, com data no nome; nunca alterados |
| Prata | `dados/prata/` | Parquet limpo, `pontos_mandante` criado, jogos enriquecidos com a região |
| Ouro | `dados/ouro/projeto.duckdb` (esquema `ouro`) | modelo dimensional construído pelo dbt |

Cada etapa acrescenta um registro em `proveniencia.jsonl` (fonte, arquivos de origem e destino, linhas antes/depois, decisões, data). A proveniência da Ouro também guarda a versão do dbt, o resultado dos testes e o commit do código.

```
src/                 ingestão, transformação, enriquecimento, carga, pipeline, análise
brasileirao_dbt/     projeto dbt: modelos, testes e profiles.yml (banco em dados/ouro)
dashboard/           consultas.py (SQL) e painel.py (interface Streamlit)
dados/               bronze, prata, ouro
resultados/          tabelas e gráficos da análise
```

## Etapas

1. **Ingestão** (`ingerir.py`, `ingerir_municipios.py`): baixa os dois arquivos para a Bronze e registra a origem.
2. **Transformação** (`transformar_*.py`, `limpeza.py`): remove espaços, remove duplicadas (0 encontradas), converte placares e cria `pontos_mandante` (3 vitória, 1 empate, 0 derrota).
3. **Enriquecimento** (`enriquecer.py`): extrai uma linha por UF do IBGE e junta à tabela de jogos por `mandante_Estado = UF` (`left`, `validate="many_to_one"`). As chaves são comparadas antes da junção. Resultado: 8.785 linhas antes e depois, 0 jogos sem região.
4. **Carga** (`carga.py`): copia a Prata para o DuckDB (esquema `prata`).
5. **Modelagem** (`brasileirao_dbt/`): o dbt constrói a Ouro e roda os testes.
6. **Análise** (`analisar.py`): lê a view da Ouro e gera tabelas, testes estatísticos e gráficos em `resultados/`.

## Modelo da Ouro

Esquema estrela, um fato e duas dimensões, mais uma view achatada para consulta.

| Tabela | Grão | Linhas |
|---|---|---|
| `dim_estado` | um registro por UF | 27 |
| `dim_time` | um registro por time (mapeado a um único estado) | 45 |
| `fato_partida` | uma linha por partida (o time mandante é o foco) | 8.785 |
| `vw_desempenho_mandante` | uma linha por partida, com time, estado e região | 8.785 |

Decisões: um time pertence a um único estado (verificado: 45 times, cada um com uma UF); a view usa `left join` para não perder partidas; a análise e o painel só leem a view, em modo somente leitura.

## Qualidade

**dbt (28 testes, todos passando):** `unique` e `not_null` nas chaves, `relationships` fato→dimensões e dim_time→dim_estado, `accepted_values` em `resultado` (V/E/D), mais 5 testes singulares em `brasileirao_dbt/tests/`:

| Teste singular | Garante |
|---|---|
| `pontos_coerentes_com_placar` | pontos = 3/1/0 conforme o placar |
| `mandante_diferente_do_visitante` | nenhum time joga contra si mesmo |
| `fato_tem_todas_as_partidas` | a Ouro tem as partidas da Prata |
| `vw_sem_perda_de_linhas` | a view tem as mesmas linhas do fato |
| `vw_sem_estado_ausente` | todo jogo tem estado e região |

**Python (`carga.conferir`):** partidas repetidas = 0, fatos sem time na dimensão = 0, diferença Prata × Ouro = 0. Se algum for diferente de zero, o pipeline para.

## Resultados

Base: 8.785 jogos, 45 times, 15 estados, de 29/03/2003 a 08/12/2024. Média geral do mandante: **1,75 ponto por jogo** (aproveitamento ≈ 58%).

| Estado | Jogos | Pontos/jogo | IC 95% |
|---|---|---|---|
| RS | 959 | 1,93 | 1,85–2,01 |
| SP | 2.173 | 1,88 | 1,82–1,93 |
| MG | 913 | 1,80 | 1,72–1,89 |
| PR | 828 | 1,80 | 1,71–1,89 |
| RJ | 1.556 | 1,76 | 1,69–1,82 |
| SC | 606 | 1,48 | 1,38–1,58 |

(tabela completa em `resultados/tabela_por_estado.csv`; estados com menos de 100 jogos aparecem marcados como amostra pequena e não entram nas conclusões.)

- Existe diferença entre estados: qui-quadrado (V/E/D × estado) = 158,0, p < 0,001; Kruskal-Wallis H = 140,1, p < 0,001.
- O efeito é **pequeno**: V de Cramér = 0,09; o estado explica 1,6% da variação dos pontos (R² ajustado 1,4%), enquanto o time explica 2,6%.
- Dentro de um mesmo estado os times também diferem (6 de 10 estados com 2+ times têm p < 0,05): o estado sozinho não é o fator.

**Conclusão:** há relação estatisticamente detectável, mas fraca. Estados com times historicamente fortes (RS, SP, MG, PR) aparecem à frente; a diferença vem mais dos times do que do estado em si.

## Limitações

- O estado é o do time (mandante), não necessariamente o da cidade do estádio.
- Estados com um único time (PA, AL, MT, DF, RN) têm poucos jogos e ficam fora das conclusões (mínimo de 100 jogos, `MIN_JOGOS` em `config.py`).
- Os dados vão até 2024 (a ficha do projeto citava 2025). O ano usado é o da data do jogo, então 2020/2021 ficam divididos pela temporada que atravessou o fim do ano.
- Estado e time estão misturados: com a base disponível, não é possível separar o efeito do estado do efeito do time.
- A API do IBGE depende de rede; a Bronze versionada permite reproduzir sem baixar de novo (`python src/pipeline.py transformacao`).

## Governança

Dados públicos, sem informação pessoal. Bronze imutável, com data no nome; Prata e Ouro são recriadas a cada execução e rastreáveis pela proveniência. As credenciais (se houver, como `kaggle.json`) não são versionadas.
