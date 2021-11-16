import pandas as pd


if __name__ == '__main__':
    pd.set_option('display.max_columns', None)  # 修改输出限制

    # 读取表格
    df = pd.read_csv("./spider/result.csv", sep='|', encoding='utf-8')

    # 前几行
    print(df.head())

    print('\n---------------------------------\n')

    # 第0行, 答复内容 字段
    print(df.iloc[0]["答复内容"])
