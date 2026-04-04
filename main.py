import customtkinter as ctk
from gui.app import App
from database.db_manager import init_db

if __name__ == "__main__":
    init_db()  # Ensure database tables are created on launch
    app = App()
    app.mainloop()
