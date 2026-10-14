# Projeto de Engenharia de Dados

## Objetivo

Realizar a ingestão de dados de diferentes fontes para a camada Bronze, preservando os dados originais e registrando sua proveniência.

## Fontes de dados

| Fonte | Tipo | Dados |
|---|---|---|
| Brasileirão Dataset | CSV / GitHub | Dados dos jogos do Campeonato Brasileiro |
| API de Localidades do IBGE | JSON / API REST | Informações sobre os municípios brasileiros |

## Estrutura do projeto

- `src/`: códigos de ingestão.
- `dados/bronze/brasileirao/`: dados do Brasileirão.
- `dados/bronze/ibge/`: dados dos municípios do IBGE.

## Proveniência

Cada ingestão gera um arquivo com data e hora, e as informações sobre a extração são acrescentadas ao arquivo `proveniencia.jsonl`.

## Tecnologias utilizadas

- Python
- Requests
- Git e GitHub