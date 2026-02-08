from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from .llms import LLMClient
from loguru import logger

class SupabaseClient:
    """Handles all Supabase database interactions."""

    # Table name constants
    TABLE_FABRITIUS = "fabritius"
    TABLE_TAGS = "tags"
    TABLE_ARTWORK_TAGS = "artwork-tags"
    VIEW_ARTWORK_WITH_TAGS = "artwork_with_tags_view"

    # Configureerbare zoekvelden
    SEARCH_FIELDS = {
        'basic': [
            'inventarisnummer',
            'beschrijving_kunstenaar',
            'beschrijving_titel',
            'imageOpacLink'
        ],
    }
    
    
    def __init__(self):
        load_dotenv()
        # Try FABRITIUS_ prefix first, fallback to direct name
        self.url = os.getenv("FABRITIUS_SUPABASE_URL") or os.getenv("SUPABASE_URL")
        self.key = os.getenv("FABRITIUS_SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.client: Client = create_client(self.url, self.key)
    
    # Analytics / Insights methods (mockup data for now)
    
    def get_total_artworks(self) -> int:
        """Get total number of artworks in database.
        
        Returns:
            Total artwork count (currently mockup: 12,375)
        """
        # TODO: Replace with actual query: self.client.table(self.TABLE_FABRITIUS).select("count", count="exact").execute().count
        return 12375
    
    def get_unique_tags_count(self) -> int:
        """Get number of unique tags in database.
        
        Returns:
            Unique tags count (currently mockup: 4,597)
        """
        # TODO: Replace with actual query: self.client.table(self.TABLE_TAGS).select("count", count="exact").execute().count
        return 4597
    
    def get_assigned_tags_count(self) -> int:
        """Get total number of tag assignments (artwork-tag relationships).
        
        Returns:
            Total assigned tags count (currently mockup: 63,200)
        """
        # TODO: Replace with actual query: self.client.table(self.TABLE_ARTWORK_TAGS).select("count", count="exact").execute().count
        return 63200
    
    def get_tag_activity(self, period: str = 'day', days: int = 30) -> List[Dict]:
        """Get tag activity over time (created, deleted, promoted, demoted).
        
        Args:
            period: Aggregation period ('day', 'week', 'month')
            days: Number of days to look back
            
        Returns:
            List of dicts with date, created, deleted, promoted, demoted counts (mockup data)
        """
        # TODO: Replace with actual query from tag history/audit table
        from datetime import datetime, timedelta
        import random
        
        # Fixed date range: Dec 1, 2025 to Feb 9, 2026 (70 days)
        start_date = datetime(2025, 12, 1)
        end_date = datetime(2026, 2, 9)
        total_days = (end_date - start_date).days + 1
        
        data = []
        
        if period == 'day':
            num_days = min(days, total_days)
            for i in range(num_days):
                date = start_date + timedelta(days=i)
                data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'created': random.randint(10, 50),
                    'deleted': random.randint(0, 15),
                    'promoted': random.randint(5, 25),
                    'demoted': random.randint(0, 10)
                })
        elif period == 'week':
            num_weeks = min(days // 7, total_days // 7)
            for i in range(num_weeks):
                date = start_date + timedelta(weeks=i)
                data.append({
                    'date': date.strftime('Week %W'),
                    'created': random.randint(100, 300),
                    'deleted': random.randint(10, 80),
                    'promoted': random.randint(50, 150),
                    'demoted': random.randint(10, 60)
                })
        else:  # month
            # Dec 2025, Jan 2026, Feb 2026
            data.append({
                'date': 'December 2025',
                'created': random.randint(400, 1200),
                'deleted': random.randint(50, 300),
                'promoted': random.randint(200, 600),
                'demoted': random.randint(50, 250)
            })
            data.append({
                'date': 'January 2026',
                'created': random.randint(400, 1200),
                'deleted': random.randint(50, 300),
                'promoted': random.randint(200, 600),
                'demoted': random.randint(50, 250)
            })
            data.append({
                'date': 'February 2026',
                'created': random.randint(200, 600),
                'deleted': random.randint(25, 150),
                'promoted': random.randint(100, 300),
                'demoted': random.randint(25, 125)
            })
        
        return data
    
    def get_user_contributions(self, days: int = 90) -> Dict[str, List[Dict]]:
        """Get user contribution activity (GitHub-style calendar data).
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dict mapping usernames to list of {date, count} contributions (mockup data)
        """
        # TODO: Replace with actual query from tag history/audit table grouped by user
        from datetime import datetime, timedelta
        import random
        
        # Fixed date range: Dec 1, 2025 to Feb 9, 2026 (70 days)
        start_date = datetime(2025, 12, 1)
        end_date = datetime(2026, 2, 9)
        total_days = (end_date - start_date).days + 1
        
        users = ['Dieter', 'Lies', 'Karine', 'Lara', 'Wouter', 'Roxanne']
        
        contributions = {}
        for user in users:
            user_data = []
            for i in range(total_days):
                date = start_date + timedelta(days=i)
                # Random contributions with some days having 0 (realistic pattern)
                count = random.choices([0, random.randint(1, 5), random.randint(5, 15), random.randint(15, 40)], 
                                      weights=[0.3, 0.4, 0.2, 0.1])[0]
                user_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'count': count
                })
            contributions[user] = user_data
        
        return contributions
    
    def get_llm_statistics(self, period: str = 'day', days: int = 30) -> List[Dict]:
        """Get LLM usage statistics (API calls and token consumption).
        
        Args:
            period: Aggregation period ('day', 'week', 'month')
            days: Number of days to look back
            
        Returns:
            List of dicts with date, api_calls, tokens_used (mockup data)
        """
        # TODO: Replace with actual query from LLM usage logs/metrics table
        from datetime import datetime, timedelta
        import random
        
        # Fixed date range: Dec 1, 2025 to Feb 9, 2026 (70 days)
        start_date = datetime(2025, 12, 1)
        end_date = datetime(2026, 2, 9)
        total_days = (end_date - start_date).days + 1
        
        data = []
        
        if period == 'day':
            num_days = min(days, total_days)
            for i in range(num_days):
                date = start_date + timedelta(days=i)
                data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'api_calls': random.randint(50, 200),
                    'tokens_used': random.randint(5000, 25000)
                })
        elif period == 'week':
            num_weeks = min(days // 7, total_days // 7)
            for i in range(num_weeks):
                date = start_date + timedelta(weeks=i)
                data.append({
                    'date': date.strftime('Week %W'),
                    'api_calls': random.randint(500, 1400),
                    'tokens_used': random.randint(50000, 180000)
                })
        else:  # month
            # Dec 2025, Jan 2026, Feb 2026
            data.append({
                'date': 'December 2025',
                'api_calls': random.randint(2000, 6000),
                'tokens_used': random.randint(200000, 750000)
            })
            data.append({
                'date': 'January 2026',
                'api_calls': random.randint(2000, 6000),
                'tokens_used': random.randint(200000, 750000)
            })
            data.append({
                'date': 'February 2026',
                'api_calls': random.randint(1000, 3000),
                'tokens_used': random.randint(100000, 375000)
            })
        
        return data
    
    def search_artworks_by_tag(self, tag_query: str, limit: int = 10) -> List[Dict]:
        """Search artworks that contain a specific tag.
        
        Args:
            tag_query: Tag name to search for (partial match)
            limit: Maximum number of results to return
            
        Returns:
            List of artwork dicts with tag information (mockup data)
        """
        # TODO: Replace with actual query joining artwork-tags, tags, and fabritius tables
        import random
        
        # Mock data - in reality would query VIEW_ARTWORK_WITH_TAGS or join tables
        artists = ['Peter Paul Rubens', 'Pieter Bruegel', 'René Magritte', 'James Ensor', 'Anthony van Dyck']
        centuries = ['15th', '16th', '17th', '18th', '19th', '20th']
        
        results = []
        for i in range(limit):
            results.append({
                'inventarisnummer': f'INV-{random.randint(1000, 9999)}',
                'beschrijving_kunstenaar': random.choice(artists),
                'beschrijving_titel': f'Artwork Title {i+1}',
                'tag_name': tag_query,
                'tag_level': random.randint(1, 3),
                'confidence': round(random.uniform(0.7, 0.99), 2)
            })
        
        return results
    
    def get_tag_distribution(self, page: int = 1, page_size: int = 100) -> Dict:
        """Get tag distribution with occurrence counts (paginated).
        
        Args:
            page: Page number (1-based)
            page_size: Number of tags per page
            
        Returns:
            Dict with tags, counts, total_tags, current_page, total_pages (mockup data)
        """
        # TODO: Replace with actual query grouping by tag and counting artworks
        # SELECT tag_name, COUNT(*) as count FROM artwork_tags GROUP BY tag_name ORDER BY count DESC
        import random
        
        # Real tag names from KMSKB (only meaningful tags)
        all_tags = [
            'naakt', 'man', 'vrouw', 'figuur', 'interieur', 'profiel', 'water', 'zeilboot', 
            'officieel bezoek', 'oever', 'Schelde', 'bezoek', 'brug', 'koe', 'Maria de\' Medici', 
            'Antwerpen', 'scene', 'omwalling', 'Sint-Walburgiskerk', 'Sint-Andrieskerk', 
            'Vlaams Hoofd', 'dier', 'Sint-Michielsabdij', 'huis', 'stroom', 'toeschouwer', 
            'stad', 'groet', 'toren', 'Onze-Lieve-Vrouwekathedraal', 'vlotten', 'kanon', 
            'Isabella Clara Eugenia', 'cirkel', 'steen', 'gebed', 'kind', 'kerk', 'buste', 
            'portret', 'hand', 'open', 'deur', 'naaktheid', 'ten voeten uit', 'samengevoegd', 
            'kunstenaar', 'ten halven lijve', 'Carel de Moor', 'zelfportret'
        ]
        
        total_tags = len(all_tags)
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_tags)
        
        tags = []
        counts = []
        
        for i in range(start_idx, end_idx):
            tags.append(all_tags[i])
            # Realistic distribution: some tags very common, most rare
            if i < 10:
                count = random.randint(800, 2000)
            elif i < 25:
                count = random.randint(200, 800)
            else:
                count = random.randint(50, 200)
            counts.append(count)
        
        return {
            'tags': tags,
            'counts': counts,
            'total_tags': total_tags,
            'current_page': page,
            'total_pages': (total_tags + page_size - 1) // page_size
        }
        
    def get_artworks(self, page: int = 1, items_per_page: int = 12, search_params: dict = None) -> List[Dict]:
        """Fetch artworks with pagination and optional search filters.
    
        Implementation details:
        1. First gets total count for pagination
        2. Then fetches actual data for current page
        3. Handles both regular and semantic search through search_params
        
        Args:
            page: Current page number (1-based)
            items_per_page: Number of items per page
            search_params: Optional filters for inventory number, artist, title
                        For semantic search, inventory_number will be a list
        """
        try:
            # Calculate pagination bounds
            start = (page - 1) * items_per_page
            end = start + items_per_page - 1


            # Get total count with filters
            count_query = self.client.table(self.TABLE_FABRITIUS).select("count", count="exact")
            if search_params:
                count_query = self._apply_search_filters(count_query, search_params)
            count_response = count_query.execute()
            total_items = count_response.count
            total_pages = (total_items + items_per_page - 1) // items_per_page

            # Get data for current page
            data_query = self.client.table(self.TABLE_FABRITIUS).select(",".join(self.SEARCH_FIELDS['basic']))
            if search_params:
                data_query = self._apply_search_filters(data_query, search_params)
        
            response = data_query.range(start, end).execute()
                        
            logger.info(f"Retrieved {len(response.data)} artworks of {total_items} total")
            
            return {
                'items': response.data,
                'total_items': total_items,
                'total_pages': total_pages,
                'current_page': page
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch artworks: {e}")
            return {
                'items': [],
                'total_items': 0,
                'total_pages': 1,
                'current_page': page
            }

    def _apply_search_filters(self, query, search_params: dict):
        """Apply search filters to query.
    
        Handles two types of inventory number searches:
        1. Regular search: Uses ILIKE for partial matches
        2. Semantic search: Uses IN with list of inventory numbers from vector similarity
        
        Other fields use ILIKE for partial text matching.
        """
        try:
            #logger.debug(f"Applying search filters: {search_params}")
            
            if inv_nr := search_params.get('inventory_number'):
                
                # Vector search results come as a list of inventory numbers
                if isinstance(inv_nr, list):
                    # For semantic search results
                    query = query.in_('inventarisnummer', inv_nr)
                    logger.info(f"Vector search filter applied with {len(inv_nr)} matches")
                
                # Regular search uses partial text matching
                else:
                    query = query.ilike('inventarisnummer', f'%{inv_nr}%')
                    logger.info(f"Regular inventory search: {inv_nr}")

 
            # Text search filters
            if artist := search_params.get('artist'):
                query = query.ilike('beschrijving_kunstenaar', f'%{artist}%')
                logger.debug(f"Applied artist filter: {artist}")

            if title := search_params.get('title'):
                query = query.ilike('beschrijving_titel', f'%{title}%')
                logger.debug(f"Applied title filter: {title}")
            
            # Year range filter (assuming beschrijving_datering contains year info)
            if year_range := search_params.get('year_range'):
                min_year, max_year = year_range
                # Ensure integers (convert if needed)
                if min_year is not None:
                    min_year = int(min_year)
                if max_year is not None:
                    max_year = int(max_year)
                # Note: beschrijving_datering might be text like "1642" or "ca. 1640-1650"
                # For now, we'll do text-based filtering with ILIKE
                # TODO: Consider parsing years from text for more accurate filtering
                if min_year is not None:
                    query = query.gte('beschrijving_datering', str(min_year))
                if max_year is not None:
                    query = query.lte('beschrijving_datering', str(max_year))
                logger.debug(f"Applied year range filter: {min_year} - {max_year}")
            
            # Source filter (multiselect on collection source)
            if source := search_params.get('source'):
                if isinstance(source, list) and source:
                    # Assuming there's a 'source' or 'collection' field
                    # TODO: Verify actual field name in database
                    query = query.in_('bron', source)
                    logger.debug(f"Applied source filter: {source}")
             
            return query

        except Exception as e:
            logger.error(f"Error applying search filters: {e}")
            return query
    
    def get_artwork_metadata(self, inventory_number: str) -> Optional[Dict]:
        """Fetch full metadata for a single artwork."""
        try:
            response = (self.client
                       .table(self.TABLE_FABRITIUS)
                       .select("*")
                       .eq("inventarisnummer", inventory_number)
                       .single()
                       .execute())
            return response.data
            
        except Exception as e:
            logger.error(f"Failed to fetch metadata for {inventory_number}: {e}")
            return None
            
    def search_artworks(self, 
                       inventory_number: str = None,
                       artist: str = None,
                       title: str = None) -> List[Dict]:
        """Search artworks based on criteria."""
        try:
            query = self.client.table(self.TABLE_FABRITIUS).select("*")
            
            if inventory_number:
                query = query.ilike("inventarisnummer", f"%{inventory_number}%")
            if artist:
                query = query.or_(f"kunstenaar_voornaam.ilike.%{artist}%,kunstenaar_familienaam.ilike.%{artist}%")
            if title:
                query = query.ilike("beschrijving_titel", f"%{title}%")
                
            response = query.execute()
            return response.data
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def count_artworks(self) -> int:
        """Get total number of artworks in database."""
        try:
            response = self.client.table(self.TABLE_FABRITIUS).select("count", count="exact").execute()
            return response.count
        except Exception as e:
            logger.error(f"Failed to count artworks: {e}")
            return 0
        
    
    def vector_search(self, query_text: str, limit: int = 5) -> list:
        """Search artworks using vector similarity.
        
        Args:
            query_text: Text to search for
            limit: Maximum number of results to return
            
        Returns:
            List of artworks with similarity scores
        """
        try:
            # Generate embedding for query
            llm = LLMClient()
            query_embedding = llm.get_embedding(query_text)
            
            if not query_embedding:
                logger.error("Failed to generate embedding for query")
                return []
            
            # Call stored procedure through RPC
            response = (self.client.rpc('vector_search', {
                'query_embedding': query_embedding,
                'match_count': limit
            }).execute())
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return []
        

    
        

    def get_artwork_by_inventory(self, inventory_number: str) -> dict:
        """Fetch complete artwork record by inventory number."""
        try:
            response = (self.client.table("fabritius")
                    .select("*")
                    .eq('inventarisnummer', inventory_number)
                    .limit(1)
                    .execute())
            
            return response.data[0] if response.data else None
            
        except Exception as e:
            logger.error(f"Error fetching artwork details: {e}")
            return None
    


    #get available tags in fabritius
    def get_all_tags_fabritius(self, batch_size: int = 1000) -> List[str]:

        all_data = []
        offset = 0
        column = "label"

        while True: 
            #query with pagination
            response = (
                self.client
                .table(self.TABLE_TAGS)
                .select(column)
                .range(offset, offset + batch_size - 1)
                .execute()
            )

            data = response.data
            if not data:
                break
            all_data.extend(data)
            offset += batch_size

        #FIXME: sometimes "label" key is missing or it has a none value
        all_tags = [kv["label"] for kv in all_data if "label" in kv and kv["label"] is not None]
        return all_tags
    

    def fetch_artworks_by_label_and_prov(self, label, provenance, limit=20) -> List[Dict]:
        """
        Haal artworks die matchen met een bepaald label en een bepaalde provenance hebben.
        """
        #OLD: #.in_("label", labels) (multiselect)
        query = (
            self.client
            .table(self.VIEW_ARTWORK_WITH_TAGS)
            .select("*")
            .eq("label", label)
            .eq("provenance", provenance)
            .limit(limit)
            .execute()
        )
        return query.data if query.data else []
    

    def delete_tag_from_artworks(self, selected_ids):
        """
        Verwijder artwork-tag links
        """
        logger.debug(f"Geselecteerde werken/tags voor verwijdering: {selected_ids}")
        
        for item in selected_ids:
            inventarisnummer = item.get('inventarisnummer', None)
            tag = item.get('tag', None)
            tag_id = item.get('tag_id', None)

            if not inventarisnummer or not tag_id:
                logger.warning(f"Ongeldig item, sla over [kan niet verwijderen]: {item}")
                continue

            try:
                response = (
                    self.client
                    .table(self.TABLE_ARTWORK_TAGS)
                    .delete()
                    .eq("artwork_id", inventarisnummer)
                    .eq("tag_id", tag_id)
                    .execute()
                )
                if response.data:
                    logger.info(f"Verwijderde tag '{tag}' van werk '{inventarisnummer}'")
                else:
                    logger.error(f"Verwijderen mislukt voor tag '{tag}' van werk '{inventarisnummer}' (geen data terug)")
            except Exception as e:
                logger.error(f"Fout bij verwijderen tag '{tag}' van werk '{inventarisnummer}': {e}")
        return True
    
    def insert_new_tag(self, label: str) -> bool:
        """
        Voeg een nieuw label toe aan de tags-tabel.
        Returns True als succesvol, anders False.
        """
        try:
            response = (
                self.client
                .table(self.TABLE_TAGS)
                .insert({"label": label})
                .execute()
            )
            return bool(response.data)
        except Exception as e:
            # Optioneel: log de fout
            print(f"Fout bij toevoegen tag: {e}")
            return False
        
    def get_artworks_with_tag(self, inventarisnummers: list, tag_label: str) -> set:
        """
        Geeft een set van inventarisnummers waarvoor de opgegeven tag al bestaat.
        """
        if not inventarisnummers or not tag_label:
            return set()
        response = (
            self.client
            .table("artwork_with_tags_view")
            .select("inventarisnummer")
            .in_("inventarisnummer", inventarisnummers)
            .eq("label", tag_label)
            .execute()
        )
        if response.data:
            return set(row["inventarisnummer"] for row in response.data)
        return set()
    
    def get_tagID_by_label(self, label: str) -> int | None:
        """
        Haal het tag_id op voor een gegeven label uit de tags-tabel.
        Geeft None terug als het label niet bestaat.
        """
        response = (
            self.client
            .table(self.TABLE_TAGS)
            .select("id")
            .eq("label", label)
            .limit(1)
            .execute()
        )
        if response.data and len(response.data) > 0:
            return response.data[0]["id"]
        return None
    

    def insert_artwork_tag_link(self, inventarisnummer: str, tag_id: int, provenance: str) -> bool:
        """
        Voeg een link toe tussen een werk en een tag in de artwork-tags tabel.
        Returns True als succesvol, anders False.
        """
        #FIXME ik denk dat we meerdere keren dezelfde tag kunnen verbinden met een andere Provenance
        try:
            response = (
                self.client
                .table(self.TABLE_ARTWORK_TAGS)
                .insert({
                    "artwork_id": inventarisnummer,
                    "tag_id": tag_id,
                    "provenance": provenance
                })
                .execute()
            )
            return bool(response.data)
        except Exception as e:
            # Optioneel: log de fout
            print(f"Fout bij toevoegen artwork-tag link: {e}")
            return False
        


    def promote_artwork_tag_link(self, inventarisnummer: str, tag_id: int) -> bool:
        """
        Zet de provenance van een bestaande artwork-tag link op 'EXPERT'.
        """
        try:
            response = (
                self.client
                .table(self.TABLE_ARTWORK_TAGS)
                .update({"provenance": "EXPERT", "updated_at": "now()"})
                .eq("artwork_id", inventarisnummer)
                .eq("tag_id", tag_id)
                .eq("provenance", "AI")
                .execute()
            )
            return bool(response.data)
        except Exception as e:
            print(f"Fout bij promoten artwork-tag link: {e}")
            return False