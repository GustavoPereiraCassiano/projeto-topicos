# Desempenho dos times no Campeonato Brasileiro por estado

Pipeline de dados em camadas (bronze → prata → ouro) da disciplina Engenharia de Dados na Prática (UNIFEI).

**Aluno:** Gustavo Pereira Cassiano

**Pergunta norteadora:** existe relação entre o estado de origem de um time e seu desempenho como mandante no Campeonato Brasileiro (Série A)?

**Recorte:** partidas da Série A de 2003 a 2024 (ver *Defeitos conhecidos*, item 1).

## Estrutura

```
Projeto Tópicos/
  dados/
    bronze/
      brasileirao/   partidas_AAAAMMDD.csv, proveniencia.jsonl
      ibge/          municipios_AAAAMMDD.json, proveniencia.jsonl
    prata/           partidas.parquet, clubes.parquet, ufs.parquet, proveniencia.jsonl
    ouro/            (próxima etapa)
  src/
    ingerir_partidas.py        bronze: Brasileirão (CSV no GitHub)
    ingerir_ibge.py            bronze: municípios do IBGE (API aberta)
    explorar.py                perfilamento automático da bronze
    limpeza.py                 funções de limpeza que servem a qualquer fonte
    transformar_ibge.py        prata: municípios → tabela de UFs
    transformar_partidas.py    prata: partidas e clubes
    carregar_banco.py          carga da prata em SQLite (opcional)
    rodar_pipeline.py          roda tudo na ordem
  README.md  requirements.txt  .gitignore
```

## Como executar

Na raiz do projeto, com o ambiente virtual ativado (PowerShell: `.venv\Scripts\Activate.ps1`):

```
pip install -r requirements.txt
python src/rodar_pipeline.py            # bronze e prata
python src/rodar_pipeline.py --banco    # e carrega a prata no SQLite
python src/explorar.py                  # relatórios de perfil em relatorios/
```

Cada script também roda sozinho. A prata é reconstruível: apagar `dados/prata/` e rodar de novo refaz tudo. A bronze nunca é editada.

`setuptools<82` está travado no `requirements.txt` porque o `fg-data-profiling` usa o módulo `pkg_resources`, removido no setuptools 82.

## Fontes de dados

| Fonte | Formato | Acesso | Extraído | Link |
|---|---|---|---|---|
| Brasileirão Dataset (`campeonato-brasileiro-full.csv`) | CSV | aberto, download direto | 01/10/2026 | https://github.com/adaoduque/Brasileirao_Dataset |
| IBGE, API de Localidades (municípios) | JSON | aberto, sem chave | rodar `ingerir_ibge.py` e preencher | https://servicodados.ibge.gov.br/api/v1/localidades/municipios |

**Chave de ligação:** sigla da UF. A fonte primária traz `mandante_Estado` e `visitante_Estado` (ex.: `SP`); cada município do IBGE traz a UF aninhada, e o agrupamento de municípios por UF gera a tabela `ufs`, que traz região e número de municípios.

**Proveniência:** cada extração acrescenta uma linha em `dados/bronze/<fonte>/proveniencia.jsonl` com fonte, URL, arquivo gravado, número de registros, SHA-256, data de extração e, no Brasileirão, o commit do arquivo na fonte. As extrações são datadas e a de hoje não apaga a de ontem.

**Primária, volume:** 8.785 linhas (uma por partida) × 16 colunas, de 29/03/2003 a 08/12/2024.

## Defeitos conhecidos das fontes

Achados do perfilamento (`explorar.py`) e das conferências de ingestão e prata.

### Brasileirão (GitHub)

