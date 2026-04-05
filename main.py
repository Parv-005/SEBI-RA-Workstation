from utils.startup_checks import check_constants_file

if __name__ == "__main__":
    check_constants_file()
    
    from gui.app import App
    from database.db_manager import init_db

    init_db()  # Ensure database tables are created on launch
    app = App()
    app.mainloop()
