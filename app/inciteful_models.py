from typing import List
from typing import Any
from dataclasses import dataclass
import json

from types import SimpleNamespace


@dataclass
class Institution:
    id: int
    name: str

    @staticmethod
    def from_dict(obj: Any) -> "Institution":
        _id = int(obj.get("id"))
        _name = str(obj.get("name"))
        return Institution(_id, _name)


@dataclass
class Author:
    author_id: float
    name: str
    sequence: int
    position: str
    institution: Institution

    @staticmethod
    def from_dict(obj: Any) -> "Author":
        _author_id = float(obj.get("author_id"))
        _name = str(obj.get("name"))
        _sequence = int(obj.get("sequence"))
        _position = str(obj.get("position"))
        _institution = Institution.from_dict(obj.get("institution"))
        return Author(_author_id, _name, _sequence, _position, _institution)


@dataclass
class Paper:
    id: str
    doi: str
    author: List[Author]
    title: str
    sources: List[object]
    fields_of_study: List[object]
    pdf_urls: List[object]
    published_year: int
    journal: str
    # The ids of the papers that this paper cites
    citing: List[str]
    cited_by: List[str]
    num_citing: int
    num_cited_by: int

    @staticmethod
    def from_dict(obj: Any) -> "Paper":
        _id = str(obj.get("id"))
        _doi = str(obj.get("doi"))
        _author = [Author.from_dict(y) for y in obj.get("author")]
        _title = str(obj.get("title"))
        _sources = [y for y in obj.get("sources")]
        _fields_of_study = [y for y in obj.get("fields_of_study")]
        _pdf_urls = [y for y in obj.get("pdf_urls")]
        _published_year = int(obj.get("published_year"))
        _journal = str(obj.get("journal"))
        _citing = [y for y in obj.get("citing")]
        # The ids of the papers that cite this paper
        _cited_by = [y for y in obj.get("cited_by")]
        _num_citing = int(obj.get("num_citing"))
        _num_cited_by = int(obj.get("num_cited_by"))
        return Paper(
            _id,
            _doi,
            _author,
            _title,
            _sources,
            _fields_of_study,
            _pdf_urls,
            _published_year,
            _journal,
            _citing,
            _cited_by,
            _num_citing,
            _num_cited_by,
        )


# Example Usage
# jsonstring = json.loads(myjsonstring)
# root = Root.from_dict(jsonstring)
