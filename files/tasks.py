import os
import json
import uuid
import hashlib

from PIL import Image
from django.conf import settings

from oraaange import celery_app
from .models import File


class FileTask(celery_app.Task):
    """
    File converter.
    """
    name = 'files.tasks.file_compress'

    MINIO_PATH = '/srv/storage/data'

    IMAGE_SIZES = {
        'lq': (640, 480),   # 480p
        'mq': (1280, 720),  # 720p
        'hq': (1920, 1080)  # 1080p
    }

    def __init__(self):
        self.file = None
        self.meta_dir = os.path.join(
            self.MINIO_PATH,
            '.minio.sys/buckets',
            settings.AWS_STORAGE_BUCKET_NAME,
        )

    def run(self, file_uuid):
        """
        Main task body.
        """
        # Workin with UUID's only
        uuid.UUID(file_uuid)

        # Get file entry
        self.file = File.objects.get(uuid=file_uuid)

        # Default handler
        if self.file.handler != self.file.Handler.NONE:
            self._handle_default(file_uuid)

        # Run specific file handler
        if self.file.handler:
            getattr(self, f'_handle_{self.file.handler}')(file_uuid)

        # Mark file as compressed and ready
        self.file.is_compressed = True
        self.file.save()

    def _handle_default(self, file_name):
        """
        Default file handler (compress images).
        """
        for quality in self.IMAGE_SIZES:

            # Thumbnail processing with Pillow
            image = Image.open(self._get_full_path(file_name))
            image.thumbnail(self.IMAGE_SIZES[quality], Image.LANCZOS)
            image.save(
                self._get_full_path(quality, file_name),
                image.format,
                optimize=True
            )

            # Copy meta data from original file
            self._copy_meta_data(file_name, quality, Image.MIME[image.format])

    def _handle_none(self, file_name):
        pass

    def _handle_speech(self, file_name):
        raise NotImplementedError

    def _handle_avatar(self, file_name):
        """
        Scale image for avatar (128*128px).
        """
        avatar_size = (128, 128)
        avatar_prefix = 'av'

        image = Image.open(self._get_full_path(file_name))
        image.thumbnail(avatar_size, Image.LANCZOS)
        image.save(
            self._get_full_path(avatar_prefix, file_name),
            image.format,
            optimize=True,
        )

        self._copy_meta_data(file_name, avatar_prefix, Image.MIME[image.format])

    def _get_full_path(self, *args):
        """ Get full file path on storage. """
        full_path = os.path.join(
            self.MINIO_PATH,
            settings.AWS_STORAGE_BUCKET_NAME,
            *args
        )
        return full_path

    def _copy_meta_data(self, file_name, quality, content_type=None):
        """ Copy metadata for minio. """
        data = {
            'version': '1.0.2',
            'checksum': {
                'algorithm': '',
                'blocksize': 0,
                'hashes': None
            },
            'meta': {
                'content-type': 'application/octet-stream',
                'etag': ''
            }
        }
        meta_path = os.path.join(self.meta_dir, quality, file_name)
        try:
            os.mkdir(meta_path)
        except FileExistsError:
            pass
        data['meta']['etag'] = hashlib.md5(file_name.encode()).hexdigest()
        with open(os.path.join(meta_path, 'fs.json'), 'w') as fp:
            data['meta']['content-type'] = content_type
            json.dump(data, fp)


celery_app.tasks.register(FileTask())
