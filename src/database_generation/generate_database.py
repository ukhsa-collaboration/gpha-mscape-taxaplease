#!/usr/bin/env python3
import sqlite3
import shutil
import requests
import pandas as pd
import datetime
import os
import tempfile
from pathlib import Path

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
        destinationDir = os.getcwd()

    local_filename = os.path.join(destinationDir, url.split("/")[-1])

    ## NOTE the stream=True parameter below
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                # if chunk:
                f.write(chunk)

    return local_filename


def main(
    tempdir,
    ncbi_taxonomy_data_url="https://ftp.ncbi.nih.gov/pub/taxonomy/new_taxdump/new_taxdump.tar.gz",
):
    start_time = datetime.datetime.now()

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
        ncbi_taxonomy_data_compressed, extract_dir=os.path.join(tempdir, "new_taxdump")
    )

    ## technically I think you could download the stream straight into
    ## the gzip extrator, but this works.

    ##################################
    # Processing the downloaded data #
    ##################################

    ## get half the required info
    print(f"{datetime.datetime.now()} Processing nodes (file 1/2)")
    taxid_to_rank_df = pd.read_csv(
        os.path.join(tempdir, "new_taxdump", "nodes.dmp"),
        sep="|",
        quotechar="\t",
        index_col=0,
        names=["taxid", "parent_taxid", "rank"],
        usecols=["taxid", "parent_taxid", "rank"],
    )

    ## get the other half
    print(f"{datetime.datetime.now()} Processing lineages (file 2/2)")
    taxid_to_name_df = pd.read_csv(
        os.path.join(tempdir, "new_taxdump", "fullnamelineage.dmp"),
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
        os.path.join(tempdir, "new_taxdump", "delnodes.dmp"),
        sep="|",
        index_col=0,
        quotechar="\t",
        names=["taxid", "_"],
    ).drop("_", axis=1)

    ## prep the merged ids table
    print(f"{datetime.datetime.now()} Processing merged nodes")
    merged_ids_df = pd.read_csv(
        os.path.join(tempdir, "new_taxdump", "merged.dmp"),
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
    db_dir = os.path.join(Path.home(), ".taxaplease")
    db_path = os.path.join(db_dir, "taxa.db")
    conn = sqlite3.connect(db_path)

    ## push the result to the database
    ## should overwrite the table if exists
    print(f"{datetime.datetime.now()} Writing taxa table to taxa.db")
    concat_df.to_sql("taxa", con=conn, index_label="taxid", if_exists="replace")

    print(f"{datetime.datetime.now()} Writing deleted_taxa table to taxa.db")
    deleted_ids_df.to_sql(
        "deleted_taxa", con=conn, index_label="taxid", if_exists="replace"
    )

    print(f"{datetime.datetime.now()} Writing merged_taxa table to taxa.db")
    merged_ids_df.to_sql(
        "merged_taxa", con=conn, index_label="old_taxid", if_exists="replace"
    )

    ## create a metadata table that contains
    ## the current taxdatabase URL
    metadata_table_df = pd.DataFrame(
        [("ncbi_taxonomy_data_url", ncbi_taxonomy_data_url)]
    ).rename({0: "key", 1: "value"}, axis=1).set_index("key")

    metadata_table_df.to_sql(
        "metadata", con=conn, index_label="key", if_exists="replace"
    )

    print(f"{datetime.datetime.now()} Done in {datetime.datetime.now() - start_time}")


#################
# Actual script #
#################

if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tempdir:
        main(tempdir)
