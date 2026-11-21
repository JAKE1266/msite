"""支持 ``python -m msite`` 直接运行。"""

import sys

from msite.cli import main

if __name__ == "__main__":
    sys.exit(main())
