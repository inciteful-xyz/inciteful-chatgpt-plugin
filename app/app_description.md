This is a ChatGPT plugin wrapper around the Inciteful API.

Inciteful's primary purpose is to accelerate academic research by providing specialized tools for literature discovery and analysis. Unlike traditional search engines, Inciteful focuses on citations as the cornerstone of its functionality. It aims to help researchers quickly get up to speed on new topics, find the latest literature, and understand how different ideas are connected in the academic landscape.

The main method is through it's Paper Discovery API: This tool builds a network of academic papers based on citations. It then employs network analysis algorithms to sift through this network and provide users with relevant papers, important authors, and institutions in a particular field.

The API itself follows the same structure as the Inciteful API, but with a few minor changes that allow it to be used as a ChatGPT plugin.

The original API is available at https://api.inciteful.xyz

## API inputs
All `paper_id` fields can either be an OpenAlex ID or a DOI.  The API will automatically detect which type of ID is being used and return the appropriate results.

## API Workflow 
Typically 

## Querying the Database API
All endpoints under the `/query` folder accept a parameter named `sql_query`.  This query is submitted to a SQLite database of a local citation network centered around the `paper_id`s submitted. 

### Database Schema
The `papers` table contains all of the papers in the graph

|    Column Name |    Type |                                                                                                                                                    Description |
| -------------: | ------: | -------------------------------------------------------------------------------------------------------------------------------------------------------------: |
|       paper_id | INTEGER |                                                                                                                                    The unique id of the paper. |
|            doi |    TEXT |                                                                                                                              The doi of the paper in question. |
|        authors |    TEXT |                                                                                                                  A json field of all the authors on the paper. |
|          title |    TEXT |                                                                                                                                        The title of the paper. |
| published_year | INTEGER |                                                                                                                              The year the paper was published. |
|        journal |    TEXT |                                                                                                                  The journal in which the paper was published. |
|         volume |    TEXT |                                                                                                    The volume of the journal in which the paper was published. |
|    num_authors | INTEGER |                                                                                                                            The number of authors on the paper. |
|     num_citing | INTEGER |                                                                                                                  The number of papers which this papers cites. |
|   num_cited_by | INTEGER |                                                                                                                    The number of papers which cite this paper. |
|       distance | INTEGER |                                                                              The distance away (as an undirected graph) this paper lies from the `seed paper`. |
|      page_rank |    REAL |                                                                                                                                    The PageRank of this paper. |
|    adamic_adar |    REAL | The Adamic/Adar score of the paper. Adamic/Adar is a link prediction algorithm which, when used in this context, can help to detect similarity between papers. |
|         cocite |    REAL |                                                                      The co-citation score between two papers. We use the Salton Index to calculate the score. |


The `authors` table is a denormalized table containing the metadata about each author for each paper.

| Column Name |    Type |                                                     Description |
| ----------: | ------: | --------------------------------------------------------------: |
|   author_id | INTEGER |                                    The unique id of the author. |
|    paper_id | INTEGER |                                     The unique id of the paper. |
|        name |    TEXT |                                         The name of the author. |
|    sequence | INTEGER |                        The sequence of the author in the paper. |
| affiliation |    TEXT | The affiliation of the author at the time the paper was written |


The `title_search('SEARCH_TERM')` table contains a full text index of the paper titles that can be searched by replacing `SEARCH_TERM` with the query of your choice. You can use Boolean operators like AND, OR, and NOT in addition to parenthesis to create matching logic. An example finding the best match for the term `refugee` is as follows:

`SELECT * FROM title_search('refugee') ORDER BY bm25(title_search)`

The schema for the table is here: 

|        Column Name |    Type |                                                                                                                                             Description |
| -----------------: | ------: | ------------------------------------------------------------------------------------------------------------------------------------------------------: |
|           paper_id | INTEGER |                                                                                                                             The unique id of the paper. |
|              title |    TEXT |                                                                                                                            The text which was searched. |
| bm25(title_search) |    REAL | Returns a real value indicating how well the current row matches the full-text query. The better the match, the numerically smaller the value returned. |
