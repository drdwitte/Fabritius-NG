CREATE OR REPLACE VIEW artwork_with_tags_view AS

SELECT
    f."inventarisnummer",
    f."linkToVubis",
    f."beschrijving_titel",
    f."beschrijving_kunstenaar",
    f."imageOpacLink",
    t."label",
    at."provenance",
    at."tag_id",
    f."caption_embedding"
        
FROM fabritius f

JOIN "artwork-tags" at 
    ON f."inventarisnummer" = at."artwork_id"

JOIN tags t
    ON t."id" = at."tag_id";