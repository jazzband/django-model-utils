def pre_save_test(instance, *args, **kwargs):
    instance.pre_save_runned = True


def post_save_test(instance, created, *args, **kwargs):
    instance.post_save_runned = True
