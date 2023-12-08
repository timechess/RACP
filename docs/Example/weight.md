# How to calculate the citation weight of a paper

When calculate the citation similarity between papers, our algorithm is based on co-citation and bibliography coupling. A naive version of this algorithm is `racp.utils.ccbc`, which treat every paper as the same. However, papers of different fields may refer to the same fundamental paper with high citations. To avoid this error, we assign a weight to each paper according to their citations.

The citations of papers satisfy power-law distribution. We use a relatively large dataset of citations to fit a cdf function. Let's say `ciationcounts` is a `List[int]` containing citations. You want to get the weight of a paper, represented as a `PaperItem` named `paper`. Here is the example.
```python
from racp.utils import powerlaw_fit_cdf

cdf = powerlaw_fit_cdf(citationcounts) # A dict mapping citations to 1 - weight
weight = 1 - cdf.get(len(paper.citations), 0)
```

If you want to construct a retriever, you need the weight of all the paper involved in the dataset. Luckily, you only need to fit the cdf once. In our experiment, we use over 5 million papers to fit this function.