import json
import os
import re
import tempfile
from pathlib import Path

from backend.evidence_layer import EvidenceLayer
from backend.technical_intelligence_collector import TechnicalIntelligenceCollector
from backend.tool_knowledge_builder import ToolKnowledgeBuilder


class ToolCandidatePromoter:
    """Promote only validated, evidence-backed candidates into the Knowledge Base."""

    def __init__(self, knowledge_dir=None, min_samples=2, min_confidence=0.80):
        project_root = Path(__file__).resolve().parents[2]
        default_dir = project_root / "knowledge_base" / "tools"
        self.knowledge_dir = Path(knowledge_dir) if knowledge_dir else default_dir
        self.index_path = self.knowledge_dir / "tools_index.json"
        self.min_samples = int(min_samples)
        self.min_confidence = float(min_confidence)
        self.technical_collector = TechnicalIntelligenceCollector()
        self.knowledge_builder = ToolKnowledgeBuilder()
        self.evidence_layer = EvidenceLayer()

    def _slug(self, brand, model, variant=""):
        value = "_".join(part for part in [brand, model, variant] if str(part).strip())
        value = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_")
        return value.lower()

    def _build_default_knowledge(self, candidate):
        brand = str(candidate.get("brand", "")).strip()
        model = str(candidate.get("model", "")).strip()
        variant = str(candidate.get("variant", "")).strip()
        confidence = float(candidate.get("confidence", 0))
        evidence = candidate.get("evidence", [])
        market_data = candidate.get("market_data") if isinstance(candidate.get("market_data"), dict) else {}
        market_sample_count = int(market_data.get("sample_count", candidate.get("market_sample_count", 0)))
        technical_result = self.technical_collector.collect(candidate=candidate, description=candidate.get("description", ""), sources=candidate.get("technical_sources", []))
        technical_data = technical_result.get("technical", {}) if technical_result.get("success") else {}
        technical_sources = technical_result.get("technical_sources", []) if technical_result.get("success") else []
        sources = list(dict.fromkeys([*(["divar"] if market_data else []), *technical_sources, *([str(item).strip() for item in evidence if str(item).strip()] if isinstance(evidence, list) else [])]))
        market_status = "available" if market_data else "unavailable"
        return {"tool_name": f"{brand} {model}".strip(), "category": candidate.get("category", "toolbox"), "brand": brand, "aliases": list(dict.fromkeys([model, f"{brand} {model}".strip(), variant] if variant else [model, f"{brand} {model}".strip()])), "technical": technical_data, "brand_info": {"score": 0}, "market": {"new_price": market_data.get("new_price"), "used_price_min": market_data.get("used_price_min"), "used_price_max": market_data.get("used_price_max"), "median_price": market_data.get("median_price"), "sample_count": market_sample_count, "price_confidence": market_data.get("price_confidence", 0.0), "sources": market_data.get("sources", ["divar"] if market_data else []), "status": market_status, "last_updated": market_data.get("last_updated")}, "common_failures": candidate.get("common_failures", []), "inspection": candidate.get("inspection", []), "repair": candidate.get("repair", {}), "risk": candidate.get("risk", {"score": 50, "level": "Medium"}), "confidence": confidence, "sources": sources, "buy_score": candidate.get("buy_score", 50), "recommendation": candidate.get("recommendation", "REVIEW"), "discovery": {"variant": variant, "confidence": confidence, "evidence": evidence, "market_sample_count": market_sample_count, "technical_sources": technical_sources, "technical_confidence": technical_result.get("technical_confidence", "NONE")}}

    def _write_json_atomic(self, path, payload):
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
                handle.flush(); os.fsync(handle.fileno())
            os.replace(temp_name, path)
        except Exception:
            try: os.unlink(temp_name)
            except OSError: pass
            raise

    def _load_index(self):
        if not self.index_path.exists(): return {"tools": []}
        with self.index_path.open("r", encoding="utf-8") as handle: index = json.load(handle)
        if not isinstance(index, dict) or not isinstance(index.get("tools"), list): raise ValueError("tools_index.json must contain an object with a tools list")
        return index

    def promote(self, candidate, knowledge=None):
        if not isinstance(candidate, dict) or candidate.get("status") != "VALIDATED": return {"status": "REJECTED", "reason": "Candidate is not validated."}
        brand = str(candidate.get("brand", "")).strip(); model = str(candidate.get("model", "")).strip(); variant = str(candidate.get("variant", "")).strip(); evidence = candidate.get("evidence", []); market_data = candidate.get("market_data") if isinstance(candidate.get("market_data"), dict) else None
        try: confidence = float(candidate.get("confidence", 0))
        except (TypeError, ValueError): confidence = 0
        try: market_sample_count = int(market_data.get("sample_count", 0)) if market_data else 0
        except (TypeError, ValueError): market_sample_count = 0
        if not brand or not model: return {"status": "REJECTED", "reason": "Brand and model are required."}
        if confidence < self.min_confidence: return {"status": "REJECTED", "reason": "Discovery confidence is below promotion threshold."}
        if market_sample_count < self.min_samples: return {"status": "REJECTED", "reason": "Insufficient marketplace evidence for promotion."}
        if not isinstance(evidence, list) or not evidence: return {"status": "REJECTED", "reason": "Evidence is required for promotion."}
        if market_data is None or not market_data.get("valid"): return {"status": "REJECTED", "reason": "Validated market data is required for promotion."}
        technical_result = self.technical_collector.collect(candidate=candidate, description=candidate.get("description", ""), sources=candidate.get("technical_sources", []))
        technical_data = technical_result.get("technical", {}) if technical_result.get("success") else {}
        technical_sources = technical_result.get("technical_sources", []) if technical_result.get("success") else []
        evidence_result = self.evidence_layer.build(discovery={"confidence": confidence, "sources": evidence}, technical={"confidence": technical_result.get("technical_confidence", "NONE"), "sources": technical_sources, **technical_data}, market=market_data)
        if not evidence_result["sufficient"]: return {"status": "REJECTED", "reason": "Unified evidence is insufficient for promotion.", "evidence": evidence_result}
        tool_id = self._slug(brand, model, variant); filename = f"{tool_id}.json"; self.knowledge_dir.mkdir(parents=True, exist_ok=True); tool_path = self.knowledge_dir / filename
        try: index = self._load_index()
        except (OSError, ValueError, TypeError) as exc: return {"status": "REJECTED", "reason": "Knowledge index is invalid or unreadable.", "error": type(exc).__name__}
        tools = index["tools"]
        existing = next((item for item in tools if isinstance(item, dict) and item.get("id") == tool_id), None)
        if tool_path.exists() or existing:
            return {"status": "EXISTS", "tool_id": tool_id, "file": filename, "existing": existing}
        data = knowledge if isinstance(knowledge, dict) else self._build_default_knowledge(candidate)
        data["evidence"] = evidence_result; data["confidence"] = confidence; data.setdefault("sources", evidence_result.get("sources", [])); data["technical"] = technical_data; data.setdefault("discovery", {})["technical_sources"] = technical_sources; data["discovery"]["technical_confidence"] = technical_result.get("technical_confidence", "NONE"); data["discovery"]["technical_last_updated"] = technical_result.get("last_updated")
        technical_normalized = self.knowledge_builder.normalize_technical(data.get("technical", {}), technical_sources)
        if technical_normalized.get("success"): data["technical"] = technical_normalized["technical"]
        validation = self.knowledge_builder.build(data)
        if not validation["success"]: return {"status": "REJECTED", "reason": "Generated knowledge failed schema validation.", "errors": validation["errors"]}
        new_index = dict(index); new_tools = list(tools); new_tools.append({"id": tool_id, "name": f"{brand} {model}".strip(), "brand": brand, "category": data.get("category", "toolbox"), "file": filename, "aliases": data.get("aliases", [model, f"{brand} {model}".strip()])}); new_index["tools"] = new_tools
        tool_written = False
        try:
            self._write_json_atomic(tool_path, data); tool_written = True; self._write_json_atomic(self.index_path, new_index)
        except Exception as exc:
            if tool_written:
                try: tool_path.unlink()
                except OSError: pass
            return {"status": "REJECTED", "reason": "Knowledge Base persistence failed.", "error": type(exc).__name__}
        return {"status": "PROMOTED", "tool_id": tool_id, "file": filename, "evidence": evidence_result, "validation": validation}
