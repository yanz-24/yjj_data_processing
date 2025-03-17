# 使用说明

```python
import sys  
sys.path.append('D:/Roche/code/roche_db')

from roche_db.data_processing import map2db


output_path = 'test_data/temp.xlsx' # output可以是一个新文件，可以是原来的DB

input_path = '../data/MD/xxx.xlsx'
map2db(input_path, output_path, '常规审批')

# input_path = '../data/MD/创新2022.xlsx'
# map2db(input_path, output_path, '创新审批')

# input_path = '../data/MD/优先审批_20230919173353_1595699578026229761.xls'
# map2db(input_path, output_path, '优先审批')

# input_path = '../data/MD/创新审批_20230907_MD.xls'
# map2db(input_path, output_path, '创新审批')
```
