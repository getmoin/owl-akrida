from locust import SequentialTaskSet, task, User, between
from locustClient import CustomClient
import time
import inspect
import json

import fcntl
import os
import signal

WITH_MEDIATION = os.getenv("WITH_MEDIATION")

class CustomLocust(User):
    abstract = True
    def __init__(self, *args, **kwargs):
        super().__init__(*args,**kwargs)
        self.client = CustomClient(self.host)

class UserBehaviour(SequentialTaskSet):
    # Class-level counters for all tasks
    credentials_issued = 0
    invites_gotten = 0
    invites_accepted = 0
    
    def on_start(self):
        print("Started process")
        self.client.startup(withMediation=bool(WITH_MEDIATION))

    def on_stop(self):
        print("\n=== Summary ===")
        print(f"Invitations Retrieved: {UserBehaviour.invites_gotten}")
        print(f"Invitations Accepted: {UserBehaviour.invites_accepted}")
        print(f"Credentials Issued: {UserBehaviour.credentials_issued}")
        print("===========================\n")
        self.client.shutdown()
        self.interrupt()

    @task
    def get_invite(self):
        invite = self.client.issuer_getinvite()
        self.invite = invite
        UserBehaviour.invites_gotten += 1

    @task
    def accept_invite(self):
        self.client.ensure_is_running()
        connection = self.client.accept_invite(self.invite['invitation_url'])
        self.connection = connection
        UserBehaviour.invites_accepted += 1

    @task
    def receive_cred_2_0(self):
        self.client.ensure_is_running()
        self.client.receive_credential_v_2_0(self.invite['connection_id'])
        UserBehaviour.credentials_issued += 1

class Issue(CustomLocust):
    tasks = [UserBehaviour]
    wait_time = between(float(os.getenv('LOCUST_MIN_WAIT',0.1)), float(os.getenv('LOCUST_MAX_WAIT',1)))
#    host = "example.com"
