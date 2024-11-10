from Config import configs

from MainApp.appFactory import create_app

app = create_app()


if __name__ == '__main__':
    flask_cfg = configs.get('flask')
    PORT = flask_cfg.get('port')
    HOST = flask_cfg.get('host')
    DEBUG = flask_cfg.get('debug')

    # if flask_cfg.get('key') and flask_cfg.get('cert'):
    #     # run via ssl context
    #     context = (flask_cfg.get('cert'), flask_cfg.get('key'))
    #     app.run(port=PORT, host=HOST, debug=DEBUG, ssl_context=context)
    # else:
    app.run(port=PORT, host=HOST, debug=DEBUG)
