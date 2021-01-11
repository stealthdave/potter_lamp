'''
Configuration variables for Potter Lamp server
'''

potter_lamp_config = {
    # Flask Server
    'host': '0.0.0.0',
    'port': 5000,

    # Redis
    'redis_namespace': 'potterlamp',

    # OpenCV
    'debug_opencv': False, # requires desktop x11 server

    # Spells
    'watch_on_start': False,
    'wand_timeout': 600,
}
