-- Set up table
CREATE TABLE Image_Tags (
    ImageTagId integer NOT NULL,
    ImageId integer REFERENCES Image_Info(ImageId) ON DELETE RESTRICT,
    --ClassificationId text NOT NULL, --Needed?
    --Confidence double precision NOT NULL, --Needed?
    X_Min integer NOT NULL,
    X_Max integer NOT NULL,
    Y_Min integer NOT NULL,
    Y_Max integer NOT NULL,
    --VOTT_Data json NOT NULL
    PRIMARY KEY (ImageTagId,ImageId)
);