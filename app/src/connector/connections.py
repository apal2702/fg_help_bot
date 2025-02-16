from app.src.connector.presto import PrestoConnector
#from src.connector.elasticsearch import ElasticSearchConnector
#from src.connector.redis import RedisConnector


class Connections:
    def __init__(self):
        self.presto_conn = None
        self.es_conn = None
        self.redis_conn = None
        self.rollbar_conn = None
    def presto_connector(self, username, password, host=None, port=None):
        """

        @param username: Presto Username
        @type username: string
        @param password: Presto Password
        @type password: string
        @param host: Presto host
        @type host: string
        @param port: Presto port
        @type port: string
        @return: None
        @rtype: None
        """
        conn = PrestoConnector(username, password, host, port)
        self.presto_conn = conn

    # def es_connector(self, es_url, es_index):
    #     """
    #     @param es_url: Elasticsearch url
    #     @type es_url: string
    #     @param es_index: Ellasticsearch index
    #     @type es_index: string
    #     @return: None
    #     @rtype: None
    #     """
    #     conn = ElasticSearchConnector(es_url, es_index)
    #     self.es_conn = conn

    # def redis_connector(
    #     self, redis_host, redis_reader_host
    # ):
    #     """
    #     @param redis_host: Elasticache Redis host
    #     @type redis_host: string
    #     @return: None
    #     @rtype: None
    #     """
    #     conn = RedisConnector(redis_host, redis_reader_host)
    #     self.redis_conn = conn

    # def create_connections(
    #     self,
    #     presto_username,
    #     presto_password,
    #     es_url,
    #     es_index,
    #     redis_host=None,
    #     redis_reader_host=None,
    #     presto_host=None,
    #     presto_port=None,
    # ):
    #     """
    #     @param presto_username: Presto Username
    #     @type presto_username: string
    #     @param presto_password: Presto Password
    #     @type presto_password: string
    #     @param es_url: Elasticsearch url
    #     @type es_url: string
    #     @param es_index: Elasticsearch index
    #     @type es_index: string
    #     @param redis_host: Elasticache Redis host
    #     @type redis_host: string
    #     @param presto_host: Presto host
    #     @type presto_host: string
    #     @param presto_port: Presto port
    #     @type presto_port: string
    #     @return: None
    #     @rtype: None
    #     """
    #     self.es_connector(es_url, es_index)
    #     self.redis_connector(redis_host, redis_reader_host)
    #     #self.presto_connector(
    #     #    presto_username, presto_password, presto_host, presto_port
    #     #)

