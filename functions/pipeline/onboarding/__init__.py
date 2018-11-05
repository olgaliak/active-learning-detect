import logging
import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        req_body = req.get_json()
        logging.error(req.get_json())
        url_list = req_body["imageUrls"]
        url_string = (", ".join(url_list))
    except ValueError:
        print("Unable to decode JSON body")
        return func.HttpResponse("Unable to decode POST body", status_code=400)

    logging.error(req_body)
    return func.HttpResponse("Got body: " + url_string, status_code=200)