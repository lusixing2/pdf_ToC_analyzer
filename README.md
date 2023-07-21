# pdf_ToC_analyzer
A Python tool that extract and parse table of contents in PDF file

用 Python 提取 pdf 文档目录信息的工具

使用方法：
1.将openai 的 api_key 复制到/src/config.json 里
2.运行：
```
python main.py -f {pdf_file_path}
```
例如：
```
python main.py -f '../pdf_files/Szonyi-2017-The Art of Being Governed_ Everyda.pdf'
```

效果：
![alt text](https://github.com/lusixing2/pdf_ToC_analyzer/blob/main/imgs/ToC_Analyzer_screenshot1.jpg?raw=true)
