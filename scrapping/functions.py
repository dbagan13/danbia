import pandas as pd

SAVE_DIR = "data/"

def save_to_csv(df, file_name, path=SAVE_DIR):
    df.to_csv(f"{path}{file_name}")
    print(f"{file_name} saved!")
