-- Passa quando devolve ZERO linhas.
-- A view achatada precisa ter uma linha por partida: se uma juncao
-- duplicasse ou perdesse linhas, a contagem mudaria.
select
    (select count(*) from {{ ref('vw_desempenho_mandante') }}) as na_view,
    (select count(*) from {{ ref('fato_partida') }}) as na_fato
where (select count(*) from {{ ref('vw_desempenho_mandante') }})
   <> (select count(*) from {{ ref('fato_partida') }})
