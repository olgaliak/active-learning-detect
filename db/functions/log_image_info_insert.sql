--On insert of new image info rows we automatically create an entry in the state table
CREATE OR REPLACE FUNCTION log_image_info_insert()
    RETURNS trigger AS
    '
        BEGIN
            INSERT INTO Image_Tagging_State(ImageId,TagStateId,ModifiedDtim,CreatedDtim)
            VALUES(NEW.ImageId,0,current_timestamp,current_timestamp);
            
            RETURN NEW;
        END;
    '
    LANGUAGE plpgsql; 