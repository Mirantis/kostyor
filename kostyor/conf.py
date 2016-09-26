from oslo_config import cfg
CONF = cfg.CONF


database_group = cfg.OptGroup(name='database',
                              title='Database settings')
connection_opt = cfg.StrOpt('connection', default='sqlite:////tmp/kostyor.db',
                            help='path to the database')
CONF.register_group(database_group)
CONF.register_opt(connection_opt, group=database_group)


def parse_args(args=[]):
    CONF(args)
