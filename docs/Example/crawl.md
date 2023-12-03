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

It will take a long time, which relates to the number of the papers. If everything goes well, there will be a `data/targets.json` in your current directory, which contains all the arXiv paper ids you need to download. Let's say you load it in a variable `target_ids`, which is a `List[Str]`.

You need both raw text data and citation data to construct your dataset. We use `racp.data.PaperItem` to store data of a paper. For detailed information please refer to [PaperItem](../../Reference/data#data.PaperItem).

Note that to get citation data from Semantics Scholar, you need to apply for an [api key](https://www.semanticscholar.org/product/api) first. If you don't have an api key, the parameter is defaultly set to None, which could cause download fails.

Here is an example to use `PaperItem`.

```python
from racp.data import PaperItem

item = PaperItem(
    arxiv_id = target_ids[0],
    key={your-api-key}
)

item.save_json("./data")
```

It will save data into a json file `{arxiv_id}.json` in `./data` directory. If the `data` directory doesn't exist, it will create one.  You can change the savepath by changing the parameter. 

If you want to check if all the papers in `targets.json` are downloaded successfully, use `racp.crawl.check_download`.
```python
from racp.crawl import check_download

failed_ids = check_download(target_ids, "./data")
```

Feel free to use the `crawl.py` script in `example`.

After collecting all the items in the `data` directory, you can use `racp.data.RawSet` to load them into a `torch.utils.data.Dataset` object.
```python
from racp.data import RawSet

dataset = RawSet("./data")
dataset.save("dataset.json")
```

It will save all the items in a json file. You can load it by using the `load` method of `RawSet`. Note that all the items in `RawSet` are `PaperItem`, not `dict`.