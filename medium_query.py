import os
import requests
import json
import time
import click

headers = {
    'x-xsrf-token': os.getenv('X_XSRF_TOKEN', 'any text!'),
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
    'accept': 'application/json'
}

@click.group()
def cli():
    pass

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield len(lst[i:i + n])

def generate_loop_index_list(start, stop, step=1):
  return list(chunks(range(start, stop), step))

@cli.command()
@click.option('-q', '--query', required=True, help='query input')
@click.option('-n', '--maxnum', default=9999, help='max. number of results. [10 - 9999)')
@click.option('-o', '--output', default="results.json", help='Maximum number of results. Default: No restriction.')
def query_medium(query, maxnum, output):
  print(os.getenv('X_XSRF_TOKEN', 'Token Not found'))
  params = (
      ('q', query),
  )
  offset = len(b'])}while(1);</x>')
  result_size = 10 if maxnum >= 10 else maxnum
  data = json.dumps({"page": 1, "pageSize": result_size})
  article_list = []
  Users = {}
  Collections = {}
  article_num = 0
  loop_index_list = generate_loop_index_list(0, maxnum, 10)
  tic = time.time()
  for result_size in loop_index_list:
      response = requests.post('https://medium.com/search/posts', headers=headers, params=params, data=data)
      if response.status_code != 200:
          print("Not successfull: ", response)
          break
      res_dict = json.loads(response.text[offset:])
      value = res_dict["payload"].get("value", None)
      if value:
          article_list += value
          article_num += len(value)
      print("number of articles: ", article_num, end='\r')
      references = res_dict["payload"].get("references", None)
      if references:
          Users.update(references["User"])
          Collections.update(references["Collection"])
      paging = res_dict["payload"].get("paging", None)
      if paging:
          next_page = paging.get("next", None)
          if not next_page:
              print("No 'next' element. End of queries!")
              break
      else:
          print("No 'paging' element")
          break
      next_page['pageSize'] = result_size
      data = json.dumps(next_page)
      #break

  final_data = {
      "articles": article_list,
      "users": Users,
      "collections": Collections
  }
  toc = time.time()
  print("it takes {:.1f} sec to crawl".format(toc - tic))
  print("total number of articles crawled: ", article_num)

  with open(output, 'w') as fp:
    json.dump(final_data, fp)

@cli.command()
@click.option('-t', '--tag', required=True, help='tag string to search')
#@click.option('-n', '--maxnum', default=9999, help='max. number of results. [10 - 9999)')
@click.option('-o', '--output', default="archive.json", help='output file path')
def collect_archive(tag, output):
    offset = len(b'])}while(1);</x>')

    def update_data(res):
        references = res["payload"]["references"]
        Users.update(references["User"])
        Collections.update(references.get("Collection", {}))
        Posts.update(references["Post"])
        print("number of articles: ", len(Posts), end='\r')

    base_url = 'https://medium.com/tag'
    base_url = '/'.join([base_url, tag, 'archive'])
    response = requests.get(base_url, headers=headers)
    res_dict = json.loads(response.text[offset:])
    yearlyBuckets = res_dict["payload"]["archiveIndex"]["yearlyBuckets"]

    Posts = {}
    Users = {}
    Collections = {}

    tic = time.time()
    for yb in yearlyBuckets:
        year = yb["year"]
        url = "/".join([base_url, year])
        print("url: ", url)
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
          print("Not successfull: ", response)
          continue
        try:
            res_dict = json.loads(response.text[offset:])
        except:
            continue
        monthlyBuckets = res_dict["payload"]["archiveIndex"]["monthlyBuckets"]
        if not monthlyBuckets:
            update_data(res_dict)
            continue
        for mb in monthlyBuckets:
            month = mb["month"]
            url = "/".join([base_url, year, month])
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                print("Not successfull: ", response)
                continue
            try:
                res_dict = json.loads(response.text[offset:])
            except:
                continue
            dailyBuckets = res_dict["payload"]["archiveIndex"]["dailyBuckets"]
            if not dailyBuckets:
                update_data(res_dict)
                continue
            for db in dailyBuckets:
                day = db["day"]
                url = "/".join([base_url, year, month, day])
                response = requests.get(url, headers=headers)
                if response.status_code != 200:
                    print("Not successfull: ", response)
                    continue
                try:
                    res_dict = json.loads(response.text[offset:])
                except:
                    continue
                update_data(res_dict)

    toc = time.time()
    print("it takes {:.1f} sec to crawl".format(toc - tic))
    print("total number of articles crawled: ", len(Posts))

    final_data = {
        "Post": Posts,
        "User": Users,
        "Collection": Collections
    }

    with open(output, 'w') as fp:
        json.dump(final_data, fp)

if __name__ == '__main__':
    cli()