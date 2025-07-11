

# class FilmQuery(IDocumentQuery[Film]):

#     client: kuzu.Database
#     settings: Settings

#     def __init__(
#         self,
#         settings: Settings,
#     ):

#         self.settings = settings
#         self.client = kuzu.Database(settings.db_persistence_directory)

#     def query(
#         self,
#         query: str,
#         params: dict = None,
#         *args,
#         **kwargs,
#     ) -> list[Film]:
#         """
#         Execute a query against the graph database and return the results.

#         Args:
#             query (str): The query to execute.
#             params (dict, optional): Parameters for the query.

#         Returns:
#             list[dict]: A list of dictionaries representing the query results.
#         """
#         conn = kuzu.Connection(self.client)
#         if params is None:
#             params = {}

#         try:
#             result = conn.execute(query, params)
#             return [row for row in result]
#         except kuzu.KuzuError as e:
#             logger.error(f"Query execution failed: {e}")
#             raise
