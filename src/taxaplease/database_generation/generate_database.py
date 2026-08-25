#!/usr/bin/env python3
import os
import datetime
import shutil
import sqlite3
import tempfile
from pathlib import Path
from glob import glob

import pandas as pd  # type: ignore
import requests  # type: ignore

#####################
# Utility functions #
#####################


def download_file(url, *, destinationDir=None):
    """
    Nicked from https://stackoverflow.com/a/16696317
    It's a large file so we don't just load it all into memory

    A destination directory can optionally be specified
    If not specified, we use the current working directory
    """
    if not destinationDir:
        destinationDir = Path.cwd()

    local_filename = Path(destinationDir, url.split("/")[-1])

    ## NOTE the stream=True parameter below
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with Path.open(local_filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                # if chunk:
                f.write(chunk)

    return local_filename


def build_and_ingest_local(tempdir, *, ncbi_taxonomy_data_url=None, db_path=None):
    start_time = datetime.datetime.now()

    ## must be specified and must be a valid folder
    if not ncbi_taxonomy_data_url or not os.path.isdir(ncbi_taxonomy_data_url):
        raise Exception(f"Invalid local taxonomy folder: {ncbi_taxonomy_data_url}")

    #############################
    # Locate the files required #
    #############################

    local_nodes_dmp = os.path.join(ncbi_taxonomy_data_url, "nodes.dmp")
    local_names_dmp = os.path.join(ncbi_taxonomy_data_url, "names.dmp")

    if not os.path.isfile(local_nodes_dmp):
        print(f"{local_nodes_dmp} not found")
    if not os.path.isfile(local_names_dmp):
        print(f"{local_names_dmp} not found")
    if (not os.path.isfile(local_nodes_dmp)) or (not os.path.isfile(local_names_dmp)):
        raise Exception(
            f"Required taxonomy files not found in folder {ncbi_taxonomy_data_url}"
        )

    ##################################
    # Processing the downloaded data #
    ##################################

    ## get half the required info
    print(f"{datetime.datetime.now()} Processing nodes (file 1/2)")
    taxid_to_rank_df = pd.read_csv(
        local_nodes_dmp,
        sep="|",
        quotechar="\t",
        index_col=0,
        names=["taxid", "parent_taxid", "rank"],
        usecols=["taxid", "parent_taxid", "rank"],
    )

    ## get the other half
    print(f"{datetime.datetime.now()} Processing lineages (file 2/2)")
    taxid_to_name_df = pd.read_csv(
        local_names_dmp,
        sep="|",
        quotechar="\t",
        index_col=0,
        names=["taxid", "name", "_", "name_type", "__"],
        usecols=["taxid", "name", "name_type"],
    )
    ## filter to just scientific name entries
    taxid_to_name_df = taxid_to_name_df[
        taxid_to_name_df["name_type"] == "scientific name"
    ]
    taxid_to_name_df = taxid_to_name_df.drop("name_type", axis=1)

    ## join the halves together on taxid
    print(f"{datetime.datetime.now()} Joining nodes and lineages")
    concat_df = pd.concat([taxid_to_rank_df, taxid_to_name_df], axis=1)[
        ["name", "rank", "parent_taxid"]
    ]

    #########################
    # Optional extra tables #
    #########################

    local_delnodes_dmp = os.path.join(ncbi_taxonomy_data_url, "delnodes.dmp")
    local_merged_dmp = os.path.join(ncbi_taxonomy_data_url, "merged.dmp")
    do_ingest_delnodes = False
    do_ingest_merged = False

    if os.path.isfile(local_delnodes_dmp):
        ## prep the deleted ids table
        print(f"{datetime.datetime.now()} Processing deleted nodes")
        deleted_ids_df = pd.read_csv(
            local_delnodes_dmp,
            sep="|",
            index_col=0,
            quotechar="\t",
            names=["taxid", "_"],
        ).drop("_", axis=1)

        do_ingest_delnodes = True
    else:
        print(
            f"{datetime.datetime.now()} No delnodes.dmp file detected, skipping deleted_taxa table generation"
        )

    if os.path.isfile(local_merged_dmp):
        ## prep the merged ids table
        print(f"{datetime.datetime.now()} Processing merged nodes")
        merged_ids_df = pd.read_csv(
            local_merged_dmp,
            sep="|",
            index_col=0,
            quotechar="\t",
            names=["old_taxid", "new_taxid", "_"],
        ).drop("_", axis=1)

        do_ingest_merged = True
    else:
        print(
            f"{datetime.datetime.now()} No merged.dmp file detected, skipping merged_taxa table generation"
        )

    ###################
    # Database ingest #
    ###################

    ## create an sqlite database
    print(f"{datetime.datetime.now()} Staging taxa.db")
    if not db_path:
        db_dir = Path(Path.home(), ".taxaplease")
        db_path = Path(db_dir, "taxa.db")
    else:
        db_dir = Path(db_path).parent

    conn = sqlite3.connect(db_path)

    ## push the result to the database
    ## should overwrite the table if exists
    print(f"{datetime.datetime.now()} Writing taxa table to {db_path.name}")
    concat_df.to_sql("taxa", con=conn, index_label="taxid", if_exists="replace")

    ## create a metadata table that contains
    ## the current taxdatabase URL
    metadata_table_df = (
        pd.DataFrame([("ncbi_taxonomy_data_url", str(ncbi_taxonomy_data_url))])
        .rename({0: "key", 1: "value"}, axis=1)
        .set_index("key")
    )

    metadata_table_df.to_sql(
        "metadata", con=conn, index_label="key", if_exists="replace"
    )

    #########################
    # Optional table ingest #
    #########################

    ## We need to make sure we delete these tables if they already exist
    ## and we aren't overwriting them with new data
    cur = conn.cursor()
    res = cur.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
    ).fetchall()
    existing_tables = set([x[0] for x in res])
    if "deleted_taxa" in existing_tables:
        print(f"{datetime.datetime.now()} Deleting existing deleted_taxa table")
        cur.execute("DROP TABLE deleted_taxa")
    if "merged_taxa" in existing_tables:
        print(f"{datetime.datetime.now()} Deleting existing merged_taxa table")
        cur.execute("DROP TABLE merged_taxa")
    
    ## okay now go ahead
    if do_ingest_delnodes:
        print(f"{datetime.datetime.now()} Writing deleted_taxa table to {db_path.name}")
        deleted_ids_df.to_sql(
            "deleted_taxa", con=conn, index_label="taxid", if_exists="replace"
        )
    else:
        print(
            f"{datetime.datetime.now()} Local build - deleted_taxa table will not be generated"
        )

    if do_ingest_merged:
        print(f"{datetime.datetime.now()} Writing merged_taxa table to {db_path.name}")
        merged_ids_df.to_sql(
            "merged_taxa", con=conn, index_label="old_taxid", if_exists="replace"
        )
    else:
        print(
            f"{datetime.datetime.now()} Local build - merged_taxa table will not be generated"
        )

    #######
    # End #
    #######

    print(f"{datetime.datetime.now()} Done in {datetime.datetime.now() - start_time}")


