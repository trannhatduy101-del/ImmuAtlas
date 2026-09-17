"""
Start ImmuAtlas.

    python run.py

Then open http://127.0.0.1:5000. On the first start the application builds its
working database, which takes a few seconds; every start after that is
immediate.

The application itself lives in src/. Putting that directory on sys.path here
means every module inside it keeps importing its siblings by plain name --
`import db`, `import config`, `from routes.coverage import fix_region` -- exactly
as it did when all of them sat in the repository root. The alternative, turning
src/ into a package, would have rewritten an import line in ten files to buy
precisely the same result.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

# Imported after the path is set, so `app` resolves to src/app.py.
from app import app  # noqa: E402


if __name__ == "__main__":
    app.run(debug=True)
