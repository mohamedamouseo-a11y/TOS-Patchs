#!/usr/bin/env python3
import importlib.util
from pathlib import Path

V1 = Path(__file__).with_name("generate_phase5_3_4_tgws.py")
spec = importlib.util.spec_from_file_location("phase5_3_4_tgws_v1", V1)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# V1 replacement #5 legitimately occurs twice in two different TGWS backend-build guards.
# V2 splits that duplicate into two exact, context-scoped replacements while preserving
# every other V1 replacement and all V1 HEAD/blob/parser/apply safety gates.
old_message = 'throw new Error("نسخة Backend الخاصة بربط Google Editor Email ليست V1R7.");'
new_message = 'throw new Error(tgwsText("نسخة Backend الخاصة بربط Google Editor Email ليست V1R7.", "The Google Editor Email backend build is not V1R7."));'

assert module.REPLACEMENTS[4] == (old_message, new_message)

load_old = '''if (googleIdentities?.buildTag !== EXPECTED_TGWS_BUILD) {\n        throw new Error("نسخة Backend الخاصة بربط Google Editor Email ليست V1R7.");\n      }'''
load_new = '''if (googleIdentities?.buildTag !== EXPECTED_TGWS_BUILD) {\n        throw new Error(tgwsText("نسخة Backend الخاصة بربط Google Editor Email ليست V1R7.", "The Google Editor Email backend build is not V1R7."));\n      }'''

mapping_old = '''if (updated?.buildTag !== EXPECTED_TGWS_BUILD || refreshed?.buildTag !== EXPECTED_TGWS_BUILD) {\n        throw new Error("نسخة Backend الخاصة بربط Google Editor Email ليست V1R7.");\n      }'''
mapping_new = '''if (updated?.buildTag !== EXPECTED_TGWS_BUILD || refreshed?.buildTag !== EXPECTED_TGWS_BUILD) {\n        throw new Error(tgwsText("نسخة Backend الخاصة بربط Google Editor Email ليست V1R7.", "The Google Editor Email backend build is not V1R7."));\n      }'''

module.REPLACEMENTS = (
    module.REPLACEMENTS[:4]
    + [(load_old, load_new), (mapping_old, mapping_new)]
    + module.REPLACEMENTS[5:]
)

if __name__ == "__main__":
    module.main()
