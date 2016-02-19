import django.dispatch

field_tracker_presave = django.dispatch.Signal(providing_args=["sender", "instance", "changed"])
field_tracker_postsave = django.dispatch.Signal(providing_args=["sender", "instance", "created", "changed"])
