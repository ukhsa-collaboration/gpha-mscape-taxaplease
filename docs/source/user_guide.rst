##########
User guide
##########

*****************************
Customising your installation
*****************************

TaxaPlease has some sane defaults, but if you need to customise it this section documents
some of the options available for doing this.

Using a different version of the NCBI taxonomy database
=======================================================

By default, on first run taxaPlease retrieves the latest version of the NCBI taxonomy.

If you wish to use a specific version, you can pass the URL for this to taxaPlease, which
will rebuild the database with that version.

.. warning::
    If you find yourself changing versions often, you might want to store multiple taxaPlease
    databases in different locations - this will save you from hammering the NCBI server
    with a lot of traffic!

    See **Storing the taxaPlease sqlite database in a different location** for how to do this.

To get valid URLs you can either visit the `NCBI taxdump archive page <"https://ftp.ncbi.nih.gov/pub/taxonomy/taxdump_archive/">`__
or the `NCBI taxdump latest page <"https://ftp.ncbi.nih.gov/pub/taxonomy/new_taxdump/">`__ or run ``taxaplease taxonomy --get`` which returns
a json result of the latest URL, and older "archive" URLs.

Once you have the URL of interest, you can set the database to use this either from the CLI or from
Python.

.. code-block::
    :caption: Setting the taxonomy URL from the CLI

    ## use the 2019-01-01 version of the taxonomy
    taxaplease taxonomy --set https://ftp.ncbi.nih.gov/pub/taxonomy/taxdump_archive/new_taxdump_2019-01-01.zip

.. code-block::
    :caption: Setting the taxonomy URL from Python

    from taxaplease import TaxaPlease

    tp = TaxaPlease()

    ## use the 2019-01-01 version of the taxonomy
    tp.set_taxonomy_url("https://ftp.ncbi.nih.gov/pub/taxonomy/taxdump_archive/new_taxdump_2019-01-01.zip")

This should only be run when changing the taxonomy - there is no need to run it more often than this.

Storing the taxaPlease sqlite database in a different location
==============================================================

By default, the taxaPlease database is stored in your home directory - ``~/.taxaplease/taxa.db``.

If you wish to store it elsewhere, or to have multiple databases (perhaps built with different versions
of the NCBI taxonomy) you can specify a path to the database when using the CLI or Python.

.. code-block::
    :caption: Using a custom database location from the CLI

    ## use a custom database from the CLI
    taxaplease --database mydir/custom.db record --record 1337

.. code-block::
    :caption: Using a custom database location in Python

    from taxaplease import TaxaPlease

    ## specify a custom database location in Python
    tp = TaxaPlease(database="mydir/custom.db")

*****************
Reusable patterns
*****************

This section documents some reusable patterns that might fit in your code.

Getting all the parent records for a taxid
==========================================

TaxaPlease has a method for getting a record given a taxid, and for getting parent taxids
given a taxid. There is no method for getting all parent records, however.

You can do this with a pattern like this:

.. code-block::
    :caption: Getting all parent records

    from taxaplease import TaxaPlease

    tp = TaxaPlease()
    taxid_of_interest = 1337

    list_of_records = [
        tp.get_record(taxid)
        for taxid in
        tp.get_all_parent_taxids(taxid_of_interest, includeSelf=True)
    ]

The ``includeSelf=True`` is an optional flag that will include taxid 1337 along with its
parent taxids.

Initialisation for single process and multiprocess scripts
==========================================================

The basic method for initialising taxaPlease is by "instantiating an instance of the class".

.. code-block::

    from taxaplease import TaxaPlease

    tp = TaxaPlease()

With this, a taxaPlease object has been created and assigned to the variable ``tp``.

If you wanted to loop through a set of IDs, it might be tempting to do something like this:

.. code-block::
    :caption: Don't do this

    from taxaplease import TaxaPlease

    ids = [68, 419, 665, 1336, 8007]

    for id in ids:
        tp = TaxaPlease()
        print(tp.get_record(id))

However, this approach would keep reinitialising taxaPlease on each loop. It's more efficient to
initialise the class outside the loop so the object can be reused:

.. code-block::
    :caption: Do this!

    from taxaplease import TaxaPlease

    ids = [68, 419, 665, 1336, 8007]
    tp = TaxaPlease()

    for id in ids:
        print(tp.get_record(id))

There is an exception to this - multiprocessing. TaxaPlease runs an sqlite3 database behind the scenes
which does support being accessed from multiple processes, but individual cursor objects do not. In this
case, it is best to have a taxaPlease instance *per process* in order to avoid any concurrency issues.

