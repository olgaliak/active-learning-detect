-- Set up the states
INSERT INTO TagState VALUES (0, 'Not Ready');
INSERT INTO TagState VALUES (1, 'Ready To Tag');
INSERT INTO TagState VALUES (2, 'Tag In Progress');
INSERT INTO TagState VALUES (3, 'Completed Tag');
INSERT INTO TagState VALUES (4, 'Incomplete Tag');
INSERT INTO TagState VALUES (5, 'Abandoned');

-- Create fake image entries
INSERT INTO Image_Info (OriginalImageName,ImageLocation,Height,Width) 
VALUES ('MyTestImage.jpg', 'https://csehackstorage.blob.core.windows.net/image-to-tag/1.jpg', 40,40);
INSERT INTO Image_Info (OriginalImageName,ImageLocation,Height,Width) 
VALUES ('AnotherImage.jpg', 'https://csehackstorage.blob.core.windows.net/image-to-tag/2.jpg', 60, 80);
INSERT INTO Image_Info (OriginalImageName,ImageLocation,Height,Width) 
VALUES ('NonexistantImage.jpg', 'https://csehackstorage.blob.core.windows.net/image-to-tag/3.jpg', 60, 80);

-- Create "ready to tag" states for the 2 fake images
INSERT INTO Image_Tagging_State (ImageId,TagStateId) VALUES (1, 1);
INSERT INTO Image_Tagging_State (ImageId,TagStateId) VALUES (2, 1);
INSERT INTO Image_Tagging_State (ImageId,TagStateId) VALUES (3, 1);

