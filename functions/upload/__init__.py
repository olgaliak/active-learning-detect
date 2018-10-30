import os
import json

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

def main():
    try:
        vott_json = json.loads(open(os.environ['req']).read())

        stats = process_vott_json(vott_json)
        # TODO: Call interface to update imagesVisited to 'COMPLETED_TAG' state and imageNotVisisted to 'INCOMPLETE_TAG'

        response = open(os.environ['res'], 'w')
        response.write(str(stats))
        response.close()
    except Exception as e:
        response = open(os.environ['res'], 'w')
        # TODO: Add error status code and proper message?
        response.write(str(e))
        response.close()

if __name__ == "__main__":
    main()