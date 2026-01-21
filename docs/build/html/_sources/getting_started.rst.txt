Getting started
===============

Installation
------------

taxaPlease can be installed with pip directly from GitHub:

.. code-block:: console

   pip install git+https://github.com/ukhsa-collaboration/gpha-mscape-taxaplease.git

Testing the install
-------------------

If you'd like to verify that everything is working as expected, you can run the included
test suite. You may need to `pip install pytest` if this is not already in your environment.

.. code-block:: bash

   ## optional - if required
   pip install pytest
   
   ## clone the repo
   git clone https://github.com/ukhsa-collaboration/gpha-mscape-taxaplease.git
   
   ## enter the directory
   cd gpha-mscape-taxaplease

   ## run the tests
   pytest

Basic query with the CLI
------------------------

The command `taxaplease` should now be available on your CLI. Here's an example usage:

.. code-block:: bash

   taxaplease record --record 1337

This will return the following record:

.. code-block:: json

   {"taxid": 1337, "name": "Streptococcus hyointestinalis", "rank": "species", "parent_taxid": 1301} 

Basic query with Python
-----------------------

taxaPlease can also be imported into a Python script. Here's the equivalent code for that:

.. code-block:: python

   from taxaplease import TaxaPlease

   ## create an instance of the class
   tp = TaxaPlease()

   ## use that instance to run a query
   rec = tp.get_record(1337)

   ## print the result
   print(rec)

This will print the following record:

.. code-block:: json

   {"taxid": 1337, "name": "Streptococcus hyointestinalis", "rank": "species", "parent_taxid": 1301}
