Release instructions
====================

This page contains the steps to make a release and some helpful resources to get you started.

Create an issue and copy/paste the steps below to release a new version. Close the issue when it is done.

These steps should be taken in order to create a new release!

.. code-block:: md

    **Double check for quality-control**

    - [ ] There are no [open issues with a `impact: block-release` label](https://github.com/gee-community/geetools/labels/impact%3A%20block-release)

    **Prepare the codebase for a new version**

    - [ ] Bump a new version using `commitizen`. use the `--pre-release` flag if it's a **release candidate**.
    - [ ] Push the RLS commit `git push upstream main`
    - [ ] If a **release candidate** is needed, tick this box when we're now ready for a full release.

    **Make the release**

    - [ ] [Start a new GitHub release](https://github.com/gee-community/geetools/releases/new)
    - Call the release the current version, e.g. `v0.2.0`
    - In the **`Choose a Tag:`** dropdown, type in the release name (e.g., `v0.2.0`) and click "Create new tag"
    - In the **`Target:`** dropdown, pin it to the release commit that you've just pushed.
    - Generate the automatic release notes, eventually manually specify the previous version (useful when several release candidate have been made)
    - [ ] Confirm that the release completed
    - [The `publish` github action job](https://github.com/gee-community/geetools/actions/workflows/release.yaml) has completed successfully in the [actions tab](https://github.com/gee-community/geetools/actions).
    - [The PyPI version is updated](https://pypi.org/project/geetools/)
    - [ ] Hide the previous patch version build in the RDT interface if needed.
    - [ ] Celebrate, you're done!

    Taken from [the release checklist](https://github.com/gee-community/geetools/blob/main/RELEASE.rst).
