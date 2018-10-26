import os
import json

def getId(filename):
    pathComponents = filename.split('/')
    filename = pathComponents[-1]
    return int(filename.split('.')[0])

def processVottJson(vottJson):
    frameTagDict = vottJson['frames']

    # Scrub filename keys to only have integer Id, drop path and file extensions.
    tagsByIdDict = {}
    for oldkey in sorted(frameTagDict.keys()):
        tagsByIdDict[getId(oldkey)] = frameTagDict[oldkey]
    allImageIds = tagsByIdDict.keys()

    # Do the same with visitedFrames
    visitedIds = sorted(vottJson['visitedFrames'])
    for index, filename in enumerate(visitedIds):
        visitedIds[index] = getId(filename)

    # Unvisisted imageIds
    notVisitedIds = sorted(list(set(allImageIds) - set(visitedIds)))

    return {
            "totalNumImages" : len(allImageIds),
            "numImagesVisted" : len(visitedIds),
            "numImagesNotVisted" : len(notVisitedIds),
            "imagesVisited" : visitedIds,
            "imageNotVisisted" : notVisitedIds
        }

try:
    vottJson = json.loads(open(os.environ['req']).read())

    stats = processVottJson(vottJson)
    # TODO: Call interface to update imagesVisited to 'COMPLETED_TAG' state and imageNotVisisted to 'INCOMPLETE_TAG'

    response = open(os.environ['res'], 'w')
    response.write(str(stats))
    response.close()
except Exception as e:
    response = open(os.environ['res'], 'w')
    # TODO: Add error status code and proper message?
    response.write(str(e))
    response.close()