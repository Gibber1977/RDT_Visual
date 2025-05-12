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
    python -m visual.app
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

## 生成静态网站并部署到 GitHub Pages

除了运行 Flask 应用动态查看结果外，您还可以生成静态网站文件，并将其部署到 GitHub Pages 等静态网站托管服务上。

1.  **确保已安装依赖**：运行静态网站生成脚本需要与运行 Flask 应用相同的依赖。请按照上面的“依赖安装”步骤确保所有依赖已安装。
2.  **运行生成脚本**：在项目根目录下执行 `generate_static.py` 脚本：

    ```bash
    python generate_static.py
    ```

    这个脚本会读取数据，生成包含结果表格的静态 HTML 文件，并将所有静态资源（CSS、图片等）复制到一个名为 `docs` 的目录中。
3.  **部署到 GitHub Pages**：
    *   将您的项目（包括新生成的 `docs` 目录）推送到 GitHub 仓库。
    *   在您的 GitHub 仓库页面，进入 "Settings" -> "Pages"。
    *   在 "Source" 部分，选择您用于部署的分支（例如 `main` 或 `master`），并选择 `/docs` 文件夹作为静态网站的来源。
    *   点击 "Save"。GitHub Pages 将自动构建并部署您的网站。部署完成后，您将在该页面看到网站的访问链接。

通过这种方式，您可以方便地分享您的实验结果可视化页面，而无需运行一个完整的 Flask 服务器。