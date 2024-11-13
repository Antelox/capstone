import logging
import os
from pathlib import Path

logger = logging.getLogger('tests')
logging.basicConfig(level=logging.INFO)
root_dir = Path(__file__).parent.parent.resolve()
tests = [
    f"python {root_dir}/bindings/python/tests/test_all.py",
    f"python {root_dir}/suite/cstest/test/integration_tests.py cstest_py",
    f"cstest_py {root_dir}/tests/MC/",
    f"cstest_py {root_dir}/tests/details/",
    f"cstest_py {root_dir}/tests/issues/",
    f"cstest_py {root_dir}/tests/features/",
]

for test in tests:
    logger.info(f'Running {test}')
    logger.info("#######################")
    os.system(test)
    logger.info("-----------------------")
