"""支持 ``python -m mdown`` 直接运行。"""

import sys

from mdown.cli import main

if __name__ == "__main__":
    sys.exit(main())
