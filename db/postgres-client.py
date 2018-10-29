import sys
import string
import pg8000
import random
import os
import time
from enum import IntEnum, unique

@unique
class ImageTagState(IntEnum):
    NOT_READY = 0
    READY_TO_TAG = 1
    TAG_IN_PROGRESS = 2
    COMPLETED_TAG = 3
    INCOMPLETE_TAG = 4
    ABANDONED = 5

# An entity class for a VOTT image
class ImageInfo(object):
    def __init__(self, image_name, image_location, height, width):
        self.image_name = image_name
        self.image_location = image_location
        self.height = height
        self.width = width

def get_connection():
    return __new_postgres_connection(os.environ['DB_HOST'],os.environ['DB_NAME'],os.environ['DB_USER'],os.environ['DB_PASS'])

def __new_postgres_connection(host_name,db_name,db_user,db_pass):
    return pg8000.connect(db_user, host=host_name, unix_sock=None, port=5432, database=db_name, password=db_pass, ssl=True, timeout=None, application_name=None)

def __verify_connect_to_db(conn):
    cursor = conn.cursor()
    cursor.execute('select * from tagstate')
    row = cursor.fetchone()  
    print()
    while row:  
        print(str(row[0]) + " " + str(row[1]))    
        row = cursor.fetchone()

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def generate_test_image_infos(count):
    list_of_image_infos = []
    for i in range(count):
        file_name = f'{id_generator(size=random.randint(4,10))}.jpg'
        image_location = f'https://mock-storage.blob.core.windows.net/new-uploads/{file_name}'
        img = ImageInfo(file_name,image_location,random.randint(100,600),random.randint(100,600))
        list_of_image_infos.append(img)
    return list_of_image_infos

def get_image_ids_for_new_images(conn, list_of_image_infos):
    url_to_image_id_map = {}
    if(len(list_of_image_infos) > 0):
        cursor = conn.cursor()
        for img in list(list_of_image_infos):
            query = "INSERT INTO Image_Info (OriginalImageName,ImageLocation,Height,Width) VALUES ('{0}','{1}',{2},{3}) RETURNING ImageId;"
            cursor.execute(query.format(img.image_name,img.image_location,str(img.height),str(img.width)))
            new_img_id = cursor.fetchone()[0]
            url_to_image_id_map[img.image_location] = new_img_id
            #__update_images(conn,[new_img_id],ImageTagState.NOT_READY)
        conn.commit()
    print(f"Inserted {len(url_to_image_id_map)} images to the DB")
    return url_to_image_id_map

def get_new_images(conn,number_of_images):
    cursor = conn.cursor()

    # GET N existing UNTAGGED rows
    selected_images_to_tag = {}
    query = ("SELECT b.ImageId, b.ImageLocation, a.TagStateId FROM Image_Tagging_State a "
            "JOIN Image_Info b ON a.ImageId = b.ImageId WHERE a.TagStateId = 1 order by "
            "a.createddtim DESC limit {0}")
    cursor.execute(query.format(number_of_images))
    for row in cursor:
        print('Image Id: {0} \t\tImage Name: {1} \t\tTag State: {2}'.format(row[0], row[1], row[2]))
        selected_images_to_tag[str(row[0])] = str(row[1])

    __update_images(conn,selected_images_to_tag,ImageTagState.TAG_IN_PROGRESS)
    return selected_images_to_tag.values()

def update_image_urls(conn,image_id_to_url_map):
     for image_id, new_url in image_id_to_url_map.items():
        cursor = conn.cursor()
        query = "UPDATE Image_Info SET ImageLocation = '{0}', ModifiedDtim = now() WHERE ImageId = {1}"
        cursor.execute(query.format(new_url,image_id))
        print(f"Updated ImageId: {image_id} to new ImageLocation: {new_url}")
        __update_images(conn,[image_id],ImageTagState.READY_TO_TAG)
        print(f"ImageId: {image_id} to has a new state: {ImageTagState.READY_TO_TAG.name}")
        conn.commit()
        
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
        
def get_transformed_id_to_url_map(id_to_url_map):
    updated_image_id_url_map = {}
    for image_id, old_url in id_to_url_map.items():
        replaced_path = old_url.replace('new-uploads','perm-uploads')   
        file_name_to_replace = extract_image_name_no_suffix(replaced_path)
        transformed_path = replaced_path.replace(file_name_to_replace,str(image_id))
        updated_image_id_url_map[image_id] = transformed_path
    return updated_image_id_url_map

