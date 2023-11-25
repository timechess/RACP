# How to crawl arXiv papers

Here is an example to download data from arXiv using `racp`.

If you want to download all arXiv papers in the field cs.IR from 2021-2023, then you first need all the ids of targeted papers. You can get these ids using `racp.crawl.get_ids`.

Here is an example:
```python
from racp.crawl import get_ids

get_ids(
    3, # from 2023-3+1=2021 to 2023
    [cs.IR],
    "./data", # The path to save data
)
```

It will take a long time, which relates to the number of the papers. If everything goes well, there will be a `data/targets.json` in your current directory, which contains all the arXiv paper ids you need to download. Let's say you load it in a variable `target_ids`, which is a `List[Str]`. Then you can use the `racp.crawl.download` to crawl data.
```python
from racp.crawl import download

download(
    target_ids,
    "./data"
)
```

It will create `data/data` directory to save data. You can change the save path by changing the parameter. Here is an example of the data file:
```json
{
    "Published": "2021-01-20",
    "Title": "Open-Domain Conversational Search Assistant with Transformers",
    "Authors": "Rafael Ferreira, Mariana Leite, David Semedo, Joao Magalhaes",
    "Summary": "Open-domain conversational search assistants aim at answering user questions\nabout open topics in a conversational manner....",
    "Content": "Open-Domain Conversational Search Assistant\nwith Transformers\nA Preprint\nRafael Ferreira, Mariana Leite,\nDavid Semedo, ..."
}
```

If you want to check if all the papers in `targets.json` are downloaded successfully, use `racp.crawl.check_download`.
```python
from racp.crawl import check_download

failed_ids = check_download(target_ids, "./data")

# download again
download(
    failed_ids,
    "./data"
)
```
