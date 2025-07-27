
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import math

from ..models.product import Product
from ..models.user import Supplier, Vendor
from ..schemas.chat import RequirementExtraction

class MatchingEngine:
    def __init__(self):
        self.max_distance_km = 25
        self.price_tolerance = 0.15  # 15% price tolerance
        
    def find_best_matches(self, 
                         requirements: RequirementExtraction, 
                         vendor: Vendor, 
                         db: Session,
                         limit: int = 5) -> List[Dict[str, Any]]:
        """Find best matching suppliers for vendor requirements"""
        
        # Get base query
        query = self._build_base_query(requirements, db)
        
        # Apply filters
        query = self._apply_filters(query, requirements, vendor)
        
        # Get results
        results = query.all()
        
        # Score and rank results
        scored_results = []
        for product, supplier in results:
            score = self._calculate_match_score(product, supplier, vendor, requirements)
            if score > 0:
                result_data = self._format_result(product, supplier, vendor, requirements, score)
                scored_results.append(result_data)
        
        # Sort by score (descending)
        scored_results.sort(key=lambda x: x['match_score'], reverse=True)
        
        return scored_results[:limit]
    
    def _build_base_query(self, requirements: RequirementExtraction, db: Session):
        """Build base query for product search"""
        return db.query(Product, Supplier).join(
            Supplier, Product.supplier_id == Supplier.id
        )
    
    def _apply_filters(self, query, requirements: RequirementExtraction, vendor: Vendor):
        """Apply various filters to the query"""
        
        # Basic availability filters
        query = query.filter(
            and_(
                Product.is_available == True,
                Supplier.is_active == True,
                Product.available_quantity >= requirements.quantity
            )
        )
        
        # Product name filter (fuzzy matching)
        if requirements.product_name and requirements.product_name != "vegetables":
            search_terms = requirements.product_name.lower().split()
            name_conditions = []
            for term in search_terms:
                name_conditions.append(Product.name.ilike(f"%{term}%"))
                name_conditions.append(Product.category.ilike(f"%{term}%"))
            
            if name_conditions:
                query = query.filter(or_(*name_conditions))
        
        # Minimum order quantity filter
        query = query.filter(Product.minimum_order_quantity <= requirements.quantity)
        
        # Budget filter (with some tolerance)
        if requirements.budget and requirements.budget > 0:
            max_total_cost = requirements.budget * (1 + self.price_tolerance)
            max_price_per_unit = max_total_cost / requirements.quantity
            query = query.filter(Product.price_per_unit <= max_price_per_unit)
        
        # Quality preference filter
        if requirements.quality_preference == "premium":
            query = query.filter(Product.quality_score >= 4.0)
        elif requirements.quality_preference == "good":
            query = query.filter(Product.quality_score >= 3.0)
        
        return query
    
    def _calculate_match_score(self, 
                              product: Product, 
                              supplier: Supplier, 
                              vendor: Vendor, 
                              requirements: RequirementExtraction) -> float:
        """Calculate match score for a product-supplier combination"""
        
        score = 0.0
        max_score = 100.0
        
        # Distance score (30% weight)
        distance = self._calculate_distance(
            vendor.latitude, vendor.longitude,
            supplier.latitude, supplier.longitude
        )
        
        if distance <= self.max_distance_km:
            distance_score = max(0, (self.max_distance_km - distance) / self.max_distance_km * 30)
            score += distance_score
        else:
            return 0  # Too far away
        
        # Price score (25% weight)
        if requirements.budget and requirements.budget > 0:
            total_cost = product.price_per_unit * requirements.quantity
            if total_cost <= requirements.budget:
                price_score = max(0, (requirements.budget - total_cost) / requirements.budget * 25)
                score += price_score
            else:
                score += 5  # Small penalty for being over budget
        else:
            score += 15  # Neutral score when no budget specified
        
        # Quality score (20% weight)
        quality_score = (product.quality_score / 5.0) * 20
        score += quality_score
        
        # Supplier trust score (15% weight)
        trust_score = (supplier.trust_score / 5.0) * 15
        score += trust_score
        
        # Availability score (10% weight)
        if product.available_quantity >= requirements.quantity * 2:
            score += 10  # Bonus for high availability
        elif product.available_quantity >= requirements.quantity:
            score += 5   # Normal availability
        
        return min(score, max_score)
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance using Haversine formula"""
        if not all([lat1, lon1, lat2, lon2]):
            return 5.0  # Default distance if coordinates missing
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return c * 6371  # Radius of Earth in km
    
    def _format_result(self, 
                      product: Product, 
                      supplier: Supplier, 
                      vendor: Vendor, 
                      requirements: RequirementExtraction,
                      score: float) -> Dict[str, Any]:
        """Format search result for response"""
        
        distance = self._calculate_distance(
            vendor.latitude, vendor.longitude,
            supplier.latitude, supplier.longitude
        )
        
        total_cost = product.price_per_unit * requirements.quantity
        
        return {
            "product_id": product.id,
            "supplier_id": supplier.id,
            "supplier_name": supplier.business_name or supplier.name,
            "product_name": product.name,
            "category": product.category,
            "price_per_unit": product.price_per_unit,
            "unit_type": product.unit_type,
            "minimum_order_quantity": product.minimum_order_quantity,
            "available_quantity": product.available_quantity,
            "quality_score": product.quality_score,
            "trust_score": supplier.trust_score,
            "distance_km": round(distance, 1),
            "total_cost": round(total_cost, 2),
            "match_score": round(score, 1),
            "phone": supplier.phone,
            "image_urls": product.image_urls,
            "supplier_location": supplier.location,
            "delivery_available": distance <= 10,  # Delivery for distances <= 10km
            "video_verification_eligible": total_cost >= 1000
        }
