# Tasks: PRISM Explainability & Reporting

**Input**: Design documents from `/specs/001-prism-platform/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md

**Organization**: Tasks are organized by user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Environment preparation and base structure

- [x] T001 [P] Install dependencies: shap, reportlab, matplotlib, scikit-learn
- [x] T002 [P] Create directory scripts/ at project root

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Model evaluation and utility functions

- [x] T003 Implement evaluate_model.py in scripts/evaluate_model.py
- [x] T004 Implement show_shap() function in app.py
- [x] T005 Implement generate_pdf_report() function in app.py

---

## Phase 3: User Story 1 - Clinical Scan Integration (Priority: P1) 🎯

**Goal**: Add SHAP and PDF reporting to the main diagnostic tab.

**Independent Test**: Perform an assessment and verify SHAP plot appears and PDF can be downloaded.

### Implementation for User Story 1

- [x] T006 [US1] Integrate show_shap() into tab1 of app.py
- [x] T007 [US1] Integrate generate_pdf_report() into tab1 with download button
- [x] T008 [US1] Update reportlab styles to match PRISM dark theme in generate_pdf_report()

---

## Phase 4: Polish & Cross-Cutting Concerns

- [x] T009 [P] Add unit test for PDF generation consistency in tests/test_reporting.py
- [x] T010 [P] Finalize evaluate_model.py output formatting for pitch deck screenshots

---

## Dependencies & Execution Order

### Phase Dependencies
- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Phase 1.
- **User Story 1 (Phase 3)**: Depends on Phase 2.
- **Polish (Phase 4)**: Depends on Phase 3 completion.

---

## Implementation Strategy

### MVP First
1. Complete Setup and Foundational (T001–T005).
2. Integrate into UI (T006–T007).
3. Run evaluation (T010) to get numbers for the pitch deck.

---

### Phase 5: Production Core ML Integration
- [x] T011 [P] Create prism/backend/core_ml/ for centralized model storage
- [x] T012 [P] Integrate prism_yamnet_audio.h5 into Sensing Layer
- [x] T013 [P] Integrate lstm_trajectory.pth into Projecting Layer
- [x] T014 [P] Integrate causal_explainer.pkl into Reasoning Layer
