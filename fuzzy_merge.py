from fuzzywuzzy import fuzz, process
import pandas as pd

def __fuzzy_compare_one(list_ex:str, query:str):
    '''
    一个产品名称与一个品名举例比较
    '''
    list_ratio = []
    list_ex = list_ex.split("、")
    
    for ex in list_ex:
        ratio = fuzz.ratio(query, ex)  
        list_ratio.append(ratio)
    
    m = max(list_ratio)
    i = list_ratio.index(m)
    return m, list_ex[i]

def __fuzzy_compare_all(list_ex:list, query:str):
    '''
    一个产品名称与所有的品名举例比较
    '''
    list_ratio = []
    list_best_name = []
    for i in list_ex:
        ratio, name = __fuzzy_compare_one(i, query)
        list_ratio.append(ratio)
        list_best_name.append(name)

    m = max(list_ratio)
    i = list_ratio.index(m)
    if m < 50:
        return (None, None, len(list_ex))
    else:
        return m, list_best_name[i], i
    

def fuzzy_merge_software_device(df, df_cat):
    """
    医用软件、临床检验器械
    """
    df[['fuzzy_ratio', 'best_match', 'index_cat']] = df['产品名称'].apply(lambda x: pd.Series(__fuzzy_compare_all(df_cat['品名举例'], x)))

    # add an empty row to df_cat
    df_cat_copy = df_cat.copy() # 创造一个copy，避免修改了df_cat
    new_row = [None] * len(df_cat_copy.columns)
    df_cat_copy.loc[len(df_cat_copy.index)] = new_row

    # reorder df_cat
    index_list = df['index_cat']
    reordered_df_cat = df_cat_copy.iloc[index_list].reset_index(drop=True)

    # merge two df
    df_merge = pd.concat([df, reordered_df_cat], axis=1)
    return df_merge


def fuzzy_merge_in_vitro(df, df_cat):
    """
    体外诊断试剂
    """
    df[['best_match', 'fuzzy_ratio', 'index_cat']] = df['被测物质的名称'].apply(
        lambda x: pd.Series(process.extractOne(x, df_cat['被测物质的名称2'], scorer=fuzz.partial_ratio)) # scorer=fuzz.partial_ratio
        )
    df = df.reset_index(drop=True)  


    # add an empty row to df_cat
    df_cat_copy = df_cat.copy() # 在函数内部创建 df_cat 的副本，避免直接修改df_cat
    new_row = [None] * len(df_cat_copy.columns) # 创建一个空白行
    df_cat_copy.loc[len(df_cat_copy)] = new_row

    # 对于ratio < 80的值，将该行设为全是None的行
    df.loc[df['fuzzy_ratio'] < 80, "index_cat"] = len(df_cat_copy.index) - 1 

    # reorder df_cat
    index_list = df['index_cat']
    reordered_df_cat = df_cat_copy.iloc[index_list].reset_index(drop=True)

    # concat two df
    df_merge = pd.concat([df, reordered_df_cat], axis=1)
    return df_merge