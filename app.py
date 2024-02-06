from flask import Flask, render_template, request

app = Flask(__name__) # 创建服务

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    # 在这里添加你的Python代码，处理Web表单提交的数据
    # 示例：接收表单数据
    input_data = request.form['input_data']

    # 在这里可以调用你的函数或处理数据的代码
    result = 0
    return render_template('result.html', result=result)