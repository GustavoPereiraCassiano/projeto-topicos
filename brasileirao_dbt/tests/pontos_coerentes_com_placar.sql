-- Passa quando devolve ZERO linhas.
-- Os pontos do mandante precisam bater com o placar: 3 se ganhou,
-- 1 se empatou, 0 se perdeu.
select partida_id, gols_mandante, gols_visitante, pontos_mandante
from {{ ref('fato_partida') }}
where pontos_mandante <> case
        when gols_mandante > gols_visitante then 3
        when gols_mandante = gols_visitante then 1
        else 0
    end
