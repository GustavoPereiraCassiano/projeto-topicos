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