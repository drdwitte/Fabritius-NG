# This script is used to generate captions for images in the fabritius dataset online.

from backend.supabase_client import SupabaseClient
from loguru import logger
from backend.llms import LLMClient
from backend.prompts import FULL_PROMPT_VISION

from datetime import datetime, timedelta
import argparse



def get_n_uncaptioned_artworks(db: SupabaseClient, n: int = 5, offset: int = 0) -> list:
    """Get n artworks that have images but no captions."""
    try:
        # Get first artwork with image but no caption
        response = (db.client.table("fabritius")
                   .select("inventarisnummer, imageOpacLink")
                   .neq("imageOpacLink", None)
                   .neq("imageOpacLink", "")  # Exclude empty strings
                   .neq("imageOpacLink", " ")  # Exclude single spaces
                   .is_("gpt_vision_caption", "null")
                   .limit(n)
                   .offset(offset)  # Add offset to skip records
                   .execute())
        
        if response.data:
            artworks = response.data
            logger.info(f"Found {len(artworks)} artworks (offset: {offset})")
            return artworks
        else:
            logger.info(f"No uncaptioned artworks found (offset: {offset})")
            return None
            
    except Exception as e:
        logger.error(f"Error fetching artwork: {e}")
        return None


def update_artwork_caption(db: SupabaseClient, inventory_number: str, caption: str) -> bool:
    """Update the GPT vision caption for an artwork."""
    try:
        response = (db.client.table("fabritius")
                   .update({"gpt_vision_caption": caption})
                   .eq("inventarisnummer", inventory_number)
                   .execute())
        
        if response.data:
            logger.info(f"Updated caption for {inventory_number}")
            return True
        return False
    
    except Exception as e:
        logger.error(f"Error updating caption for {inventory_number}: {e}")
        return False

def update_artwork_captions(db: SupabaseClient, artworks: list) -> None:
    """Update artworks with captions GPT Vision."""
    total = len(artworks)
    successful = 0
    failed = 0
    start_time = datetime.now()
    runtimes = []

    logger.info(f"Starting to process {total} artworks...")
    for idx, artwork in enumerate(artworks, 1):
        item_start = datetime.now()
        logger.info(f"Processing artwork {idx}/{total}: {artwork['inventarisnummer']}")

        try:
            image_url = f"http://193.190.214.119{artwork['imageOpacLink']}"    
            # Generate caption using GPT Vision
            caption = generate_gpt_vision_caption(image_url)

            if caption: 
                    success = update_artwork_caption(   
                        db=db,
                        inventory_number=artwork['inventarisnummer'],
                        caption=caption
                    )
            if success:
                successful += 1
                logger.info(f"✓ Updated {artwork['inventarisnummer']} ({idx}/{total})")
            else:
                failed += 1
                logger.error(f"× Failed to update {artwork['inventarisnummer']} in database")

        except  Exception as e:
            failed += 1
            logger.error(f"× Error processing {artwork['inventarisnummer']}: {e}")
            continue
        
        # Calculate timing for this iteration
        item_duration = datetime.now() - item_start
        runtimes.append(item_duration)
        avg_runtime = sum(runtimes, timedelta()) / len(runtimes)
        
        # Progress summary with timing
        logger.info(f"Progress: {successful} successful, {failed} failed, {total-idx} remaining")
        logger.info(f"Time: This item: {item_duration.seconds}s, Average: {avg_runtime.seconds}s")
        
        if total-idx > 0:  # Estimate remaining time
            est_remaining = avg_runtime * (total-idx)
            est_completion = datetime.now() + est_remaining
            logger.info(f"Estimated completion at: {est_completion.strftime('%H:%M:%S')}")

    # Final summary
    total_duration = datetime.now() - start_time
    logger.info("\n=== Caption Generation Summary ===")
    logger.info(f"Total time: {total_duration}")
    logger.info(f"Average time per artwork: {sum(runtimes, timedelta()) / len(runtimes)}")
    logger.info(f"Successful: {successful}/{total} ({(successful/total)*100:.1f}%)")
    logger.info(f"Failed: {failed}/{total}")


