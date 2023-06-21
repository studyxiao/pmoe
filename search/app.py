import json
from pathlib import Path

import meilisearch
from meilisearch.errors import MeilisearchApiError

try:
    client = meilisearch.Client("http://localhost:7700", "master")
except MeilisearchApiError as e:
    print(e)
    raise


index = client.index("movies")

# https://www.meilisearch.com/docs/reference/api/settings
index.update_filterable_attributes(["title", "genres"])  # 允许过滤的属性
index.update_sortable_attributes(["title"])  # 允许排序的属性
index.update_stop_words(["of", "the"])  # 停用词(过滤掉)
index.update_pagination_settings({"maxTotalHits": 500})  # 限制搜索结果的数量

# 中文同义词 https://github.com/jaaack-wang/Chinese-Synonyms
synon = Path(__file__).parent / "resource/synonyms.json"
with synon.open() as f:
    res = json.load(f)
    index.update_synonyms(res)  # 同义词

index.update_ranking_rules(
    [
        "words",  # 根据匹配数量
        "typo",  # 拼写错误的在后
        "proximity",  # 查询词之间的距离
        "attribute",
        "sort",  # 查询时指定排序
        "exactness",  # 相似度排序
    ]
)
# 查看设置
settings = index.get_settings()
print(settings)

documents = [
    {"id": 1, "title": "Carol", "genres": ["Romance", "Drama"]},
    {"id": 2, "title": "Wonder Woman", "genres": ["Action", "Adventure"]},
    {"id": 3, "title": "Life of Pi", "genres": ["Adventure", "Drama"]},
    {
        "id": 4,
        "title": "Mad Max: Fury Road",
        "genres": ["Adventure", "Science Fiction"],
    },
    {"id": 5, "title": "Moana", "genres": ["Fantasy", "Action"]},
    {"id": 6, "title": "Philadelphia", "genres": ["Drama"]},
]

# 添加数据
task = index.add_documents(documents)

while (status := client.get_task(task.task_uid).status) != "succeeded":
    import time

    print(status)
    print("waiting for indexation")
    time.sleep(1)
print("indexation done")

# 查询
# https://www.meilisearch.com/docs/reference/api/search#search-parameters
res = index.search(
    "caorl",
    {
        "limit": 2,  # 限制返回的结果数量
        "offset": 0,  # 跳过前面的结果
        "attributesToRetrieve": ["title"],  # 仅返回指定的属性
        "hitsPerPage": 2,  # 限制每页数量
        "page": 1,  # 页码从开始
        "attributesToHighlight": ["title"],  # 高亮指定的属性
        "attributesToCrop": ["title"],  # 截断指定的属性
        "cropLength": 10,  # 截断长度
        "filter": "genres = Action",  # 过滤,必须是可过滤的属性
        "sort": ["title:desc"],  # 排序,必须是可排序的属性
    },
)  # 具有容错能力 carol
print(res)

# 删除
index.delete_document(1)  # 删除指定的文档
index.delete_documents([1, 2, 3])  # 删除指定的文档
index.delete_documents({filter: "genres=action OR genres=adventure"})  # 按条件删除
index.delete_all_documents()  # 删除所有
# WARNING 删除 index
index.delete()

# 更新文档
index.update_documents(documents)  # 更新
index.add_documents(documents)  # 当id存在时更新,不存在时添加