.. code-block::
    :caption: Multiprocessing example, only do this if you have to...

    import multiprocessing as mp
    from taxaplease import TaxaPlease

    ids = [68, 419, 665, 1336, 8007]
    number_of_processes = 5
    input_queue = mp.Queue()
    output_queue = mp.Queue()
    result_list = []

    ## load ids into the queue
    for i in ids:
        input_queue.put(i)

    def process_input_queue(source_queue, target_queue):
        ## initialise a taxaplease instance
        ## for this process
        tp = TaxaPlease()
        
        while not source_queue.empty():
            ## get a message from the queue
            msg = source_queue.get()

            ## process the message
            rec = tp.get_record(msg)

            ## push the result 
            target_queue.put(rec)

    ## list containing process objects
    process_list = []

    ## create processes and add to list
    ## making either the defined number of processes,
    ## or one per item in the queue, whichever is smaller
    for _ in range(min(number_of_processes, input_queue.qsize())):
        process_list.append(
            mp.Process(target=process_input_queue, args=[input_queue, output_queue])
        )

    ## start the processes
    for p in process_list:
        p.daemon = True
        p.start()

    ## collect all the processes once they are done
    for p in process_list:
        p.join()

    ## get and print the results
    while not output_queue.empty():
        result_list.append(output_queue.get())

    print(result_list)

The above is a toy example that spins up 5 processes, each with a taxaPlease instance which
is then used to process incoming data from a queue. You probably won't need to write code to
multiprocess in this way, but you can!

Efficiently running lots of queries
===================================

With a typical database (such as postgres), you can achieve better performance by writing a
big query that generates the results you need instead of sending many small queries. However,
sqlite3 does not suffer from the network latency seen in such databases, and as such it is
actually reasonably efficient to send many small queries.

That said, if you have a list with duplicate taxids, you can save a bit of compute by using
one of two key patterns: deduplication and dictionary lookup or sorting and memoisation.

Deduplication and dictionary lookup
-----------------------------------

.. code-block::
    :caption: Deduplication and dictionary lookup

    from taxaplease import TaxaPlease

    tp = TaxaPlease()

    ## list of ids that contains several duplicates
    ids = [
        68, 419, 665, 1336, 8007,
        68, 419, 665, 1336, 8007,
        68, 419, 665, 1336, 8007,
        68, 419, 665, 1336, 8007,
        68, 419, 665, 1336, 8007
    ]

    ## sets are an efficient way to ensure
    ## only unique values are present
    ids_set = set(ids)

    ## use a comprehension to generate a lookup
    ## dictionary from id to record
    lookup_dict = {taxid: tp.get_record(taxid) for taxid in ids_set}

    ## create a new list of records in the same order
    ## as the original, including duplicate records
    records_list = [lookup_dict.get(x) for x in ids]

Sorting and memoisation
-----------------------

Memoisation is a technique that caches the result of a function, so if it is called with
the same arguments again the previous result can be retrieved instead of calculating it
again using a potentially exspensive bit of code such as a database lookup.

If the order of results is not important, sorting will improve cache hits but this is optional.

.. code-block::
    :caption: Sorting and memoisation

    import functools
    from taxaplease import TaxaPlease

    tp = TaxaPlease()

    ## list of ids that contains several duplicates
    ids = [
        68, 419, 665, 1336, 8007,
        68, 419, 665, 1336, 8007,
        68, 419, 665, 1336, 8007,
        68, 419, 665, 1336, 8007,
        68, 419, 665, 1336, 8007
    ]

    ## use the functools.cache decorator
    ## to do memoisation of expensive results
    @functools.cache
    def get_record_helper(input_taxid):
        return tp.get_record(input_taxid)

    ## sort the list to improve cache hits
    sorted_ids = sorted(ids)

    ## generate the records list
    records_list = [get_record_helper(x) for x in sorted_ids]

***********
Quirky bits
***********

This section documents *ad hoc* features of taxaPlease that might be useful for random
queries and one-off investigations.

Reverse lookup
==============

TaxaPlease is designed to go from an NCBI taxid (for example, 1337) to a taxon (for example, *Streptococcus hyointestinalis*).
The reverse, starting with a taxon and finding the corresponding taxid is deliberately not supported as it delves into the
vagaries of fuzzy string matching, changing taxon names and many to one relationships. Other tools are available that attempt
to tackle this problem!

If you insist; however, there is a way to do this by using the taxaPlease database directly.

.. warning::
    This is not a supported feature of taxaPlease, and the database structure is potentially
    subject to change, which may break any code depending on "reverse lookup".

.. code-block::
    :caption: Querying the taxaPlease sqlite database directly

    import sqlite3
    import pandas as pd
    from pathlib import Path 

    ## connect to database
    db_dir = Path(Path.home(), ".taxaplease")
    db_path = Path(db_dir, "taxa.db")

    db_conn = sqlite3.connect(db_path)

    ## get top 5 rows from taxa table
    pd.read_sql("select * from taxa limit 5", db_conn)

    ## get a taxa by name
    pd.read_sql(
        """
        SELECT 
            * 
        FROM 
            taxa 
        WHERE 
            name LIKE 'Pseudomonas aeruginosa'
        """,
        db_conn
    )


