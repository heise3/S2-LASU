"""Rebuild K4 from frozen UI captures and explicitly reviewed study decisions.

No live browser traffic and no inferred zero hits on access failures.
Title normalization is an audit aid, not bibliographic study deduplication.
"""
from pathlib import Path
import csv, json, re, unicodedata
from urllib.parse import quote

O=Path(__file__).resolve().parents[1]

def norm(s):
    s=re.sub(r'^\[[^\]]+\]\s*','',s)
    return re.sub(r'\W+',' ',unicodedata.normalize('NFKC',s).casefold()).strip()

def write_csv(name, rows, cols):
    with (O/name).open('w', newline='') as f:
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(rows)

def finalize():
    pages=json.loads((O/'evidence/scholar_pages_20261026.json').read_text())
    decision=json.loads((O/'evidence/scholar_review_decisions.json').read_text())
    current=list(csv.DictReader((O/'K4_key_studies.csv').open()))
    seen={r['pmid'] for r in current}
    current += [r for r in decision['added_key_studies'] if r['pmid'] not in seen]
    write_csv('K4_key_studies.csv',current,list(current[0]))
    reviews=[dict(zip(['title_pattern','study','review_level','reason_not_exact_kill','source_url'],r)) for r in decision['candidate_reviews']]
    write_csv('K4_Scholar_candidate_review.csv',reviews,list(reviews[0]))
    ledger=[];groups={};query_rows=[]
    for qid in ['Q1','Q2','Q3']:
        pp=sorted([p for p in pages if p['qid']==qid],key=lambda p:p['page'])
        assert [p['page'] for p in pp]==list(range(1,pp[-1]['page']+1)), qid
        assert not pp[-1]['results'] and not pp[-1].get('next'), qid
        terminal=(O/f'evidence/Scholar_{qid}_terminal_20261027.txt').read_text()
        assert '(disabled) 下一页' in terminal, qid
        records=sum(len(p['results']) for p in pp)
        query_rows.append({'query_id':qid,'query':pp[0]['query'],'year_filter':'2023–2026' if qid=='Q2' else 'all years','initial_estimate_text':pp[0]['count'],'result_pages':len(pp)-1,'terminal_page':pp[-1]['page'],'actual_result_records':records,'terminal_status':'NO_RESULTS_NEXT_DISABLED','terminal_estimate_text':pp[-1]['count']})
        for p in pp:
            for i,r in enumerate(p['results'],1):
                title=r['title'];key=norm(title)
                # Exactly the normalization used for the reported title-group count.
                groupkey=re.sub(r'\s+',' ',re.sub(r'^\[[^\]]+\]\s*','',title)).strip().casefold()
                if groupkey not in groups:groups[groupkey]=f'T{len(groups)+1:04d}'
                review=next((v for v in reviews if norm(v['title_pattern']) in key),None)
                ledger.append({'query_id':qid,'page':p['page'],'rank_on_page':i,'title_group':groups[groupkey],'title':title,'metadata':r.get('meta',''),'url':r.get('url',''),'snippet':r.get('snippet',''),'screen_stage':'TITLE_SCREEN_WITH_TARGETED_PRIMARY_REVIEW','screen_decision':'TARGETED_REVIEW_NO_EXACT_KILL' if review else 'NO_EXACT_COLLISION_IDENTIFIED_AT_TITLE_SCREEN','targeted_study':review['study'] if review else '', 'targeted_reason':review['reason_not_exact_kill'] if review else '', 'full_text_review':'see_candidate_review_or_key_study_table' if review else 'NOT_CLAIMED'})
    assert [r['actual_result_records'] for r in query_rows]==[340,260,840]
    assert len(ledger)==1440 and len(groups)==1328
    write_csv('K4_Scholar_screening_ledger.csv',ledger,list(ledger[0]))
    write_csv('K4_Scholar_query_counts.csv',query_rows,list(query_rows[0]))
    status={'status':decision['status'],'review_date':decision['review_date'],'exact_kill_studies':decision['exact_kill_studies'],'pubmed_unique_records':205,'scholar_records':len(ledger),'scholar_normalized_title_groups':len(groups),'scholar_queries_completed':3,'scholar_query_counts':query_rows,'key_studies':len(current),'additional_scholar_candidates_reviewed':len(reviews),'scope':decision['scope']}
    (O/'K4_final_decision.json').write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n')
    log=json.loads((O/'evidence/pubmed_search_log.json').read_text())
    text=['# K4 检索记录与最终判定','', '**最终判定：PASS（限本轮检索范围）；已核实精确 KILL 研究为0。** KILL需同时满足全国Medicare/Part D、处方者层面、长/短效SU拆分、跨年趋势。','', '首次PubMed检索：2026-10-26；Scholar恢复检索及最终核查：2026-10-26至2026-10-27（America/Los_Angeles）。本次是选题预检，未声称系统综述或证明所有文献中绝无撞题。','', '## PubMed','', '|查询|检索式|命中数|','|---|---|---:|']
    for r in log:text.append(f"|{r['id']}|{r['query']}|{r['count']}|")
    text+=['','六式合计281次命中，去重205篇。205篇题名筛查，加定向摘要/全文核查；不是205篇全文评审。原始esearch和XML保存于evidence/。PubMed截止日仍为2026-10-26，没有将后续一天的Scholar补核写成PubMed重新运行。','', '## Google Scholar 三组','', '|查询|年份限制|实际结果页|实际结果记录|末页|末页状态|','|---|---|---:|---:|---:|---|']
    for r in query_rows:
        u='https://scholar.google.com/scholar?q='+quote(r['query'])+('&as_ylo=2023&as_yhi=2026' if r['query_id']=='Q2' else '')
        text.append(f"|[{r['query_id']}: {r['query']}]({u})|{r['year_filter']}|{r['result_pages']}|{r['actual_result_records']}|{r['terminal_page']}|0条，下一页禁用|")
    text+=['','合计1,440条结果记录；去除方括号格式标签、合并空白和忽略大小写后为1,328个标题组。标题组不是经文献学去重的独立研究数，包含重复版本、书籍、引用记录和非研究网页。不能把Scholar估算总数当作已筛查篇数。','', '三式首页估算分别约651、280、1,090条；深分页末页显示的总数又变为87、83、225，存在明显不稳定。实际沿网页提供的分页链接到达禁用“下一页”的空结果末页，未自行构造额外页码、未声称穷尽Google索引。原始逐页结果保留在 [scholar_pages_20261026.json](evidence/scholar_pages_20261026.json)；文件名沿用首次保存日，末页核查在2026-10-27。三张末页AX快照与 [查询计数CSV](K4_Scholar_query_counts.csv) 可复核。','', '1,440条记录进行题名筛查，可能相关者作定向原始摘要/全文核查。全部结果记录见 [Scholar筛查台账](K4_Scholar_screening_ledger.csv)，19条新增/复核候选及排除理由见 [候选复核表](K4_Scholar_candidate_review.csv)。没有把题名筛查写成全文审阅。','', '## 关键撞题边界','', '合并关键表由13项扩为18项，新增Hume 2022、Jayaweera 2020、Riester 2023、McCoy 2025和Herzik 2020。特别核对Jayaweera完整PDF及附录：确有全国2013–2015处方者PIM率分布/趋势，但未分析长效与短效SU的份额趋势；PIM表中的长效SU只列chlorpropamide/glyburide。Hume在全国2016年养老院数据中单列SU分子，但为单年住民分析。两者均不满足全部四条件。','', 'Landon已有全国患者层面长/短效趋势；Sangha/Hayes已有全国处方者趋势但SU合并；Trombetta及Herzik已有区域性/项目性处方者或处方者类型研究。这些都限制宽泛“首次全国研究/首次处方者研究”的表述，PASS不等于已证实创新性。见 [18项关键研究表](K4_key_studies.csv)。','', '## 访问与版本记录','', '初始Scholar访问为CAPTCHA_BLOCKED，旧结论UNKNOWN_EXTERNAL保存在 [历史报告](history/pre_scholar_completion/S2_LASU_K0_K4_summary.md)。用户手动完成验证后取得三式结果；Q1第35页再次出现验证，用户再次完成后确认该页为空结果且下一页禁用。未由程序绕过验证。Q2/Q3末页亦重新核查。两次访问屏障均不是零命中证据；最终PASS基于已实际取得并筛查的结果及关键原始文献。','', 'K0–K3源数据、分析表和药名清单未改变。此轮仅更新K4、汇总、可复现代码说明和文件校验记录。']
    (O/'K4_search_log.md').write_text('\n'.join(text)+'\n')
    print('K4 finalized:',json.dumps({k:v for k,v in status.items() if k not in ['scholar_query_counts','scope']},ensure_ascii=False))

if __name__=='__main__':finalize()
