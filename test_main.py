import os
from redbaron_type_hinting.adding_type_hints import enrich_pyfiles_by_type_hints

from corteconstitucional.main import main
FILE_NAME = "types.jsonl"

def test_type_hinting(tmp_path):
    TYPES_JSONL = str(tmp_path / FILE_NAME)
    os.environ["TYPES_JSONL"] = TYPES_JSONL
    main()
    enrich_pyfiles_by_type_hints(TYPES_JSONL)
