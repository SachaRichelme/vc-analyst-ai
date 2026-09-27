"""Two selectable synthetic fixtures, plus duplicates/stale records for the funnel."""
from datetime import timedelta
from .core import Candidate, DiscoveryExtraction

class OfflineDiscovery:
    def discover(self, mandate, today):
        recent=(today-timedelta(days=3)).isoformat()
        old=(today-timedelta(days=400)).isoformat()
        descriptions=[
            f'Lumen Fixture Software is Enterprise Software / SaaS for regional distributors. It is based in France and sells B2B software. Founded in 2021, its official website is https://lumen.example/. On {recent}, Lumen Fixture Software announced a Seed funding round of USD 2 million. Total funding is USD 3 million.',
            f'Lumen Sparse develops Enterprise Software / SaaS for distributors. On {recent}, Lumen Sparse announced a product launch. Its funding and headquarters were not disclosed.',
        ]
        sources=[{'id':f'S{i+1}','url':f'https://synthetic-news.example/{i+1}','title':'Synthetic startup announcement — NOT REAL',
                  'text':text,'published_at':recent,'retrieved_at':today.isoformat()+'T00:00:00+00:00'} for i,text in enumerate(descriptions)]
        def value(v, i=0): return {'source_id':f'S{i+1}','quote':descriptions[i], 'value':v}
        def excerpt(i=0): return {'source_id':f'S{i+1}','quote':descriptions[i]}
        first=Candidate(name=value('Lumen Fixture Software'),website='https://lumen.example/',description=excerpt(),
            sectors=[value('Enterprise Software / SaaS')],stage=value('Seed'),geography=value('France'),business_models=[value('B2B')],founded_year=value('2021'),
            total_funding={**excerpt(),'amount':'3','scale':'million','currency':'USD'},
            latest_round={**excerpt(),'amount':'2','scale':'million','currency':'USD'},
            signal={**excerpt(),'kind':'Funding round','date_text':recent})
        second=Candidate(name=value('Lumen Sparse',1),website=None,description=excerpt(1),
            sectors=[value('Enterprise Software / SaaS',1)],stage=None,geography=None,business_models=[],founded_year=None,
            total_funding=None,latest_round=None,signal={**excerpt(1),'kind':'Product launch','date_text':recent})
        stale_text=descriptions[0].replace(recent,old).replace('Lumen Fixture Software','Historical Fixture')
        sources.append({'id':'S3','url':'https://synthetic-news.example/old','title':'Synthetic old announcement',
                        'text':stale_text,'published_at':old,'retrieved_at':today.isoformat()+'T00:00:00+00:00'})
        stale=second.model_copy(update={'name':type(second.name)(source_id='S3',quote=stale_text,value='Historical Fixture'),
                                      'signal':type(second.signal)(source_id='S3',quote=stale_text,kind='Funding round',date_text=old)})
        return sources,DiscoveryExtraction(candidates=[first,first.model_copy(deep=True),second,stale])

    def usage(self):
        return {'searches':0,'model_calls':0,'input_tokens':0,'output_tokens':0,
                'reserved_estimate_usd':0,'queries':[],'model':'synthetic sourcing fixtures','retries':0}
