-- Passa quando devolve ZERO linhas.
-- A fato precisa ter exatamente as partidas da Prata: nem uma a mais,
-- nem uma a menos.
select
    (select count(*) from {{ ref('fato_partida') }}) as na_ouro,
    (select count(*) from {{ source('prata', 'brasileirao_enriquecido') }}) as na_prata
where (select count(*) from {{ ref('fato_partida') }})
   <> (select count(*) from {{ source('prata', 'brasileirao_enriquecido') }})
