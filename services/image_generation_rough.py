"""
image_generation_rough.py

PSD-based image generation service.

Pipeline:
    PSD template
        ↓
    PhotoshopAPI (psapi) — edit text layers in-memory
        ↓
    psd-tools — composite/render the modified PSD
        ↓
    PNG output

Dependencies:
    pip install photoshop-python-api psd-tools pillow

NOTE: PhotoshopAPI (photoshop-python-api) is the Python wrapper around the
      Adobe Photoshop scripting COM API (Windows only).  However, the intent
      of this rough service is to use the *pure-Python* photoshop-api that
      works offline.  Two viable approaches are shown below:

      Approach A  — photoshop-python-api (requires Photoshop installed, Windows)
      Approach B  — psd_tools only, editing text via psd_tools internals
                     (cross-platform, no Photoshop needed)

      Because the chat conversation explicitly asked for the
      "PhotoshopAPI → output.psd → psd-tools composite()" pipeline
      and also said "no Photoshop installed", we implement Approach B:

      1.  Open the PSD with psd_tools.
      2.  Walk the layer tree and replace text in TypeLayer nodes.
      3.  Save to a temp/output PSD.
      4.  Composite with psd_tools.composite() → PIL Image.
      5.  Save as PNG.

      If you later decide to use the full Adobe API (Approach A), the
      PSDImageGeneratorAdobe class is also stubbed out below.
"""

from __future__ import annotations

import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))

# pyrefly: ignore [missing-import]
from psd_tools import PSDImage
from psd_tools.api.layers import TypeLayer
from psd_tools.psd import engine_data
from psd_tools.psd.descriptor import String
from PIL import Image, ImageDraw, ImageFont

from core.paths import CONFIG_PATH, IMAGES_DIR, DATA_DIR
from utils.constants import CURRENCY_SYMBOL, EMPTY_PLACEHOLDER
from utils.formatters import format_currency
from utils.logger import setup_logger

logger = setup_logger("PSDImageGenerator")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
OUTPUT_DIR = IMAGES_DIR
TEMPLATE_PSD = DATA_DIR / "template_file_image.psd"


# ---------------------------------------------------------------------------
# Helper — find and patch text layers inside a PSD layer tree
# ---------------------------------------------------------------------------

def _set_text_in_layer_tree(layer_group, replacements: dict[str, str]) -> None:
    """
    Recursively walk *layer_group* and replace the text content of any
    TypeLayer whose name matches a key in *replacements*.

    Args:
        layer_group: A psd_tools PSDImage or GroupLayer.
        replacements: Mapping of layer_name → new_text_content.
    """
    for layer in layer_group:
        if layer.name in replacements and isinstance(layer, TypeLayer):
            try:
                new_text = replacements[layer.name] + "\x00"
                layer._engine_data["EngineDict"]["Editor"]["Text"] = engine_data.String(new_text)
                layer._data.text_data[b"Txt "] = String(value=new_text)
            except Exception as exc:
                logger.warning(
                    f"Could not patch text in layer '{layer.name}': {exc}"
                )
        if layer.is_group():
            _set_text_in_layer_tree(layer, replacements)


# ---------------------------------------------------------------------------
# Main service class — pure Python, no Photoshop required
# ---------------------------------------------------------------------------

