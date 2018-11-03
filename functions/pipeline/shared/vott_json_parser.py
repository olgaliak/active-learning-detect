import json

def __build_frames_data(images):
    frames = {}
    for filename in images:
        # TODO: Build tag data per frame if they exist already
        frames[__get_filename_from_fullpath(filename)] = [] #list of tags
    return frames

# TODO: Change return from db to have more tag data...for now input is a list of blobstore urls
def create_starting_json(images):
    return {
        "frames" : __build_frames_data(images),
        "inputTags": "", # TODO: populate classifications that exist in db already
    }

def __get_filename_from_fullpath(filename):
    path_components = filename.split('/')
    return path_components[-1]

def __get_id_from_fullpath(fullpath):
    return int(__get_filename_from_fullpath(fullpath).split('.')[0])

def process_vott_json(json):
    all_frame_data = json['frames']

    # Scrub filename keys to only have integer Id, drop path and file extensions.
    id_to_tags_dict = {}
    for full_path_key in sorted(all_frame_data.keys()):
        id_to_tags_dict[__get_id_from_fullpath(full_path_key)] = all_frame_data[full_path_key]
    all_ids = id_to_tags_dict.keys()

    # Do the same with visitedFrames
    visited_ids = sorted(json['visitedFrames'])
    for index, filename in enumerate(visited_ids):
        visited_ids[index] = __get_id_from_fullpath(filename)

    # Unvisisted imageIds
    unvisited_ids = sorted(list(set(all_ids) - set(visited_ids)))

    return {
            "totalNumImages" : len(all_ids),
            "numImagesVisted" : len(visited_ids),
            "numImagesNotVisted" : len(unvisited_ids),
            "imagesVisited" : visited_ids,
            "imagesNotVisited" : unvisited_ids
        }

def main():
    images = {
		"1012.png" : {},
		"1013.png" : {},
		"1014.png" : {},
		"1015.png" : {},
		"1016.png" : {}
	}
    generated_json = create_starting_json(images)
    print(json.dumps(generated_json))

if __name__ == '__main__':
    main()
