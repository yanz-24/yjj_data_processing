import pandas as pd
import re
import hashlib
from Constants import MAPPING_NORMAL, MAPPING_INNO_PRIO, COLUMN_NAMES, IN_VITRO_TYPES, DISEASES
from fuzzy_merge import fuzzy_merge_in_vitro, fuzzy_merge_software_device

def generate_ID(df, new_column_name):
    """
    根据产品名称、申请人、日期组成的字符串生成哈希值
    """
    new_df = df.copy()
    df['concatenated_column'] = df.apply(lambda row: ''.join(map(str, row)), axis=1)
    new_df[new_column_name] = df['concatenated_column'].apply(lambda data: hashlib.md5(data.encode()).hexdigest()).astype(str)
    return new_df


def get_mapping(data_source):
    '''
    按照data_source（申请渠道）获取mapping词典
    '''
    if data_source == '创新审批' or data_source == '优先审批':
        return MAPPING_INNO_PRIO
    elif data_source == '常规审批':
        return MAPPING_NORMAL
    else:
        raise ValueError("输入数据来源错误。请从‘创新审批’, ‘常规审批’, ‘优先审批’中选择")
    

def get_df_to_change(df, data_type):
    """
    df提取含有体外诊断试剂、医用软件、临床检验器械的部分，以便后期添加其他信息

    data_type: 体外诊断试剂、医用软件、临床检验器械
    """
    if data_type == "体外诊断试剂":
        # selected_df = df[(df["产品大类"] == "体外诊断试剂") & (df["申请渠道"] != "常规审批")]
        # remaining_df = df[~((df["产品大类"] == "体外诊断试剂") & (df["申请渠道"] != "常规审批"))]
        selected_df = df[df["产品大类"] == "体外诊断试剂"].copy()
        remaining_df = df[~(df["产品大类"] == "体外诊断试剂")].copy()

        # 把用途和方法方法从产品名称中分离出来
        method_list = []
        name_list = []
        usage_list = []
        for index, row in selected_df.iterrows():  
            # method = row["产品名称"].str.extract(r'[(,（](.*?)[),）]')
            name =  row["产品名称"]
            method = re.findall(r'[(,（](.*?)[),）]', name)
            if method:
                method_list.append(method[-1])
                # name = name.replace(f'（{method[-1]}）', '')
                name = re.sub(f'[(,（]{method[-1]}[),）]', '', name) 
            else:
                method_list.append(None)
            usage = [word for word in IN_VITRO_TYPES if word in name]
            if usage:
                usage = max(usage, key=len)  
                name = name.replace(usage, '')
            else:
                usage = None
            name_list.append(name)
            usage_list.append(usage)

        selected_df['被测物质的名称'] = name_list
        selected_df['用途'] = usage_list
        selected_df["方法学"] = method_list
        return selected_df, remaining_df
    
    elif data_type == "医用软件" or data_type == "临床检验器械":
        # df = df.drop('管理类别', axis=1)
        selected_df = df[(df["产品大类"] == data_type) & (df["申请渠道"] != "常规审批")] # 从0开始重新排序
        remaining_df = df[~((df["产品大类"] == data_type) & (df["申请渠道"] != "常规审批"))]
        selected_df = selected_df.reset_index(drop=True)
        return selected_df, remaining_df
    else:
        raise ValueError("输入必须为 体外诊断试剂、医用软件、临床检验器械 中的一个")
        

def get_df_cat(data_type):
    '''
    根据产品大类，获取相对应的分类目录。

    data_type: 体外诊断试剂、医用软件、临床检验器械
    '''
    if data_type == "体外诊断试剂":
        df_in_vitro = pd.read_excel('data/外诊断试剂分类子目录.xls', index_col=0, header=0)
        name_list = [] # 被测物质的名称
        usage_list = [] # 用途
        regulation_list = [] #管理类别

        for index, row in df_in_vitro.iterrows(): #
            regulation = re.findall(r"(\w+-\w+)", row["产品类别"])[0] # 产品类别举例：“Ⅲ-1 与致病性病原体抗原、抗体以及核酸等检测相关的试剂”，我们只需要获得“Ⅲ-1”
            name =  row["产品分类名称"] # 产品分类名称举例：“志贺菌属多价诊断血清”，需要从中提取“志贺菌属”
            usage = [word for word in IN_VITRO_TYPES if word in name] 
            if usage: # 如何有usage
                usage = max(usage, key=len)  # “志贺菌属多价诊断血清”同时满足“多价诊断血清”和 “诊断血清”，我们从中选择最长的，即“多价诊断血清”
                name = name.replace(usage, '') # “志贺菌属多价诊断血清”去掉“多价诊断血清”后剩下的“志贺菌属”就是被测物质的名称
            else:
                usage = None

            usage_list.append(usage)
            name_list.append(name)
            regulation_list.append(regulation)

        df_in_vitro['被测物质的名称2'] = name_list
        df_in_vitro['用途2'] = usage_list
        df_in_vitro["管理类别2"] = regulation_list
        df_in_vitro = df_in_vitro.reset_index(drop=True)
        df_in_vitro.rename(columns={'产品类别':'一级类别', '产品分类名称':'二级类别', '产品描述':'描述'}, inplace=True)
        return df_in_vitro
    
    elif data_type == "医用软件" or data_type == "临床检验器械":
        df_cat = pd.read_excel("data/医疗器械分类目录21和22（2023-手动修改-最终版）.xlsx", sheet_name=data_type) # 分类目录
        df_cat = df_cat.replace('\n', '', regex=True)
        df_cat["分类"] = data_type
        df_cat.rename(columns={'一级产品类别':'一级类别', '二级产品类别':'二级类别', '预期用途':'适用领域'}, inplace=True)
        return df_cat

    else:
        raise ValueError("输入必须为 体外诊断试剂、医用软件、临床检验器械 中的一个")


