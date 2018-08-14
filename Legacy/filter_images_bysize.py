#source: https://www.geeksforgeeks.org/filtering-images-based-size-attributes-python/
from PIL import Image
from shutil import copyfile
import os, os.path


def filterImages(path, thresholdWidth, thresholdHeight):
    # Defining images array for
    # identifying only image files
    imgs = []

    # List of possible images extensions
    # add if you want more
    valid_images = [".jpg", ".gif", ".png", ".tga",
                    ".jpeg", ".PNG", ".JPG", ".JPEG"]

    # Storing all images in images array (imgs)
    for f in os.listdir(path):
        ext = os.path.splitext(f)[1]

        if ext.lower() not in valid_images:
            continue
        imgs.append(f)

    # Checking whether the filteredImages
    # directory exists or not
    directory = os.path.dirname('filteredImages' + path)
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Defining filteredIMages array for
    # storing all the images we need
    filteredImages = []

    for i in imgs:
        image = Image.open(os.path.join(path, i))

        # Storing width and height of a image
        width, height = image.size

        # if only width exceeds the thresholdWidth
        if (width > thresholdWidth and
                height <= thresholdHeight):

            image.resize((thresholdWidth,
                          (thresholdWidth * height)
                          // width)).save(i)

        # if only height exceeds the thresholdHeight
        elif (width <= thresholdWidth and
              height > thresholdHeight):

            image.resize(((thresholdHeight * width)
                          // height, thresholdHeight)).save(i)

        # if both the paramateres exceeds
        # the threshold attributes
        elif (width > thresholdWidth and
              height > thresholdHeight):

            image.resize((thresholdWidth, thresholdHeight)).save(i)

        copyfile(os.path.join(path, i),
                 os.path.join(path + '/filteredImages', i))

        filteredImages.append(i)

    # returning the filteredImages array
    return filteredImages


# Driver Code
if __name__ == '__main__':
    filteredImages = []

    # Enter the path of the python sizeFilter
    # file, the thresholdWidth(in pixels) and
    # thresholdHeight(in pixels)
    filteredImages = filterImages("path", 1000, 1000)
