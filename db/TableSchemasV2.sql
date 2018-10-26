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

-- Set up table and autoincrementing primary key
CREATE TABLE Image_Tagging_State (
    ImageId integer REFERENCES Image_Info(ImageId),
    TagStateId integer NOT NULL,
    ModifiedDtim timestamp NOT NULL default current_timestamp,
    CreatedDtim timestamp NOT NULL default current_timestamp
);

CREATE TABLE Image_Tagging_State_Audit (
    RowId serial primary key,
    ImageId integer NOT NULL,
    TagStateId integer NOT NULL,
    ModifiedDtim timestamp NOT NULL,
    ArchiveDtim timestamp NOT NULL,
    ActionFlag integer NOT NULL 
);

--On insert of new image info rows we automatically create an entry in the state table
CREATE OR REPLACE FUNCTION log_image_info_insert()
    RETURNS trigger AS
    $BODY$
        BEGIN
            INSERT INTO Image_Tagging_State(ImageId,TagStateId,ModifiedDtim,CreatedDtim)
            VALUES(NEW.ImageId,0,current_timestamp,current_timestamp);
            
            RETURN NEW;
        END;
    $BODY$
    LANGUAGE plpgsql; 

DROP TRIGGER IF EXISTS image_info_insert ON Image_Info;
CREATE TRIGGER image_info_insert
    AFTER INSERT ON Image_Info
    FOR EACH ROW
        EXECUTE PROCEDURE log_image_info_insert();


-- ActionFlag: 1 = insert, 2 = update, 3 = delete
CREATE OR REPLACE FUNCTION log_image_tagging_state_insert()
    RETURNS trigger AS
    $BODY$
        BEGIN
            INSERT INTO Image_Tagging_State_Audit(ImageId,TagStateId,ModifiedDtim,ArchiveDtim,ActionFlag)
            VALUES(NEW.ImageId,NEW.TagStateId,NEW.ModifiedDtim,current_timestamp,1);
            
            RETURN NEW;
        END;
    $BODY$
    LANGUAGE plpgsql; 

DROP TRIGGER IF EXISTS image_tagging_state_insert ON Image_Tagging_State;
CREATE TRIGGER image_tagging_state_insert
    AFTER INSERT ON Image_Tagging_State
    FOR EACH ROW
        EXECUTE PROCEDURE log_image_tagging_state_insert();


CREATE OR REPLACE FUNCTION log_image_tagging_state_changes()
    RETURNS trigger AS
    $BODY$
        BEGIN
            IF NEW.TagStateId <> OLD.TagStateId THEN
                INSERT INTO Image_Tagging_State_Audit(ImageId,TagStateId,ModifiedDtim,ArchiveDtim,ActionFlag)
                VALUES(NEW.ImageId,NEW.TagStateId,NEW.ModifiedDtim,current_timestamp,2);
            END IF;
            
            RETURN NEW;
        END;
    $BODY$
    LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS image_tagging_state_changes ON Image_Tagging_State;
CREATE TRIGGER image_tagging_state_changes
    BEFORE UPDATE ON Image_Tagging_State
    FOR EACH ROW
        EXECUTE PROCEDURE log_image_tagging_state_changes();