# 加载三个分类目录
df_in_vitro = get_df_cat("体外诊断试剂")
df_software = get_df_cat("医用软件")
df_clinical_divice = get_df_cat("临床检验器械")


def add_info(df, df_cat, data_type):
    '''
    提取df中的data_type部分，例如只提取df中的“医用软件”相关的数据
    '''
    selected_df, remaining_df = get_df_to_change(df, data_type)     
    df_original_index = selected_df.index

    if data_type == "体外诊断试剂":
        merge = fuzzy_merge_in_vitro(selected_df, df_cat)
    elif data_type == "医用软件" or data_type == "临床检验器械":
        merge = fuzzy_merge_software_device(selected_df, df_cat)
    merge.index = df_original_index
    merge = merge.loc[:,~merge.columns.duplicated()] #去掉重复的列（通常来说只有“管理类别”重复）

    # merge = pd.concat([merge, remaining_df]).sort_index()
    return merge

def find_diseases(row, is_clinical=False):
    '''
    对与某一个产品的检测项目，寻找与之匹配的疾病，并返回疾病名称
    '''
    df_biomarker = pd.read_csv("roche_db/data/biomarker_data_clinical_status_all.tsv", sep='\t', index_col=0)
    if is_clinical: # 只筛选clinical biomarker
        df_biomarker = df_biomarker[df_biomarker["Clinical Status"] == "Clinical"]
    
    if not pd.isnull(row['检测项目']):
        disease_str = []
        for i, df_row in df_biomarker.iterrows():
            if not pd.isnull(df_row["Biomarker"]):
                if df_row["Biomarker"] in row['检测项目']:
                    disease_str.append(df_row["Condition Types Full"])
            if not pd.isnull(df_row["Chinese Name"]):
                if df_row["Chinese Name"] in row['检测项目']:
                    disease_str.append(df_row["Condition Types Full"])
        return ','.join(set(disease_str))
    else:
        return None

def map2db(input_path, output_path, data_source):
    '''
    data_source: '创新审批', '常规审批', '优先审批'
    '''
    # 加载原始文件
    original_df = pd.read_excel(input_path)
    original_df = generate_ID(original_df, '产品ID')
    # 添加新的列
    original_df["申请渠道"] = data_source


    # 给df加上信息
    if data_source == '创新审批' or data_source == '优先审批':
        remaining_df = original_df[~(original_df["产品大类"].isin(["体外诊断试剂", "临床检验器械", "医用软件"]))].copy()
        df1 = add_info(original_df, df_in_vitro, "体外诊断试剂")
        df2 = add_info(original_df, df_software, "医用软件")
        df3 = add_info(original_df, df_clinical_divice, "临床检验器械")
        df = pd.concat([df1, df2, df3, remaining_df]).sort_index() 
        # df.to_excel('test_data/temp2.xlsx')
    elif data_source == '常规审批': #只处理数据，不添加额外信息。例如把体外诊断试剂的产品名称分成3部分。
        a, b = get_df_to_change(original_df, "体外诊断试剂")
        df = pd.concat([a, b]).sort_index()

    # 根据数据来源获取mapping
    mapping = get_mapping(data_source)

    target_df = pd.DataFrame(columns=COLUMN_NAMES)

    # 将映射关系列复制到目标DataFrame
    for original_col, target_col in mapping.items():
        try:
            target_df[target_col] = df[original_col]
        except KeyError as e:
            print(e, "does not exist, skip")


    # 添加疾病领域
    target_df['疾病领域'] = target_df.apply(find_diseases, axis=1)  

    # 统一日期格式为year/month/day
    target_df['发布/批准日期'] = pd.to_datetime(target_df['发布/批准日期']) # 确保日期列是datetime类型

    target_df["发布/批准日期"] = target_df["发布/批准日期"].dt.strftime('%Y/%m/%d')


    try: 
        df1 = pd.read_excel(output_path, engine='openpyxl') #读取原数据文件和表
        with pd.ExcelWriter(output_path, engine='openpyxl', mode='a',if_sheet_exists='overlay') as writer:
            df_rows = df1.shape[0] #获取原数据的行数
            target_df.to_excel(writer, sheet_name='Sheet1',startrow=df_rows+1, index=False, header=False)#将数据写入excel中的aa表,从第一个空行开始写
    except OSError as e:
        print('output file does not exist:', e)
        print('create a new output file.')
        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            # 将df1写入一个名为 'Sheet1' 的表单
            target_df.to_excel(writer, index=False, sheet_name="Sheet1")
