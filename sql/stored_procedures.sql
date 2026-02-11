
#vector_search function (procedure for search in fabritius)

#arguments: query_embedding (vector(1536)), match_count (int)

select
    inventarisnummer,
    gpt_vision_caption,
    "imageOpacLink",
    1 - (caption_embedding <=> query_embedding) as similarity

from fabritius
where caption_embedding is not null
order by caption_embedding <=> query_embedding
limit match_count;


