from PyPDF2 import PdfReader
from fuzzywuzzy import fuzz
import re
import openai
import pickle
import json
import os


class Pdf_ToC_analyzer:
    def __init__(self, f_path) -> None:
        self.reader = PdfReader(f_path)
        self.pages_text = []
        self.ToC_liklihood_ratios = []
        self.ToC_text = ""
        self.ToC_data = {}

        f_name = f_path.split('/')[-1]
        # check if buffer already exist
        buffer_path = '../buffer/'+f_name+'.pkl'
        if os.path.exists(buffer_path):
            print('found buffer')
            with open(buffer_path, 'rb') as file:
                self.pages_text = pickle.load(file)

        else:
            for i in range(len(self.reader.pages)):
                print(f"scanning page {i}")
                page_txt = self.reader.pages[i].extract_text()
                self.pages_text.append(page_txt) 

            with open(buffer_path, 'wb') as file:
                pickle.dump(self.pages_text, file)

        print('finished loading page text') 


        try:
            with open('./config.json', "r") as file:
                configs = json.load(file)
        except FileNotFoundError:
            print(f"config.json not found.")
        except json.JSONDecodeError as e:
            print(f"JSON decoding error: {e}")
        
        openai.api_key = configs['api_key']


    # matching method 1, matching by page head
    def locate_section_by_head(self, content_start_idx):
        for chapter in self.ToC_data["chapters"]:
            for section in chapter["sections"]:
                ratios = [0 for i in range(len(self.reader.pages))]
                for i in range(content_start_idx, len(self.reader.pages)):
                    head_text = self.pages_text[i].replace('\n', ' ')[:int(1.2*len(section['section_name']))].lower()
                    ratios[i] = fuzz.ratio(head_text, section['section_name'].lower())
                max_idx = ratios.index(max(ratios))
                max_val = max(ratios)
                if max_val<60:
                    # fail to locate section
                    return False
                else:
                    section_name = section['section_name']
                    #print(f'found section "{section_name}" in page {max_idx}')
                    section['pdf_page'] = max_idx
        return True



#   # matching method 2, matching line by line
    def locate_section_by_line(self, content_start_idx):
        for chapter in self.ToC_data["chapters"]:
            for section in chapter["sections"]:
                found = False
                for i in range(content_start_idx, len(self.reader.pages)):
                    if found:
                        break
                    lines = self.pages_text[i].split('\n')
                    for line in lines:
                        ratio = fuzz.ratio(line.lower(), section['section_name'].lower())
                        if ratio>70:
                            section_name = section['section_name']
                            #print(f'found section "{section_name}" in page {i}')
                            section['pdf_page'] = i
                            found = True
                            break
                if not found:
                    section['pdf_page'] = None
        print('done')            


    # match section names with their real page in pdf using two different methods                   
    def match_sections(self):
        content_start_idx = 0
        for i in range(len(self.ToC_liklihood_ratios)):
            if 0.25 <= self.ToC_liklihood_ratios[i]:
                content_start_idx = i+1

        print(f"content of this book start from {content_start_idx}")
        res1 = self.locate_section_by_head(content_start_idx)
        if not res1:
            print(f'matching by head failed, try mathcing by line')
            self.locate_section_by_line(content_start_idx)


    # find out what pages likely contains table of content                    
    def compute_ToC_likehood_ratio(self):
        ToC_liklihood_ratios = []

        ToC_texts = ""

        for i in range(20):
            page_txt = self.reader.pages[i].extract_text()
            # strip empty lines
            page_txt = re.sub(r'\n\s*\n', '\n', page_txt)

            nums = re.findall(r'\b\d+\s*\n', page_txt)
            N_lines = len(page_txt.strip().split('\n'))

            ToC_ratio = len(nums)/N_lines
            ToC_liklihood_ratios.append(ToC_ratio)

            if 0.25 <= ToC_ratio:
                ToC_texts += page_txt
                print(f'page {i} likely contains ToC')

        self.ToC_text = ToC_texts
        self.ToC_liklihood_ratios = ToC_liklihood_ratios

        return ToC_texts
    


    def Toc_parsing_by_gpt(self, ToC_text):
        print('extracting ToC data from ToC text.......................')
        query1 = """here is a example json data of a book index information:

{"introduction": {"introduction_name": "intro", 
                      "sections": [{"section_name": "sec1",
                                     "page": 3}, 
                                     {"section_name": "sec2", 
                                      "page": 5}]
                      , "page": 2},

     "chapters": [{"chapter_name":"chapter1",
                    "page":10,
                    "sections": [{"section_name": "sec1",
                                     "page": 3}, 
                                     {"section_name": "sec2", 
                                      "page": 5}]}]
  }


extract all the index information from the following text with structure same as the example, some fields are allowed to leave empty, return json object only:

"""
        query = query1 + ToC_text

        while True:
            try: 
                completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo", 
                messages=[{"role": "user", "content": query}]
                )

                #print(completion["choices"][0]["message"]["content"])
                self.ToC_data = json.loads(completion["choices"][0]["message"]["content"])
                return True

            except openai.error.AuthenticationError as e:
                # Handle the incorrect API key error
                print("Invalid API key:", e)
                return False
            except openai.error.OpenAIError as e:
                # Handle other OpenAI API errors
                print("An error occurred:", e)
                print("retrying---------")
            except json.JSONDecodeError as e:
                # Handle the JSON loading error
                print("JSON decoding error:", e)
                print("bad gpt parsing result, retrying")
            

    def run(self):
        # step1: exract the page text that likely contains the table of content
        ToC_texts = self.compute_ToC_likehood_ratio()
        # step2: parse the table of content using gpt
        res = self.Toc_parsing_by_gpt(ToC_texts)
        if not res:
            return
        # step3: match sections to their real page in the pdf file
        self.match_sections()


    def display_ToC(self):
        if len(self.ToC_data)==0:
            print('pls run analyse first')
            return

        print('-'*30)
        for chapter in self.ToC_data["chapters"]:
            chapter_name = chapter["chapter_name"]
            for section in chapter["sections"]:
                section_name = section['section_name']
                book_page = section['page']
                pdf_page = section['pdf_page']

                print(f"{chapter_name} | {section_name} | book_page = {book_page} |  pdf_page = {pdf_page}")
