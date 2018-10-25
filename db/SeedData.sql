-- Set up the states
INSERT INTO TagState VALUES (0, 'Untagged')
INSERT INTO TagState VALUES (1, 'Tag in progress')
INSERT INTO TagState VALUES (2, 'Tagged')
INSERT INTO TagState VALUES (3, 'Abandoned')

-- Create fake image entries
INSERT INTO Image_Info (OriginalImageName,ImageLocation,Height,Width) 
VALUES ('MyTestImage.jpg', 'https://csehackstorage.blob.core.windows.net/image-to-tag/1.jpg', 40,40)
INSERT INTO Image_Info (OriginalImageName,ImageLocation,Height,Width) 
VALUES ('AnotherImage.jpg', 'https://csehackstorage.blob.core.windows.net/image-to-tag/2.jpg', 60, 80)

-- Create untagged states for the 2 fake images. Assumes the Image Ids are 1 and 2
INSERT INTO Image_Tagging_State (ImageId,TagStateId) VALUES (1, 0)
INSERT INTO Image_Tagging_State (ImageId,TagStateId) VALUES (2, 0)

