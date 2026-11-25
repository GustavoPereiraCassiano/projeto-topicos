-- Passa quando devolve ZERO linhas.
-- Um time nao joga contra si mesmo.
select partida_id, time_mandante_id
from {{ ref('fato_partida') }}
where time_mandante_id = time_visitante_id
