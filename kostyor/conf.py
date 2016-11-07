from oslo_config import cfg
CONF = cfg.CONF


database_group = cfg.OptGroup(name='database',
                              title='Database settings')
connection_opt = cfg.StrOpt('connection', default='sqlite:////tmp/kostyor.db',
                            help='path to the database')

upgrade_group = cfg.OptGroup(name='upgrades',
                             title="Upgrade settings")

upgrade_driver = cfg.StrOpt('driver', default="noop")


CONF.register_group(database_group)
CONF.register_opt(connection_opt, group=database_group)


rpc_group = cfg.OptGroup(name='rpc', title='RPC settings')
rpc_opts = [
    cfg.StrOpt('broker_url',
               default='redis://localhost:6379/0',
               help=('Broker backend to be used. Must be an URL in the form '
                     'of "transport://user:pass@host:port/vhost".')),
    cfg.StrOpt('celery_result_backend',
               default='db+sqlite:////tmp/celery.db',
               help=('The backend to be used to store task results.')),
    cfg.StrOpt('celery_task_serializer',
               default='json',
               help=('A default serialization method to be used.')),
    cfg.StrOpt('celery_result_serializer',
               default='json',
               help=('Result serialization format to be used.')),
    cfg.ListOpt('celery_accept_content',
                default=['json'],
                help=('A whitelist of serializers to be allowed. If a message '
                      'is received that is not in this list then the message '
                      'will be discarded with an error.')),
]
CONF.register_group(rpc_group)
CONF.register_opts(rpc_opts, group=rpc_group)


def parse_args(args=[]):
    CONF(args)
