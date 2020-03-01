import os
import requests
import json
import time
import click
from collections import Counter
import datetime

headers = {
    'x-xsrf-token': os.getenv('X_XSRF_TOKEN', 'any text!'),
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
    'accept': 'application/json'
}

keys_parent = [
    "creatorId", "homeCollectionId", "title", "detectedLanguage", "latestVersion", "latestPublishedVersion",
    "hasUnpublishedEdits", "latestRev", "createdAt", "updatedAt", "acceptedAt", "firstPublishedAt",
    "latestPublishedAt", "uniqueSlug", "isEligibleForRevenue"
]

keys_virtuals = [
    "imageCount", "readingTime", "subtitle", "recommends", "isBookmarked",
    "socialRecommendsCount", "responsesCreatedCount", "totalClapCount", "sectionCount"
]

keys_others = [
    "linkCount", "userId", "name", "username", "collectionName", "followerCount"
]

saveIndex = 0

def is_keys_unique(*key_lists):
    all_keys = []
    for key_list in key_lists:
        if not isinstance(key_list, list):
            return (False, [])
        all_keys += key_list

    freq = Counter(all_keys)
    common_keys = [k for k,v in dict(freq).items() if v > 1]

    return (len(common_keys) == 0, common_keys)

def get_required_fields(artical):
    fields = {}
    for key in keys_parent:
        fields[key] = artical[key]

    virtuals = artical["virtuals"]
    for key in keys_virtuals:
        fields[key] = virtuals[key]
        
    links = virtuals.get("links", None)
    if links:
        fields["linkCount"] = len(links["entries"])
    else:
        fields["linkCount"] = 0
    #fields["userId"] = virtuals["userPostRelation"]["userId"]
    tags = virtuals.get("tags", None)
    if tags:
        tagList = [x["name"] for x in tags]
    else:
        tagList = []

    fields["tags"] = tagList

    return fields

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
          t = references.get("User", None)
          if t: Users.update(t)
          t = references.get("Collection", None)
          if t: Collections.update(t)
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
  print("it took {:.1f} sec to crawl".format(toc - tic))
  print("total number of articles crawled: ", article_num)

  with open(output, 'w') as fp:
    json.dump(final_data, fp)

