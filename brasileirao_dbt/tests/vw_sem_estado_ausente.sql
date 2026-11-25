-- Passa quando devolve ZERO linhas.
-- Todo jogo da view precisa ter estado e regiao do mandante.
select partida_id, time_mandante_id
from {{ ref('vw_desempenho_mandante') }}
where uf_id is null or estado is null or regiao is null
