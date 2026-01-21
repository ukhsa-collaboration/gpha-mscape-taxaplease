Introduction
=============

What is this?
-------------

taxaPlease: A CLI utility and importable python module for wrangling NCBI taxids.

Installation?
-------------

.. code-block:: bash

   ## pip install straight from the github repo
   pip install git+https://github.com/ukhsa-collaboration/gpha-mscape-taxaplease.git

When first instantiated, an NCBI taxonomy database will be downloaded. This only happens once.

What can it do?
---------------

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
  * Phage?

How do I use it?
----------------

To use it in your code, have a look at ``demo.iypnb`` or just jump in and ``from taxaplease import TaxaPlease``.

If you just want a commandline tool, try ``taxaplease -h`` to see what it can do.