Generating a graph
==================

Let's say you have a set of taxids and you want to know how many levels there
are between them. You can run a query like this:

.. code-block::
    :caption: Getting levels between a set of taxids

    taxaplease check --levels-between 1337 42

    {"left_levels_to_common_parent": 7, "right_levels_to_common_parent": 7, "total_levels_between_taxa": 14}

If you want to visualise that, you can use the ``--graph`` option:

.. code-block::
    :caption: Using --graph

    taxaplease check --graph 1337 42

    ╙── root
    └─╼ cellular organisms
        └─╼ Bacteria
            ├─╼ Bacillati
            │   └─╼ Bacillota
            │       └─╼ Bacilli
            │           └─╼ Lactobacillales
            │               └─╼ Streptococcaceae
            │                   └─╼ Streptococcus
            │                       └─╼ Streptococcus hyointestinalis
            └─╼ Pseudomonadati
                └─╼ Myxococcota
                    └─╼ Myxococcia
                        └─╼ Myxococcales
                            └─╼ Cystobacterineae
                                └─╼ Archangiaceae
                                    └─╼ Cystobacter

This gives a tree-like plot of the relationship between the two taxa.
`taxaplease check --graph` can actually take an arbitrary number of taxids
as arguments, so it is possible to have much more than two.

Behind the scenes, this is rendered using `NetworkX <https://networkx.org/en/>`__.
Using the corresponding methods in Python allows full control over how the graph is rendered.

.. code-block::
    :caption: Interacting with taxaPlease networkX directed graphs in python

    import networkx as nx
    import pylab as plt
    from taxaplease import TaxaPlease

    tp = TaxaPlease()

    ## generate the taxonomy graph using taxaPlease
    G = tp.generate_taxonomy_graph(1337, 42)

    ## draw using the spectral layout and save to file
    nx.draw_spectral(G, with_labels=True)
    plt.savefig("nx_example_spectral.png")

.. figure:: images/nx_example_spectral.png
    
    Directed graph plotted using the networkX spectral layout

*****************************
Useful concepts to understand
*****************************

Baltimore classification
========================

Baltimore classification is a scheme for grouping viruses based on nucleic acid type,
sense and transcription method. See `the Wikipedia page on Baltimore classification <"https://en.wikipedia.org/wiki/Baltimore_classification">`__
for more information.

There are 7 groups within the classification:

===== ========================================================================= ============
Group Description                                                               Abbreviation
===== ========================================================================= ============
I     double-stranded DNA viruses                                               dsDNA
II    single-stranded DNA viruses                                               ssDNA
III   double-stranded RNA viruses                                               dsRNA
IV    positive-sense single-stranded RNA viruses                                +ssRNA
V     negative-sense single-stranded RNA viruses                                -ssRNA
VI    single-stranded RNA viruses with a DNA intermediate in their life cycle   ssRNA-RT
VII   double-stranded DNA viruses with an RNA intermediate in their life cycle  dsDNA-RT
===== ========================================================================= ============

TaxaPlease can be used to get the abbreviated column from the above table, given a taxid:

.. code-block::
    :caption: Getting the Baltimore classification for a taxid

    from taxaplease import TaxaPlease

    tp = TaxaPlease()

    ## look up SARS-CoV-2
    print(tp.get_baltimore_classification(2697049))

.. note::
    The command doesn't actually return a Baltimore group (I to VII) - instead it returns the
    abbreviation, for example "+ssRNA" for SARS-CoV-2. This is probably more useful...

Phages
======

When we're talking about phages, we're probably talking about bacteriophages which for the most
part sit under the taxonomic class **Caudoviricetes** which contains double-stranded DNA bacteriophagees.
There are other bacteriophages, however, such as the single-stranded DNA bacteriophages in the **Loebvirae**
kingdom, RNA bacteriophages in the class **Vidaverviricetes** and several others.

.. note::
    There is a genus **Atsuirnavirus** which contains the species **Atsuirnavirus caloris**.
    This is a bacteriophage that infects thermoacidophiles, but it does not have a taxid at
    present and so cannot be labelled with taxaPlease.

Bacteriophages are viruses which infect bacteria, but there are other phages such as archaeal
viruses (viruses that infect archaea) and virophages (viruses that require the co-infection of another virus).

TaxaPlease has the ability to check if a given taxid corresponds to any of these 3 phage groups.

.. code-block::
    :caption: Checking a taxid to see if it is a phage

    from taxaplease import TaxaPlease

    tp = TaxaPlease()

    ## Bowservirus bowser
    phage_taxid = 2560487

    assert tp.isPhage(phage_taxid)
