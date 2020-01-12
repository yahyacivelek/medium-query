import requests
import json
import time
import click

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield len(lst[i:i + n])

def generate_loop_index_list(start, stop, step=1):
  return list(chunks(range(start, stop), step))

@click.command()
@click.option('-q', '--query', required=True, help='query input')
@click.option('-n', '--maxnum', default=9999, help='max. number of results. [10 - 9999)')
@click.option('-o', '--output', default="results.json", help='Maximum number of results. Default: No restriction.')
def query_medium(query, maxnum, output):
  headers = {
      'authority': 'medium.com',
      'pragma': 'no-cache',
      'cache-control': 'no-cache',
      'x-client-date': '1578149049243',
      'origin': 'https://medium.com',
      'x-xsrf-token': '2HwkM3LR57ah',
      'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
      'content-type': 'application/json',
      'accept': 'application/json',
      'x-obvious-cid': 'web',
      'sec-fetch-site': 'same-origin',
      'sec-fetch-mode': 'cors',
      #'referer': 'https://medium.com/search/posts?q=python',
      'accept-encoding': 'gzip, deflate, br',
      'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8,tr;q=0.7,ru;q=0.6',
      #'cookie': '__cfduid=db577dfbf15d24836cc86858cf5e94aa21570375758; _ga=GA1.2.70317468.1570375760; _parsely_visitor={%22id%22:%22pid=5dc8a4e4fa4bd8d0797b9a85e107731e%22%2C%22session_count%22:1%2C%22last_session_ts%22:1570375761408}; lightstep_guid/lite-web=328bc18254245108; lightstep_session_id=6af920180687e670; lightstep_guid/medium-web=a8b100c4c2399456; pr=1; tz=-120; __cfruid=12c2fd853ce5aa32449c49b23eb67afef66daf93-1578111157; optimizelyEndUserId=e570a6b31af3; uid=e570a6b31af3; sid=1:VqJiCkQTSP0K8CikBXdclsnxkbJDeq8nTaTrc2dJ8az3POzmGWgbp6qM3ti7skFr; xsrf=2HwkM3LR57ah; sz=762',
  }

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

if __name__ == '__main__':
    query_medium()