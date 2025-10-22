'''
import sqlite3
import pandas as pd

def read_trades_from_db(db_path):
    try:
        con = sqlite3.connect(db_path)
        df = pd.read_sql_query("SELECT * from trades", con)
        con.close()
        if df.empty:
            print("Nessun trade trovato nel database.")
        else:
            print("Dati dei trade recuperati:")
            print(df.to_markdown(index=False))
    except Exception as e:
        print(f"Errore durante la lettura del database: {e}")

if __name__ == "__main__":
    read_trades_from_db("/home/ubuntu/AurumBotX/data/trading_engine.db")
'''
