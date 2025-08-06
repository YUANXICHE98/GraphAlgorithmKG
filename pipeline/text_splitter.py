"""
文本切片器 - 简化版
将长文本切分为适合LLM处理的文本块
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class TextChunk:
    """文本块"""
    content: str
    chunk_id: str
    start_pos: int
    end_pos: int
    metadata: Dict[str, Any]

class TextSplitter:
    """文本切片器"""
    
    def __init__(self, max_tokens: int = 2000, overlap: int = 200):
        self.max_tokens = max_tokens
        self.overlap = overlap
        
        # 分割优先级：段落 > 句子 > 固定长度
        self.paragraph_separators = ['\n\n', '\n\n\n', '\r\n\r\n']
        self.sentence_separators = ['。', '！', '？', '.', '!', '?']
    
    def split_text(self, text: str) -> List[str]:
        """基础文本切分"""
        if len(text) <= self.max_tokens:
            return [text]
        
        chunks = []
        
        # 首先按段落分割
        paragraphs = self._split_by_paragraphs(text)
        
        current_chunk = ""
        
        for paragraph in paragraphs:
            # 如果当前段落太长，需要进一步分割
            if len(paragraph) > self.max_tokens:
                # 保存当前chunk
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                
                # 分割长段落
                sub_chunks = self._split_long_paragraph(paragraph)
                chunks.extend(sub_chunks)
                
            else:
                # 检查是否可以添加到当前chunk
                if len(current_chunk) + len(paragraph) <= self.max_tokens:
                    current_chunk += paragraph + "\n\n"
                else:
                    # 保存当前chunk，开始新chunk
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = paragraph + "\n\n"
        
        # 保存最后一个chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # 添加重叠
        if self.overlap > 0:
            chunks = self._add_overlap(chunks)
        
        return chunks
    
    def split_with_context(self, text: str, metadata: Optional[Dict] = None) -> List[TextChunk]:
        """带上下文信息的文本切分"""
        chunks = self.split_text(text)
        
        result = []
        for i, chunk_content in enumerate(chunks):
            # 计算位置信息
            start_pos = text.find(chunk_content[:100])  # 使用前100字符定位
            end_pos = start_pos + len(chunk_content) if start_pos >= 0 else -1
            
            chunk = TextChunk(
                content=chunk_content,
                chunk_id=f"chunk_{i}",
                start_pos=start_pos,
                end_pos=end_pos,
                metadata=metadata or {}
            )
            result.append(chunk)
        
        return result
    
    def _split_by_paragraphs(self, text: str) -> List[str]:
        """按段落分割文本"""
        # 尝试不同的段落分隔符
        for separator in self.paragraph_separators:
            if separator in text:
                paragraphs = text.split(separator)
                return [p.strip() for p in paragraphs if p.strip()]
        
        # 如果没有明显的段落分隔符，按单个换行符分割
        paragraphs = text.split('\n')
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _split_long_paragraph(self, paragraph: str) -> List[str]:
        """分割过长的段落"""
        if len(paragraph) <= self.max_tokens:
            return [paragraph]
        
        chunks = []
        
        # 首先尝试按句子分割
        sentences = self._split_by_sentences(paragraph)
        
        current_chunk = ""
        
        for sentence in sentences:
            if len(sentence) > self.max_tokens:
                # 句子本身太长，强制按长度分割
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                
                sub_chunks = self._split_by_length(sentence)
                chunks.extend(sub_chunks)
                
            else:
                if len(current_chunk) + len(sentence) <= self.max_tokens:
                    current_chunk += sentence
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _split_by_sentences(self, text: str) -> List[str]:
        """按句子分割文本"""
        # 使用正则表达式分割句子
        pattern = '([。！？.!?]+)'
        parts = re.split(pattern, text)
        
        sentences = []
        current_sentence = ""
        
        for part in parts:
            current_sentence += part
            if any(sep in part for sep in self.sentence_separators):
                sentences.append(current_sentence.strip())
                current_sentence = ""
        
        if current_sentence.strip():
            sentences.append(current_sentence.strip())
        
        return [s for s in sentences if s]
    
    def _split_by_length(self, text: str) -> List[str]:
        """按固定长度分割文本"""
        chunks = []
        
        for i in range(0, len(text), self.max_tokens - self.overlap):
            chunk = text[i:i + self.max_tokens]
            if chunk.strip():
                chunks.append(chunk.strip())
        
        return chunks
    
    def _add_overlap(self, chunks: List[str]) -> List[str]:
        """为文本块添加重叠"""
        if len(chunks) <= 1:
            return chunks
        
        overlapped_chunks = [chunks[0]]
        
        for i in range(1, len(chunks)):
            prev_chunk = chunks[i-1]
            current_chunk = chunks[i]
            
            # 从前一个chunk的末尾取overlap长度的文本
            if len(prev_chunk) > self.overlap:
                overlap_text = prev_chunk[-self.overlap:]
                # 尝试在句子边界处截断
                for sep in self.sentence_separators:
                    if sep in overlap_text:
                        overlap_text = overlap_text[overlap_text.rfind(sep)+1:]
                        break
                
                overlapped_chunk = overlap_text + "\n" + current_chunk
            else:
                overlapped_chunk = current_chunk
            
            overlapped_chunks.append(overlapped_chunk)
        
        return overlapped_chunks
    
    def get_splitting_stats(self, original_text: str, chunks: List[str]) -> Dict:
        """获取切分统计信息"""
        return {
            "original_length": len(original_text),
            "total_chunks": len(chunks),
            "avg_chunk_length": sum(len(chunk) for chunk in chunks) / len(chunks) if chunks else 0,
            "max_chunk_length": max(len(chunk) for chunk in chunks) if chunks else 0,
            "min_chunk_length": min(len(chunk) for chunk in chunks) if chunks else 0,
            "overlap_ratio": self.overlap / self.max_tokens if self.max_tokens > 0 else 0
        }
