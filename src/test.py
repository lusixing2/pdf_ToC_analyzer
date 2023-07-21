from Pdf_ToC_analyzer import *


pdf_name1 = '../pdf_files/《中国供销合作社史》_迟孝先著_.pdf'
pdf_name2 = '../pdf_files/Szonyi-2017-The Art of Being Governed_ Everyda.pdf'
pdf_name3 = '../pdf_files/Xie-2017-The Literary Territorialization of Ma.pdf'


ToC_analyzer = Pdf_ToC_analyzer(pdf_name3)


ToC_analyzer.run()
ToC_analyzer.display_ToC()

