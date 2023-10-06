from typing import Any, Dict, List
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from app.inciteful_models import Paper
from .inciteful_client import IncitefulClient

# Get contents of app_description.md
with open("app/app_description.md", "r") as f:
    description = f.read()


tags_metadata = [
    {
        "name": "Papers",
        "description": "Endpoints for getting information about papers",
    },
    {
        "name": "Query",
        "description": "Endpoint for using custom SQL to query the citation network.  Each endpoint returns at most 50 results.",
    },
    {
        "name": "Predefined",
        "description": "Predefined queries for common use cases.  Each endpoint returns at most 50 results.",
    },
]


app = FastAPI(
    title="Inciteful ChatGPT Plugin API",
    description=description,
    version="0.0.1",
    openapi_tags=tags_metadata,
    contact={
        "name": "Inciteful",
        "url": "https://inciteful.xyz",
        "email": "feedback@inciteful.xyz",
    },
    license_info={
        "name": "GNU Affero General Public License v3.0",
        "url": "https://www.gnu.org/licenses/agpl-3.0.en.html",
    },
)

app.mount("/static", StaticFiles(directory="static"), name="static")


inciteful = IncitefulClient()


@app.get(
    "/papers/",
    tags=["Papers"],
    response_model=List[Paper],
    description="Get information about papers.",
)
async def get_papers(
    paper_ids: list[str] = Query(None, description="The ids of the papers to retrieve.")
):
    return inciteful.get_papers(paper_ids)


id_query_description = "The single paper ids to use to build the citation network."
ids_query_description = "The paper ids to use to build the citation network."


@app.get(
    "/search/{query}",
    tags=["Papers"],
    response_model=List[Paper],
    description="Search for papers by title",
)
async def search_papers(
    query: str = Query(None, description="The term used to search the paper titles.")
):
    return inciteful.search_papers(query)


@app.get(
    "/query",
    tags=["Query"],
    response_model=List[Dict[str, Any]],
    description="Query the citation network centered around group of papers.",
)
async def query_citation_network(
    sql_query: str = Query(
        None, description="The sql to query the citation network database."
    ),
    paper_ids: list = Query(
        [], description="The paper ids to use to build the citation network."
    ),
):
    return inciteful.query_multi_paper(paper_ids, sql_query)


similar_query = """
SELECT paper_id, doi, authors, title, journal, adamic_adar + COALESCE(cocite, 0) AS similarity, published_year, num_cited_by
FROM papers p
WHERE {{filters}}
AND (adamic_adar > 0 or cocite > 0)
ORDER BY similarity DESC,  page_rank DESC
"""


@app.get(
    "/pre/similar_papers",
    tags=["Predefined"],
    response_model=List[Dict[str, Any]],
    description="Get papers similar to the submitted papers. The SQL query is: \n"
    + similar_query,
)
async def get_similar_papers(
    paper_ids: list = Query(
        [], description="The paper ids to use to build the citation network."
    ),
):
    return inciteful.query_multi_paper(paper_ids, similar_query)


important_query = """
    SELECT paper_id, doi, authors, title, journal, page_rank, num_cited_by, published_year
    FROM papers p
    WHERE {{filters}}
    ORDER BY page_rank DESC, adamic_adar DESC
"""

important_description = (
    "Get the important papers in the netowrk. The SQL query is: \n" + important_query
)


@app.get(
    "/pre/important_papers",
    tags=["Predefined"],
    response_model=List[Dict[str, Any]],
    description=important_description,
)
async def get_important_papers(
    paper_ids: list = Query(
        [], description="The paper ids to use to build the citation network."
    ),
):
    return inciteful.query_multi_paper(paper_ids, important_query)


