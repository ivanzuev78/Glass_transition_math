import numpy as np
import pandas as pd


Epoxy_name = ["KER-828", "LaprBD", "YDPN-638"]
Epoxy = np.array([0.8, 0.2, 0])
Amine_name = ["IPDA", "MXDA", "PACM"]
Amine = np.array([0.5, 0.4, 0.1])

# Amin = np.array([1,2,3])
# c = np.outer(Epoxy, Amine)
#
# print(Epoxy, Amine, c, sep='\n')

def normalize(array: np.array):
    return array / sum(array)

df = pd.DataFrame(
    np.outer(Epoxy, Amine),
    index=Epoxy_name,
    columns=Amine_name,
)
# df.columns = Amine_name
# df.rename({ i:Epoxy_name[i] for i in range(len(Epoxy_name))})
print(df)
print("-------------")
# print(Amine_name[1], '+', Epoxy_name[2], df[Amine_name[1]][Epoxy_name[2]])


df_tg_base = pd.DataFrame(index=Epoxy_name, columns=Amine_name)

df_tg_base[Amine_name[0]][Epoxy_name[0]] = 148
df_tg_base[Amine_name[0]][Epoxy_name[1]] = -10
df_tg_base[Amine_name[0]][Epoxy_name[2]] = 165
df_tg_base[Amine_name[1]][Epoxy_name[0]] = 123
df_tg_base[Amine_name[1]][Epoxy_name[1]] = -10
df_tg_base[Amine_name[1]][Epoxy_name[2]] = 185


df_tg_base.to_csv("Tg_base.csv")
df_tg_2 = pd.read_csv("Tg_base.csv", index_col=0)

df_tg_final = pd.DataFrame(
    df.values * df_tg_base.values, columns=df.columns, index=df.index
)

print(df_tg_2)
print("-----------")
print(df_tg_final)

print("ИТОГО:", sum(df_tg_final.sum()))


class BaseAnalyser:
    def __init__(self):

        self.resing_names = []

        self.amine_names = []

        pass
