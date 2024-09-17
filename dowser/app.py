from .Root import Root
import cherrypy
import logging
import logging.config

class MemoryApp:
    def __init__(self, port: int):
        self.port = port
        logging.config.dictConfig(self.LOG_CONF)

    def __enter__(self):
        self.root = Root()

        cherrypy.tree.mount(self.root)
        cherrypy.config.update({
            'environment': 'embedded',
            'server.socket_port': self.port,
            'log.screen': False,
            'log.access_file': '',
            'log.error_file': ''
        })
    
        cherrypy.engine.start()

    def __exit__(self, *args):
        cherrypy.engine.exit()

    LOG_CONF = {
        'version': 1,

        'formatters': {
            'void': {
                'format': ''
            },
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            },
        },

        'handlers': {
            'cherrypy_console': {
                'level':'WARNING',
                'class':'logging.StreamHandler',
                'formatter': 'void',
                'stream': 'ext://sys.stderr'
            },
            
            'cherrypy_access': {
                'level':'WARNING',
                'class':'logging.StreamHandler',
                'formatter': 'void',
                'stream': 'ext://sys.stderr'
            },

            'cherrypy_error': {
                'level':'WARNING',
                'class':'logging.StreamHandler',
                'formatter': 'void',
                'stream': 'ext://sys.stderr'
            },
        },

        'loggers': {
            'cherrypy.access': {
                'handlers': ['cherrypy_access'],
                'level': 'INFO',
                'propagate': False
            },
            
            'cherrypy.error': {
                'handlers': ['cherrypy_console', 'cherrypy_error'],
                'level': 'INFO',
                'propagate': False
            },
        }
    }