Contribute
==========

Thank you for your help improving **geetools**!

**geetools** uses `nox <https://nox.thea.codes/en/stable/>`__ to automate several development-related tasks.
Currently, the project uses four automation processes (called sessions) in ``noxfile.py``:

-   ``mypy``: to perform a mypy check on the lib;
-   ``test``: to run the test with pytest;
-   ``docs``: to build the documentation in the ``build`` folder;
-   ``lint``: to run the pre-commits in an isolated environment

Every nox session is run in its own virtual environment, and the dependencies are installed automatically.

To run a specific nox automation process, use the following command:

.. code-block:: console

   nox -s <session name>

For example: ``nox -s test`` or ``nox -s docs``.

Workflow for contributing changes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We follow a typical GitHub workflow of:

-   Create a personal fork of this repo
-   Create a branch
-   Open a pull request
-   Fix findings of various linters and checks
-   Work through code review

See the following sections for more details.

Clone the repository
^^^^^^^^^^^^^^^^^^^^

First off, you'll need your own copy of **geetools** codebase. You can clone it for local development like so:

Fork the repository so you have your own copy on GitHub. See the `GitHub forking guide for more information <https://docs.github.com/en/get-started/quickstart/fork-a-repo>`__.

Then, clone the repository locally so that you have a local copy to work on:

.. code-block:: console

   git clone https://github.com/<YOUR USERNAME>/geetools
   cd geetools

Then install the development version of the extension:

.. code-block:: console

   pip install -e .[dev]

This will install the **geetools** library, together with two additional tools:
-   `pre-commit <https://pre-commit.com>`__ for automatically enforcing code standards and quality checks before commits.
-   `nox <https://nox.thea.codes/en/stable/>`__, for automating common development tasks.

Lastly, activate the pre-commit hooks by running:

.. code-block:: console

    pre-commit install

This will install the necessary dependencies to run pre-commit every time you make a commit with Git.

Initialize GEE available
^^^^^^^^^^^^^^^^^^^^^^^^

All the ``geetools`` package is build around the Google Earth Engine API. It is thus impossible to work wihin it if you are not registered. Please follow `Google instructions <https://developers.google.com/earth-engine/guides/access>`__ to use the tool.

Once you get access to GEE, you have 2 authentication options to work within `geetools`:

#.  Specify your project
#.  use a service account

Specify your project
####################

Here we assume your machine is already authenticated to GEE and some credentials are saved in your computer in the confi folder: ``~/.config/earthengine/credentials``.

In this case ``geetools`` ``docs`` and ``test`` session will only need to get the name of the project to use. Specify it in a environment variable:

.. code-block:: console

    export EARTHENGINE_PROJECT=<name of your project>


Service account
###############

.. note::

   This is the method used by all the CI/CD project pipeline from documentation to deployment.

If your machine is not authenticated you can use a service account from the GCP console and save its json API key in an environment variable:

.. code-block:: console

    export EARTHENGINE_SERVICE_ACCOUNT=<your key>

The key should have the following format and is generated from the `GCP console <https://cloud.google.com/iam/docs/keys-create-delete>`__:

.. code-block:: json

    {"client_id": "value", "client_secret": "value", "refresh_token": "value", "project": "value"}

Contribute to the codebase
^^^^^^^^^^^^^^^^^^^^^^^^^^

Any larger updates to the codebase should include tests and documentation. The tests are located in the ``tests`` folder, and the documentation is located in the ``docs`` folder.

To run the tests locally, use the following command:

.. code-block:: console

    nox -s test

See :ref:`below <contributing-docs>` for more information on how to update the documentation.

.. _contributing-docs:

Contribute to the docs
^^^^^^^^^^^^^^^^^^^^^^

The documentation is built using `Sphinx <https://www.sphinx-doc.org/en/master/>`__ and deployed to `Read the Docs <https://readthedocs.org/>`__.

To build the documentation locally, use the following command:

.. code-block:: console

    nox -s docs

For each pull request, the documentation is built and deployed to make it easier to review the changes in the PR. To access the docs build from a PR, click on the "Read the Docs" preview in the CI/CD jobs.

Release new version
^^^^^^^^^^^^^^^^^^^

.. danger::

    Only maintainers can release new versions of **geetools**.

To release a new version, open an issue with the new version number e.g. ``RLS: 1.0.0``. copy/paste the instructions from the `release instructions <https://github.com/gee-community/geetools/blob/main/RELEASE.rst>`__ and follow the presented workflow.

Once you are done you can close the issue and celebrate!
