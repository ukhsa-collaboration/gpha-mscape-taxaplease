# Changelog


## [v1.1.2] - 2026-01-14

### Added Feature
Ability to supply TaxaPlease with your own database via `--database_directory` command.

### Fixed
Codebase now complies with ruff linting

## [v1.1.1] - 2025-11-27

Minor bugfix - code is now in a subfolder within src, rather than being directly under src.

### Added

None

### Changed

None

### Fixed

The src layout changes should avoid any namespace clashes - for example, previously it was possible to run `import cli`
which would import the taxaplease commandline interface. This would clash with any other packages that have a module named
"cli" and was therefore not desireable. By altering the layout, the equivalent import is now `from taxaplease import cli`
which avoids the namespace clash.

## [v1.1.0] - 2025-10-24

Various quality of life updates.

### Added

`get_taxonomy_url()` and `set_taxonomy_url()` have been added for retrieving a list of valid NCBI taxdump URLs and setting taxaPlease to use them respectively.

The taxaplease CLI utility now has a `version` command, along with `taxonomy --get` and `taxonomy --set` commands surfacing the above 2 functions, `check --phage` and `check --baltimore`.

Dependency on beautifulsoup4 added.

Added taxaplease_data - a python file that contains dictionaries with:

* a description of each viral realm
* a lookup of Baltimore classifications
* a lookup for phages

Add a `isPhage()` method, using the phage lookup in taxaplease_data. This can be overridden using the `phages` property of a TaxaPlease object.

Add a `get_baltimore_classification()` method, using the Baltimore classification lookup in taxaplease_data. Can similarly be overridden if required.

### Changed

The taxid used for the deleted taxid test has been changed.

### Fixed

isEukaryote, isBacteria and other similar methods now check if they have been passed the top level taxid for that domain.

* for example, "Bacteria" has a taxid of "2" - previously isBacteria returned False since it only checked parents, rather than the ID itself

## [v1.0.1] - 2025-10-24

Migration of code to gpha-mscape-template format for GitHub.

### Added

Changelog based on tagged release notes added as a flat file.

### Changed

None

### Fixed

None

## [v1.0.0] - 2025-06-17

Breaking change to the calling convention for print_taxonomy_graph and generate_taxonomy.

### Added

None

### Changed

The generate_taxonomy_graph method now takes an unlimited number of taxids as arguments, rather than being limited to a maximum of 2.

### Fixed

"None and null" from the taxonomic graph output is now suppressed.

Non-existent taxids should no longer cause taxaplease to hang.

## [v0.3.0] - 2025-06-16

New taxonomic graph feature.

### Added

Adds a new function that prints a taxonomy graph given one or two taxids as input.

Test it from the CLI by running taxaplease check --graph 1313 1337

The result should be something like the following:

```
╙── root
    └─╼ cellular organisms
        └─╼ Bacteria
            └─╼ Bacillati
                └─╼ Bacillota
                    └─╼ Bacilli
                        └─╼ Lactobacillales
                            └─╼ Streptococcaceae
                                └─╼ Streptococcus
                                    ├─╼ Streptococcus pneumoniae
                                    └─╼ Streptococcus hyointestinalis
None
null
```

Ignore the None and null.

### Changed

None

### Fixed

None

## [v0.2.1] - 2025-06-04

Resolve issues encountered when using the latest NCBI taxonomy.

### Added

None

### Changed

None

### Fixed

The isVirus/isBacteria and other methods previously depended on the "get_superkingdom_taxid" method; however, this level has been removed in the latest NCBI taxonomy. Instead, the code now uses the "get_all_parent_taxids" method which completely mitigates the issue.

## [v0.2.0] - 2025-03-13

Add taxaplease CLI utility.

### Added

Adds an argparse-based commandline utility for interacting with the taxaplease database, along with associated tests.

### Changed

None

### Fixed

None

## [v0.1.2] - 2025-02-27

Downloaded NCBI taxonomy files are now automatically removed once database creation is complete.

### Added

None

### Changed

Cleanup of NCBI taxonomy files implemented using tempdir.

### Fixed

None
