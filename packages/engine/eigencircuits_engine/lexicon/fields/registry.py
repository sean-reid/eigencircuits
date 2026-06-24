"""Registry of available subfields with selection weights.

The weighted draw in ``theme`` uses the ``weight`` carried by each lexicon.
"""

from __future__ import annotations

from ..schema import SubfieldLexicon
from .ac import AC
from .ag import AG
from .ap import AP
from .at import AT
from .ca import CA
from .co import CO
from .ct import CT
from .cv import CV
from .dg import DG
from .ds import DS
from .fa import FA
from .gm import GM
from .gn import GN
from .gr import GR
from .gt import GT
from .ho import HO
from .it import IT
from .kt import KT
from .lo import LO
from .mg import MG
from .mp import MP
from .na import NA
from .nt import NT
from .oa import OA
from .oc import OC
from .pr import PR
from .qa import QA
from .ra import RA
from .rt import RT
from .sg import SG
from .sp import SP
from .st import ST

FIELDS: tuple[SubfieldLexicon, ...] = (
    NT,
    AG,
    CO,
    DG,
    PR,
    AP,
    RT,
    FA,
    DS,
    CA,
    GT,
    AT,
    GR,
    MP,
    OA,
    QA,
    SG,
    AC,
    KT,
    CT,
    LO,
    MG,
    SP,
    NA,
    OC,
    ST,
    CV,
    RA,
    IT,
    GN,
    HO,
    GM,
)

BY_CODE: dict[str, SubfieldLexicon] = {f.code: f for f in FIELDS}


def weighted_fields() -> list[tuple[float, SubfieldLexicon]]:
    return [(f.weight, f) for f in FIELDS]
