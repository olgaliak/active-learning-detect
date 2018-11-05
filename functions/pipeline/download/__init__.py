import logging

import azure.functions as func
import json
import os

from ..shared import db_access as DB_Access
from ..shared import vott_json_parser as vott_json_parser

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
        # TODO: images need more meaningful data than just download urls
        image_urls = DB_Access.get_images_for_tagging(connection, imageCount)

        # TODO: Build vott json
        vott_json = vott_json_parser.create_starting_json(image_urls)

        return_body_json = {"imageUrls": image_urls, "vottJson": vott_json}

        content = json.dumps(return_body_json)
        return func.HttpResponse(
            status_code=200, 
            headers=headers, 
            body=content
        )