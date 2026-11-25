-- Uma linha por partida. O ano e o ano civil da data do jogo: a
-- temporada de 2020 terminou em 2021, e os jogos dela ficam em 2021.
select
    "ID"                                      as partida_id,
    strptime(data, '%d/%m/%Y')::date          as data_jogo,
    year(strptime(data, '%d/%m/%Y'))          as ano,
    rodata                                    as rodada,
    mandante                                  as time_mandante_id,
    visitante                                 as time_visitante_id,
    arena,
    "mandante_Placar"                         as gols_mandante,
    "visitante_Placar"                        as gols_visitante,
    pontos_mandante,
    case pontos_mandante
        when 3 then 'V'
        when 1 then 'E'
        else 'D'
    end                                       as resultado
from {{ source('prata', 'brasileirao_enriquecido') }}