1. **Cobertura menor que a declarada na ficha.** O CSV termina em 08/12/2024 (22 temporadas, 2003–2024). O repositório tem `data/brasileirao-2025.json`, mas ele não está no CSV.
2. A coluna `rodata` é erro de grafia de `rodada`. A legenda da fonte fala em `Rodada`, `Horário` e `Dia`; o CSV tem `rodata`, `hora` e não tem coluna de dia da semana.
3. **`arena` com espaço sobrando:** 5.077 de 8.785 células (57,8%) começam com espaço não separável (`\xa0`), que não aparece na tela.
4. `arena` tem 168 grafias para menos estádios: `Morumbi` e `MorumBIS`, `Beira Rio` e `Estádio Beira-Rio`, `Engenhão` e `Estádio Nilton Santos`, entre outras. Em 25 partidas (2005 e 2006) o nome vem com sufixo `*(PF)` ou `(*PF)`, cujo significado não consta na legenda.
5. **`vencedor` contradiz o placar em 1 partida:** ID 1114, 24/04/2005, Brasiliense 0 × 1 Vasco, com vencedor `-` (empate).
6. **Ausentes por não coleta:** `formacao_*` com 4.975 (56,6%) e `tecnico_*` com 4.610 (52,5%). Estão vazias em todas as partidas de 2003 a 2013; `tecnico_*` volta em 2014 e `formacao_*` em 2015, quase por inteiro.
7. **2016 tem 379 partidas, e deveriam ser 380:** falta Chapecoense (mandante) × Atlético-MG.
8. **A fonte não tem coluna de temporada**, e o ano da data não basta: a edição de 2020 terminou em 25/02/2021.
9. **Estado e clube são a mesma informação.** O perfil acusa alta correlação entre `mandante` e `mandante_Estado`, e a prata confirma que cada um dos 45 clubes tem uma única UF. Isso limita a pergunta (ver *Limitações*).
10. **Só 15 das 27 UFs aparecem.** SP, RJ, RS, MG, PR, SC, BA, GO, PE e CE concentram a maior parte; MT (76 jogos como mandante), PA (67), DF (21), RN (19) e AL (19) têm pouquíssimos.
11. Dúvida: `Barueri` e `Gremio Prudente` (19 jogos como mandante cada, ambos SP) podem ser o mesmo clube em anos diferentes. Não foram unificados.
12. Não são defeitos, mas aparecem como alerta: `visitante_Placar` com 36,3% de zeros e `ID` uniforme e único.

### IBGE (municípios)

1. A resposta é uma lista de municípios com UF aninhada (`microrregiao > mesorregiao > UF`). Alguns municípios recentes vêm com `microrregiao` nula; o script usa `regiao-imediata > regiao-intermediaria > UF` nesses casos.
2. *Preencher após rodar `transformar_ibge.py`:* total de municípios, quantos usaram o caminho alternativo, número de UFs (esperado: 27).

## Decisões de tratamento (prata)

Números da execução de 01/10/2026 sobre a bronze `partidas_20261001.csv`. As mesmas decisões ficam em `dados/prata/proveniencia.jsonl`.

### Brasileirão → `partidas.parquet` (8.785 linhas) e `clubes.parquet` (45 linhas)

