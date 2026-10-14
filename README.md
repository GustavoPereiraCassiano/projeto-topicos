# Projeto de Engenharia de Dados

## Objetivo

Realizar a ingestão de dados de diferentes fontes para a camada Bronze, preservando os dados originais, e transformar os dados para a camada Prata, realizando verificações de qualidade e registrando a proveniência das operações.

## Fontes de dados

| Fonte | Tipo | Dados |
|---|---|---|
| Brasileirão Dataset | CSV / GitHub | Dados dos jogos do Campeonato Brasileiro |
| API de Localidades do IBGE | JSON / API REST | Informações sobre os municípios brasileiros |

## Estrutura do projeto

- `src/`: códigos de ingestão, exploração e transformação dos dados.
- `dados/bronze/brasileirao/`: dados originais do Brasileirão.
- `dados/bronze/ibge/`: dados originais dos municípios do IBGE.
- `dados/prata/brasileirao/`: dados transformados do Brasileirão em formato Parquet.
- `dados/prata/ibge/`: dados transformados dos municípios do IBGE em formato Parquet.
- `proveniencia.jsonl`: registros de proveniência das operações, conforme a organização utilizada no projeto.

## Proveniência

Cada ingestão gera um arquivo com data e hora, preservando o histórico dos dados extraídos.

Os registros de proveniência documentam informações como:

- Fonte dos dados.
- Nome do arquivo de origem.
- Nome do arquivo gerado.
- Quantidade de registros antes e depois da transformação.
- Decisões tomadas durante o processamento.
- Data e hora da operação.

Esses registros permitem acompanhar a origem dos dados e as transformações realizadas.

## Transformações dos dados

### Brasileirão

O arquivo original em CSV foi processado para gerar um arquivo Parquet na camada Prata.

As transformações realizadas foram:

- Remoção de espaços desnecessários.
- Verificação e remoção de linhas duplicadas.
- Conversão das colunas de placar para valores numéricos.
- Exportação dos dados para o formato Parquet.

**Resultado:** 8.785 linhas antes e depois da transformação. Nenhuma linha duplicada foi encontrada.

### Municípios do IBGE

O arquivo original em JSON foi processado para gerar um arquivo Parquet na camada Prata.

As transformações realizadas foram:

- Remoção de espaços desnecessários.
- Verificação da chave identificadora dos municípios.
- Organização dos campos aninhados do JSON em colunas.
- Exportação dos dados para o formato Parquet.

**Resultado:** 5.571 linhas antes e depois da transformação.

Os dados originais são preservados na camada Bronze, enquanto os dados transformados são armazenados na camada Prata.

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

- As colunas `mandante` e `mandante_Estado` apresentam alta correlação.
- As colunas `visitante` e `visitante_Estado` apresentam alta correlação.
- A coluna `vencedor` apresenta alta correlação com outras colunas.
- A coluna `formacao_mandante` possui 4.975 valores ausentes (56,6%).
- A coluna `formacao_visitante` possui 4.975 valores ausentes (56,6%).
- A coluna `tecnico_mandante` possui 4.610 valores ausentes (52,5%).
- A coluna `tecnico_visitante` possui 4.610 valores ausentes (52,5%).
- A coluna `ID` apresenta valores únicos e distribuição uniforme, sem indicação de problema por esses alertas.
- A coluna `mandante_Placar` possui 1.817 valores iguais a zero (20,7%).
- A coluna `visitante_Placar` possui 3.185 valores iguais a zero (36,3%). Os zeros precisam ser interpretados no contexto das partidas, pois podem representar equipes que não marcaram gols.

### Municípios do IBGE

- As colunas `microrregiao` e `regiao-imediata` foram identificadas como tipos não suportados pela ferramenta de perfilamento e precisam de investigação.
- A coluna `id` possui valores únicos em todos os 5.571 registros, sem indicação de problema por esse alerta.
- O relatório identificou 1 valor ausente no conjunto de dados, mas o resumo consultado não permitiu confirmar em qual coluna ele está.
- Não foram encontradas linhas duplicadas.