def build_and_ingest_remote(tempdir, *, ncbi_taxonomy_data_url=None, db_path=None):
    start_time = datetime.datetime.now()

    ## default URL if not specified
    if not ncbi_taxonomy_data_url:
        ncbi_taxonomy_data_url = (
            "https://ftp.ncbi.nih.gov/pub/taxonomy/new_taxdump/new_taxdump.tar.gz"
        )

    #######################################
    # Downloading and extracting the data #
    #######################################

    ## download the data
    print(f"{datetime.datetime.now()} Downloading {ncbi_taxonomy_data_url}")
    ncbi_taxonomy_data_compressed = download_file(
        ncbi_taxonomy_data_url, destinationDir=tempdir
    )

    ## extract the archive to a subfolder
    print(f"{datetime.datetime.now()} Extracting {ncbi_taxonomy_data_compressed}")
    shutil.unpack_archive(
        ncbi_taxonomy_data_compressed, extract_dir=Path(tempdir, "new_taxdump")
    )

    ## technically I think you could download the stream straight into
    ## the gzip extrator, but this works.

    ##################################
    # Processing the downloaded data #
    ##################################

    ## get half the required info
    print(f"{datetime.datetime.now()} Processing nodes (file 1/2)")
    taxid_to_rank_df = pd.read_csv(
        Path(tempdir, "new_taxdump", "nodes.dmp"),
        sep="|",
        quotechar="\t",
        index_col=0,
        names=["taxid", "parent_taxid", "rank"],
        usecols=["taxid", "parent_taxid", "rank"],
    )

    ## get the other half
    print(f"{datetime.datetime.now()} Processing lineages (file 2/2)")
    taxid_to_name_df = pd.read_csv(
        Path(tempdir, "new_taxdump", "fullnamelineage.dmp"),
        sep="|",
        quotechar="\t",
        index_col=0,
        names=["name", "_", "__"],
    ).drop(["_", "__"], axis=1)

    ## join the halves together on taxid
    print(f"{datetime.datetime.now()} Joining nodes and lineages")
    concat_df = pd.concat([taxid_to_rank_df, taxid_to_name_df], axis=1)[
        ["name", "rank", "parent_taxid"]
    ]

    ## prep the deleted ids table
    print(f"{datetime.datetime.now()} Processing deleted nodes")
    deleted_ids_df = pd.read_csv(
        Path(tempdir, "new_taxdump", "delnodes.dmp"),
        sep="|",
        index_col=0,
        quotechar="\t",
        names=["taxid", "_"],
    ).drop("_", axis=1)

    ## prep the merged ids table
    print(f"{datetime.datetime.now()} Processing merged nodes")
    merged_ids_df = pd.read_csv(
        Path(tempdir, "new_taxdump", "merged.dmp"),
        sep="|",
        index_col=0,
        quotechar="\t",
        names=["old_taxid", "new_taxid", "_"],
    ).drop("_", axis=1)

    ###################
    # Database ingest #
    ###################

    ## create an sqlite database
    print(f"{datetime.datetime.now()} Staging taxa.db")
    if not db_path:
        db_dir = Path(Path.home(), ".taxaplease")
        db_path = Path(db_dir, "taxa.db")
    else:
        db_dir = Path(db_path).parent

    conn = sqlite3.connect(db_path)

    ## push the result to the database
    ## should overwrite the table if exists
    print(f"{datetime.datetime.now()} Writing taxa table to {db_path.name}")
    concat_df.to_sql("taxa", con=conn, index_label="taxid", if_exists="replace")

    print(f"{datetime.datetime.now()} Writing deleted_taxa table to {db_path.name}")
    deleted_ids_df.to_sql(
        "deleted_taxa", con=conn, index_label="taxid", if_exists="replace"
    )

    print(f"{datetime.datetime.now()} Writing merged_taxa table to {db_path.name}")
    merged_ids_df.to_sql(
        "merged_taxa", con=conn, index_label="old_taxid", if_exists="replace"
    )

    ## create a metadata table that contains
    ## the current taxdatabase URL
    metadata_table_df = (
        pd.DataFrame([("ncbi_taxonomy_data_url", str(ncbi_taxonomy_data_url))])
        .rename({0: "key", 1: "value"}, axis=1)
        .set_index("key")
    )

    metadata_table_df.to_sql(
        "metadata", con=conn, index_label="key", if_exists="replace"
    )

    print(f"{datetime.datetime.now()} Done in {datetime.datetime.now() - start_time}")


def main(tempdir):
    ## build remote by default
    ## to build local, call build_and_ingest_local directly from code
    build_and_ingest_remote(tempdir, ncbi_taxonomy_data_url=None, db_path=None)


#################
# Actual script #
#################

if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tempdir:
        main(tempdir)