- Colunas renomeadas para `snake_case`; `rodata` virou `rodada`, `mandante_Placar` virou `placar_mandante`, `mandante_Estado` virou `uf_mandante` (idem visitante).
- Espaços removidos: 5.077 células de `arena`; nenhuma outra coluna foi afetada.
- Chave: `partida_id` (0 repetidos). Chave natural conferida: (`data`, `mandante`, `visitante`), 0 repetidos.
- Tipos: `data` convertida com formato declarado `%d/%m/%Y` (0 viraram ausentes); `partida_id`, `rodada` e placares em inteiro (0 ausentes); `hora` mantida como texto `HH:MM` (0 fora do formato); UFs e região como categoria.
- Erros de domínio removidos: **0 linhas**. Faixas usadas: placar de 0 a 30, rodada de 1 a 60, data entre 01/01/2003 e hoje, mandante diferente de visitante.
- `vencedor` mantido como veio e conferido contra o placar: 1 divergência (partida 1114), sinalizada em `vencedor_confere`. O `resultado_mandante` sai do placar.
- Temporadas: 22. Só 2016 foge de n×(n−1) jogos (379 em vez de 380); mantida, sem preenchimento.
- Junção com o IBGE por UF: relação muitos-para-um, 8.785 linhas antes e depois, 0 mandantes sem região. O script falha se o número de linhas mudar.
- Arenas: o rótulo original limpo fica em `arena`; `arena_chave` (sem acento, minúscula, sem o sufixo PF e com 13 sinônimos evidentes unificados) reduz 168 grafias para 146. O restante fica como a fonte escreveu. `arena_pf` guarda a marca PF separada.
- Extremos marcados, **nenhum removido** (o maior placar é 7 gols, que é legítimo):

  | coluna | marcados por IQR | marcados por \|z\| > 3 |
  |---|---|---|
  | `placar_mandante` | 608 | 44 |
  | `placar_visitante` | 10 | 36 |
  | `saldo_gols_mandante` | 1.606 | 25 |

  O IQR marca muito em contagem de gols porque a distribuição é discreta e concentrada em poucos valores; o z-score é mais enxuto. A divergência entre os dois é esperada, e a coluna de sinalização serve para filtrar se for preciso.
- Ausentes mantidos: `formacao_*` e `tecnico_*` (não coletado). A pergunta não usa essas colunas.
- Saída em Parquet, sem data no nome (a prata é reconstruível).

### IBGE → `ufs.parquet` (27 UFs esperadas)

- JSON achatado em uma linha por município; agregado em uma linha por UF, com região e `n_municipios`.
- Chave: `uf_sigla`, que a conferência exige única.
- Conferir na saída: 27 UFs, 0 `municipio_id` repetidos.

## Atributos derivados

Todos calculados em funções de `transformar_partidas.py`, sempre pelo lado do mandante, que é o da pergunta.

### temporada
Ano do campeonato; jogos de janeiro e fevereiro pertencem à temporada anterior. Existe porque a fonte não tem temporada e 2020 terminou em 2021. Nunca é ausente.

### resultado_mandante
Categoria ordenada `derrota < empate < vitoria`, calculada do placar. Serve para contar vitórias, empates e derrotas por estado e corrige o caso em que `vencedor` contradiz o placar.

### pontos_mandante
0, 1 ou 3, pelo resultado. É a forma numérica do resultado, e a média dela dividida por 3 é o aproveitamento como mandante, a medida de desempenho da pergunta.

### saldo_gols_mandante
Gols do mandante menos gols do visitante. Mede a margem, que o resultado sozinho esconde.

### mesmo_estado
Verdadeiro quando mandante e visitante são da mesma UF. Serve para separar clássicos estaduais, onde o estado de origem não diferencia os dois lados.

### regiao_mandante
Região da UF do mandante, vinda do IBGE. Agrupa os 15 estados em 5 regiões, útil porque vários estados têm poucos jogos. Fica ausente se a UF não existir no IBGE (hoje, 0 casos).

### Sinalizações
`placar_mandante_extremo`, `placar_visitante_extremo` e `saldo_gols_mandante_extremo` (IQR), `vencedor_confere`, `arena_pf`.

## Limitações para a camada ouro

- **Estado e clube se confundem.** Com 45 clubes e uma UF por clube, qualquer diferença entre estados é também diferença entre os clubes daquele estado. A análise precisa dizer o que o estado explica além do clube.
- Só 15 UFs têm mandante; MT, PA, DF, RN e AL somam menos de 250 jogos.
- A Série A teve 24 clubes (2003–2004), 22 (2005) e 20 (2006 em diante); o número de jogos por clube varia entre temporadas.
- Clubes que ficam mais tempo na Série A pesam mais no total do estado.
- 2020 e 2021 foram afetadas pela pandemia; vale testar a vantagem de mandante com e sem esses anos.
