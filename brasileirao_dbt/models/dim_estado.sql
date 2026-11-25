-- Uma linha por estado (UF). Vem do IBGE, via prata.estados.
select
    "UF"   as uf_id,
    estado as nome,
    regiao
from {{ source('prata', 'estados') }}
