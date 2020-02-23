import re
from pathlib import Path


def test_build_dependencies(en_vocab):
    # Check that library requirements are pinned exactly the same across different setup files.
    libs_ignore_requirements = ["pytest", "pytest-timeout", "mock", "flake8", "jsonschema"]
    libs_ignore_setup = ["fugashi", "natto-py", "pythainlp"]

    # check requirements.txt
    req_dict = {}

    root_dir = None
    # when running tests locally, the file is 3 levels up. On the CI, it's 2 levels up.
    roots = [Path(__file__).parent.parent, Path(__file__).parent.parent.parent]  # or whatever
    for r in roots:
        req_file = r / "requirements.txt"
        if req_file.exists():
            root_dir = r
            with req_file.open() as f:
                lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    if not line.startswith("#"):
                        lib, v = _parse_req(line)
                        if lib and lib not in libs_ignore_requirements:
                            req_dict[lib] = v

    assert root_dir is not None, "Could not find the root directory of requirements.txt"

    # check setup.cfg and compare to requirements.txt
    # also fails when there are missing or additional libs
    setup_file = root_dir / "setup.cfg"
    with setup_file.open() as f:
        lines = f.readlines()
    setup_keys = set()
    for line in lines:
        line = line.strip()
        if not line.startswith("#"):
            lib, v = _parse_req(line)
            if lib and not lib.startswith("cupy") and lib not in libs_ignore_setup:
                req_v = req_dict.get(lib, None)
                assert req_v is not None, "{} in setup.cfg but not in requirements.txt".format(lib)
                assert (lib+v) == (lib+req_v), "{} has different version in setup.cfg and in requirements.txt: " \
                                               "{} and {} respectively".format(lib, v, req_v)
                setup_keys.add(lib)
    assert sorted(setup_keys) == sorted(req_dict.keys())  # if fail: requirements.txt contains a lib not in setup.cfg

    # check pyproject.toml and compare the versions of the libs to requirements.txt
    # does not fail when there are missing or additional libs
    toml_file = root_dir / "pyproject.toml"
    with toml_file.open() as f:
        lines = f.readlines()
    for line in lines:
        line = line.strip().strip(",").strip("\"")
        if not line.startswith("#"):
            lib, v = _parse_req(line)
            if lib:
                req_v = req_dict.get(lib, None)
                assert (lib+v) == (lib+req_v), "{} has different version in pyproject.toml and in requirements.txt: " \
                                               "{} and {} respectively".format(lib, v, req_v)


def _parse_req(line):
    lib = re.match(r"^[a-z0-9\-]*", line).group(0)
    v = line.replace(lib, "").strip()
    if not re.match(r"^[<>=][<>=].*", v):
        return None, None
    return lib, v
