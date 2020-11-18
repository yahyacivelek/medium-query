# medium-query
A python script to acquire metadata of stories on medium.com.

Install environment:

```
pipenv install
```

Search and download the results:

```
medium_query.py query-medium [OPTIONS]

Options:
  -q, --query TEXT      query input  [required]
  -n, --maxnum INTEGER  max. number of results. [10 - 9999)
  -o, --output TEXT     Maximum number of results. Default: No restriction.
  --help                Show this message and exit.
```

Get metadata of all stories tagged by a specific string:

```
medium_query.py collect-archive [OPTIONS]

Options:
  -t, --tag TEXT       tag string to search
  -f, --tagfile TEXT   file path containing tags to acquire
  -a, --all_ TEXT      acquire all the data
  -o, --output TEXT    output file path
  -n, --nsave INTEGER  save interval
  --help               Show this message and exit.
```