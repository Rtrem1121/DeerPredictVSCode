# 🚀 Phase 4: Coverage & Quality - Quick Start Plan

**Date**: October 2, 2025  
**Status**: ⏳ **IN PROGRESS**

---

## 🎯 Quick Wins (Priority Order)

### 1. ✅ **Fix Duplicate File** (DONE)
- Removed `tests/test_frontend_validation.py` (duplicate)
- Kept `tests/integration/test_frontend_validation.py`

### 2. 🔄 **Get Coverage Baseline** (NEXT)
- Run: `pytest --cov=backend --cov-report=html -q`
- Target: Identify modules with <30% coverage
- Focus: Critical paths first

### 3. 🎯 **Quick Coverage Wins**
- Add tests for high-value, untested modules
- Focus on: prediction_service, bedding_zone_predictor, terrain_analyzer
- Goal: 40% → 70% coverage

### 4. 🔧 **Fix Minor Issues**
- Pydantic V2 migration (9 validators in scouting_models.py)
- Integration test timeout optimization
- Add missing docstrings

### 5. 📁 **Create Subdirectories**
- `tests/unit/biological/`
- `tests/unit/gee/`
- `tests/integration/api/`

---

## ⚡ Phase 4 Strategy

**Approach**: Fast iteration, high impact
- **Don't**: Try to test everything
- **Do**: Focus on critical prediction paths
- **Don't**: Spend hours on perfect coverage
- **Do**: Get to 70% quickly with smart test selection

**Timeline**: 2-3 hours (compressed from 4-6)

---

## 📊 Success Metrics

- [ ] 70%+ backend code coverage
- [ ] 100% critical path coverage (prediction flow)
- [ ] Pydantic warnings eliminated
- [ ] Subdirectories created
- [ ] Documentation updated

---

**Next Action**: Get coverage baseline in 30 seconds
