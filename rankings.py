#
#
#
import json
from pathlib import Path
from datetime import datetime

RANKING_FILE = Path('rankings.json')

def load_rankings():
    '''读取排行榜，若不存在则返回空列表'''
    if not RANKING_FILE.exists():
        return []
    with open (RANKING_FILE, encoding='utf-8') as f:
        return json.load(f)
    
def save_rankings(rankings):
    '''将排行榜列表写入文件'''
    with open(RANKING_FILE, 'w', encoding='utf-8') as f:
        json.dump(rankings, f, ensure_ascii=False, indent=2)  #default=str去掉了，是因为下面已经提前转成str了
    print(f"saving {len(rankings)} entries to {RANKING_FILE}")
    print(RANKING_FILE.absolute())

def add_entry(name, score):
    '''添加一条新纪录，分数降序排列后保存，只保留前5名'''
    rankings = load_rankings()
    entry = {'name': name, 'score': score, 'time': datetime.now().strftime('%Y-%m-%d %H:%M')}
    rankings.append(entry)
    rankings.sort(key=lambda x: x['score'], reverse=True)
    
    rank = next((i for i, e in enumerate(rankings) if e is entry), None)
    save_rankings(rankings)
    rankings = rankings[:10]
    print(f"add_entry called: name={name}, score={score}")
    return rankings, rank

    