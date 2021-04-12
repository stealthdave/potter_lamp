'''
Configuration variables for Potter Lamp server
'''

from cv2 import ROTATE_180, ROTATE_90_CLOCKWISE, ROTATE_90_COUNTERCLOCKWISE

potter_lamp_config = {
    # Flask Server
    'host': '0.0.0.0',
    'port': 5000,

    # Redis
    'redis_namespace': 'potterlamp',

    # OpenCV
    'debug_opencv': False, # requires desktop x11 server
    'debug_test_image': False, # saves image capture with found points to file
    'rotate_camera': None, # optional camera rotation

    # Spells
    'watch_on_start': False, # start watching for spells on server start
    'wand_timeout': 600, # negative value never times out

    # IR Emitters
    'emitters_pin': 17,
}
