
import os
import json
import math
from typing import List, Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.schema import HumanMessage, SystemMessage
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
# from langchain_community.embeddings import HuggingFaceEmbeddings
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.product import Product
from ..models.user import Supplier, Vendor
from ..schemas.chat import ChatResponse, RequirementExtraction, ProductMatch
from ..config.settings import settings
# from dotenv import load_dotenv
# load_dotenv()

class VendorGPTAgent:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=settings.google_api_key,
            temperature=0.3
        )
        
        
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=settings.google_api_key
        )
        
        self.vector_store = None
        self._setup_knowledge_base()
    
    def _setup_knowledge_base(self):
        """Setup RAG system with product and market knowledge"""
        knowledge_texts = [
            "Fresh vegetables like onions, tomatoes, potatoes are essential for street food vendors",
            "Quality indicators: Fresh vegetables should be firm, no dark spots, good color",
            "Pricing factors: Season, quality, quantity, location affect vegetable prices",
            "Storage tips: Keep vegetables in cool, dry place to maintain freshness",
            "Bulk buying advantages: Better prices for larger quantities, reduced frequent trips",
            "Local suppliers often provide fresher products and better prices",
            "Video verification helps ensure product quality before purchase",
            "Trust scores help vendors choose reliable suppliers",
            "Minimum order quantities vary by supplier and product type",
            "Delivery options depend on distance and order value",
            "Seasonal variations affect prices - onions cheaper in winter, tomatoes in summer",
            "Quality grades: Premium (A), Good (B), Basic (C) with different pricing",
            "Payment terms: Cash on delivery, advance payment for bulk orders",
            "Fresh produce should be consumed within 2-3 days for best quality",
            "Wholesale markets offer better prices but require larger quantities",
        ]
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=200,
            chunk_overlap=20
        )
        
        documents = text_splitter.create_documents(knowledge_texts)
        self.vector_store = FAISS.from_documents(documents, self.embeddings)
    
    def extract_requirements(self, message: str, language: str = "hindi") -> RequirementExtraction:
        """Extract structured requirements from vendor message"""
        system_prompt = f"""
        You are an AI assistant for street food vendors in India. Extract requirements from the vendor's message.
        The message might be in {language} or English.
        
        Extract the following information and return ONLY a JSON object:
        {{
            "product_name": "name of the vegetable/ingredient needed",
            "quantity": number (convert text to number),
            "unit": "kg, pieces, liter, etc.",
            "budget": number or null (in rupees),
            "urgency": "urgent, normal, or flexible",
            "quality_preference": "premium, good, or basic",
            "location_preference": "string or null",
            "confidence_score": number between 0-1
        }}
        
        Common Hindi terms mapping:
        - प्याज/pyaz = onions
        - टमाटर/tamatar = tomatoes  
        - आलू/aloo = potatoes
        - हरी मिर्च = green chilies
        - अदरक = ginger
        - लहसुन = garlic
        - धनिया = coriander
        - पुदीना = mint
        - किलो/kg = kg
        - रुपये/rupees = budget amount
        - चाहिए/chahiye = need
        - जल्दी = urgent
        - अच्छी गुणवत्ता = good quality
        
        Examples:
        "10 किलो प्याज चाहिए बजट 300" → {{"product_name": "onions", "quantity": 10, "unit": "kg", "budget": 300, "urgency": "normal", "quality_preference": "good", "confidence_score": 0.9}}
        "Need 5kg tomatoes urgently" → {{"product_name": "tomatoes", "quantity": 5, "unit": "kg", "budget": null, "urgency": "urgent", "quality_preference": "good", "confidence_score": 0.85}}
        
        Return ONLY the JSON object, no other text.
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Extract requirements from: {message}")
        ]
        
        try:
            response = self.llm(messages)
            extracted_data = json.loads(response.content)
            return RequirementExtraction(**extracted_data)
        except Exception as e:
            # Fallback extraction
            return self._fallback_extraction(message)
    
    def _fallback_extraction(self, message: str) -> RequirementExtraction:
        """Fallback extraction if JSON parsing fails"""
        message_lower = message.lower()
        
        # Product mapping
        product_map = {
            'onion': 'onions', 'प्याज': 'onions', 'pyaz': 'onions',
            'tomato': 'tomatoes', 'टमाटर': 'tomatoes', 'tamatar': 'tomatoes',
            'potato': 'potatoes', 'आलू': 'potatoes', 'aloo': 'potatoes',
            'chili': 'green chilies', 'मिर्च': 'green chilies', 'mirch': 'green chilies',
            'ginger': 'ginger', 'अदरक': 'ginger', 'adrak': 'ginger',
            'garlic': 'garlic', 'लहसुन': 'garlic', 'lahsun': 'garlic',
        }
        
        product_name = "vegetables"
        for key, value in product_map.items():
            if key in message_lower:
                product_name = value
                break
        
        # Extract quantity using regex
        import re
        quantity_match = re.search(r'(\d+(?:\.\d+)?)', message)
        quantity = float(quantity_match.group(1)) if quantity_match else 1.0
        
        # Extract budget
        budget_match = re.search(r'(?:budget|बजट|rupees|रुपये).{0,10}(\d+)', message_lower)
        budget = float(budget_match.group(1)) if budget_match else None
        
        # Extract urgency
        urgency = "urgent" if any(word in message_lower for word in ['urgent', 'जल्दी', 'jaldi']) else "normal"
        
        return RequirementExtraction(
            product_name=product_name,
            quantity=quantity,
            unit="kg",
            budget=budget,
            urgency=urgency,
            quality_preference="good",
            confidence_score=0.6
        )
    
    def generate_response(self, 
                         message: str, 
                         vendor_id: int, 
                         language: str,
                         db: Session) -> ChatResponse:
        """Generate conversational response with product suggestions"""
        
        # Extract requirements
        requirements = self.extract_requirements(message, language)
        
        # Get relevant context from vector store
        context_docs = self.vector_store.similarity_search(
            f"{requirements.product_name} {requirements.quantity} {language}",
            k=3
        )
        context = "\n".join([doc.page_content for doc in context_docs])
        
        # Find matching products
        matching_products = self._find_matching_products(requirements, vendor_id, db)
        
        # Generate response based on language
        language_prompts = {
            "hindi": {
                "system": f"""
                आप VendorBot हैं, भारतीय स्ट्रीट फूड वेंडर्स के लिए एक सहायक AI असिस्टेंट हैं।
                हिंदी में जवाब दें, दोस्ताना और समझदार रहें।
                
                बाजार की जानकारी:
                {context}
                
                वेंडर की आवश्यकता:
                - प्रोडक्ट: {requirements.product_name}
                - मात्रा: {requirements.quantity} {requirements.unit}
                - बजट: ₹{requirements.budget} (यदि बताया गया)
                
                {len(matching_products)} सप्लायर मिले हैं।
                
                उनकी जरूरत को समझते हुए मददगार जवाब दें और सप्लायर्स के बारे में बताएं।
                """,
                "no_results": "मुझे आपकी आवश्यकता के लिए कोई सप्लायर नहीं मिला। कृपया बजट बढ़ाएं या पास के क्षेत्र देखें।",
                "found_suppliers": f"मैंने आपके लिए {len(matching_products)} सप्लायर ढूंढे हैं:"
            },
            "english": {
                "system": f"""
                You are VendorBot, a helpful AI assistant for street food vendors in India.
                Respond in English, be friendly and understanding.
                
                Market information:
                {context}
                
                Vendor's requirement:
                - Product: {requirements.product_name}
                - Quantity: {requirements.quantity} {requirements.unit}
                - Budget: ₹{requirements.budget} (if specified)
                
                Found {len(matching_products)} suppliers.
                
                Provide a helpful response acknowledging their need and mentioning the suppliers found.
                """,
                "no_results": "I couldn't find any suppliers for your requirement. Please try increasing your budget or check nearby areas.",
                "found_suppliers": f"I found {len(matching_products)} suppliers for you:"
            }
        }
        
        current_lang = language_prompts.get(language, language_prompts["english"])
        
        if matching_products:
            messages = [
                SystemMessage(content=current_lang["system"]),
                HumanMessage(content=message)
            ]
            
            response = self.llm(messages)
            bot_response = response.content
        else:
            bot_response = current_lang["no_results"]
        
        # Generate suggestions
        suggestions = self._generate_suggestions(requirements, matching_products, language)
        
        return ChatResponse(
            response=bot_response,
            suggestions=suggestions,
            products=[self._format_product_for_response(p) for p in matching_products],
            requires_clarification=len(matching_products) == 0,
            extracted_requirements=requirements.dict()
        )
    
    def _find_matching_products(self, 
                               requirements: RequirementExtraction, 
                               vendor_id: int, 
                               db: Session) -> List[ProductMatch]:
        """Find products matching vendor requirements"""
        
        # Get vendor location
        vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
        if not vendor:
            return []
        
        # Build query
        query = db.query(Product, Supplier).join(Supplier, Product.supplier_id == Supplier.id)
        
        # Filter by product name (fuzzy matching)
        if requirements.product_name and requirements.product_name != "vegetables":
            search_terms = requirements.product_name.split()
            for term in search_terms:
                query = query.filter(Product.name.ilike(f"%{term}%"))
        
        # Filter by availability
        query = query.filter(
            and_(
                Product.is_available == True,
                Supplier.is_active == True,
                Product.available_quantity >= requirements.quantity,
                Product.minimum_order_quantity <= requirements.quantity
            )
        )
        
        # Filter by budget if specified
        if requirements.budget and requirements.budget > 0:
            max_price_per_unit = requirements.budget / requirements.quantity
            query = query.filter(Product.price_per_unit <= max_price_per_unit)
        
        results = query.all()
        
        # Format and filter by distance
        matching_products = []
        for product, supplier in results:
            distance = self._calculate_distance(
                vendor.latitude, vendor.longitude,
                supplier.latitude, supplier.longitude
            ) if all([vendor.latitude, vendor.longitude, supplier.latitude, supplier.longitude]) else 5.0
            
            if distance <= 25:  # 25km radius
                total_cost = product.price_per_unit * requirements.quantity
                
                product_match = ProductMatch(
                    product_id=product.id,
                    supplier_id=supplier.id,
                    supplier_name=supplier.business_name or supplier.name,
                    product_name=product.name,
                    price_per_unit=product.price_per_unit,
                    unit_type=product.unit_type,
                    available_quantity=product.available_quantity,
                    quality_score=product.quality_score,
                    trust_score=supplier.trust_score,
                    distance_km=round(distance, 1),
                    image_urls=json.loads(product.image_urls) if product.image_urls else [],
                    total_cost=round(total_cost, 2),
                    phone=supplier.phone
                )
                matching_products.append(product_match)
        
        # Sort by relevance (total cost, distance, trust score)
        matching_products.sort(
            key=lambda x: (x.total_cost, x.distance_km, -x.trust_score)
        )
        
        return matching_products[:5]  # Return top 5 matches
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates using Haversine formula"""
        if not all([lat1, lon1, lat2, lon2]):
            return 5.0
        
        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        
        return c * r
    
    def _generate_suggestions(self, 
                            requirements: RequirementExtraction, 
                            products: List[ProductMatch],
                            language: str) -> List[str]:
        """Generate helpful suggestions based on context"""
        suggestions = []
        
        if language == "hindi":
            if not products:
                suggestions.extend([
                    "अपना बजट थोड़ा बढ़ाकर देखें",
                    "पास के क्षेत्र में और सप्लायर देखें", 
                    "कम मात्रा में खरीदारी करके देखें"
                ])
            elif len(products) > 3:
                suggestions.extend([
                    "अलग-अलग सप्लायर की कीमत compare करें",
                    "ऑर्डर देने से पहले rating check करें",
                    "बड़े ऑर्डर के लिए video verification करें"
                ])
            else:
                min_price = min(p.price_per_unit for p in products) if products else 0
                suggestions.extend([
                    f"सबसे अच्छी कीमत: ₹{min_price}/{products[0].unit_type if products else 'kg'}",
                    "बेहतर deal के लिए सप्लायर से direct बात करें",
                    "खरीदारी के बाद rating जरूर दें"
                ])
        else:
            if not products:
                suggestions.extend([
                    "Try increasing your budget slightly",
                    "Check nearby areas for more suppliers",
                    "Consider buying in smaller quantities"
                ])
            elif len(products) > 3:
                suggestions.extend([
                    "Compare prices from different suppliers",
                    "Check supplier ratings before ordering",
                    "Consider video verification for large orders"
                ])
            else:
                min_price = min(p.price_per_unit for p in products) if products else 0
                suggestions.extend([
                    f"Best price: ₹{min_price}/{products[0].unit_type if products else 'kg'}",
                    "Contact supplier directly for better deals",
                    "Rate suppliers after purchase"
                ])
        
        return suggestions
    
    def _format_product_for_response(self, product: ProductMatch) -> Dict[str, Any]:
        """Format product match for API response"""
        return {
            "product_id": product.product_id,
            "supplier_id": product.supplier_id,
            "supplier_name": product.supplier_name,
            "product_name": product.product_name,
            "price_per_unit": product.price_per_unit,
            "unit_type": product.unit_type,
            "available_quantity": product.available_quantity,
            "quality_score": product.quality_score,
            "trust_score": product.trust_score,
            "distance_km": product.distance_km,
            "image_urls": product.image_urls,
            "total_cost": product.total_cost,
            "phone": product.phone
        }
