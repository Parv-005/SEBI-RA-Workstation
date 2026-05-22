import traceback
from PySide6.QtCore import QObject, Signal, QRunnable, Slot
from utils.logger import setup_logger

logger = setup_logger("Worker")


class WorkerSignals(QObject):
    done = Signal(object)
    error = Signal(str)
    progress = Signal(str)


class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @Slot()
    def run(self):
        fn_name = getattr(self.fn, "__name__", str(self.fn))
        logger.debug(f"Worker starting: {fn_name}")
        try:
            result = self.fn(*self.args, **self.kwargs)
            logger.debug(f"Worker completed: {fn_name}")
            self.signals.done.emit(result)
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"Worker failed in {fn_name}: {e}", exc_info=True)
            self.signals.error.emit(f"{e}\n{tb}")
