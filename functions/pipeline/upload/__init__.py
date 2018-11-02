import json

from ..shared import db_access as DB_Access
from ..shared import vott_json_parser as Vott_json_parser

import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:

        vott_json = req.get_json()
        stats = Vott_json_parser.process_vott_json(vott_json)

        connection = DB_Access.get_connection()
        # Update tagged images
        DB_Access.update_tagged_images(connection, stats["imagesVisited"])

        # Update untagged images
        DB_Access.update_untagged_images(connection, stats["imageNotVisisted"])

        return func.HttpResponse(
            body = json.dumps(stats),
            status_code = 200,
            headers = {
                "content-type": "application/json"
                }
        )
    except Exception as e:
        return func.HttpResponse(
            "exception:" + str(e),
            status_code = 500
        )