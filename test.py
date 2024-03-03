import pandas as pd

df = pd.read_excel('hist_data2.xlsx')
m_names = list(set(df['merchant_name'].tolist()))
b_names = []

for n in m_names:
    count = len(df[df['merchant_name']==n])
    budget = int(df.loc[df['merchant_name'] == n, 'cashback'].sum())
    if (count > 5) and (budget > 1_000_000):
        b_names.append(n)
print(b_names)
