import os
import pg8000

from enum import IntEnum, unique

@unique
class ImageTagState(IntEnum):
    NOT_READY = 0
    READY_TO_TAG = 1
    TAG_IN_PROGRESS = 2
    COMPLETED_TAG = 3
    INCOMPLETE_TAG = 4
    ABANDONED = 5

def get_connection():
    return __new_postgres_connection(os.getenv('DB_HOST', None), os.getenv('DB_NAME', None), os.getenv('DB_USER', None), os.getenv('DB_PASS', None))

def __new_postgres_connection(host_name, db_name, db_user, db_pass):
    return pg8000.connect(db_user, host=host_name, unix_sock=None, port=5432, database=db_name, password=db_pass, ssl=True, timeout=None, application_name=None)

def update_tagged_images(conn,list_of_image_ids):
    __update_images(conn, list_of_image_ids, ImageTagState.COMPLETED_TAG)
    print(f"Updated {len(list_of_image_ids)} image(s) to the state {ImageTagState.COMPLETED_TAG.name}")

def update_untagged_images(conn,list_of_image_ids):
    __update_images(conn, list_of_image_ids, ImageTagState.INCOMPLETE_TAG)
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