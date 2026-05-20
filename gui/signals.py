from PySide6.QtCore import QObject, Signal


class AppSignals(QObject):
    navigate = Signal(str, object)

    trades_loaded = Signal(list)
    trades_error = Signal(str)

    trade_created = Signal(str)
    trade_create_error = Signal(str)
    broadcast_complete = Signal(object)

    trade_detail_loaded = Signal(dict, list)

    trade_updated = Signal(dict)
    trade_update_error = Signal(str)
    update_broadcast_complete = Signal(object)

    cmp_fetched = Signal(float)
    cmp_fetch_error = Signal(str)

    settings_saved = Signal()
    settings_error = Signal(str)
    telegram_auth_needs_otp = Signal()
    telegram_auth_needs_2fa = Signal()
    telegram_auth_success = Signal()
    telegram_auth_error = Signal(str)

    notification = Signal(str, str, int)

    theme_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)


_signals_instance = None


def get_signals():
    global _signals_instance
    if _signals_instance is None:
        _signals_instance = AppSignals()
    return _signals_instance
