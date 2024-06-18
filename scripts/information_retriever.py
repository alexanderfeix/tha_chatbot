import json
import os
import re
from typing import List, Dict
from urllib.parse import urljoin

import fitz  # PyMuPDF
import requests
from bs4 import BeautifulSoup
from tabulate import tabulate
from transformers import AutoTokenizer

"""
This is a helper file to retrieve data from websites and optionally organize it in chunks.
The data is usually stored in a JSON file in the data folder.
"""


def get_websites(filepath: str) -> List[Dict[str, str]]:
    with open(filepath) as file:
        data = json.load(file)
    return data


class WebsiteRetriever:
    def __init__(self, data_folder_path: str, website_file: str = "websites.json"):
        """
        Website Retriever initialization
        :param data_folder_path: path to the folder containing the websites.json file and the PDF files
        :param website_file: set the filename, only alternative
        """
        self.data_folder_path = data_folder_path
        self.websites = get_websites(os.path.join(data_folder_path, website_file))
        self.structured_data = []
        self.unstructured_data = []
        self.tokenizer = AutoTokenizer.from_pretrained("intfloat/multilingual-e5-large")

    def extract_text_from_url(self, response: str, url: str):
        """
        Extract text from the response of a webpage and return it as a string.
        :param response: plain text of the website
        :param url: corresponding url to the website
        """

        # replace the javascript text with empty string because cannot render page with javascript before extracting
        soup = BeautifulSoup(response.replace("[Bitte aktivieren Sie Javascript]", ""), 'html.parser')

        # Remove script, style, and image tags
        for script in soup(["script", "style", "img"]):
            script.extract()

        # Extract title from header section
        header = soup.find('header')
        title = ''

        # Build title from last two header ul items
        ul = header.find('ul') if header else None
        if ul:
            ul_items = [li.get_text(strip=True) for li in ul.find_all('li')][-2:]
            title += ' - '.join(ul_items) + ' '

        if title == '':  # if no title included in ul items
            title += header.find('h1').get_text() if header and header.find('h1') else ''

        # Skip collecting information from header
        if header:
            header.decompose()

        # Remove navigation elements
        for nav_element in soup.find_all(['nav', 'article']):
            nav_element.decompose()

        # Extract text and hyperlinks
        text_with_links = ""

        content = []
        for element in soup.find_all(
                ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'table', 'a', 'td', 'th', 'tr']):
            text = ""
            if element.name in ['p', 'ul', 'ol']:  # text paragraphs, unordered lists, ordered lists
                if element.name == 'ul':
                    text = "\n".join([f"- {li.get_text(strip=True)}" for li in element.find_all('li')])
                elif element.name == 'ol':
                    text = "\n".join(
                        [f"{i + 1}. {li.get_text(strip=True)}" for i, li in enumerate(element.find_all('li'))])
                else:
                    text += element.get_text(separator=' ', strip=True)

                if text.strip() == "":  # continue for empty paragraphs/lists
                    continue
                # Extract hyperlinks and replace text with markdown links
                text = self.retrieve_hyperlinks(url, element, text)
                content.append(text)

            elif element.name in ['h1', 'h2', 'h3']:  # headings
                text += element.get_text(separator=' ', strip=True)
                if text.strip() == "":  # continue for empty paragraphs
                    continue
                text = self.retrieve_hyperlinks(url, element, text)
                content.append(f"\n{text}:")

            elif element.name in ['h4', 'h5', 'h6']:  # smaller heading sizes
                text += element.get_text(separator=' ', strip=True)
                if text.strip() == "":  # continue for empty paragraphs
                    continue
                text = self.retrieve_hyperlinks(url, element, text)
                content.append(f"{text}:")

            elif element.name in ['table']:  # tables
                if self.render_table(element, title):  # render table only if it doesnt contain paragraphs
                    table_data = []
                    for row in element.find_all('tr'):
                        row_data = [cell.get_text(strip=True) for cell in row.find_all(['th', 'td'])]
                        table_data.append(row_data)
                    table_str = tabulate(table_data, headers="firstrow", tablefmt="simple")
                    content.append(table_str)

        text_with_links += "\n".join(content)
        return text_with_links, title

    def retrieve_hyperlinks(self, url: str, element, text: str):
        """
        Extract hyperlinks from the element and replace the text with Markdown links.
        """
        links = [(link.get('href'), link.text) for link in element.find_all('a') if link.get('href')]
        for link, link_text in links:
            if "+49" in link_text or link_text == "":  # skip javascript links and phone numbers
                continue
            text = text.replace(link_text, f" [{link_text}]({urljoin(url, link)})")
        return text

    def render_table(self, table, title):
        p = table.find_all('p')
        if p and ("Directions" not in title and "Semestertermine " not in title):
            return False
        return True

    def tokenize(self, text):
        return self.tokenizer.tokenize(text)

    def chunk_text(self, text, title, max_tokens=500):
        """
        Split text into chunks according to paragraph breaks.
        It is not splitting paragraphs, so it could appear that the length is longer than max_tokens.
        This will be handled by another chunking step in the pipeline.
        Also appends the title to the beginning of each chunk.
        """
        chunks = []
        current_chunk = ""
        current_tokens = 0
        len_title = len(self.tokenize(title))

        paragraphs = text.split('\n\n')  # Split text into paragraphs
        for p in paragraphs:
            tokens = self.tokenize(p)
            if current_tokens + len(tokens) <= max_tokens - len_title:
                current_chunk += p + '\n'
                current_tokens += len(tokens)
            else:
                if current_chunk.strip():
                    chunks.append(f"{title}\n{current_chunk}".strip().replace("\r\n\r\n", ""))
                current_chunk = p + '\n'
                current_tokens = len(tokens)

        current_chunk = current_chunk.strip()

        if current_chunk and current_chunk != title.strip():
            chunks.append(f"{title}\n{current_chunk}".strip().replace("\r\n\r\n", ""))

        return chunks

    def get_data(self, pdf_included=True) -> List:
        """
        Extracts the text from the websites and returns them as a list of dictionaries with the title, text, and url.
        Optionally extracts information from PDF files.
        """
        for raw_document in self.websites:
            url = raw_document["url"]
            try:
                response = requests.get(url)
                title_json = raw_document["title"]
                if response.status_code == 200:
                    text, title = self.extract_text_from_url(response.text, url)
                    chunks = self.chunk_text(text, title)

                    for chunk in chunks:
                        self.structured_data.append(
                            {
                                "title": title,
                                "text": str(chunk),
                                "url": url,
                            })
                    print(f"Information from '{title_json}' extracted and saved successfully.")
                else:
                    print(f"Failed to retrieve information from '{url}'. Status code: {response.status_code}")
            except Exception as e:
                print(f"An error occurred while processing '{url}': {e}")

        if pdf_included:  # Extract information from PDF files
            pdf_retriever = PDFRetriever(os.path.join(self.data_folder_path, 'pdfs'))
            pdf_contents = pdf_retriever.process_pdfs()

            for doc_title, sections in pdf_contents.items():
                try:  # chunk all sections of the document
                    for section_title, text in sections.items():
                        chunks = self.chunk_text(text, doc_title)
                        for chunk in chunks:
                            title = f"{doc_title} - {section_title}"
                            self.structured_data.append(
                                {
                                    "title": title,
                                    "text": str(chunk),
                                    "url": "",
                                })
                    print(f"Information from '{doc_title}' extracted and saved successfully.")
                except Exception as e:
                    print(f"An error occurred while processing '{doc_title}': {e}")
        return self.structured_data


