#
from graphqlclient import GraphQLClient

client = GraphQLClient("http://localhost:4000")

collectors_query = """
{
  collectors{
      id
      name
  }
}
"""

insert_collector_query = """
mutation InsertCollector($data: CollectorCreateInput!){
    insertCollector(data: $data){
        id
        name
        description
    }
}
"""

insert_record_query = """
mutation InsertRecord($data: InsertRecordInput!){
    insertRecord(data: $data){
        id
    }
}
"""
collector_data = {"data": {"name": "something", "description": "something"}}
record_connect_data = {
    "data": {
        "temperature": 1,
        "pressure": 1,
        "humidity": 1,
        "light": 1,
        "reducing": 1,
        "oxidising": 1,
        "nh3": 1,
        "pm1": 1,
        "pm2_5": 1,
        "pm10": 1,
        "noise": 1,
        "collector": {"connect": {"id": 1}},
    }
}
result = client.execute(insert_collector_query, collector_data)

print(result)

# # https://gist.github.com/gbaman/b3137e18c739e0cf98539bf4ec4366ad
# import requests


# def run_query(query, variables, headers):
#     req = requests.post(
#         "http://localhost:4000",
#         json={"query": query, "variables": variables},
#         headers=headers,
#     )
#     if req.status_code == 200:
#         return req.json()
#     else:
#         raise Exception(
#             "Query failed to run  by returning status code {}. {}".format(
#                 req.status_code, query
#             )
#         )


# headers = {"Authorization": "Bearer YOUR API KEY"}
# # query = """
# # {info}
# # """
# variables = {"name": "foo bah baz", "description": "something"}
# query = """
#   mutation InsertCollector ($data: CollectorCreateInput){
#     insertCollector(data: $data){
#         id
#         name
#     }
#   }
# """
# results = run_query(query, variables, headers)
# print(results)
