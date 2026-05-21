from dataclasses import dataclass, field


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
    telegram_msg_id: int | None = None
    errors: list[str] = field(default_factory=list)

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def is_not_configured(self, service: str) -> bool:
        if service == "sheets":
            return self.sheets_success == "not_configured"
        if service == "telegram":
            return self.telegram_success == "not_configured"
        return False