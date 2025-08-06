"""
Schema人工复核模块
支持新发现的实体类型和关系类型的人工审核
"""

import json
import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

@dataclass
class ReviewItem:
    """复核项目"""
    item_id: str
    item_type: str  # "entity_type" or "relation_type"
    name: str
    description: str
    confidence: float
    examples: List[str]
    metadata: Dict[str, Any]
    status: str = "pending"  # pending, approved, rejected
    reviewer_notes: str = ""
    created_at: str = ""
    reviewed_at: str = ""

@dataclass
class ReviewSession:
    """复核会话"""
    session_id: str
    items: List[ReviewItem]
    created_at: str
    status: str = "active"  # active, completed, cancelled

class SchemaReviewer:
    """Schema复核器"""
    
    def __init__(self, review_storage_path: str = "review_storage"):
        self.storage_path = Path(review_storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.active_sessions = {}
        self._load_active_sessions()
    
    def submit_for_review(self, extraction_results: List[Dict]) -> str:
        """提交抽取结果供人工复核"""
        session_id = str(uuid.uuid4())[:8]
        review_items = []
        
        # 收集所有需要复核的项目
        for result in extraction_results:
            # 新实体类型
            for entity in result.get('new_entities', []):
                item = ReviewItem(
                    item_id=str(uuid.uuid4())[:8],
                    item_type="entity_type",
                    name=entity['name'],
                    description=entity['description'],
                    confidence=entity.get('confidence', 0.5),
                    examples=entity.get('examples', []),
                    metadata={
                        'chunk_id': result.get('chunk_id', ''),
                        'source': 'llm_extraction'
                    },
                    created_at=datetime.now().isoformat()
                )
                review_items.append(item)
            
            # 新关系类型
            for relation in result.get('new_relations', []):
                item = ReviewItem(
                    item_id=str(uuid.uuid4())[:8],
                    item_type="relation_type",
                    name=relation['name'],
                    description=relation['description'],
                    confidence=relation.get('confidence', 0.5),
                    examples=relation.get('examples', []),
                    metadata={
                        'subject_types': relation.get('subject_types', []),
                        'object_types': relation.get('object_types', []),
                        'chunk_id': result.get('chunk_id', ''),
                        'source': 'llm_extraction'
                    },
                    created_at=datetime.now().isoformat()
                )
                review_items.append(item)
        
        # 创建复核会话
        session = ReviewSession(
            session_id=session_id,
            items=review_items,
            created_at=datetime.now().isoformat()
        )
        
        self.active_sessions[session_id] = session
        self._save_session(session)
        
        return session_id
    
    def get_pending_reviews(self, session_id: Optional[str] = None) -> Dict:
        """获取待复核项目"""
        if session_id:
            session = self.active_sessions.get(session_id)
            if not session:
                return {"error": "Session not found"}
            
            pending_items = [
                asdict(item) for item in session.items 
                if item.status == "pending"
            ]
            
            return {
                "session_id": session_id,
                "total_items": len(session.items),
                "pending_items": pending_items,
                "session_status": session.status
            }
        else:
            # 返回所有活跃会话的待复核项目
            all_pending = []
            for session in self.active_sessions.values():
                if session.status == "active":
                    pending_items = [
                        asdict(item) for item in session.items 
                        if item.status == "pending"
                    ]
                    all_pending.extend(pending_items)
            
            return {
                "total_pending": len(all_pending),
                "items": all_pending,
                "active_sessions": list(self.active_sessions.keys())
            }
    
    def apply_review_decisions(self, session_id: str, decisions: Dict[str, Dict]) -> Dict:
        """应用人工复核决策"""
        session = self.active_sessions.get(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}
        
        approved_items = []
        rejected_items = []
        
        # 应用决策
        for item in session.items:
            if item.item_id in decisions:
                decision = decisions[item.item_id]
                item.status = decision.get('status', 'pending')
                item.reviewer_notes = decision.get('notes', '')
                item.reviewed_at = datetime.now().isoformat()
                
                # 可能的修改
                if 'modified_name' in decision:
                    item.name = decision['modified_name']
                if 'modified_description' in decision:
                    item.description = decision['modified_description']
                
                if item.status == "approved":
                    approved_items.append(item)
                elif item.status == "rejected":
                    rejected_items.append(item)
        
        # 检查会话是否完成
        pending_count = sum(1 for item in session.items if item.status == "pending")
        if pending_count == 0:
            session.status = "completed"
        
        self._save_session(session)
        
        return {
            "success": True,
            "session_id": session_id,
            "approved_count": len(approved_items),
            "rejected_count": len(rejected_items),
            "pending_count": pending_count,
            "session_status": session.status,
            "approved_items": [asdict(item) for item in approved_items]
        }
    
    def get_approved_schema_updates(self, session_id: str) -> Dict:
        """获取已批准的schema更新"""
        session = self.active_sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        approved_entities = []
        approved_relations = []
        
        for item in session.items:
            if item.status == "approved":
                if item.item_type == "entity_type":
                    approved_entities.append({
                        "name": item.name,
                        "description": item.description,
                        "examples": item.examples,
                        "confidence": item.confidence,
                        "metadata": item.metadata
                    })
                elif item.item_type == "relation_type":
                    approved_relations.append({
                        "name": item.name,
                        "description": item.description,
                        "subject_types": item.metadata.get('subject_types', []),
                        "object_types": item.metadata.get('object_types', []),
                        "confidence": item.confidence,
                        "metadata": item.metadata
                    })
        
        return {
            "session_id": session_id,
            "entity_types": approved_entities,
            "relation_types": approved_relations
        }
    
    def _save_session(self, session: ReviewSession):
        """保存复核会话"""
        session_file = self.storage_path / f"session_{session.session_id}.json"
        
        session_data = {
            "session_id": session.session_id,
            "created_at": session.created_at,
            "status": session.status,
            "items": [asdict(item) for item in session.items]
        }
        
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
    
    def _load_active_sessions(self):
        """加载活跃的复核会话"""
        if not self.storage_path.exists():
            return
        
        for session_file in self.storage_path.glob("session_*.json"):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if data.get('status') == 'active':
                    items = [
                        ReviewItem(**item_data) 
                        for item_data in data['items']
                    ]
                    
                    session = ReviewSession(
                        session_id=data['session_id'],
                        items=items,
                        created_at=data['created_at'],
                        status=data['status']
                    )
                    
                    self.active_sessions[session.session_id] = session
                    
            except Exception as e:
                print(f"加载会话文件失败 {session_file}: {e}")
    
    def get_review_statistics(self) -> Dict:
        """获取复核统计信息"""
        total_sessions = len(self.active_sessions)
        total_items = 0
        pending_items = 0
        approved_items = 0
        rejected_items = 0
        
        entity_type_stats = {"pending": 0, "approved": 0, "rejected": 0}
        relation_type_stats = {"pending": 0, "approved": 0, "rejected": 0}
        
        for session in self.active_sessions.values():
            for item in session.items:
                total_items += 1
                
                if item.status == "pending":
                    pending_items += 1
                elif item.status == "approved":
                    approved_items += 1
                elif item.status == "rejected":
                    rejected_items += 1
                
                # 按类型统计
                if item.item_type == "entity_type":
                    entity_type_stats[item.status] += 1
                elif item.item_type == "relation_type":
                    relation_type_stats[item.status] += 1
        
        return {
            "total_sessions": total_sessions,
            "total_items": total_items,
            "pending_items": pending_items,
            "approved_items": approved_items,
            "rejected_items": rejected_items,
            "entity_type_stats": entity_type_stats,
            "relation_type_stats": relation_type_stats
        }