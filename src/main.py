from Pdf_ToC_analyzer import *
import argparse
import os

def main():
    parser = argparse.ArgumentParser(description='Cli entrance of pdf ToC Analyzer with argparse.')

    parser.add_argument('-f', '--file', help='Specify a pdf path you want to analyze.')
    args = parser.parse_args()

    if args.file:
        if not os.path.exists(args.file):
            print("File not exist")
            return 0
        else:
            ToC_analyzer = Pdf_ToC_analyzer(args.file)
            ToC_analyzer.run()
            ToC_analyzer.display_ToC()


if __name__ == '__main__':
    main()