

def attempt_get_blob(blob_credentials, blob_name, blob_dest):
    if blob_credentials is None:
        print ("blob_credentials is None, can not get blob")
        return  False
    blob_service, container_name = blob_credentials
    is_successful = False
    print("Dest: {0}".format(blob_dest))
    #res = blob_service.list_blobs(container_name, prefix="IC_Mona_2018_cam27_")
    # r_inf = blob_service.list_blobs(container_name, prefix="infusions/")
    #r_rand  = blob_service.list_blobs(container_name, prefix="random/")
    # r_inf.items[0].name
    #numpy.savetxt("rtest.csv", r_test.items, delimiter=",", fmt='%s')
    #[n.name for n in r_test]
    # numpy.savetxt("rtest.csv", [n.name for n in r_test] , delimiter=",", fmt='%s')
    try:
        blob_service.get_blob_to_path(container_name, blob_name, blob_dest)
        is_successful = True
    except:
        print("Error when getting blob")
        print("Src: {0} {1}".format(container_name, blob_name))


    return is_successful

