import typing as tp


if tp.TYPE_CHECKING:
    from soulstruct.darksouls1ptde.maps.msb import MSB as PTDE_MSB
    from soulstruct.darksouls1r.maps.msb import MSB as DS1R_MSB
    from soulstruct.bloodborne.maps.msb import MSB as BB_MSB
    from soulstruct.eldenring.maps.msb import MSB as ER_MSB
    MSB_TYPING = tp.Union[PTDE_MSB, DS1R_MSB, BB_MSB, ER_MSB]

    from soulstruct.darksouls1ptde.models import CHRBND as PTDE_CHRBND, OBJBND as PTDE_OBJBND, PARTSBND as PTDE_PARTSBND
    from soulstruct.darksouls1r.models import CHRBND as DS1R_CHRBND, OBJBND as DS1R_OBJBND, PARTSBND as DS1R_PARTSBND
    from soulstruct.bloodborne.models import CHRBND as BB_CHRBND, OBJBND as BB_OBJBND, PARTSBND as BB_PARTSBND
    CHRBND_TYPING = tp.Union[PTDE_CHRBND, DS1R_CHRBND, BB_CHRBND]
    OBJBND_TYPING = tp.Union[PTDE_OBJBND, DS1R_OBJBND, BB_OBJBND]
    PARTSBND_TYPING = tp.Union[PTDE_PARTSBND, DS1R_PARTSBND, BB_PARTSBND]

    from soulstruct.darksouls1ptde.models.mtd import MTDBND as PTDE_MTDBND
    from soulstruct.darksouls1r.models.mtd import MTDBND as DS1R_MTDBND
    MTDBND_TYPING = tp.Union[PTDE_MTDBND, DS1R_MTDBND]

    from soulstruct.eldenring.models.matbin import MATBINBND as ER_MATBINBND
    MATBINBND_TYPING = tp.Union[ER_MATBINBND]
