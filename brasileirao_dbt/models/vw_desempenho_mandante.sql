-- A tabela achatada, para quem vai consultar: cada partida com o time
-- mandante, o estado e a regiao dele. E uma view, entao o banco refaz
-- a juncao a cada consulta e nao ha tabela derivada para manter.
-- left join: se algo nao casar, a linha aparece com valor ausente.
{{ config(materialized='view') }}

select
    f.partida_id,
    f.data_jogo,
    f.ano,
    f.rodada,
    f.time_mandante_id,
    f.time_visitante_id,
    f.gols_mandante,
    f.gols_visitante,
    f.pontos_mandante,
    f.resultado,
    t.uf_id,
    e.nome   as estado,
    e.regiao
from {{ ref('fato_partida') }} f
left join {{ ref('dim_time') }}   t on f.time_mandante_id = t.time_id
left join {{ ref('dim_estado') }} e on t.uf_id = e.uf_id
