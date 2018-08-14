import os
from PIL import Image

curpath = os.getcwd()
for root, dirs, files in os.walk(curpath, topdown=False):
    for name in files:
        if os.path.splitext(os.path.join(root, name))[1].lower() == ".tif":
            reldir = os.path.relpath(root, curpath)
            if os.path.isfile(os.path.splitext(os.path.join(curpath, "JPEG", reldir, name))[0] + ".jpg"):
                print("A jpeg file already exists for %s" % name)
            else:
                outfile = os.path.splitext(os.path.join(curpath, "JPEG", reldir, name))[0] + ".jpg"
                if not os.path.exists(os.path.join(curpath, "JPEG", reldir)):
                    os.makedirs(os.path.join(curpath, "JPEG", reldir))
                try:
                    im = Image.open(os.path.join(root, name))
                    print("Generating jpeg for %s" % name)
                    im.thumbnail(im.size)
                    im.save(outfile, "JPEG", quality=95)
                except:
                    print("Error")
        else:
            print(os.path.join(root, name) + " is not a tiff file.")