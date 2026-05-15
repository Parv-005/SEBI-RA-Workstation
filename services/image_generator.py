import json
import os
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from core.paths import CONFIG_PATH, IMAGES_DIR, ROOT_DIR
from utils.logger import setup_logger

logger = setup_logger("ImageGenerator")

OUTPUT_DIR = IMAGES_DIR


class ImageGenerator:
    def __init__(self):
        self._load_config()
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def _load_config(self):
        self.trade_template = ""
        self.update_template = ""
        self.font_path = ""
        self.font_size = 24
        self.font_color = (255, 255, 255)
        self.positions = {}

        if CONFIG_PATH.exists():
            with open(CONFIG_PATH) as f:
                config = json.load(f)
            img = config.get("image", {})
            self.trade_template = str(ROOT_DIR / img.get("trade_template", ""))
            self.update_template = str(ROOT_DIR / img.get("update_template", ""))
            self.font_path = img.get("font_path", "")
            self.font_size = img.get("font_size", 24)
            color = img.get("font_color", [255, 255, 255])
            self.font_color = tuple(color) if isinstance(color, list) else (255, 255, 255)
            self.positions = img.get("positions", {})

    def _get_font(self, size: int | None = None) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        sz = size or self.font_size
        if self.font_path and os.path.exists(self.font_path):
            return ImageFont.truetype(self.font_path, sz)
        try:
            return ImageFont.truetype("DejaVuSans.ttf", sz)
        except OSError:
            return ImageFont.load_default()

    def generate_trade_image(self, trade: dict) -> str | None:
        try:
            template_path = self.trade_template
            if not template_path or not os.path.exists(template_path):
                logger.warning("Trade template not found, using fallback.")
                return self._generate_fallback_image(trade)

            img = Image.open(template_path).copy()
            draw = ImageDraw.Draw(img)
            font = self._get_font()

            field_map = {
                "stock_name": trade.get("stock_name", ""),
                "segment": trade.get("segment", ""),
                "action": trade.get("action", ""),
                "entry_price": f"₹{trade.get('entry_price', 0):.2f}",
                "zone": (
                    f"₹{trade['zone_start']:.2f} – ₹{trade['zone_end']:.2f}"
                    if trade.get("zone_start") and trade.get("zone_end") else ""
                ),
                "target": f"₹{trade.get('target', 0):.2f}",
                "stop_loss": f"₹{trade.get('stop_loss', 0):.2f}",
                "trade_type": trade.get("trade_type", ""),
                "approx_time": trade.get("approx_time", ""),
                "reward": f"{trade.get('reward', 0):.2f}",
                "risk": f"{trade.get('risk', 0):.2f}",
                "reward_pct": f"{trade.get('reward_pct', 0):.2f}%",
                "risk_pct": f"{trade.get('risk_pct', 0):.2f}%",
                "risk_reward": trade.get("risk_reward", ""),
                "trade_code": trade.get("trade_code", ""),
            }

            for field, text in field_map.items():
                pos = self.positions.get(field)
                if pos and text:
                    draw.text(tuple(pos), str(text), fill=self.font_color, font=font)

            filename = f"trade_{trade.get('trade_code', 'new')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            output_path = str(OUTPUT_DIR / filename)
            img.save(output_path)
            logger.info(f"Generated trade image: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error generating trade image: {e}", exc_info=True)
            return None

    def generate_update_image(self, trade: dict, update: dict) -> str | None:
        try:
            template_path = self.update_template
            if not template_path or not os.path.exists(template_path):
                template_path = self.trade_template
            if not template_path or not os.path.exists(template_path):
                logger.warning("Update template not found, using fallback.")
                return self._generate_fallback_update_image(trade, update)

            img = Image.open(template_path).copy()
            draw = ImageDraw.Draw(img)
            font = self._get_font()

            draw.text(self.positions.get("stock_name", (100, 50)),
                      trade.get("stock_name", ""), fill=self.font_color, font=font)
            draw.text(self.positions.get("segment", (100, 90)),
                      trade.get("segment", ""), fill=self.font_color, font=font)
            draw.text(self.positions.get("action", (100, 130)),
                      trade.get("action", ""), fill=self.font_color, font=font)

            status_pos = self.positions.get("status", (100, 410))
            draw.text(tuple(status_pos), update.get("update_type", ""),
                      fill=self.font_color, font=font)

            if update.get("details"):
                draw.text((100, 450), update["details"], fill=self.font_color, font=font)

            filename = f"update_{trade.get('trade_code', '')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            output_path = str(OUTPUT_DIR / filename)
            img.save(output_path)
            logger.info(f"Generated update image: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error generating update image: {e}", exc_info=True)
            return None

    def _generate_fallback_image(self, trade: dict) -> str:
        img = Image.new("RGB", (800, 500), color=(20, 20, 40))
        draw = ImageDraw.Draw(img)
        font = self._get_font(28)
        small_font = self._get_font(20)

        action_color = (0, 200, 80) if trade.get("action") == "BUY" else (220, 50, 50)
        draw.text((50, 30), f"{trade.get('action', '')} — {trade.get('stock_name', '')}",
                  fill=action_color, font=font)
        draw.line([(50, 70), (750, 70)], fill=(100, 100, 150), width=2)

        y = 90
        lines = [
            f"Segment     : {trade.get('segment', '')}",
            f"Entry Price : ₹{trade.get('entry_price', 0):.2f}",
        ]
        if trade.get("zone_start") and trade.get("zone_end"):
            lines.append(f"Zone        : ₹{trade['zone_start']:.2f} – ₹{trade['zone_end']:.2f}")
        lines += [
            f"Target      : ₹{trade.get('target', 0):.2f}",
            f"Stop Loss   : ₹{trade.get('stop_loss', 0):.2f}",
        ]
        if trade.get("trade_type"):
            lines.append(f"Trade Type  : {trade['trade_type']}")
        if trade.get("approx_time"):
            lines.append(f"Approx Time : {trade['approx_time']}")

        lines += [
            f"Reward      : ₹{trade.get('reward', 0):.2f} ({trade.get('reward_pct', 0):.2f}%)",
            f"Risk        : ₹{trade.get('risk', 0):.2f} ({trade.get('risk_pct', 0):.2f}%)",
        ]
        if trade.get("risk_reward"):
            lines.append(f"Risk:Reward : {trade['risk_reward']}")
        if trade.get("cmp_at_entry"):
            lines.append(f"CMP         : ₹{trade['cmp_at_entry']:.2f}")
        if trade.get("trade_code"):
            lines.append(f"Code        : {trade['trade_code']}")

        for line in lines:
            draw.text((60, y), line, fill=(220, 220, 240), font=small_font)
            y += 35

        draw.line([(50, y + 10), (750, y + 10)], fill=(100, 100, 150), width=2)
        draw.text((60, y + 20), datetime.now().strftime("%d-%b-%Y %I:%M %p"),
                  fill=(150, 150, 180), font=small_font)

        filename = f"trade_{trade.get('id', 'new')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        output_path = str(OUTPUT_DIR / filename)
        img.save(output_path)
        return output_path

    def _generate_fallback_update_image(self, trade: dict, update: dict) -> str:
        img = Image.new("RGB", (800, 400), color=(20, 20, 40))
        draw = ImageDraw.Draw(img)
        font = self._get_font(28)
        small_font = self._get_font(20)

        draw.text((50, 30), "TRADE UPDATE", fill=(255, 200, 50), font=font)
        draw.line([(50, 70), (750, 70)], fill=(100, 100, 150), width=2)

        y = 90
        draw.text((60, y), f"{trade.get('stock_name', '')} ({trade.get('segment', '')})",
                  fill=(220, 220, 240), font=small_font)
        y += 40
        draw.text((60, y), f"Update: {update.get('update_type', '')}",
                  fill=(100, 200, 255), font=small_font)
        y += 40
        if update.get("details"):
            draw.text((60, y), update["details"], fill=(220, 220, 240), font=small_font)
            y += 40

        draw.line([(50, y + 10), (750, y + 10)], fill=(100, 100, 150), width=2)
        draw.text((60, y + 20), datetime.now().strftime("%d-%b-%Y %I:%M %p"),
                  fill=(150, 150, 180), font=small_font)

        filename = f"update_{trade.get('id', '')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        output_path = str(OUTPUT_DIR / filename)
        img.save(output_path)
        return output_path
