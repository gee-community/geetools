"""Check the warnings from doc builds."""

import sys
from pathlib import Path


def check_warnings(file: Path) -> int:
    """Check the list of warnings produced by the CI tests.

    Raises errors if there are unexpected ones and/or if some are missing.

    Args:
        file: the path to the generated warning.txt file from
            the CI build

    Returns:
        0 if the warnings are all there
        1 if some warning are not registered or unexpected
    """
    # print some log
    print("\n=== Sphinx Warnings test ===\n")

    # find the file where all the known warnings are stored
    warning_file = Path(__file__).parent / "data" / "warning_list.txt"

    test_warnings = file.read_text().strip().split("\n")
    ref_warnings = warning_file.read_text().strip().split("\n")

    print(
        f'Checking build warnings in file: "{file}" and comparing to expected '
        f'warnings defined in "{warning_file}"\n\n'
    )

    # find all the missing warnings
    missing_warnings = []
    for wa in ref_warnings:
        index = [i for i, twa in enumerate(test_warnings) if wa in twa]
        if len(index) == 0:
            missing_warnings += [wa]
            print(f"Warning was not raised: {wa}")
        else:
            test_warnings.pop(index[0])

    # the remaining one are unexpected
    for twa in test_warnings:
        print(f"Unexpected warning: {twa}")

    # delete the tmp warnings file
    file.unlink()

    return len(missing_warnings) != 0 or len(test_warnings) != 0


if __name__ == "__main__":
    # cast the file to path and resolve to an absolute one
    file = Path.cwd() / "warnings.txt"

    # execute the test
    sys.exit(check_warnings(file))