class PSDImageGenerator:
    """
    Generates trade/update images by:

    1. Opening a PSD template (psd_tools).
    2. Patching text layers to inject trade data.
    3. Compositing the modified PSD into a PIL Image.
    4. Saving as PNG.

    All operations are pure Python — no Photoshop installation required.
    """

    def __init__(self, template_psd: Optional[str | Path] = None):
        self.template_path = Path(template_psd) if template_psd else TEMPLATE_PSD
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        if not self.template_path.exists():
            logger.warning(
                f"PSD template not found at {self.template_path}. "
                "Falling back to PIL-drawn images."
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_trade_image(self, trade: dict) -> Optional[str]:
        """
        Generate a trade signal image from the PSD template.

        Args:
            trade: Trade dictionary with keys matching layer names in the PSD.

        Returns:
            Absolute path to the saved PNG, or None on failure.
        """
        replacements = self._build_trade_replacements(trade)
        filename = (
            f"trade_{trade.get('trade_code', 'new')}"
            f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        )
        return self._render_psd(replacements, filename)

    def generate_update_image(self, trade: dict, update: dict) -> Optional[str]:
        """
        Generate a trade-update image from the PSD template.

        Args:
            trade:  Trade dictionary.
            update: Update dictionary (update_type, details, exit_price, etc.).

        Returns:
            Absolute path to the saved PNG, or None on failure.
        """
        replacements = self._build_update_replacements(trade, update)
        filename = (
            f"update_{trade.get('trade_code', 'unknown')}"
            f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        )
        return self._render_psd(replacements, filename)

    # ------------------------------------------------------------------
    # Build replacement maps
    # ------------------------------------------------------------------

    @staticmethod
    def _build_trade_replacements(trade: dict) -> dict[str, str]:
        """
        Map trade fields to PSD layer names.

        The layer names below must exactly match those in your PSD template.
        Adjust them if your template uses different layer names.
        """
        entry = trade.get("entry_price", 0) or 0
        target = trade.get("target", 0) or 0
        sl = trade.get("stop_loss", 0) or 0
        reward = trade.get("reward", 0) or 0
        risk = trade.get("risk", 0) or 0
        reward_pct = trade.get("reward_pct", 0) or 0
        risk_pct = trade.get("risk_pct", 0) or 0

        zone = ""
        if trade.get("zone_start") and trade.get("zone_end"):
            zone = f"{CURRENCY_SYMBOL}{trade['zone_start']:.2f} – {CURRENCY_SYMBOL}{trade['zone_end']:.2f}"

        return {
            # --- Core identity ---
            "stock_name":   str(trade.get("stock_name", "")),
            "trade_code":   str(trade.get("trade_code", "")),
            "long_short":   str(trade.get("action", "")),
            "trade_type":   str(trade.get("trade_type", "")),
            # --- Prices ---
            "buy_price":    f"{CURRENCY_SYMBOL}{float(entry):.2f}",
            "buy_zone":     zone,
            "target":       f"{CURRENCY_SYMBOL}{float(target):.2f}",
            "stop_loss":    f"{CURRENCY_SYMBOL}{float(sl):.2f}",
            # --- Risk/Reward ---
            "reward":       f"{CURRENCY_SYMBOL}{float(reward):.2f}",
            "risk":         f"{CURRENCY_SYMBOL}{float(risk):.2f}",
            "risk_percentage":  f"{float(risk_pct):.2f}",
            "reward_percentage": f"{float(reward_pct):.2f}",
            "rrr":          str(trade.get("risk_reward", "")),
            # --- Misc ---
            "cmp_at_entry": (
                f"{CURRENCY_SYMBOL}{float(trade['cmp_at_entry']):.2f}"
                if trade.get("cmp_at_entry") else ""
            ),
            "date":         datetime.now().strftime("%d %b %Y"),
        }

    @staticmethod
    def _build_update_replacements(trade: dict, update: dict) -> dict[str, str]:
        """
        Map update fields to PSD layer names.
        """
        return {
            "stock_name":   str(trade.get("stock_name", "")),
            "trade_code":   str(trade.get("trade_code", "")),
            "long_short":   str(trade.get("action", "")),
            "buy_price": (
                f"{CURRENCY_SYMBOL}{float(trade.get('entry_price', 0)):.2f}"
                if trade.get("entry_price") else ""
            ),
            "target": (
                f"{CURRENCY_SYMBOL}{float(trade.get('target', 0)):.2f}"
                if trade.get("target") else ""
            ),
            "stop_loss": (
                f"{CURRENCY_SYMBOL}{float(trade.get('stop_loss', 0)):.2f}"
                if trade.get("stop_loss") else ""
            ),
            "update_type":  str(update.get("update_type", "")),
            "details":      str(update.get("details", "")),
            "exit_price": (
                f"{CURRENCY_SYMBOL}{float(update['exit_price']):.2f}"
                if update.get("exit_price") else ""
            ),
            "new_sl": (
                f"{CURRENCY_SYMBOL}{float(update['latest_sl_price']):.2f}"
                if update.get("latest_sl_price") else ""
            ),
            "new_target": (
                f"{CURRENCY_SYMBOL}{float(update['latest_target']):.2f}"
                if update.get("latest_target") else ""
            ),
            "date": datetime.now().strftime("%d %b %Y"),
        }

    # ------------------------------------------------------------------
    # Core rendering logic
    # ------------------------------------------------------------------

    def _render_psd(
        self,
        replacements: dict[str, str],
        output_filename: str,
    ) -> Optional[str]:
        """
        1. Open template PSD.
        2. Patch text layers using *replacements*.
        3. Save modified PSD to a temp file.
        4. Composite with psd_tools → PIL Image.
        5. Save PNG to OUTPUT_DIR.

        Returns the path to the saved PNG or None on error.
        """
        if not self.template_path.exists():
            logger.error(
                f"Template PSD '{self.template_path}' not found. "
                "Cannot render image."
            )
            return None

        try:
            # Step 1 — open template
            psd = PSDImage.open(str(self.template_path))
            logger.debug(f"Opened PSD template: {self.template_path}")

            # Step 2 — patch text layers
            _set_text_in_layer_tree(psd, replacements)
            logger.debug(
                f"Patched {len(replacements)} text layer(s): "
                f"{list(replacements.keys())}"
            )

            # Step 3 — save modified PSD to a temp file
            #           (psd_tools composites from an open PSDImage object
            #            so we don't strictly need a temp file, but saving
            #            first makes the pipeline explicit and auditable)
            with tempfile.NamedTemporaryFile(
                suffix=".psd", delete=False, dir=OUTPUT_DIR
            ) as tmp:
                tmp_path = tmp.name

            psd.save(tmp_path)
            logger.debug(f"Saved modified PSD to temp: {tmp_path}")

            psd_modified = PSDImage.open(tmp_path)
            logger.debug("Reopened modified PSD for text-overlay compositing")

            base_img = psd_modified.composite(ignore_preview=True)
            canvas = base_img.convert("RGBA") if base_img.mode != "RGBA" else base_img.copy()

            text_img = Image.new("RGBA", canvas.size, (255, 255, 255, 0))
            text_draw = ImageDraw.Draw(text_img)

            for layer in psd_modified:
                if not isinstance(layer, TypeLayer) or not layer.visible:
                    continue
                text = replacements.get(layer.name, layer.text)
                if not text:
                    continue
                left, top, right, bottom = layer.bbox
                font_size = 48
                style_run = layer._engine_data.get("EngineDict", {}).get("StyleRun", {})
                run_array = style_run.get("RunArray", [])
                if run_array:
                    font_size = int(run_array[0].get("StyleSheet", {}).get("StyleSheetData", {}).get("FontSize", 48) or 48)

                layer_font = None
                for fp in ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"]:
                    if os.path.exists(fp):
                        try:
                            layer_font = ImageFont.truetype(fp, size=font_size)
                            break
                        except Exception:
                            pass
                if layer_font is None:
                    layer_font = ImageFont.load_default()

                text_draw.text((left, top), text, fill=(0, 0, 0, 255), font=layer_font)

            canvas.paste(text_img, (0, 0), text_img)
            rendered = canvas
            logger.debug("Text-overlay compositing complete.")

            # Step 5 — save PNG
            output_path = str(OUTPUT_DIR / output_filename)
            rendered.save(output_path)
            logger.info(f"Generated image: {output_path}")

            return output_path

        except Exception as exc:
            logger.error(
                f"PSD render failed: {exc}", exc_info=True
            )
            return None

        finally:
            # Clean up temp PSD
            try:
                if "tmp_path" in locals() and os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Stub — Adobe Photoshop API variant (requires Photoshop installed, Windows)
# ---------------------------------------------------------------------------

class PSDImageGeneratorAdobe:
    """
    Alternative implementation using photoshop-python-api (Adobe COM bridge).

    Requires:
        - Adobe Photoshop installed (Windows only).
        - pip install photoshop-python-api

    This is left as a stub.  Use PSDImageGenerator for the cross-platform path.
    """

    def generate_trade_image(self, trade: dict) -> Optional[str]:
        try:
            import photoshop.api as ps  # type: ignore[import]

            app = ps.Application()
            doc = app.open(str(TEMPLATE_PSD))

            replacements = PSDImageGenerator._build_trade_replacements(trade)

            for layer in doc.layers:
                if layer.name in replacements and layer.kind == ps.LayerKind.TextLayer:
                    layer.textItem.contents = replacements[layer.name]

            filename = (
                f"trade_{trade.get('trade_code', 'new')}"
                f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            )
            output_path = str(OUTPUT_DIR / filename)

            options = ps.PNGSaveOptions()
            doc.saveAs(output_path, options, asCopy=True)
            doc.close(ps.SaveOptions.DoNotSaveChanges)

            logger.info(f"(Adobe) Generated trade image: {output_path}")
            return output_path

        except ImportError:
            logger.error(
                "photoshop-python-api is not installed or Photoshop is not "
                "available.  Use PSDImageGenerator instead."
            )
            return None
        except Exception as exc:
            logger.error(f"(Adobe) PSD render failed: {exc}", exc_info=True)
            return None


# ---------------------------------------------------------------------------
# Quick smoke-test (run this file directly)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sample_trade = {
        "trade_code": "TC001",
        "stock_name": "RELIANCE",
        "segment": "Cash",
        "action": "LONG",
        "trade_type": "POSITIONAL",
        "entry_price": 2850.00,
        "zone_start": 2830.00,
        "zone_end": 2870.00,
        "target": 3050.00,
        "stop_loss": 2750.00,
        "reward": 200.00,
        "risk": 100.00,
        "reward_pct": 7.02,
        "risk_pct": 3.51,
        "risk_reward": "2:1",
        "approx_time": "5-7 Trading Days",
        "cmp_at_entry": 2855.00,
        "remarks": "Strong breakout above resistance.",
    }

    sample_update = {
        "update_type": "TRAIL_SL",
        "details": "Trail SL to 2900. Trade going well.",
        "latest_sl_price": 2900.00,
    }

    gen = PSDImageGenerator()

    trade_img = gen.generate_trade_image(sample_trade)
    print(f"Trade image  → {trade_img}")

    update_img = gen.generate_update_image(sample_trade, sample_update)
    print(f"Update image → {update_img}")
