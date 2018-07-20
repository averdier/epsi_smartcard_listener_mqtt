# -*- coding: utf-8 -*-

import os
import time
from configobj import ConfigObj
from app import App


if __name__ == '__main__':
    basedir = os.path.dirname(__file__)
    config_path = os.path.join(basedir, 'config.cfg')

    conf = ConfigObj(config_path)

    main_app = App(conf)

    try:
        main_app.start()

        while True:
            main_app.loop()
            time.sleep(int(conf['SLEEP_TIME']))

    except Exception as ex:
        print(ex)