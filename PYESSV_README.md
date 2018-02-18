# Setting up pyessv and CMIP6 CV integration

For working with the CMIP6 controlled vocabularies we use the `pyessv` library from:

 https://github.com/ES-DOC/pyessv

To set this up you need to do:

```
$ git clone https://github.com/ES-DOC/pyessv
$ git clone https://github.com/ES-DOC/pyessv-archive
$ mkdir -p ~/.esdoc/pyessv-archive
$ ln -s $PWD/pyessv-archive/wcrp ~/.esdoc/pyessv-archive/
$ export PYTHONPATH=$PYTHONPATH:$PWD/pyessv
```

And test it with:

```
$ python
>>> import pyessv
>>> scope = pyessv.load('wcrp', 'cmip6')
>>> for collection in scope:
...     for term in collection:
...         print scope, collection, term.label

```
