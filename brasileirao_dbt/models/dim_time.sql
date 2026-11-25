-- Uma linha por time. O estado de origem do time e o que a pergunta
-- norteadora investiga. Todo time aparece como mandante em algum jogo,
-- entao os mandantes distintos cobrem todos os times.
select distinct
    mandante        as time_id,
    "mandante_Estado" as uf_id
from {{ source('prata', 'brasileirao_enriquecido') }}
