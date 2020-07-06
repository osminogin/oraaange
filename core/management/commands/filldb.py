import datetime
import random

from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.core.management import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    """ Fill DB with fake data. """
    help = 'Fill database.'

    def add_arguments(self, parser):
        parser.add_argument(
            '-blat', '--lb_lat', dest='lb_lat', type=float, help='Left bottom latitude'
        )
        parser.add_argument(
            '-blng', '--lb_lng', dest='lb_lng', type=float, help='Left bottom longtitude'
        )
        parser.add_argument(
            '-tlat', '--rt_lat', dest='rt_lat', type=float, help='Right top latitude'
        )
        parser.add_argument(
            '-tlng', '--rt_lng', dest='rt_lng', type=float, help='Right top longtitude'
        )
        parser.add_argument(
            '-c', '--count', dest='count', type=int, help='Users count'
        )

    def handle(self, *args, **options):
        moscow_bbox = (55.5613, 37.3480, 55.9261, 37.8671)

        lb_lng = options.get('lb_lng')
        if lb_lng is None:
            lb_lng = moscow_bbox[0]

        lb_lat = options.get('lb_lat')
        if lb_lat is None:
            lb_lat = moscow_bbox[1]

        rt_lng = options.get('rt_lng')
        if rt_lng is None:
            rt_lng = moscow_bbox[2]

        rt_lat = options.get('rt_lat')
        if rt_lat is None:
            rt_lat = moscow_bbox[3]

        count = options.get('count')
        if count is None:
            count = 100

        # self.create_users((lb_lng, lb_lat, rt_lng, rt_lat), count)
        self.create_users((55.4751, 35.9785, 55.5245, 36.0722), count)  # Mozhaysk

    @transaction.atomic
    def create_users(self, bbox, users_count):
        users = [self.get_user(bbox) for _ in range(users_count)]
        get_user_model().objects.bulk_create(users)

    def get_user(self, bbox):
        # d = 100
        lb_lng, lb_lat, rt_lng, rt_lat = bbox
        lat = random.uniform(lb_lat, rt_lat)
        lng = random.uniform(lb_lng, rt_lng)
        # lat = random.randint(int(lb_lat * d), int(rt_lat * d)) / d
        # lng = random.randint(int(lb_lng * d), int(rt_lng * d)) / d
        username = '7' + ''.join(str(random.randint(0, 9)) for _ in range(10))
        user = get_user_model()(
            username=username,
            display_name=username,
            sex=random.choice(['M', 'F']),
            location=Point(lng, lat),
            birth_date=datetime.date(2000, 1, 1),
            confirm_tos=True,
            last_activity=datetime.datetime.now(),
            is_online=True,
        )
        return user
