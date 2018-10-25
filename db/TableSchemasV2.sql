-- Set up table and autoincrementing primary key
CREATE TABLE Image_Info (
    ImageId SERIAL PRIMARY KEY,
    OriginalImageName text NOT NULL,
    ImageLocation text,
    Height integer NOT NULL,
    Width integer NOT NULL
);

-- Set up table and autoincrementing primary key
CREATE TABLE Image_Tagging_State (
    ImageTaggingId SERIAL PRIMARY KEY, --Needed?
    ImageId integer NOT NULL,
    TagStateId integer NOT NULL,
    CreatedDtim date NOT NULL default current_timestamp,
    Valid boolean --Needed?
);

-- Set up table
CREATE TABLE TagState (
    TagStateId integer NOT NULL,
    TagStateName text NOT NULL
);

-- Set up table
CREATE TABLE Image_Tags (
    ImageTagId integer NOT NULL,
    ImageId integer REFERENCES Image_Info(ImageId) ON DELETE RESTRICT,
    Class text NOT NULL, --Needed?
    Confidence double precision NOT NULL, --Needed?
    X_Min integer NOT NULL,
    X_Max integer NOT NULL,
    Y_Min integer NOT NULL,
    Y_Max integer NOT NULL,
    PRIMARY KEY (ImageTagId,ImageId)
);



