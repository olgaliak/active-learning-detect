-- Set up table and autoincrementing primary key
CREATE TABLE Image_Info (
    ImageId SERIAL PRIMARY KEY,
    OriginalImageName text NOT NULL,
    ImageLocation text,
    Height integer NOT NULL,
    Width integer NOT NULL,
    ModifiedDtim timestamp NOT NULL default current_timestamp,
    CreatedDtim timestamp NOT NULL default current_timestamp
);