

def attempt_get_blob(blob_credentials, blob_name, blob_dest):
    if blob_credentials is None:
        print ("blob_credentials is None, can not get blob")
        return  False
    blob_service, container_name = blob_credentials
    is_successful = False
    print("Dest: {0}".format(blob_dest))
    try:
        blob_service.get_blob_to_path(container_name, blob_name, blob_dest)
        is_successful = True
    except:
        print("Error when getting blob")
        print("Src: {0} {1}".format(container_name, blob_name))


    return is_successful

