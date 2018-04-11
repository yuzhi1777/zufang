from datetime import datetime
from elasticsearch_dsl import connections
from elasticsearch_dsl import DocType, Date, Text ,Integer

connections.create_connection(hosts=['localhost'], timeout=20)

class Topic(DocType):
    update_time = Date(index='not_analyzed')
    title = Text()
    url = Text()
    create_time = Date(index='not_analyzed')
    comments_count = Integer()

    class Meta:
        index = 'topic'

    def add(self, ** kwargs):
        return super(Topic, self).save(** kwargs)

    def update(self, ** kwargs):
        return super(Topic, self).update(** kwargs)


    @classmethod
    def query(cls):
        s = cls.search()
        topics = s.query('multi_match', query='整租', fields=['title']).execute()
        for hit in topics:
            print(hit.title, hit.url)



Topic().query()
