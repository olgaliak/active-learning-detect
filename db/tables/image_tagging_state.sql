-- Set up table and autoincrementing primary key
CREATE TABLE Image_Tagging_State (
    ImageId integer REFERENCES Image_Info(ImageId),
    TagStateId integer NOT NULL,
    ModifiedDtim timestamp NOT NULL default current_timestamp,
    CreatedDtim timestamp NOT NULL default current_timestamp
);