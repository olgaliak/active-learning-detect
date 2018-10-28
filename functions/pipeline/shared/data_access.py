import logging
import json
import azure.functions as func  # Getting an error - E0401: Unable to import
import os
import pg8000   # Getting an error - E0401: Unable to import

# Constants
untagged_state = 0
tagging_state = 1
tagged_state = 2


host = os.getenv('DB_HOST', None)
user = os.getenv('DB_USER', None) 
dbname = os.getenv('DB_NAME', None)
password = os.getenv('DB_PASS', None)

# Creates rows in the database for new images uploaded to blob storage.
# Requires: TBD
# Receives: List of new image names, user id of the user performing the upload
# Returns: None.
# TODO: Clarify if input list is a list of original image names or new ImageIds
# Code:

# get_unvisited_items
# # Retrieves a number of untagged images for the user to tag.
# Requires: Assumes that the CLI (the requestor) handles setting a cap on the number of images that may be requested.
#           For now, assumes the user wants to use a LIFO strategy, and pull newest images first.
# Receives: num_images = Number of images the user wants to download for tagging
# Returns: List of URLs to the selected images (in blob storage) that need to be tagged.  Status for these images is updated to "tagging" status in the DB.
# TODO: Future inputs: Strategy for selecting images (enum), user_id for tracking which user made the request (string)
def get_unvisited_items(num_images):
        # Connect to database
        # TODO: Add error handling
        db = pg8000.connect(user, host=host, unix_sock=None, port=5432, database=dbname, password=password, ssl=True, timeout=None, application_name=None)
        cursor = db.cursor()

        # From the database, select the number of images the user requested where tag state is "untagged"
        cursor.execute("SELECT b.ImageId, b.OriginalImageName, a.TagStateId, b.ImageLocation FROM Image_Tagging_State a JOIN Image_Info b ON a.ImageId = b.ImageId WHERE a.TagStateId = {0} order by a.createddtim DESC limit {1}".format(untagged_state, num_images))

        # Put the ImageId and ImageLocation (URL) for the images to tag into a dictionary named selected_images_to_tag
        selected_images_to_tag = {}
        for row in cursor:
                print('Image Id: {0} \t\tImage Name: {1} \t\tTag State: {2}'.format(row[0], row[1], row[2]))
                selected_images_to_tag[str(row[0])] = str(row[3])

        # If there are images in the list, update the tagging state for the selected images from "untagged" to "tagging" state
        # If there are no images left to tag, output a message to the user
        # TODO: Separate this code out into an "update" helper function?
        if(len(selected_images_to_tag) > 0):
                images_to_update = '{0}'.format(', '.join(selected_images_to_tag.keys()))
                cursor.execute("UPDATE Image_Tagging_State SET TagStateId = {0} WHERE ImageId IN ({1})".format(tagging_state,images_to_update))
                db.commit()
                print(f"Updated {len(selected_images_to_tag)} images to the state {tagging_state}")
        else:
                print("No images untagged images left!")

        # Return the list of URLs to the user (values in the selected_images_to_tag dictionary)
        return list(selected_images_to_tag.values())

# TODO: Create helper function to update status of a list of images in the DB from one state to another.
 
# get_unvisited_items (count of items, strategy enum, user id) 
# Returns a list of image locations 
# update_visited_items (List of visited image names, user id) 
# void 
# update_unvisited_items (List of unvisited image names, user id) 
# Void