@cli.command()
@click.option('-t', '--tag', default="", help='tag string to search')
@click.option('-f', '--tagfile', default="tagfile.txt", help='file path containing tags to acquire')
@click.option('-a', '--all_', default=False, help='acquire all the data')
#@click.option('-n', '--maxnum', default=9999, help='max. number of results. [10 - 9999)')
@click.option('-o', '--output', default="", help='output file path')
@click.option('-n', '--nsave', default=1000, help='save interval')
def collect_archive(tag, tagfile, output, all_, nsave):
    def update_data(res, all_, year, month='', day=''):
        references = res["payload"]["references"]
        users = references.get("User", None)
        collection = references.get("Collection", None)
        post = references.get("Post", None)

        if post:
            if not all_:
                #print(post)
                newPost = {}
                for k,v in post.items():
                    newPost.update({k: get_required_fields(v)})
                post = newPost

            for k, _ in post.items():
                post[k].update({'latestAcquiredDate': (year, month, day)})

        global saveIndex
        saveIndex += len(post)

        if users: Users.update(users)
        if collection: Collections.update(collection)
        if post: Posts.update(post)
        #print("number of articles: ", len(Posts), end='\r')
        print("year: {0}, month: {1}, day: {2}, articles: {3}"\
              .format(year, month, day, len(Posts)), end = '\r')

        if saveIndex >= nsave:
            saveIndex = 0
            final_data = {
                "Post": Posts,
                "User": Users,
                "Collection": Collections
            }

            with open(outputPath, 'w') as fp:
                json.dump(final_data, fp)

    tags = []
    if os.path.isfile(tagfile):
        print("will use tagfile...")
        with open(tagfile, "r") as fp:
            tags = fp.readlines()
            tags = [tag.strip() for tag in tags]
            print("tags: ", tags)
    else:
        tags = [tag]

    if not output:
        output = os.getcwd()

    if not os.path.exists(os.path.dirname(output)):
        print("Output directory doesn't exist!")
        return

    for tag in tags:
        print("\n###################")
        print("TAG: ", tag)
        print("###################\n")

        Posts = {}
        Users = {}
        Collections = {}
        currentDateListforUrl = None
        saveIndex = 0

        outputPath = os.path.join(output, tag + '.json')
        if os.path.isfile(outputPath):
            with open(outputPath, "r") as fp:
                temp = json.load(fp)
                Users = temp.get("User", {})
                Collections = temp.get("Collection", {})
                Posts = temp.get("Post", {})
                latests = [v['latestAcquiredDate'] for k,v in Posts.items()]
                res = (None, 0)
                for t in latests:
                    m = t[1] if t[1] else 1
                    d = t[2] if t[2] else 1
                    resNew = (t, 365 * int(t[0]) + 30 * int(m) + int(d))
                    if resNew[1] > res[1]:
                        res = resNew
                currentDateListforUrl = res[0]

        offset = len(b'])}while(1);</x>')

        base_url = 'https://medium.com/tag'
        base_url = '/'.join([base_url, tag, 'archive'])

        buckets = "yearlyBuckets"
        bucketList = ["yearlyBuckets", "monthlyBuckets", "dailyBuckets"]
        
        if currentDateListforUrl:
            print("currentDateListforUrl: ", currentDateListforUrl)
            for i in list(range(3))[::-1]:
                fine = '/'.join(currentDateListforUrl[:i+1])
                url = '/'.join([base_url, fine])
                print("decided base_url:", url)
                response = requests.get(url, headers=headers)
                buckets = bucketList[i]
                if response.status_code == 200:
                    print("status: ", response.status_code)
                    break
        else:
            response = requests.get(base_url, headers=headers)
        res_dict = json.loads(response.text[offset:])
        yearlyBuckets = res_dict["payload"]["archiveIndex"][buckets]

        tic = time.time()
        for yb in yearlyBuckets:
            if not yb["hasStories"]:
                continue
            year = yb["year"]
            url = "/".join([base_url, year])
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                print("Error: ", response, ", url: ", url)
                continue
            try:
                res_dict = json.loads(response.text[offset:])
            except:
                print("error parsing res_dict!")
                continue
            monthlyBuckets = res_dict["payload"]["archiveIndex"]["monthlyBuckets"]
            if not monthlyBuckets:
                update_data(res_dict, all_, year)
                continue
            for mb in monthlyBuckets:
                if not mb["hasStories"]:
                    continue
                month = mb["month"]
                url = "/".join([base_url, year, month])
                response = requests.get(url, headers=headers)
                if response.status_code != 200:
                    print("Not successfull: ", response)
                    continue
                try:
                    res_dict = json.loads(response.text[offset:])
                except:
                    print("error parsing res_dict!")
                    continue
                dailyBuckets = res_dict["payload"]["archiveIndex"]["dailyBuckets"]
                if not dailyBuckets:
                    update_data(res_dict, all_, year, month)
                    continue
                for db in dailyBuckets:
                    if not db["hasStories"]:
                        continue
                    day = db["day"]
                    url = "/".join([base_url, year, month, day])
                    response = requests.get(url, headers=headers)
                    if response.status_code != 200:
                        print("Not successfull: ", response)
                        continue
                    try:
                        res_dict = json.loads(response.text[offset:])
                    except:
                        print("error parsing res_dict!")
                        continue
                    update_data(res_dict, all_, year, month, day)

        toc = time.time()
        print("it takes {:.1f} sec to crawl".format(toc - tic))
        print("total number of articles crawled: ", len(Posts))

        final_data = {
            "Post": Posts,
            "User": Users,
            "Collection": Collections
        }

        with open(outputPath, 'w') as fp:
            json.dump(final_data, fp)

if __name__ == '__main__':
    cli()