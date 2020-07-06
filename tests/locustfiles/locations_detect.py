"""
pipenv run locust -f tests/locustfiles/locations_detect.py -H http://oraaange.herokuapp.com
"""
from locust import HttpLocust, TaskSet, task


class LocationsDetectTaskSet(TaskSet):

    @task
    def get(self):
        self.client.get('/v2/locations/detect/')


class WebsiteUser(HttpLocust):
    task_set = LocationsDetectTaskSet
    min_wait = 100
    max_wait = 100