def generate_gpt_vision_caption(image_url: str) -> str:
    """Generate a caption for an image using GPT Vision."""
    try:
        llm = LLMClient()
        
        # Use the URL-specific method (other method works with string)
        prompt_obj = llm.create_llm_message_with_image_url(
            msg=FULL_PROMPT_VISION,
            image_url=image_url
        )
        
        # Get response from GPT Vision
        response = llm.prompt_llm(prompt_obj)
        
        if response and response.output_text:
            logger.info("Successfully generated caption")
            return response.output_text
        else:
            logger.error("No caption generated")
            return None
            
    except Exception as e:
        logger.error(f"Error generating caption: {e}")
        return None


def generate_caption_from_base64(image_base64: str) -> str:
    """Generate a caption for a base64-encoded image using GPT Vision.
    
    Args:
        image_base64: Base64-encoded image data (without data:image prefix)
        
    Returns:
        Caption text or None if failed
    """
    try:
        llm = LLMClient()
        
        # Construct data URL if not already present
        if not image_base64.startswith('data:image'):
            image_url = f"data:image/jpeg;base64,{image_base64}"
        else:
            image_url = image_base64
        
        # Use the URL method (works with data URLs too)
        prompt_obj = llm.create_llm_message_with_image_url(
            msg=FULL_PROMPT_VISION,
            image_url=image_url
        )
        
        # Get response from GPT Vision
        response = llm.prompt_llm(prompt_obj)
        
        if response and response.output_text:
            logger.info("Successfully generated caption from uploaded image")
            return response.output_text
        else:
            logger.error("No caption generated from uploaded image")
            return None
            
    except Exception as e:
        logger.error(f"Error generating caption from base64: {e}")
        return None



def clear_all_captions(db: SupabaseClient) -> bool:
    """Clear all GPT vision captions."""
    try:
        response = (db.client.table("fabritius")
                   .update({"gpt_vision_caption": None})
                   .neq("gpt_vision_caption", None)
                   .execute())
       
    
    except Exception as e:
        logger.error(f"Error clearing captions: {e}")
        return False

def get_caption_stats(db: SupabaseClient) -> tuple[int, int]:
    """Get statistics about captioned and uncaptioned artworks."""
    try:
        # Get total count of artworks with images
        total_response = (db.client.table("fabritius")
                        .select("*", count="exact")
                        .neq("imageOpacLink", None)
                        .execute())
        
        # Get count of captioned artworks
        captioned_response = (db.client.table("fabritius")
                            .select("*", count="exact")
                            .neq("imageOpacLink", None)
                            .neq("gpt_vision_caption", None)
                            .execute())
        
        total = total_response.count
        captioned = captioned_response.count
        
        return captioned, total
    
    except Exception as e:
        logger.error(f"Error fetching caption stats: {e}")
        return 0, 0

def main():
    # Add command line argument parsing
    parser = argparse.ArgumentParser(description='Generate captions for artworks')
    parser.add_argument('-n', '--number', type=int, default=5,
                       help='Number of artworks to process (default: 5)')
    parser.add_argument('-o', '--offset', type=int, default=0,
                       help='Skip first N artworks (default: 0)')
    parser.add_argument('--stats', action='store_true',
                       help='Only show statistics without processing')
    args = parser.parse_args()
    
    db = SupabaseClient()

    # Get current statistics
    captioned, total = get_caption_stats(db)
    logger.info("\n=== Current Caption Status ===")
    logger.info(f"Total artworks with images: {total}")
    logger.info(f"Already captioned: {captioned}")
    logger.info(f"Remaining to caption: {total - captioned}")
    logger.info(f"Progress: {(captioned/total)*100:.1f}%\n")


    #offset zorgt ervoor dat we artworks kunnen skippen in multi-threaded mode
    artworks = get_n_uncaptioned_artworks(db, n=args.number, offset=args.offset)

    if artworks:
        logger.info(f"Starting caption generation for {len(artworks)} artworks...")

        # Process each artwork
        for artwork in artworks:
             image_url = f"{artwork['inventarisnummer']}  http://193.190.214.119{artwork['imageOpacLink']}"
             logger.info(f"Image URL: {image_url}")
        
        # Generate and update captions
        update_artwork_captions(db, artworks)
        
        logger.info("Finished processing batch")
    
    else:
        logger.info("No uncaptioned artworks found to process")
    
    #logger.info("Clearing all captions...")
    #clear_all_captions(db)

if __name__ == "__main__":
    main()