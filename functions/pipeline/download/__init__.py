import logging

import azure.functions as func
import json
import os
from ..shared import db_access as DB_Access

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    imageCount = req.params.get('imageCount')
    # setup response object
    headers = {
        "content-type": "application/json"
    }
    if not imageCount:
        return func.HttpResponse(
            status_code=400,
            headers=headers,
            body=json.dumps({"error": "image count not specified"})
        )
    else:
        # setup response object
        connection = DB_Access.get_connection()
        images = DB_Access.get_images_for_tagging(connection, imageCount)

        # TODO: Build vott json

        content = json.dumps(images)
        return func.HttpResponse(
            status_code=200, 
            headers=headers, 
            body=content
        )