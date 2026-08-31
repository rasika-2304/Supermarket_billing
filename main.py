from database import Database
from ui.main_window import MainWindow

if __name__ == "__main__":
    db = Database()
    db.initialize()
    MainWindow(db).mainloop()
