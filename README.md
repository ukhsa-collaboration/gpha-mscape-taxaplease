# gpha-mscape-taxaplease

## What is this?

taxaPlease: A CLI utility and importable python module for wrangling NCBI taxids.

## Installation?

```bash
## pip install straight from the github repo
pip install git+https://github.com/ukhsa-collaboration/gpha-mscape-taxaplease.git
```

When first instantiated, an NCBI taxonomy database will be downloaded. This only happens once.

## What can it do?

For a given taxid, we can:

* get metadata (taxa name, rank, parent taxid)
* get the parent taxid
* find the corresponding species-level taxid
* find the corresponding genus-level taxid
* given two taxids, find the common parent taxid
* given two taxids, how many levels ("ranks") are between:
  * those two taxids (sum of the below)
  * each of those taxids and their common parent taxa
* given a taxid, is it:
  * Archaea?
  * Eukaryota?
  * Bacteria?
  * Virus?

## How do I use it?

To use it in your code, have a look at `demo.iypnb` or just jump in and `from taxaplease import TaxaPlease`.

If you just want a commandline tool, try `taxaplease -h` to see what it can do.

Realistically, you're probably trying to do one of the following:

```bash
## get a record given a taxid
## >> {"taxid": 1337, "name": "Streptococcus hyointestinalis", "rank": "species", "parent_taxid": 1301}
taxaplease record --record 1337

## get a parent taxid
## >> 1301
taxaplease taxid --parent 1337
```

Each subcommand also has `-h` help information.

## Where did that database come from?

From [NCBI](https://ftp.ncbi.nih.gov/pub/taxonomy/new_taxdump/) plus some wrangling.

The code for generating it is in `database_generation/generate_database.py`

## Do you really need to include taxa like wolves and aloe vera?

Maybe not, but they're in there for now.

## Where is the database stored?

By default, the taxaplease database is stored in your home directory, in a `.taxaplease` folder. 
To recreate the database, you can just delete this folder.

## But I want to use a different database location!

As of v2.0.0 you can supply taxaPlease with a custom database location - just provide the path to
the database file using the `--database` command or as an argument when instantiating the class.

If the file exists, this will be used as the sqlite database for taxaPlease queries - else the
database will be created at this location.

```bash
## use a custom database from the CLI
taxaplease --database <path-to-database-file> record --record 1337
```

```python
from taxaplease import TaxaPlease

## specify a custom database location in Python
tp = TaxaPlease(database="mydir/custom.db")
```
