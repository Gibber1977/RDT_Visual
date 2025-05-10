- 本项目是RDT项目的子项目，主要用于结果可视化的分享与保存
- 原项目可见：[Gibber1977/Reverse_Distill_Training](https://github.com/Gibber1977/Reverse_Distill_Training)

## 项目依赖

本项目主要使用 Python 语言编写，并依赖以下库：

- Flask
- Pandas
- NumPy
- Matplotlib
- Seaborn

## 依赖安装

您可以使用 pip 来安装这些依赖。建议在虚拟环境中进行安装：

```bash
# 创建并激活虚拟环境 (可选但推荐)
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 安装依赖
pip install Flask pandas numpy matplotlib seaborn
```

## 如何运行

1.  确保所有依赖已正确安装。
2.  进入 `visual` 目录。
3.  运行 Flask 应用：

    ```bash
    cd visual
    python app.py
    ```

4.  在浏览器中打开显示的地址 (通常是 `http://127.0.0.1:5000/`) 来查看可视化结果。

## 项目结构

- `README.md`: 本说明文件
- `results/`: 存放原始实验数据的目录
    - `collected_partial_summary.csv`: 汇总的实验结果数据
- `visual/`: 可视化应用代码目录
    - `app.py`: Flask 应用主文件
    - `data_processor.py`: 数据处理模块
    - `plotter.py`: 绘图模块
    - `static/`: 静态文件目录
        - `css/style.css`: 应用的 CSS 样式文件
        - `images/plots/`: 生成的图表存放目录
    - `templates/`: HTML 模板目录
        - `base.html`: 基础 HTML 模板
        - `index.html`: 主页 HTML 模板