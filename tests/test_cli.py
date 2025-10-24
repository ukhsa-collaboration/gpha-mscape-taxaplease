import json
import pytest
import subprocess


def test_root_returns_itself_as_parent():
    result = subprocess.run(
        ["taxaplease", "taxid", "--parent", "1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.stdout.strip() == b"1"


def test_root_record_as_expected():
    result = subprocess.run(
        ["taxaplease", "record", "--record", "1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert json.loads(result.stdout.decode("utf-8")) == {
        "taxid": 1,
        "name": "root",
        "rank": "no rank",
        "parent_taxid": 1,
    }


def test_taxid_2000_is_streptosporangium():
    result = subprocess.run(
        ["taxaplease", "record", "--record", "2000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert json.loads(result.stdout.decode("utf-8")).get("name") == "Streptosporangium"


def test_parent_taxa():
    result = subprocess.run(
        ["taxaplease", "taxid", "--parent", "2004"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert json.loads(result.stdout.decode("utf-8")) == 85012


def test_get_genus_taxid():
    result = subprocess.run(
        ["taxaplease", "taxid", "--genus", "562"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert json.loads(result.stdout.decode("utf-8")) == 561


def test_common_parent_record_distant_taxa():
    taxid_canis_lupus = 9612
    taxid_aloe_vera = 34199

    result = subprocess.run(
        [
            "taxaplease",
            "record",
            "--common",
            str(taxid_canis_lupus),
            str(taxid_aloe_vera),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert json.loads(result.stdout.decode("utf-8")).get("name") == "Eukaryota"


def test_common_parent_record_close_taxa():
    ## E. coli and a random Shigella are both Enterobacteriaceae
    taxid_e_coli = 562
    taxid_s_flexneri = 623

    result = subprocess.run(
        ["taxaplease", "record", "--common", str(taxid_e_coli), str(taxid_s_flexneri)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert json.loads(result.stdout.decode("utf-8")).get("name") == "Enterobacteriaceae"


def test_levels_between_close_taxa():
    ## levels between close taxa
    taxid_e_coli = 562
    taxid_s_flexneri = 623

    result = subprocess.run(
        [
            "taxaplease",
            "check",
            "--levels-between",
            str(taxid_e_coli),
            str(taxid_s_flexneri),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert json.loads(result.stdout.decode("utf-8")) == {
        "left_levels_to_common_parent": 2,
        "right_levels_to_common_parent": 2,
        "total_levels_between_taxa": 4,
    }


def test_levels_between_distant_taxa():
    ## levels between distant taxa
    taxid_e_coli = 562
    taxid_canis_lupus = 9612

    result = subprocess.run(
        [
            "taxaplease",
            "check",
            "--levels-between",
            str(taxid_e_coli),
            str(taxid_canis_lupus),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert json.loads(result.stdout.decode("utf-8")) == {
        "left_levels_to_common_parent": 26,
        "right_levels_to_common_parent": 8,
        "total_levels_between_taxa": 34,
    }


def test_is_virus_fail():
    ## is aloe vera a virus? (no)
    taxid_aloe_vera = 34199

    result = subprocess.run(
        ["taxaplease", "check", "--is-virus", str(taxid_aloe_vera)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert not json.loads(result.stdout.decode("utf-8"))


def test_is_eukaryote_pass():
    taxid_aloe_vera = 34199

    result = subprocess.run(
        ["taxaplease", "check", "--is-eukaryote", str(taxid_aloe_vera)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert json.loads(result.stdout.decode("utf-8"))


def test_is_archaea_fail():
    ## Shigella is not Archaea
    taxid_s_flexneri = 623

    result = subprocess.run(
        ["taxaplease", "check", "--is-archaea", str(taxid_s_flexneri)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert not json.loads(result.stdout.decode("utf-8"))


def test_is_archaea_pass():
    ## Methanobrevibacter smithii is Archaea
    taxid_random_archaea = 2173

    result = subprocess.run(
        ["taxaplease", "check", "--is-archaea", str(taxid_random_archaea)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert json.loads(result.stdout.decode("utf-8"))


def test_current_taxid():
    taxid_bacteria = 2

    result = subprocess.run(
        ["taxaplease", "check", "--status", str(taxid_bacteria)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert json.loads(result.stdout.decode("utf-8")) == {
        "isCurrent": True,
        "isDeleted": False,
        "isMerged": False,
    }


def test_deleted_taxid():
    deletedTaxid = 3400745

    result = subprocess.run(
        ["taxaplease", "check", "--status", str(deletedTaxid)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert json.loads(result.stdout.decode("utf-8")) == {
        "isCurrent": False,
        "isDeleted": True,
        "isMerged": False,
    }


def test_merged_taxid():
    photobacteriumProfundumOld = 12
    photobacteriumProfundumNew = 74109

    result = subprocess.run(
        ["taxaplease", "check", "--status", str(photobacteriumProfundumOld)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert json.loads(result.stdout.decode("utf-8")) == {
        "isCurrent": False,
        "isDeleted": False,
        "isMerged": photobacteriumProfundumNew,
    }
