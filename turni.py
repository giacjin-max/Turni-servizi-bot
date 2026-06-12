import os
import pandas as pd

df = pd.read_excel("turni.xlsx")

print(df.head())
print(df.columns.tolist())
