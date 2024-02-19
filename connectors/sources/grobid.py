import os, requests
import re
from grobid_tei_xml.parse import (
    _string_to_tree,
    _parse_biblio, ns, xml_ns
)
from secrets import token_hex as hex
from typing import Any
from connectors.sources.grobid_services import (
    GrobidDocument,
    GrobidSection,
    GrobidFullText
)


# GROBID Token
GROBID_TOKEN = os.environ.get("GROBID_TOKEN", "grobid")
GROBID_URL = os.environ.get("GROBID_URL", "http://localhost:8070/api/processFulltextDocument")

FILE_SIZE_LIMIT = 1048576000  # ~1000 Megabytes




class GrobidParser:
    
    def __init__(self, *args, **kwargs):
        # self._logger = logger
        pass
    
    @staticmethod
    def build_section_tree(heads: list[tuple[str, str]]) -> list[dict[str, Any]]:
        
        """
        Build sections tree from section heads
        :param heads: list of tuples (section id, section head)
        :return: list of section numbers w\o unknown sections numbered
        """
        section_list = [i[1] for i in heads]
        section_list = [
            re.sub(
                r'[a-zA-Z]', # Convert letters to numbers
                lambda x: str(ord(x.group(0).lower()) - 96),
                section
            ) if not section.startswith('UNK')
            else section
            for section in section_list
        ]
        new_heads = []
        current_section = None
        sub_section_counter = 1

        # Assign numbers to unknown sections
        for section in section_list:
            if section.startswith('UNK'):
                if current_section:
                    new_section = f'{current_section}.{sub_section_counter}'
                    sub_section_counter += 1
                else:
                    new_section = '1'
                while new_section in new_heads + section_list:
                    sub_section_counter += 1
                    new_section = f'{current_section}.{sub_section_counter}'
                new_heads.append(new_section)
            else:
                current_section = section
                sub_section_counter = 1
                new_heads.append(section)

        heads = {sec: h[0] for sec, h in zip(new_heads, heads)}
        sections = []
        stack = []
        
        # Build sections tree
        for section in new_heads:
            section_dict = dict(
                _id = heads[section],
                section = section,
                children = []
            )
            level = section.count('.')
            
            while len(stack) > level:
                stack.pop()
            
            if stack and section.startswith(stack[-1]["section"]):
                stack[-1]["children"].append(section_dict)
            else:
                sections.append(section_dict)
            
            stack.append(section_dict)
        
        return sections



    @staticmethod
    def xml_document(content: str) -> GrobidDocument:
        """
        Parse XML to Grobid document
        :param content: XML document content
        :return: GrobidDocument object
        """
        tree = _string_to_tree(content)
        tei = tree.getroot()

        header = tei.find(f".//{{{ns}}}teiHeader")
        if header is None:
            raise ValueError("XML does not look like TEI format")

        application_tag = header.findall(f".//{{{ns}}}appInfo/{{{ns}}}application")[0]

        doc = GrobidDocument(
            grobid_version=application_tag.attrib["version"].strip(),
            grobid_timestamp=application_tag.attrib["when"].strip(),
            header=_parse_biblio(header),
            pdf_md5=header.findtext(f'.//{{{ns}}}idno[@type="MD5"]'),
        )

        refs = []
        for (i, bs) in enumerate(tei.findall(f".//{{{ns}}}listBibl/{{{ns}}}biblStruct")):
            ref = _parse_biblio(bs)
            ref.index = i
            refs.append(ref)
        doc.citations = refs

        text = tei.find(f".//{{{ns}}}text")

        if text and text.attrib.get(f"{{{xml_ns}}}lang"):
            # this is the 'body' language
            doc.language_code = text.attrib[f"{{{xml_ns}}}lang"]  # xml:lang

        el = tei.find(f".//{{{ns}}}profileDesc/{{{ns}}}abstract")
        doc.abstract = el is not None and " ".join(el.itertext()).strip() or None

        sections, heads = dict(), list()
        for div in tei.findall(f".//{{{ns}}}text/{{{ns}}}body/{{{ns}}}div"):
            _id = hex(5)
            head = div.find(f".//{{{ns}}}head")
            n = head is not None and head.attrib.get("n") or None
            title = head is not None and " ".join(head.itertext()).strip() or "Untitled Section"

            paragraphs = div.findall(f".//{{{ns}}}p")
            bibs = sum([p.findall(f".//{{{ns}}}ref[@type='bibr']") for p in paragraphs], list())

            for bib in bibs:
                target = bib.attrib.get("target", "")
                index = re.sub(r"[^0-9]", "", target).strip()
                index = index.isdigit() and int(index) or None
                if index is None or index >= len(refs):
                    for p in paragraphs:
                        try: p.remove(bib) # Remove invalid bibs if any
                        except: pass
                    continue
                bib.text = f'("{refs[index].title}") '

            text = "\n".join([re.sub(r"\s+", " ", " ".join(p.itertext()).strip()) for p in paragraphs])

            # TODO: Compute real embeddings
            embeddings = list()

            sections[_id] = GrobidSection(
                n=n, title=title,
                content=text,
                embeddings=embeddings
            )
            heads.append((_id, n or "UNK"))
        structure = GrobidParser.build_section_tree(heads)
        doc.fulltext = GrobidFullText(content=sections, structure=structure)
        return doc
    @staticmethod
    def parse_pdf(filename: str) -> GrobidDocument:
        """
        Parse PDF to Grobid document
        :param filename: PDF file path
        :return: GrobidDocument object
        """
        name = filename.rsplit("/")[-1]
        
        if name.endswith(".pdf"):
            f1 = open(filename, "rb")
            files = dict(
                input = (
                    name, f1,
                    'application/pdf',
                    {'Expires': '0'}
                    )
                )

            headers = dict(Accept = 'application/xml')
            response = requests.post(
                GROBID_URL,
                files=files,
                headers=headers,
                timeout=60)
            f1.close()
            if not response.ok:
                response.close()
                return None
            content = response.text
            response.close()

            return GrobidParser.xml_document(content)
        return None


def create_authors(x):
    authors=[]
    for elem in x:
        try:
            if elem['full_name']:
                name = elem['full_name']
            else:
                name=None
        except:
            name=None
        authors.append(name)
        
    return authors

def get_value_nested_dict(d, key):
    for level in key:
        d = d[level]
    return d

def extract_structure(x):
    structure=[]
    for elem in x['structure']:
        structure.append(elem['_id'])
    return structure

def extract_sections(d,names):
    sections=[]
    for name in names:
        key1 = ("content", name, "title")
        title = get_value_nested_dict(d, key1)
        key2 = ("content", name, "content")
        content = get_value_nested_dict(d, key2)
        dictio = {'title':title, 'content':content}
        sections.append(dictio)
    return sections


async def pdf_parser(filename, doc):
    authors_list = []
    structure = []
    try:
        response_data = GrobidParser.parse_pdf(filename)
        if not response_data:
            return doc
        authors_json = response_data['header'].to_dict()
        
        for k, v in authors_json.items():
            if k in ['authors']:
                authors_list = create_authors(v)
        doc["authors"] = authors_list
        
        for k, v in response_data.items():
            if k in ['fulltext']:
                structure = extract_structure(v)
                
        if 'fulltext' in response_data:
           sections_json = response_data['fulltext']
           sections = extract_sections(sections_json, structure)
           doc['sections'] = sections
           
        doc['title'] = authors_json['title'] if 'title' in authors_json else None
        doc['abstract'] = response_data['abstract'] if 'abstract' in response_data else None
    except Exception as e:
        print(f'Error parsing pdf: {e}')
        
    return doc
                
        