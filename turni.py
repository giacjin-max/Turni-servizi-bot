import os
import pandas as pd

df = pd.read_excel("Turni.xlsx")

print(df.head())
print(df.columns.tolist())