class PDFRetriever:

    def __init__(self, folder_path):
        """
        Extracts the content of PDF files
        :param folder_path: path to the folder containing the PDF files
        """
        self.folder_path = folder_path
        self.pdf_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.pdf')]

    def extract_title(self, file_path) -> str:
        return os.path.splitext(os.path.basename(file_path))[0]

    def extract_sections(self, doc) -> Dict[str, str]:
        """
        Extracts the sections from a PDF document based on first two levels of table of content and returns them as a dictionary.
        """
        toc = doc.get_toc(simple=True)
        sections = {}

        level_1_header = ""  # store the current level 1 headline to include it later for more context
        for i, (level, title, page_num) in enumerate(toc):
            if level <= 2:  # only extract first two levels
                if title not in sections:
                    sections[title] = ""

                if level == 1:  # store the current level 1 headline
                    level_1_header = title

                # find next chapter to determine the end of the current section
                next_page_num = self.find_next_chapter(toc, i)[2] \
                    if self.find_next_chapter(toc, i) != -1 else doc.page_count - 1

                section_text = ""  # store the text of the determined pages
                for page in range(page_num - 1, next_page_num):
                    section_text += doc.load_page(page).get_text()

                # filter the text of the current section to only receive the text of the current section
                section_text = self.filter_text_section(section_text, toc, i)

                # if section has no text, skip it
                if section_text.strip() == title.strip():
                    continue

                sections[title] += f"{level_1_header}\n{section_text}"

        # remove empty sections
        sections = {title: text for title, text in sections.items() if text.strip()}
        return sections

    def find_next_chapter(self, toc, index):
        """
        Finds the next chapter in the table of content based on the current index. Because only the first two levels are extracted, all the other levels will be skipped.
        """
        curr_level = toc[index][0]
        index += 1
        while index < len(toc) and toc[index][0] > curr_level:
            index += 1
        if index == len(toc):
            return -1
        return toc[index]

    def filter_text_section(self, section_text, toc, index):
        """
        Filters the text of the current section to only include the text of the current section and not the text of the next or previous chapter.
        """
        current_title = toc[index][1]
        next_title = toc[index + 1][1] if index + 1 < len(toc) else None

        if toc[index][0] == 2:  # Add new lines before each subchapter (level 3 or higher)
            new_index = index + 1
            section_text_list = list(section_text)
            # search for subchapters using the table of content
            while new_index < len(toc) and toc[new_index][0] > 2:
                pattern_subchapters = re.compile(re.escape(toc[new_index][1].strip()), re.MULTILINE)
                match = pattern_subchapters.search(section_text)
                if match:
                    section_text_list.insert(match.start(), '\n\n')  # Insert two new lines before subchapter
                new_index += 1
            section_text = ''.join(section_text_list)

            # find text before current chapter
            pattern_chapter = re.compile(re.escape(current_title.strip()), re.MULTILINE)
            match = pattern_chapter.search(section_text)

            # find text after current chapter
            next_chapter = self.find_next_chapter(toc, index)[1] if self.find_next_chapter(toc, index) != -1 else None
            if next_chapter:
                pattern_next_chapter = re.compile(re.escape(next_chapter.strip()), re.MULTILINE)
                match_next_chapter = pattern_next_chapter.search(section_text)
                if match:  # shorten text before current chapter
                    section_text = section_text[match.start():]
                    if match_next_chapter:  # shorten text if next chapter is found
                        section_text = section_text[:match_next_chapter.start()]
        elif next_title:  # exclude text of next chapter
            pattern_subchapters = re.compile(re.escape(next_title.strip()), re.MULTILINE)
            match = pattern_subchapters.search(section_text)
            if match:
                section_text = section_text[:match.start()]

        return section_text

    def save_sections(self, title, sections):
        """
        Saves the sections of a PDF document in separate text files in a folder with the title of the document.
        """

        output_folder = os.path.join(self.folder_path, title.replace(' ', '_'))
        os.makedirs(output_folder, exist_ok=True)
        for section_title, text in sections.items():
            filename = f"{section_title.replace(' ', '_')}.txt"
            file_path = os.path.join(output_folder, filename)
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(text.strip())

    def process_pdfs(self) -> Dict[str, Dict[str, str]]:
        """
        Extracts the text from all PDF files in the folder and returns them as a dictionary with the title as key and the dict of sections as value.
        """
        all_docs = {}
        for pdf_file in self.pdf_files:
            with fitz.open(pdf_file) as doc:
                title = self.extract_title(pdf_file)
                sections = self.extract_sections(doc)
                all_docs[title] = sections
        return all_docs
