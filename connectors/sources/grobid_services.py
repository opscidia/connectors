from dataclasses import dataclass, field
from grobid_tei_xml.types import (
    GrobidDocument as BaseDocument
)
from ninja import Schema, Field
from typing import Optional, Any




@dataclass
class GrobidSection:
    title: str
    content: str
    n: Optional[str] = None
    embeddings: Optional[list[float]] = field(default_factory=list)

class Section(Schema):
    title: str
    content: Optional[str] = None
    n: Optional[str] = None
    embeddings: Optional[list[float]] = Field(
        [],
        description="Section embeddings"
    )




@dataclass
class GrobidFullText:
    content: dict[str, GrobidSection]
    structure: list[dict[str, Any]]

class FullText(Schema):
    content: dict[str, Section]
    structure: list[dict[str, Any]] = Field(
        [],
        description="Full text structure"
    )




@dataclass
class GrobidDocument(BaseDocument):
    fulltext: Optional[GrobidFullText] = None




class Address(Schema):
    addr_line: Optional[str] = None
    post_code: Optional[str] = None
    settlement: Optional[str] = None
    country: Optional[str] = None




class Affiliation(Schema):
    institution: Optional[str] = None
    department: Optional[str] = None
    laboratory: Optional[str] = None
    address: Optional[Address] = None




class Author(Schema):
    full_name: Optional[str]
    given_name: Optional[str] = None
    middle_name: Optional[str] = None
    surname: Optional[str] = None
    email: Optional[str] = None
    orcid: Optional[str] = None
    affiliation: Optional[Affiliation] = None




class Biblio(Schema):
    authors: list[Author]
    index: Optional[int] = None
    id: Optional[str] = None
    unstructured: Optional[str] = None

    date: Optional[str] = None
    title: Optional[str] = None
    book_title: Optional[str] = None
    series_title: Optional[str] = None
    editors: Optional[list[Author]] = None
    journal: Optional[str] = None
    journal_abbrev: Optional[str] = None
    publisher: Optional[str] = None
    institution: Optional[str] = None
    issn: Optional[str] = None
    eissn: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    first_page: Optional[str] = None
    last_page: Optional[str] = None
    note: Optional[str] = None

    doi: Optional[str] = None
    pmid: Optional[str] = None
    pmcid: Optional[str] = None
    arxiv_id: Optional[str] = None
    pii: Optional[str] = None
    ark: Optional[str] = None
    istex_id: Optional[str] = None
    url: Optional[str] = None




class Document(Schema):
    header: Biblio = Field(
        ...,
        description="Bibliographical metadata extracted from the document"
    )
    pdf_md5: Optional[str] = Field(
        None,
        description="MD5 checksum of the PDF file, if available"
    )
    language_code: Optional[str] = Field(
        None,
        description="ISO 639-1 language code of the full text, if available"
    )
    citations: Optional[list[Biblio]] = Field(
        None,
        description="List of bibliographical references extracted from the document"
    )
    abstract: Optional[str] = Field(
        None,
        description="Document abstract"
    )
    fulltext: Optional[FullText] = Field(
        None,
        description="Structured Full text of the document"
    )
    acknowledgement: Optional[str] = Field(
        None,
        description="Acknowledgement section of the document"
    )
    annex: Optional[str] = Field(
        None,
        description="Annex/Appendix section of the document"
    )