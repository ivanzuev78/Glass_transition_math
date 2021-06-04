import numpy as np
import pandas as pd


Smola_name = ['KER-828', 'LaprBD', 'YDPN-638']
Smola = np.array([0.8, 0.2, 0])
Amine_name = ['IPDA', 'MXDA', 'PACM']
Amine = np.array([0.5, 0.5, 0])

# Amin = np.array([1,2,3])
# c = np.outer(Smola, Amine)
#
# print(Smola, Amine, c, sep='\n')


df = pd.DataFrame(np.outer(Smola, Amine), index=Smola_name, columns=Amine_name, )
# df.columns = Amine_name
# df.rename({ i:Smola_name[i] for i in range(len(Smola_name))})
print(df)
print('-------------')
# print(Amine_name[1], '+', Smola_name[2], df[Amine_name[1]][Smola_name[2]])


df_tg_base = pd.DataFrame(index=Smola_name, columns=Amine_name)

df_tg_base[Amine_name[0]][Smola_name[0]] = 148
df_tg_base[Amine_name[0]][Smola_name[1]] = -10
df_tg_base[Amine_name[0]][Smola_name[2]] = 165
df_tg_base[Amine_name[1]][Smola_name[0]] = 123
df_tg_base[Amine_name[1]][Smola_name[1]] = -10
df_tg_base[Amine_name[1]][Smola_name[2]] = 185


df_tg_base.to_csv('Tg_base.csv')
df_tg_2 = pd.read_csv('Tg_base.csv', index_col=0)

df_tg_final = pd.DataFrame(df.values*df_tg_base.values, columns=df.columns, index=df.index)

print(df_tg_2)
print('-----------')
print(df_tg_final)

print('ИТОГО:', sum(df_tg_final.sum()))


class BaseAnalyser:
    def __init__(self):

        self.resing_names = []

        self.amine_names = []

        pass