review_paper_query = """      
      SELECT paper_id, doi, authors, p.journal, title, p.num_citing, num_cited_by,
      p.published_year
      FROM papers p
      LEFT JOIN (
        SELECT num_citing, published_year, journal, COUNT(*)
        FROM papers p
        WHERE num_citing > 10
        GROUP BY 1, 2, 3
        HAVING COUNT(*) > 8
        ORDER BY 4 DESC
        LIMIT 10
      ) b ON b.num_citing = p.num_citing AND b.published_year = p.published_year AND b.journal = p.journal
      WHERE {{filters}}
      AND b.num_citing IS NULL
      ORDER BY p.num_citing DESC, adamic_adar DESC, num_cited_by DESC
"""

review_description = (
    "Get the likely literature review papers in the netowrk. The SQL query is: \n"
    + review_paper_query
)


@app.get(
    "/pre/review_papers",
    tags=["Predefined"],
    response_model=List[Dict[str, Any]],
    description=review_description,
)
async def get_review_papers(
    paper_ids: list = Query(
        [], description="The paper ids to use to build the citation network."
    ),
):
    return inciteful.query_multi_paper(paper_ids, review_paper_query)


recent_important_author_query = """      
      SELECT p.paper_id, doi, authors, title, journal, num_cited_by, published_year, adamic_adar
      FROM (
        SELECT paper_id
        FROM (
          SELECT name
          FROM authors a
          JOIN papers p ON p.paper_id = a.paper_id
          GROUP BY a.name
          ORDER BY SUM(p.page_rank / (
            CASE 
              WHEN num_authors < 4 THEN num_authors
              WHEN a.sequence = 1 OR a.sequence = num_authors THEN 3
              ELSE num_authors * 3
            END)) DESC
          LIMIT 100
        ) ta 
        JOIN authors a ON a.name = ta.name
        GROUP BY paper_id
      ) a
      JOIN papers p ON p.paper_id = a.paper_id
      WHERE {{filters}}
      AND p.published_year > (strftime('%Y', 'now') - 3)
      ORDER BY adamic_adar DESC, page_rank DESC
"""

recent_important_author_description = (
    "The papers published in the last three years by the top authors. The SQL query is: \n"
    + review_paper_query
)


@app.get(
    "/pre/recent_papers_by_top_authors",
    tags=["Predefined"],
    response_model=List[Dict[str, Any]],
    description=recent_important_author_description,
)
async def get_recent_papers_by_important_authors(
    paper_ids: list = Query([], description=ids_query_description),
):
    return inciteful.query_multi_paper(paper_ids, recent_important_author_query)


most_important_recent_query = """      
      SELECT paper_id, doi, authors, title, journal, page_rank, num_cited_by, published_year
      FROM papers p
      WHERE p.published_year > (strftime('%Y', 'now') - 3)
      AND {{filters}}
      ORDER BY page_rank DESC, adamic_adar DESC
"""

most_important_recent_description = (
    "The most papers published in the last three years as measured by PageRank. The SQL query is: \n"
    + most_important_recent_query
)


@app.get(
    "/pre/most_important_recent_papers",
    tags=["Predefined"],
    response_model=List[Dict[str, Any]],
    description=most_important_recent_description,
)
async def get_most_important_recent_papers(
    paper_ids: list = Query([], description=ids_query_description),
):
    return inciteful.query_multi_paper(paper_ids, most_important_recent_query)


top_authors_query = """      
      SELECT name as author_name, a.author_id, SUM(p.page_rank / (
        CASE 
          WHEN num_authors < 4 THEN num_authors
          WHEN a.sequence = 1 OR a.sequence = num_authors THEN 3
          ELSE num_authors * 3
        END)) as total_page_rank, COUNT(*) as num_papers
      FROM papers p
      JOIN authors a ON p.paper_id = a.paper_id
      GROUP BY a.name, name, a.author_id
      ORDER BY total_page_rank DESC
"""

top_authors_description = (
    "The top authors as defined by the total PageRank of their papers. The SQL query is: \n"
    + top_authors_query
)


