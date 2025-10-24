import os
import requests
import sqlite3
import tempfile
import functools
import networkx as nx
import taxaplease_data as tpData
from typing import Optional
from pathlib import Path
from bs4 import BeautifulSoup as bs
from urllib.parse import urljoin


__version__ = "1.1.0"


class TaxaPlease:
    """
    Class for wrangling NCBI taxids
    """

    def __init__(self):
        self.con = self._init_database_connection()
        self.column_names = self._init_column_names()
        self.phages = tpData.PHAGES
        self.baltimore = tpData.BALTIMORE_CLASSIFICATION
        self.viral_realms = tpData.VIRAL_REALMS

    def _init_database_connection(self):
        db_dir = os.path.join(Path.home(), ".taxaplease")
        db_path = os.path.join(db_dir, "taxa.db")

        ## if the folder doesn't exist, create it
        if not os.path.isdir(db_dir):
            os.mkdir(db_dir)

        ## if the database doesn't exist, create it
        if not os.path.isfile(db_path):
            self._create_database()

        return sqlite3.connect(db_path)

    def _create_database(self, taxonomy_url=None):
        import database_generation.generate_database as gd

        with tempfile.TemporaryDirectory() as tempdir:
            if taxonomy_url:
                ## if specified, use that
                gd.main(tempdir, taxonomy_url)
            else:
                ## else use the latest
                gd.main(tempdir)

    def _init_column_names(self) -> list:
        """
        Creates a cursor, sends a query to the database that
        returns 0 rows, and apparently that's enough to get the
        column names
        """
        cur = self.con.cursor()
        cur.execute("SELECT * FROM taxa LIMIT 0")
        return list(map(lambda x: x[0], cur.description))

    def set_taxonomy_url(self, url: str):
        self._create_database(url)

        return None

    @staticmethod
    def __process_file_listing(file_listing, url):
        """
        Helper function only used by get_taxonomy_url

        Parameters
        ----------
        file_listing: list
            A list of <a> tags from a beautifulsoup findall query
        url: str
            A URL to be added to the front of the filename in the file listing

        Returns
        -------
        List
            A list of absolute URLs
        """
        relative_url_list = list(
            filter(
                lambda x: x.endswith(".zip") or x.endswith(".tar.gz"),
                map(lambda x: x.get("href"), file_listing),
            )
        )

        absolute_url_list = [
            urljoin(url, os.path.basename(x)) for x in relative_url_list
        ]

        return absolute_url_list

    def get_taxonomy_url(self) -> dict:
        """
        Gets a dictionary of valid taxonomy database URLs.

        Keys: latest, archive
        Values: list of fully qualified URLs for each database file
        """
        taxdump_archive_page = "https://ftp.ncbi.nih.gov/pub/taxonomy/taxdump_archive/"
        taxdump_latest_page = "https://ftp.ncbi.nih.gov/pub/taxonomy/new_taxdump/"

        td_archive = bs(requests.get(taxdump_archive_page).text, features="html.parser")
        td_latest = bs(requests.get(taxdump_latest_page).text, features="html.parser")

        file_listing_archive = self.__process_file_listing(
            td_archive.find_all(name="a"), taxdump_archive_page
        )
        file_listing_latest = self.__process_file_listing(
            td_latest.find_all(name="a"), taxdump_latest_page
        )

        available_taxdump_files = {
            "latest": file_listing_latest,
            "archive": file_listing_archive,
        }

        return available_taxdump_files

    def get_parent_taxid(self, inputTaxid: int | str) -> Optional[int]:
        """
        Takes in an NCBI taxid, returns the corresponding parent
        taxid if there is one, or None

        Parameters
        ----------
        inputTaxid : int or str
            NCBI taxid

        Returns
        -------
        Optional[int]
            Parent NCBI taxid or None
        """
        cur = self.con.cursor()
        res = cur.execute(
            "SELECT parent_taxid FROM taxa WHERE taxid = ?", [inputTaxid]
        ).fetchone()

        if res:
            return res[0]
        else:
            return None

    def get_record(self, inputTaxid: int | str) -> Optional[dict]:
        """
        Takes in an NCBI taxid, returns the corresponding record
        from the taxa database if there is one, or None

        Parameters
        ----------
        inputTaxid : int or str
            NCBI taxid

        Returns
        -------
        Optional[dict]
            taxa database record for inputTaxid
        """
        cur = self.con.cursor()
        res = cur.execute("SELECT * FROM taxa WHERE taxid = ?", [inputTaxid]).fetchone()

        if res:
            return dict(zip(self.column_names, res))
        else:
            return None

    def get_parent_record(self, inputTaxid: int | str) -> Optional[dict]:
        """
        Takes in an NCBI taxid, gets the parent taxid if there is one,
        then gets its corresponding record.

        Will return None if there is no corresponding taxid/record

        Parameters
        ----------
        inputTaxid : int or str
            NCBI taxid

        Returns
        -------
        Optional[dict]
            taxa database record for the parent of inputTaxid
        """
        parent_taxid = self.get_parent_taxid(inputTaxid)

        if not parent_taxid:
            return None

        cur = self.con.cursor()
        res = cur.execute(
            "SELECT * FROM taxa WHERE taxid = ?", [parent_taxid]
        ).fetchone()

        if res:
            return dict(zip(self.column_names, res))
        else:
            return None

    def get_genus_taxid(self, inputTaxid: int | str) -> Optional[int]:
        """
        Kinda naff function that only works if your inputTaxid is
        at or below genus level (naturally!).

        Takes in an NCBI taxid, traverses up the tree until we find
        something labelled genus, or hit a brick wall.

        Parameters
        ----------
        inputTaxid: int or str
            NCBI taxid

        Returns
        -------
        Optional[int]
            NCBI taxid corresponding to the genus
        """
        ## check we aren't already a genus
        rec = self.get_record(inputTaxid)

        if not rec:
            return None

        if rec["rank"] == "genus":
            return inputTaxid

        ## check we didn't get nothing
        if not rec["rank"]:
            return None

        if inputTaxid == 1:
            return None

        ## recursively get the parent until we find the genus
        ## or end up with nothing
        return self.get_genus_taxid(rec["parent_taxid"])

    @functools.cache
    def get_species_taxid(self, inputTaxid: int | str) -> Optional[int | str]:
        """
        Kinda naff function that only works if your inputTaxid is
        at or below species level - for example, if you have a strain
        level record.

        Takes in an NCBI taxid, traverses up the tree until we find
        something labelled species, or hit a brick wall.

        Yes this could be refactored because it shares a lot of code
        with the genus function. Let me prove it works first.

        Parameters
        ----------
        inputTaxid: int or str
            NCBI taxid

        Returns
        -------
        Optional[int]
            NCBI taxid corresponding to the species
        """
        ## check we aren't already a species
        rec = self.get_record(inputTaxid)

        if not rec:
            return None

        if rec["rank"] == "species":
            return inputTaxid

        ## check we didn't get nothing
        if not rec["rank"]:
            return None

        if inputTaxid == 1:
            return None

        ## recursively get the parent until we find the species
        ## or end up with nothing
        return self.get_species_taxid(rec["parent_taxid"])

    def get_superkingdom_taxid(self, inputTaxid: int | str) -> Optional[int]:
        """
        Takes in an NCBI taxid, traverses up the tree until we find
        something labelled superkingdom, or hit a brick wall.

        Parameters
        ----------
        inputTaxid: int or str
            NCBI taxid

        Returns
        -------
        Optional[int]
            NCBI taxid corresponding to the superkingdom
        """
        ## check we aren't already a superkingdom
        rec = self.get_record(inputTaxid)

        if rec["rank"] == "superkingdom":
            return inputTaxid

        ## check we didn't get nothing
        if not rec["rank"]:
            return None

        if inputTaxid == 1:
            return None

        ## recursively get the parent until we find the superkingdom
        ## or end up with nothing
        return self.get_superkingdom_taxid(rec["parent_taxid"])

    def get_all_parent_taxids(
        self, inputTaxid: int | str, *, includeSelf: bool = False
    ) -> tuple:
        """
        Takes in an NCBI taxid, gets all parent taxids in order of
        most specific to least specific.

        Can optionally include the input taxid in the result.

        Parameters
        ----------
        inputTaxid: int or str
            NCBI taxid
        includeSelf: bool (default: False)
            Include the input taxid in the result

        Returns
        -------
        tuple:
            tuple of parent taxids, from most to least specific
        """
        return_list = []

        if includeSelf:
            return_list.append(inputTaxid)

        tempTaxa = inputTaxid

        while tempTaxa != 1:
            tempTaxa = self.get_parent_taxid(tempTaxa)

            if not tempTaxa:
                break

            return_list.append(tempTaxa)

        return tuple(return_list)

    def get_common_parent_taxid(
        self, inputTaxidLeft: int | str, inputTaxidRight: int | str
    ) -> Optional[int | str]:
        """
        Takes two NCBI taxids as input, traverses up the taxonomic
        tree to find the first parent taxid that both share.

        Parameters
        ----------
        inputTaxidLeft: int or str
            NCBI taxid
        inputTaxidRight: int or str
            NCBI taxid

        Returns
        -------
        Optional[int]:
            Taxid of shared parent, or None
        """
        left_parents = set(self.get_all_parent_taxids(inputTaxidLeft, includeSelf=True))

        if (inputTaxidLeft != 1) and (len(left_parents) <= 1):
            return None

        tempRightId = inputTaxidRight

        while tempRightId not in left_parents:
            tempRightId = self.get_parent_taxid(tempRightId)
            if not tempRightId:
                return None

        return tempRightId

    def get_common_parent_record(
        self, inputTaxidLeft: int | str, inputTaxidRight: int | str
    ) -> Optional[dict]:
        """
        Takes two NCBI taxids as input, traverses up the taxonomic
        tree to find the first parent taxid record that both share.

        Parameters
        ----------
        inputTaxidLeft: int or str
            NCBI taxid
        inputTaxidRight: int or str
            NCBI taxid

        Returns
        -------
        Optional[dict]:
            Record for shared parent, or None
        """
        result = self.get_common_parent_taxid(inputTaxidLeft, inputTaxidRight)

        if result:
            return self.get_record(result)
        else:
            return None

    def get_number_of_levels_between_taxa(
        self, inputTaxidLeft: int | str, inputTaxidRight: int | str
    ) -> Optional[dict]:
        """
        Takes two NCBI taxids as input, finds the common parent taxa
        and gets the number of levels from each input taxid to that
        parent taxa.

        Parameters
        ----------
        inputTaxidLeft: int or str
            NCBI taxid
        inputTaxidRight: int or str
            NCBI taxid

        Returns
        -------
        Optional[dict]:
            Dictionary with the following keys:
            - left_levels_to_common_parent
            - right_levels_to_common_parent
            - total_levels_between_taxa
        """
        ## do it one way
        left_parents = set(self.get_all_parent_taxids(inputTaxidLeft, includeSelf=True))

        tempRightId = inputTaxidRight
        left_levels = 0

        while tempRightId not in left_parents:
            tempRightId = self.get_parent_taxid(tempRightId)
            left_levels += 1
            if not tempRightId:
                return None

        ## do it the other way
        right_parents = set(
            self.get_all_parent_taxids(inputTaxidRight, includeSelf=True)
        )

        tempLeftId = inputTaxidLeft
        right_levels = 0

        while tempLeftId not in right_parents:
            tempLeftId = self.get_parent_taxid(tempLeftId)
            right_levels += 1
            if not tempLeftId:
                return None

        result_dict = {
            "left_levels_to_common_parent": left_levels,
            "right_levels_to_common_parent": right_levels,
            "total_levels_between_taxa": left_levels + right_levels,
        }

        return result_dict

    def isArchaea(self, inputTaxid: int | str) -> bool:
        """
        Is the input taxid in the Archaea superkingdom?

        Parameters
        ----------
        inputTaxidLeft: int or str
            NCBI taxid

        Returns
        -------
        bool:
            True it is or False it isn't
        """
        targetTaxid = 2157
        return targetTaxid in self.get_all_parent_taxids(inputTaxid, includeSelf=True)

    def isBacteria(self, inputTaxid: int | str) -> bool:
        """
        Is the input taxid in the Bacteria superkingdom?

        Parameters
        ----------
        inputTaxidLeft: int or str
            NCBI taxid

        Returns
        -------
        bool:
            True it is or False it isn't
        """
        targetTaxid = 2
        return targetTaxid in self.get_all_parent_taxids(inputTaxid, includeSelf=True)

    def isEukaryote(self, inputTaxid: int | str) -> bool:
        """
        Is the input taxid in the Eukaryota superkingdom?

        Parameters
        ----------
        inputTaxidLeft: int or str
            NCBI taxid

        Returns
        -------
        bool:
            True it is or False it isn't
        """
        targetTaxid = 2759
        return targetTaxid in self.get_all_parent_taxids(inputTaxid, includeSelf=True)

    def isVirus(self, inputTaxid: int | str) -> bool:
        """
        Is the input taxid in the Viruses superkingdom?

        Parameters
        ----------
        inputTaxidLeft: int or str
            NCBI taxid

        Returns
        -------
        bool:
            True it is or False it isn't
        """
        targetTaxid = 10239

        ## check the parents
        return targetTaxid in self.get_all_parent_taxids(inputTaxid, includeSelf=True)

    def isPhage(self, inputTaxid: int | str) -> bool:
        """
        Is the input taxid a phage?

        Parameters
        ----------
        inputTaxidLeft: int or str
            NCBI taxid

        Returns
        -------
        bool:
            True it is or False it isn't
        """
        ## check the parents
        parents = set(self.get_all_parent_taxids(inputTaxid, includeSelf=True))
        ## get all the phage taxids
        phages = set(list(self.phages.keys()))
        ## check if the sets have any items in common
        intersection = phages.intersection(parents)

        return bool(len(intersection))

    def __checkIfTaxidDeleted(self, inputTaxid: int | str) -> bool:
        """
        Check if a taxid is in the deleted_taxa table

        Parameters
        ----------
        inputTaxidLeft: int or str
            NCBI taxid

        Returns
        -------
        bool:
            True if in the deleted table, else False
        """
        cur = self.con.cursor()
        res = cur.execute(
            "SELECT * FROM deleted_taxa WHERE taxid = ?", [inputTaxid]
        ).fetchone()

        return bool(res)

    def __checkIfTaxidMerged(self, inputTaxid: int | str) -> bool:
        """
        Check if a taxid is in the merged table

        Parameters
        ----------
        inputTaxidLeft: int or str
            NCBI taxid

        Returns
        -------
        bool:
            If in the table, return the new taxid, else return False
        """
        cur = self.con.cursor()
        res = cur.execute(
            "SELECT new_taxid FROM merged_taxa WHERE old_taxid = ?", [inputTaxid]
        ).fetchone()

        if res:
            return res[0]
        else:
            return False

    def checkTaxidStatus(self, inputTaxid: int | str) -> dict:
        """
        Is the input taxid valid?

        Parameters
        ----------
        inputTaxidLeft: int or str
            NCBI taxid

        Returns
        -------
        dict:
            dictionary with status of id
        """
        return_dict = {}

        return_dict["isCurrent"] = bool(self.get_record(inputTaxid))
        return_dict["isDeleted"] = self.__checkIfTaxidDeleted(inputTaxid)
        return_dict["isMerged"] = self.__checkIfTaxidMerged(inputTaxid)

        return return_dict

    def generate_taxonomy_graph(self, *args) -> nx.DiGraph:
        """
        Takes in taxids as positional arguments, gets all the parents
        and returns a networkx directed graph of the result.

        Parameters
        ----------
        *args

        Returns
        -------
        networkx.DiGraph:
            networkx directed graph object
        """
        assert len(args)

        ## instantiate a directed graph object
        graph = nx.DiGraph()

        for inputTaxid in args:
            ## get all the parents of taxid1, include self, reverse list
            parents = [
                self.get_record(inputTaxid),
                *[self.get_record(x) for x in self.get_all_parent_taxids(inputTaxid)],
            ][::-1]
            ## add edges to graph
            for rec, next_rec in zip(parents, parents[1:]):
                graph.add_node(rec["name"])
                graph.add_edge(rec["name"], next_rec["name"])

        ## return graph object
        return graph

    def print_taxonomy_graph(self, *args) -> str:
        """
        Takes in taxids as arguments, gets all the parents,
        generates a networkx directed graph of the result and
        prints an ASCII representation.

        Returns an empty string

        Parameters
        ----------
        *args int or str
            NCBI taxid

        Returns
        -------
        int
            -1
        """
        taxgraph = self.generate_taxonomy_graph(*args)

        ## write_network_text just writes straight
        ## to the terminal. Not sure how you get
        ## just a string as output. generate_network_text
        ## seems to return a generator, which doesn't help.
        nx.write_network_text(taxgraph)

        ## suppress "None" being printed
        ## by returning -1, which we will
        ## detect in the CLI
        return -1
    
    def get_baltimore_classification(self, inputTaxid: int | str) -> Optional[str]:
        """
        Takes in a taxid

        Returns Baltimore classification if applicable, or None
        if either the taxid either not a Virus, or not in the
        lookup dictionary.

        Technically the Baltimore classification should be a
        Group number from I to VII, but I choose to return the
        corresponding type of nucleic acid and sense instead.

        Parameters
        ----------
        inputTaxid int or str
            NCBI taxid

        Returns
        -------
        Optional[str]
            Baltimore classification as a string (for example, -ssRNA)
            or None
        """
        if not self.isVirus(inputTaxid):
            return None
        
        parents = set(self.get_all_parent_taxids(inputTaxid, includeSelf=True))
        baltimore_keys = set(self.baltimore)

        intersection = parents.intersection(baltimore_keys)

        if len(intersection):
            ## get the key, and use that to get the value
            return self.baltimore[list(intersection)[0]]
        else:
            ## got nothing
            return None
