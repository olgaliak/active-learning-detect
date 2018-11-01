--DROP TRIGGER IF EXISTS image_info_insert ON Image_Info;
CREATE TRIGGER image_info_insert
    AFTER INSERT ON Image_Info
    FOR EACH ROW
        EXECUTE PROCEDURE log_image_info_insert();