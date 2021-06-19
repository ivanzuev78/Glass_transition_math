import pandas as pd

# pandas
df = pd.DataFrame()
# Добавить колонку. Все строки будут с присвоенным значением
df["MXDA"] = 2.0
# Добавить строку. Все колонки будут с присвоенным значением
df.loc["KER-828"] = 1
# Все столбцы списком
df.columns.values.tolist()
# Все строки списком
df.index.tolist()
print(df)
