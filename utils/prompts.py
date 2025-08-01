def get_location_analysis_prompt(context):
    return f"""
        Analyze this TikTok video content and extract comprehensive location information. Handle these edge cases:

        1. **Single Places**: One restaurant/business featured in the video
        2. **Multiple Places**: Area guides or videos featuring multiple locations
        3. **Popup Events**: Temporary events, markets, or limited-time restaurants
        4. **Carousel Content**: Multiple images with different text/locations per image
        5. **Market Vendors**: Individual vendors/stalls within food courts, farmer's markets, flea markets, night markets
        6. **Non-English Names**: Places with Chinese, Korean, Japanese, or other non-English names

        {context}

        **IMPORTANT**: Pay special attention to:
        - Chinese characters or non-English place names (e.g., 满小满, 老友记, etc.)
        - Market references ("inside [mall name] food court", "stall in", "vendor at", "farmer's market", "flea market", "night market")
        - Address information mentioned in hashtags or location descriptions
        - Mall, plaza, or market names that contain the individual vendors

        Extract information in this EXACT JSON format:
        {{
            "content_analysis": {{
                "content_type": "single_place|multiple_places|popup_event|area_guide",
                "confidence_score": 0.0-1.0,
                "primary_focus": "description of main subject"
            }},
            "places": [
                {{
                    "name": "Restaurant/Business Name",
                    "address": "Full address if mentioned",
                    "neighborhood": "Area/neighborhood",
                    "categories": ["restaurant", "chinese", "casual dining"],
                    "recommendations": "Specific menu items or recommendations",
                    "hours": "Opening hours or schedule",
                    "website": "Website URL if mentioned",
                    "is_popup": false,
                    "popup_details": {{
                        "duration": "how long the popup runs",
                        "host_location": "where the popup is hosted",
                        "event_type": "popup market|temporary restaurant|special event"
                    }}
                }}
            ],
            "area_info": {{
                "area_theme": "neighborhood food guide|shopping district|etc",
                "total_places_mentioned": 0,
                "area_description": "overall area description"
            }}
        }}

        **CRITICAL INSTRUCTIONS**:
        - For popups: Set is_popup=true and fill popup_details
        - For area guides: Set content_type="area_guide" and fill area_info
        - If no clear location info: Return empty places array
        - Use exact JSON format - no extra text or explanations
        - Extract specific menu items, not generic descriptions
        - Look for temporal indicators like "this weekend", "popup", "limited time"
        - DO NOT return generic names like "unnamed", "unknown", "restaurant", "cafe", "store", "business", etc.
        - Only return specific, identifiable business names with actual place names
        - If only generic descriptions are available, return the name as "establishment in location" (e.g., "Korean restaurant in Flushing")
        - ALWAYS extract Chinese/non-English place names - they are valid specific business names
        - For market vendors WITH specific names: Use the actual vendor name and include market address
        - For market vendors WITHOUT specific names: Format as directional location (e.g., "Corner Stall at Golden Mall Food Court", "Stand 5 at Union Square Farmer's Market", "Booth A12 at Brooklyn Flea")
        - When market/mall address is mentioned, use that as the address for individual vendors
        - Look for location clues in hashtags, descriptions, and 📍 location pins
        """
