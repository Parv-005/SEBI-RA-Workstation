from dataclasses import dataclass, field
from utils.constants import BROADCAST_NOT_CONFIGURED, BROADCAST_NOT_AUTHORIZED


@dataclass
class ServiceResult:
    success: bool
    error: str | None = None


@dataclass
class AppendResult:
    success: bool
    unmapped_columns: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass
class BroadcastResult:
    image_success: bool = False
    image_path: str | None = None
    sheets_success: bool | str = False
    sheets_unmapped: list[str] = field(default_factory=list)
    telegram_success: bool | str = False
    telegram_msg_ids: dict[str, int] | None = None
    telegram_failures: dict[str, str] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def has_errors(self) -> bool:
        return len(self.errors) > 0 or len(self.telegram_failures) > 0

    def is_not_configured(self, service: str) -> bool:
        if service == "sheets":
            return self.sheets_success == BROADCAST_NOT_CONFIGURED
        if service == "telegram":
            return self.telegram_success == BROADCAST_NOT_CONFIGURED
        return False


def build_broadcast_summary(result: BroadcastResult) -> str:
    parts = []
    if result.image_success:
        parts.append("Image generated")
    if result.sheets_success is True:
        parts.append("Google Sheets updated")
    elif result.sheets_success == BROADCAST_NOT_CONFIGURED:
        parts.append("Sheets not configured")
    elif not result.sheets_success:
        parts.append("Sheets failed")
    if result.telegram_success is True:
        parts.append("Telegram sent")
    elif result.telegram_success == BROADCAST_NOT_CONFIGURED:
        parts.append("Telegram not configured")
    elif result.telegram_success == BROADCAST_NOT_AUTHORIZED:
        parts.append("Telegram not authorized")
    elif not result.telegram_success:
        parts.append("Telegram failed")
    return " | ".join(parts)


def build_broadcast_detail(result: BroadcastResult) -> list[str]:
    detail_lines = []
    if result.errors:
        detail_lines.append("Errors:")
        for err in result.errors:
            detail_lines.append(f"  \u2022 {err}")
    if result.telegram_failures:
        detail_lines.append("Telegram failures:")
        for name, err in result.telegram_failures.items():
            detail_lines.append(f"  \u2022 {name}: {err}")
    if not result.sheets_success and result.sheets_success != BROADCAST_NOT_CONFIGURED:
        detail_lines.append("  \u2022 Google Sheets failed")
    return detail_lines