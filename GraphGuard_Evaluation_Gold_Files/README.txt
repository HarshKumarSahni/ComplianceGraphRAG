GraphGuard Evaluation Gold Files

These files are for private benchmark evaluation only.

questions.json
- 14 benchmark questions
- Q1-Q10 are answerable
- Q11-Q14 are hallucination-containment tests
- Includes expected answers, keywords and source filenames

gold_entities.json
- Expected entities for Entity Extraction Precision/Recall/F1

gold_relationships.json
- Expected semantic relationships for optional relationship evaluation

questions_answers.csv
- Human-readable version of questions + expected answers

Use these inside backend/evaluation/.
Do not connect them to normal production upload/chat routes.
