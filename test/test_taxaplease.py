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
        taxaPlease.get_common_parent_record(taxid_canis_lupus, taxid_aloe_vera).get("name")
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

    assert taxaPlease.get_number_of_levels_between_taxa(taxid_e_coli, taxid_s_flexneri) == {
        "left_levels_to_common_parent": 2,
        "right_levels_to_common_parent": 2,
        "total_levels_between_taxa": 4,
    }


def test_levels_between_distant_taxa():
    taxaPlease = TaxaPlease()

    ## levels between distant taxa
    taxid_e_coli = 562
    taxid_canis_lupus = 9612

    assert taxaPlease.get_number_of_levels_between_taxa(taxid_e_coli, taxid_canis_lupus) == {
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

    deletedTaxid = 3

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

    topLevelPhage = 2731619  ## Caudoviricetes
    subLevelPhage = 2560487  ## Bowservirus bowser

    assert taxaPlease.isPhage(topLevelPhage)
    assert taxaPlease.isPhage(subLevelPhage)


def test_get_child_taxids():
    taxaPlease = TaxaPlease()

    taxid_lassa = 3052310  ## Mammarenavirus lassaense
    taxid_lassa_ga391 = 11621  ## Lassa virus GA391
    taxid_lassa_josiah = 11622  ## Lassa virus Josiah

    assert set(taxaPlease.get_child_taxids(taxid_lassa)) == {
        taxid_lassa_ga391,
        taxid_lassa_josiah,
    }


def test_get_all_child_taxids():
    taxaPlease = TaxaPlease()

    taxid_mammarenavirus = 1653394  ## Mammarenavirus

    ## all descendants of Mammarenavirus obtained from
    ## https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=taxonomy&term=txid1653394[Subtree]&retmax=100000

    taxids_mammarenavirus_descendants = {
        144752,
        2022411,
        2022412,
        2201416,
        2479483,
        2838264,
        2877494,
        2877495,
        2877496,
        2877497,
        2877498,
        2877499,
        2929006,
        2934317,
        3014462,
        3385012,
        3386165,
        3386197,
        3396567,
        3411295,
        3467812,
        2169991,
        2734414,
        2847047,
        2956183,
        3070199,
        2956184,
        3070923,
        3052296,
        2886894,
        3052297,
        2850049,
        3052298,
        3052299,
        2907957,
        3052300,
        2905917,
        3052301,
        2010246,
        3052302,
        3052303,
        11624,
        11625,
        11626,
        11627,
        483046,
        3052304,
        3052305,
        3052306,
        3052307,
        3052308,
        3052309,
        2847814,
        3052310,
        11621,
        11622,
        3052311,
        3052312,
        2201415,
        3052313,
        3052314,
        3052315,
        3052316,
        1134579,
        3052317,
        3052318,
        3052319,
        3052320,
        300175,
        573900,
        3052321,
        3052322,
        3052323,
        2905947,
        3052324,
        3052325,
        3052326,
        3052327,
        1518603,
        3052328,
        31614,
        31615,
        31616,
        928313,
        1095757,
        1163668,
        3052329,
        3052330,
        1587502,
        1587503,
        2079549,
        3052331,
        404768,
        466143,
        466144,
        481886,
        481887,
        523743,
        568065,
        3052332,
        2267561,
        3060184,
        3070833,
        3416945,
        3416946,
        3430643,
        2800209,
        3430644,
        3030865,
        3430645,
        3028231,
        3430646,
        913012,
        3430647,
        3036599,
        3430648,
        3030863,
        3430649,
        3030864,
        3430650,
        2994979,
        3430651,
    }

    assert (
        set(taxaPlease.get_all_child_taxids(taxid_mammarenavirus))
        == taxids_mammarenavirus_descendants
    )
