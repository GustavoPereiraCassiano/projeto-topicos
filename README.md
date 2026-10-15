# Projeto de Engenharia de Dados

## Objetivo

Realizar a ingestão de dados de diferentes fontes para a camada Bronze, preservando os dados originais, e transformar os dados para a camada Prata, realizando verificações de qualidade, criando atributos derivados e registrando a proveniência das operações.

O projeto utiliza dados do Campeonato Brasileiro e do IBGE para preparar os dados para análises posteriores.

## Fontes de dados

| Fonte | Tipo | Dados |
|---|---|---|
| Brasileirão Dataset | CSV / GitHub | Dados dos jogos do Campeonato Brasileiro |
| API de Localidades do IBGE | JSON / API REST | Informações sobre os municípios brasileiros |

## Estrutura do projeto

- `src/`: códigos de ingestão, exploração, limpeza e transformação dos dados.
- `dados/bronze/brasileirao/`: dados originais do Brasileirão.
- `dados/bronze/ibge/`: dados originais dos municípios do IBGE.
- `dados/prata/brasileirao/`: dados transformados do Brasileirão em formato Parquet.
- `dados/prata/ibge/`: dados transformados dos municípios do IBGE em formato Parquet.
- `proveniencia.jsonl`: registros de proveniência das operações, armazenados junto aos dados transformados.

## Proveniência

Os processos de ingestão e transformação registram informações que permitem acompanhar a origem dos dados e as operações realizadas.

Os registros de proveniência documentam informações como:

- Fonte dos dados.
- Nome do arquivo de origem.
- Nome do arquivo gerado.
- Quantidade de registros antes e depois da transformação.
- Decisões tomadas durante o processamento.
- Data e hora da operação.

Esses registros permitem rastrear as transformações e manter um histórico do processamento dos dados.

## Transformações dos dados

### Brasileirão

O arquivo original em CSV foi processado para gerar um arquivo Parquet na camada Prata.

As transformações realizadas foram:

- Remoção de espaços desnecessários nos nomes das colunas e nos valores textuais.
- Verificação e remoção de linhas duplicadas.
- Conversão das colunas de placar para valores numéricos.
- Criação do atributo derivado `pontos_mandante`.
- Exportação dos dados para o formato Parquet.

**Resultado:** 8.785 linhas e 17 colunas após a transformação. Nenhuma linha duplicada foi encontrada.

### Municípios do IBGE

O arquivo original em JSON foi processado para gerar um arquivo Parquet na camada Prata.

As transformações realizadas foram:

- Remoção de espaços desnecessários.
- Verificação de chaves identificadoras repetidas.
- Organização dos campos aninhados do JSON em colunas.
- Exportação dos dados para o formato Parquet.

**Resultado:** 5.571 linhas e 4 colunas após a transformação. Nenhuma chave identificadora repetida foi encontrada.

Os dados originais são preservados na camada Bronze, enquanto os dados transformados são armazenados na camada Prata.

## Atributos derivados

### Brasileirão

O atributo `pontos_mandante` foi criado a partir dos placares das partidas:

- **3 pontos:** vitória do mandante.
- **1 ponto:** empate.
- **0 pontos:** derrota do mandante.

Esse atributo facilita a análise do desempenho dos times como mandantes, permitindo comparar os resultados por estado.

## Tecnologias utilizadas

- Python
- Pandas
- PyArrow
- Requests
- JSON e CSV
- Parquet
- Git e GitHub

## Defeitos conhecidos das fontes

### Brasileirão

- As colunas `mandante` e `mandante_Estado` apresentam associação entre o nome do time e seu estado.
- As colunas `visitante` e `visitante_Estado` apresentam associação entre o nome do time e seu estado.
- A coluna `vencedor` contém informações relacionadas ao resultado da partida e deve ser interpretada em conjunto com os placares.
- A coluna `formacao_mandante` possui 4.975 valores ausentes (56,6%).
- A coluna `formacao_visitante` possui 4.975 valores ausentes (56,6%).
- A coluna `tecnico_mandante` possui 4.610 valores ausentes (52,5%).
- A coluna `tecnico_visitante` possui 4.610 valores ausentes (52,5%).
- A coluna `ID` apresenta valores únicos nos registros analisados.
- A coluna `mandante_Placar` possui 1.817 valores iguais a zero (20,7%).
- A coluna `visitante_Placar` possui 3.185 valores iguais a zero (36,3%). Os zeros podem representar equipes que não marcaram gols e não devem ser considerados erros automaticamente.

### Municípios do IBGE

- A coluna `microrregiao` possui 1 valor ausente.
- As colunas `microrregiao` e `regiao-imediata` contêm estruturas que precisam ser verificadas durante a transformação.
- A coluna `id` apresenta valores únicos nos 5.571 registros.
- Não foram encontradas chaves identificadoras repetidas.

## Próximas etapas

- Validar os dados transformados na camada Prata.
- Analisar a distribuição dos pontos conquistados pelos mandantes por estado.
- Utilizar os resultados para investigar a relação entre o estado dos times e seu desempenho como mandantes no Campeonato Brasileiro.