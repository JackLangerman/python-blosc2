python-blosc2 release procedure
===============================

Preliminaries
-------------

* Check that `VERSION` file contains the correct number.

* Make sure that the c-blosc2 submodule is updated to the latest version (or a specific version that will be documented in the `RELEASE_NOTES.md`)::

    cd blosc2/c-blosc2
    git checkout <desired tag>
    git pull
    cd ../..
    git commit -m "Update c-blosc2 sources" blosc2/c-blosc2
    git push

* Make sure that the current master branch is passing the tests in continuous integration.

* Build the package and make sure that::

    PYTHONPATH=. python -c "import blosc2; blosc2.print_versions()"

is printing the correct versions.

* Make sure that `RELEASE_NOTES.md` and `ANNOUNCE.rst` are up to date with the latest news
  in the release.

* Commit the changes::

    git commit -a -m "Getting ready for release X.Y.Z"
    git push

* Double check that the supported Python versions for the wheels are the correct ones
  (`.github/workflows/cibuildwheels.yml`).  Add/remove Python version if needed.
  Also, update the `classifiers` field for the supported Python versions.

* Check that the metainfo for the package is correct::

    python setup.py sdist
    twine check dist/*


Tagging
-------

* Create a (signed, if possible) tag ``X.Y.Z`` from ``main``.  Use the next message::

    git tag -a vX.Y.Z -m "Tagging version X.Y.Z"

* Push the tag to the github repo::

    git push --tags

* Go to Blosc/blogsite repo and click on the `Re-run all jobs` button to regenerate the
  documentation and check that it has been correctly updated in https://www.blosc.org.


Checking packaging
------------------

* Check that the package (and wheels!) have been uploaded to PyPI
  (they should have been created when GHA would finish the tag trigger):
  https://pypi.org/project/blosc2/

* Check that the packages and wheels are sane::

    python -m pip install blosc2 -U
    cd tests
    python -c"import blosc2; blosc2.print_versions()"
    pytest

* Do an actual release in github by visiting:
  https://github.com/Blosc/python-blosc2/releases/new
  Add the notes specific for this release.


Announcing
----------

* Send an announcement to the Blosc list.  Use the ``ANNOUNCE.rst`` file as skeleton
  (or possibly as the definitive version). Start the subject with ANN:.

* Announce in Twitter via @Blosc2 account and rejoice.


Post-release actions
--------------------

* Change back to the actual python-blosc2 repo::

    cd $HOME/blosc/python-blosc2

* Create new headers for adding new features in ``RELEASE_NOTES.md``
  add this place-holder:

  XXX version-specific blurb XXX

* Edit ``VERSION`` in master to increment the version to the next
  minor one (i.e. X.Y.Z --> X.Y.(Z+1).dev0).

* Commit your changes with::

    git commit -a -m "Post X.Y.Z release actions done"
    git push


That's all folks!