@app.get(
    "/pre/top_authors",
    tags=["Predefined"],
    response_model=List[Dict[str, Any]],
    description=top_authors_description,
)
async def top_authors(
    paper_ids: list = Query([], description=ids_query_description),
):
    return inciteful.query_multi_paper(paper_ids, top_authors_query)


upcoming_authors_query = """      
      SELECT name as author_name, SUM(p.page_rank / (
        CASE 
          WHEN num_authors < 4 THEN num_authors
          WHEN a.sequence = 1 OR a.sequence = num_authors THEN 3
          ELSE num_authors * 3
        END)) as total_page_rank, COUNT(*) as num_papers
      FROM papers p
      JOIN authors a ON p.paper_id = a.paper_id
      WHERE {{filters}}
      GROUP BY name
      HAVING MIN(p.published_year) > (strftime('%Y', 'now')) - 10
      ORDER BY total_page_rank DESC
"""

upcoming_authors_description = (
    "This trys to identify upcoming Authors who started publishing in the last 10 years. The SQL query is: \n"
    + upcoming_authors_query
)


@app.get(
    "/pre/upcoming_authors",
    tags=["Predefined"],
    response_model=List[Dict[str, Any]],
    description=upcoming_authors_description,
)
async def upcoming_authors(
    paper_ids: list = Query([], description=ids_query_description),
):
    return inciteful.query_multi_paper(paper_ids, upcoming_authors_query)


top_institutions_query = """      
      SELECT affiliation, SUM(page_rank) as total_page_rank, COUNT(*) as num_papers
      FROM papers p
      JOIN (
        SELECT paper_id, affiliation, affiliation_id
        FROM authors
        GROUP
      BY affiliation_id, affiliation, paper_id
      ) a ON p.paper_id = a.paper_id
      WHERE {{filters}}
      AND a.affiliation <> ''
      AND p.published_year > (strftime('%Y', 'now') - 20)
      GROUP BY  a.affiliation_id, a.affiliation
      ORDER BY SUM(page_rank) DESC
"""

top_institutions_description = (
    "The top institutions in the space. The SQL query is: \n" + top_institutions_query
)


@app.get(
    "/pre/top_institutions",
    tags=["Predefined"],
    response_model=List[Dict[str, Any]],
    description=top_institutions_description,
)
async def top_institutions(
    paper_ids: list = Query([], description=ids_query_description),
):
    return inciteful.query_multi_paper(paper_ids, top_institutions_query)


top_journals_query = """      
      SELECT journal, SUM(page_rank) as total_page_rank, COUNT(*) as num_papers
      FROM papers p
      WHERE {{filters}}
      AND journal <> ''
      AND journal NOT LIKE '%ebook%'
      GROUP BY journal
      ORDER BY SUM(page_rank) DESC
"""

top_journals_description = (
    "The top journals in the citation network. The SQL query is: \n"
    + top_journals_query
)


@app.get(
    "/pre/top_journals",
    tags=["Predefined"],
    response_model=List[Dict[str, Any]],
    description=top_journals_description,
)
async def top_journals(
    paper_ids: list = Query([], description=ids_query_description),
):
    return inciteful.query_multi_paper(paper_ids, top_journals_query)


similar_journals_query = """
    SELECT journal, SUM(COALESCE(adamic_adar, 0) + COALESCE(cocite, 0)) AS similarity, COUNT(*) AS num_papers
    FROM papers p
    WHERE {{filters}}
    AND (adamic_adar > 0 or cocite > 0)
    AND journal <> ''
    AND journal NOT LIKE '%ebook%'
    GROUP BY journal
    ORDER BY similarity DESC,  page_rank DESC
"""


@app.get(
    "/pre/similar_journals",
    tags=["Predefined"],
    response_model=List[Dict[str, Any]],
    description="Get the names of journals which published similar papers. The SQL query is: \n"
    + similar_query,
)
async def similar_journals(
    paper_ids: list = Query(
        [], description="The paper ids to use to build the citation network."
    ),
):
    return inciteful.query_multi_paper(paper_ids, similar_query)
