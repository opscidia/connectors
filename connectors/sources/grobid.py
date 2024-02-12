import os, requests


# GROBID Token
GROBID_TOKEN = os.environ.get("GROBID_TOKEN", "grobid")
GROBID_URL = os.environ.get("GROBID_URL", "http://localhost:8070/api/processFulltextDocument")

FILE_SIZE_LIMIT = 1048576000  # ~1000 Megabytes


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


async def pdf_parser(files, doc):
    authors_list = []
    structure = []
    try:
        headers = dict(Accept = 'application/xml')
        response = requests.post(
            GROBID_URL,
            files=files,
            headers=headers,
            timeout=60)
        if response.status_code == 200:
            response_data = response.json()
        else:
            return doc
        authors_json = response_data['header']
        
        
        
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
        print(e)
    
    return doc
                
        