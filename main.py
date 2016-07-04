#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
import os
from concurrent.futures import ThreadPoolExecutor
from tornado.gen import coroutine
from tornado import ioloop
from tornado.web import RequestHandler, Application, url
from tornado.log import enable_pretty_logging
import tormysql
import settings

pool = tormysql.ConnectionPool(
    max_connections=20,
    host=settings.MYSQL_HOST,
    user=settings.MYSQL_LOGIN,
    passwd=settings.MYSQL_PASSWORD,
    db=settings.MYSQL_DATABASE,
    charset="utf8"
)

IMAGE_MIME_TYPES = (
    'image/gif',
    'image/jpeg',
    'image/pjpeg',
    'image/png',
)


def write_error(self, status_code, **kwargs):
    """Convert all errors into JSON response format"""
    self.set_status(status_code)
    self.finish({
        'code': 'INTERNAL_ERR',
        'message': 'Error #{code}: {reason}'.format(code=status_code, reason=self._reason),
        'data': {},
    })

RequestHandler.write_error = write_error


class BaseHandler(RequestHandler):

    def response(self, data=None, code='OK', message='Operation is successfully executed', **kwargs):
        if data is None:
            data = {}
        elif data == -1:
            data = None

        self.finish(dict({
            'code': code,
            'message': message,
            'data': data,
        }, **kwargs))


class ImageUploader(BaseHandler):
    executor = ThreadPoolExecutor(max_workers=os.cpu_count())

    @coroutine
    def post(self):
        if 'file' in self.request.files:
            file = self.request.files['file'][0]
            file.filename = file.filename.replace(' ', "_")
            if file.content_type not in IMAGE_MIME_TYPES:
                self.response(code='ERR', message='file type is not supported')
            with (yield pool.Connection()) as conn:
                try:
                    with conn.cursor() as cursor:
                        yield cursor.execute(
                            """
                            INSERT INTO
                                images(name, mimetype, body, timestamp)
                            VALUES(%s, %s, %s, UNIX_TIMESTAMP())
                            """, (file.filename, file.content_type, file.body))
                except Exception as e:
                    self.response(code='ERR', message=str(e))
                    return
                else:
                    yield conn.commit()
                    image_url = self.make_image_url(file.filename)
                    self.response(data={'url': image_url})
        else:
            print('no files')

    @staticmethod
    def make_image_url(image_name):
        return '{}/img/{}'.format(settings.SELF_HOST, image_name)


class ImageShower(BaseHandler):

    @coroutine
    def get(self, image_name):
        with (yield pool.Connection()) as conn:
            try:
                with conn.cursor() as cursor:
                    yield cursor.execute(
                        """
                        SELECT
                            name, mimetype, body
                        FROM
                            images
                        WHERE
                            name = %s
                        LIMIT 1
                        """, (image_name, ))
            except Exception as e:
                self.response(code='ERR', message=str(e))
                return
            else:
                image_data = cursor.fetchone()
                if image_data:
                    self.set_header('Content-Type', image_data[1])
                    self.set_header('Content-Length', len(image_data[2]))
                    self.write(image_data[2])

app = Application([
    url(r'/upload', ImageUploader),
    url(r'/img/(.*)', ImageShower),
],
    debug=settings.DEBUG,
)
enable_pretty_logging()

app.listen(settings.PORT)
ioloop.IOLoop.instance().start()
