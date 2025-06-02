


* Process MBPP
  * Read `data/evaluation/mbpp.jsonl`
  * Split by new line
  * Parse

```json
{
  "text": "Write a function to find the longest chain which can be formed from the given set of pairs.",
  "code": "class Pair(object): \r\n\tdef __init__(self, a, b): \r\n\t\tself.a = a \r\n\t\tself.b = b \r\ndef max_chain_length(arr, n): \r\n\tmax = 0\r\n\tmcl = [1 for i in range(n)] \r\n\tfor i in range(1, n): \r\n\t\tfor j in range(0, i): \r\n\t\t\tif (arr[i].a > arr[j].b and\r\n\t\t\t\tmcl[i] < mcl[j] + 1): \r\n\t\t\t\tmcl[i] = mcl[j] + 1\r\n\tfor i in range(n): \r\n\t\tif (max < mcl[i]): \r\n\t\t\tmax = mcl[i] \r\n\treturn max",
  "task_id": 601,
  "test_setup_code": "",
  "test_list": [
    "assert max_chain_length([Pair(5, 24), Pair(15, 25),Pair(27, 40), Pair(50, 60)], 4) == 3",
    "assert max_chain_length([Pair(1, 2), Pair(3, 4),Pair(5, 6), Pair(7, 8)], 4) == 4",
    "assert max_chain_length([Pair(19, 10), Pair(11, 12),Pair(13, 14), Pair(15, 16), Pair(31, 54)], 5) == 5"
  ],
  "challenge_test_list": []
}
```

```python
class Pair(object):
  def __init__(self, a, b):
    self.a = a
    self.b = b

def max_chain_length(arr, n):
  max = 0
  mcl = [1 for i in range(n)]
  for i in range(1, n):
    for j in range(0, i):
      if (arr[i].a > arr[j].b and mcl[i] < mcl[j] + 1):
        mcl[i] = mcl[j] + 1
    for i in range(n):
      if (max < mcl[i]):
        max = mcl[i]
  return max
```


* Convert asserts to ReasonML or Javascript statements
  * 
* 
