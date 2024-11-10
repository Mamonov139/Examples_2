from Config import configs

RC = configs.get("redis")
pw_string = f':{RC.get("password")}@' if RC.get("password") else ''

# ----------------------------------------------------------------------------------------------------------------------
#                                               configs
# ----------------------------------------------------------------------------------------------------------------------

broker_url = f'redis://{pw_string}{RC.get("host")}:{RC.get("port")}/{RC.get("db")}'
result_backend = broker_url
timezone = 'Europe/Moscow'
imports = ('API.tasks',)
task_routes = {
    'API.tasks.get_acquiring_reports_task': {
        'queue': 'identification'
    },
}
