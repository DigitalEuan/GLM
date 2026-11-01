"""``glm_universal.knowledge`` -- the corpus as what the GLM knows.

The project's own text (the studies, the state documents, the Lean
development, the Python package, the JSON and CSV the instruments emit, and
the supplied material in ``source_material/``) read by rule into folder,
document, paragraph, sentence and token, and **counted, not trained**: every
figure is an integer with a witness sentence, and the counts grow with the
corpus (``studies/CORPUS_KNOWLEDGE_STUDY.md``; the module table is in
``README.md`` beside this file).

The sub-modules are imported by name (``from glm_universal.knowledge import
model``); importing the package itself loads nothing, so a caller that needs
only one reading never pays for the corpus walk or the cache.

*Created 31 October 2026 (repository check): the package had no
``__init__.py`` after the October 2026 reorganisation (it was importable only
as an implicit namespace package).*
"""