def pretty_print_audit_history(conn, list_of_image_ids):
    if(len(list_of_image_ids) > 0):
        cursor = conn.cursor()
        image_ids_as_strings = [str(i) for i in list_of_image_ids]
        images_to_audit = '{0}'.format(', '.join(image_ids_as_strings))
        query = ("SELECT a.imageid,c.originalimagename, b.tagstatename, a.ArchiveDtim FROM image_tagging_state_audit a "
                "JOIN tagstate b ON a.tagstateid = b.tagstateid "
                "JOIN image_info c on a.imageid = c.imageid "
                "WHERE a.ImageId in ({0}) "
                "ORDER BY a.ImageId,ArchiveDtim ASC")
        cursor.execute(query.format(images_to_audit))
        row = cursor.fetchone()  
        print()
        if(row != None):
            print("ImageId\t\tOriginalImageName\t\tTagState\t\tTransitionTime")
        while row:  
            print(f"{str(row[0])}\t\t{str(row[1])}\t\t{str(row[2])}\t\t{str(row[3])}")  
            row = cursor.fetchone()
    else:
        print("No images!")

def extract_image_name_no_suffix(url):
    start_idx = url.rfind('/')+1
    end_idx = url.rfind('.')
    return url[start_idx:end_idx]

def extract_image_id_from_urls(list_of_image_urls):
        extracted_image_ids = []
        for url in list_of_image_urls:
            extracted_id = int(extract_image_name_no_suffix(url))
            extracted_image_ids.append(extracted_id)
        return extracted_image_ids

def main():
    try:
        if(os.getenv("DB_HOST") is None or os.getenv("DB_USER") is None or os.getenv("DB_NAME") is None or os.getenv("DB_PASS") is None):
            print("Please set environment variables for DB_HOST, DB_USER, DB_NAME, DB_PASS")
            return
        #################################################################
        # Below we simulate the following scenarios:
        #   Onboarding of new images
        #   Checking out images to tag
        #   Checking in images that have or have not been tagged
        #################################################################   

        NUMBER_OF_IMAGES = 5
        
        # Simulate new images from VOTT getting created in some blob store
        mocked_images = generate_test_image_infos(NUMBER_OF_IMAGES)
        print()
        print("***\tSubject matter experts use the CLI to upload new images...")
        time.sleep(1)
        print()
        # Simulate the data access layer creating entries in the DB for the new images
        # and returning a map of the original image url to generaled image id 
        url_to_image_id_map = get_image_ids_for_new_images(get_connection(),mocked_images)
        print()

        print("***\tBehind the scenes Az Functions move the images to a new blob location")
        time.sleep(1)
        print()
        #Invert the above map since the client will now be using the image id as a key
        image_to_url = {v: k for k, v in url_to_image_id_map.items()}

        # Simulates when the client has moved images to a new blob store container
        # and creates a payload for the data access layer with a map for image id to new urls
        updated_image_id_url_map = get_transformed_id_to_url_map(image_to_url)
        
        # Simulates the call the client makes to the data access layer
        # with the new payload. Image urls get updated in the DB
        update_image_urls(get_connection(),updated_image_id_url_map)
        
        print()
        print("***\tThe newly uploaded images are now onboarded with a 'ready to tag' state.  See audit history")
        print()
        time.sleep(1)
        
        # Prints the audit history of the generated of all the newly onboarded 
        # images involved in the simulation to prove the state tracking for onboarding.
        image_ids = list(updated_image_id_url_map.keys())
        pretty_print_audit_history(get_connection(),image_ids)
        time.sleep(3)
        print()

        print("***\tSubject matter experts use the CLI to retrieve images in a 'ready to tag' state")
        time.sleep(2)
        print()

        list_of_image_urls = get_new_images(get_connection(),NUMBER_OF_IMAGES)
        print()
        print("***\tLet's wait for image taggers to get through the set of images....")
        time.sleep(5)
        print()
        print("***\tDone! Though the subject matter experts didn't complete tagging all images")
        time.sleep(2)
        print()
        
        print("***\tRegardless the SMEs use the CLI to post the VOTT json results")
        print()
        # Since we rename the original image name to a integer that matchs the DB image id
        # we need to extract out the image ids. Below this code is simulates extracting 
        # image ids from the VOTT JSON
        extracted_image_ids = extract_image_id_from_urls(list_of_image_urls)
       
        # Let assume 3 images got tagged and 2 images did not. The client will
        # call corresponding methods to update tagged and untagged states
        completed_tagged_ids = []
        incomplete_tagged_ids = []
        for idx, img_id in enumerate(extracted_image_ids):
            if(idx > 2):
                incomplete_tagged_ids.append(img_id)
            else:
                completed_tagged_ids.append(img_id)

        update_tagged_images(get_connection(),completed_tagged_ids)
        update_untagged_images(get_connection(),incomplete_tagged_ids)
        
        print()
        print("***\tVOTT json results are posted. Lets take a look at the audit history")
        time.sleep(2)
        # Finally lets look at the audit history again. We expect to see some images as tagged
        # and some as incomplete
        print()
        pretty_print_audit_history(get_connection(),image_ids)

        print()
        print("Success!")
        
        #__verify_connect_to_db(get_connection())
        #get_unvisited_items(get_connection(),count_of_images)
    except Exception as e: print(e)

if __name__ == "__main__":
    main()
