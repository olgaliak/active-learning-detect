import logging
import os
import json
import pg8000

import azure.functions as func

from enum import IntEnum, unique

# TODO: Create DB access library ------------------------
@unique
class ImageTagState(IntEnum):
    NOT_READY = 0
    READY_TO_TAG = 1
    TAG_IN_PROGRESS = 2
    COMPLETED_TAG = 3
    INCOMPLETE_TAG = 4
    ABANDONED = 5

def get_connection():
    return __new_postgres_connection(os.environ['DB_HOST'],os.environ['DB_NAME'],os.environ['DB_USER'],os.environ['DB_PASS'])

def __new_postgres_connection(host_name,db_name,db_user,db_pass):
    return pg8000.connect(db_user, host=host_name, unix_sock=None, port=5432, database=db_name, password=db_pass, ssl=True, timeout=None, application_name=None)

def update_tagged_images(conn,list_of_image_ids):
    __update_images(conn,list_of_image_ids,ImageTagState.COMPLETED_TAG)
    print(f"Updated {len(list_of_image_ids)} image(s) to the state {ImageTagState.COMPLETED_TAG.name}")

def update_untagged_images(conn,list_of_image_ids):
    __update_images(conn,list_of_image_ids,ImageTagState.INCOMPLETE_TAG)
    print(f"Updated {len(list_of_image_ids)} image(s) to the state {ImageTagState.INCOMPLETE_TAG.name}")

def __update_images(conn, list_of_image_ids, new_image_tag_state):
    if not isinstance(new_image_tag_state, ImageTagState):
        raise TypeError('new_image_tag_state must be an instance of Direction Enum')

    if(len(list_of_image_ids) > 0):
        cursor = conn.cursor()
        image_ids_as_strings = [str(i) for i in list_of_image_ids]
        images_to_update = '{0}'.format(', '.join(image_ids_as_strings))
        query = "UPDATE Image_Tagging_State SET TagStateId = {0}, ModifiedDtim = now() WHERE ImageId IN ({1})"
        cursor.execute(query.format(new_image_tag_state,images_to_update))
        conn.commit()
        #print(f"Updated {len(list_of_image_ids)} image(s) to the state {new_image_tag_state.name}")
    else:
        print("No images to update")

# TODO: Create DB access library ------------------------

# TODO: Move this into a library
def get_id_from_filename(filename):
    path_components = filename.split('/')
    filename = path_components[-1]
    return int(filename.split('.')[0])

# TODO: Move this into a library
def process_vott_json(json):
    all_frame_data = json['frames']

    # Scrub filename keys to only have integer Id, drop path and file extensions.
    id_to_tags_dict = {}
    for full_path_key in sorted(all_frame_data.keys()):
        id_to_tags_dict[get_id_from_filename(full_path_key)] = all_frame_data[full_path_key]
    all_ids = id_to_tags_dict.keys()

    # Do the same with visitedFrames
    visited_ids = sorted(json['visitedFrames'])
    for index, filename in enumerate(visited_ids):
        visited_ids[index] = get_id_from_filename(filename)

    # Unvisisted imageIds
    unvisited_ids = sorted(list(set(all_ids) - set(visited_ids)))

    return {
            "totalNumImages" : len(all_ids),
            "numImagesVisted" : len(visited_ids),
            "numImagesNotVisted" : len(unvisited_ids),
            "imagesVisited" : visited_ids,
            "imageNotVisisted" : unvisited_ids
        }

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:

        vott_json = req.get_json()
        stats = process_vott_json(vott_json)

        # Update tagged images
        update_tagged_images(get_connection(), stats["imagesVisited"])

        # Update untagged images
        update_untagged_images(get_connection(), stats["imageNotVisisted"])

        return func.HttpResponse(
             str(stats),
             status_code=200
        )
    except Exception as e:
        return func.HttpResponse(
             "exception:" + str(e),
             status_code=500
        )