import shutil

import os
from redbaron_type_hinting.adding_type_hints import enrich_pyfiles_by_type_hints

from corteconstitucional.compare_data import compare_data
from corteconstitucional.main import main
FILE_NAME = "types.jsonl"

def test_type_hinting(tmp_path):
    """
    This is NOT a test!
    pytest --typeguard-packages=corteconstitucional
    """
    TYPES_JSONL = str(tmp_path / FILE_NAME)
    os.environ["TYPES_JSONL"] = TYPES_JSONL # this is for typeguard
    compare_data()
    shutil.copy(TYPES_JSONL,"/tmp/types.jsonl") # just for debugging
    enrich_pyfiles_by_type_hints(TYPES_JSONL)
    compare_data() # rerun with newly added type-hints to check whether type-hints actually pass typeguard-checks



if __name__ == '__main__':
    # enrich_pyfiles_by_type_hints("/tmp/types.jsonl",overwrite=True)
    enrich_pyfiles_by_type_hints("/tmp/types.jsonl",overwrite=True,verbose=True)
