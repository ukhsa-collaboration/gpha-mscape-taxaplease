import pytest
from taxaplease import TaxaPlease


def test_root_returns_itself_as_parent():
    taxaPlease = TaxaPlease()
    assert taxaPlease.get_parent_taxid(1) == 1


def test_root_record_as_expected():
    taxaPlease = TaxaPlease()
    assert taxaPlease.get_record(1) == {
        "taxid": 1,
        "name": "root",
        "rank": "no rank",
        "parent_taxid": 1,
    }


def test_taxid_2000_is_streptosporangium():
    taxaPlease = TaxaPlease()
    assert taxaPlease.get_record(2000).get("name") == "Streptosporangium"


def test_parent_taxa():
    taxaPlease = TaxaPlease()
    assert taxaPlease.get_parent_taxid(2004) == 85012


def test_get_genus_taxid():
    taxaPlease = TaxaPlease()
    assert taxaPlease.get_genus_taxid(562) == 561


def test_common_parent_record_distant_taxa():
    taxaPlease = TaxaPlease()
    taxid_canis_lupus = 9612
    taxid_aloe_vera = 34199
    assert (
        taxaPlease.get_common_parent_record(taxid_canis_lupus, taxid_aloe_vera).get(
            "name"
        )
        == "Eukaryota"
    )


def test_common_parent_record_close_taxa():
    taxaPlease = TaxaPlease()
    ## E. coli and a random Shigella are both Enterobacteriaceae
    taxid_e_coli = 562
    taxid_s_flexneri = 623

    assert (
        taxaPlease.get_common_parent_record(taxid_e_coli, taxid_s_flexneri).get("name")
        == "Enterobacteriaceae"
    )


def test_levels_between_close_taxa():
    taxaPlease = TaxaPlease()

    ## levels between close taxa
    taxid_e_coli = 562
    taxid_s_flexneri = 623

    assert taxaPlease.get_number_of_levels_between_taxa(
        taxid_e_coli, taxid_s_flexneri
    ) == {
        "left_levels_to_common_parent": 2,
        "right_levels_to_common_parent": 2,
        "total_levels_between_taxa": 4,
    }


def test_levels_between_distant_taxa():
    taxaPlease = TaxaPlease()

    ## levels between distant taxa
    taxid_e_coli = 562
    taxid_canis_lupus = 9612

    assert taxaPlease.get_number_of_levels_between_taxa(
        taxid_e_coli, taxid_canis_lupus
    ) == {
        "left_levels_to_common_parent": 26,
        "right_levels_to_common_parent": 8,
        "total_levels_between_taxa": 34,
    }


def test_is_virus_fail():
    taxaPlease = TaxaPlease()

    ## is aloe vera a virus? (no)
    taxid_aloe_vera = 34199

    assert not taxaPlease.isVirus(taxid_aloe_vera)


def test_is_eukaryote_pass():
    taxaPlease = TaxaPlease()

    taxid_aloe_vera = 34199

    assert taxaPlease.isEukaryote(taxid_aloe_vera)


def test_is_archaea_fail():
    taxaPlease = TaxaPlease()

    ## Shigella is not Archaea
    taxid_s_flexneri = 623

    assert not taxaPlease.isArchaea(taxid_s_flexneri)


def test_is_archaea_pass():
    taxaPlease = TaxaPlease()

    ## Methanobrevibacter smithii is Archaea
    taxid_random_archaea = 2173

    assert taxaPlease.isArchaea(taxid_random_archaea)


def test_current_taxid():
    taxaPlease = TaxaPlease()

    taxid_bacteria = 2

    assert taxaPlease.checkTaxidStatus(taxid_bacteria) == {
        "isCurrent": True,
        "isDeleted": False,
        "isMerged": False,
    }


def test_deleted_taxid():
    taxaPlease = TaxaPlease()

    deletedTaxid = 3467805

    assert taxaPlease.checkTaxidStatus(deletedTaxid) == {
        "isCurrent": False,
        "isDeleted": True,
        "isMerged": False,
    }


def test_merged_taxid():
    taxaPlease = TaxaPlease()

    photobacteriumProfundumOld = 12
    photobacteriumProfundumNew = 74109

    assert taxaPlease.checkTaxidStatus(photobacteriumProfundumOld) == {
        "isCurrent": False,
        "isDeleted": False,
        "isMerged": photobacteriumProfundumNew,
    }

def test_phages():
    taxaPlease = TaxaPlease()

    topLevelPhage = 2731619 ## Caudoviricetes
    subLevelPhage = 2560487 ## Bowservirus bowser

    assert taxaPlease.isPhage(topLevelPhage)
    assert taxaPlease.isPhage(subLevelPhage)