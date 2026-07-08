"""Build the FraudOps assignment presentation deck.

Run: python scripts/build_presentation.py

Produces `fraudops-presentation.pptx` (22 slides, 16:9) that embeds the
12 storyboard screenshots from `docs/demo_screenshots/`. Rendered in the
same dark theme as the running console so the deck feels cohesive with
the app.

Dependencies:
    pip install python-pptx pillow
"""
import os
import sys
from pathlib import Path

# Re-exports the same builder used in the demo pipeline.
sys.path.insert(0, str(Path(__file__).parent))

# The actual implementation lives in this file so the archive doesn't
# depend on any /tmp scaffolding.
from build_presentation_impl import make_deck  # noqa: E402


if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "docs" / "fraudops-presentation.pptx"
    make_deck(out_path=str(out))
